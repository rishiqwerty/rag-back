from fastapi import FastAPI, UploadFile, File, Depends, Form
from contextlib import asynccontextmanager
from mangum import Mangum
from .services.ingestion import process_document
from .services.weaviate_client import get_client, create_schema
from sqlalchemy.orm import Session
from .core.database import engine, get_db
from .core import models
from .core.validator import (
    AggregationResult,
    TaskStatusCreate,
    QuestionRequest,
    AggregationResponse,
)
from .core.config import development, SQS_QUEUE_URL
from .utils.upload_files_to_s3 import upload_file_to_s3
from .services.embedding import generate_embedding
from .middleware import add_cors_middleware
from weaviate.classes.query import Filter
import weaviate.classes as wvc

import json
import boto3

# from slowapi import Limiter, _rate_limit_exceeded_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan event handler to create the database tables
    and Weaviate schema
    """
    models.Base.metadata.create_all(bind=engine)
    create_schema()

    yield


app = FastAPI(lifespan=lifespan)

add_cors_middleware(app)


@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running
    """
    return {"Hello": "World"}


@app.post("/document/query")
def answer_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Endpoint to answer questions based on the document
    chunks stored in Weaviate.

    args:
        request (QuestionRequest): The request containing the
            question and task ID.
        db (Session): The database session dependency.
    returns:
        dict: A dictionary containing the answers to the question.
    """
    question_vec = generate_embedding([{"text": request.question}])
    doc_id = request.task_id
    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == doc_id).first()
    )
    if not task:
        return {"error": "Task not found"}
    with get_client() as client:
        results = client.collections.get("DocumentChunk").query.near_vector(
            near_vector=question_vec[0].embedding,
            filters=Filter.by_property("document_name").like(task.file_path),
            limit=3,
        )
        answers = [obj.properties["text"] for obj in results.objects]
    return {"answers": answers}


@app.post("/upload-document")
async def doc_upload(
    file: UploadFile = File(...),
    user_email: str = Form(...),
    structured_json: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    Upload a document to send queue message for parsing and embedding.

    - Accepts a document file and the user's email.
    - Stores file locally or uploads to S3 based on environment.
    - Creates a processing task in the database.
    - Sends a task to SQS queue (in production) or
    processes it directly (in development).

    args:
        - **file**: The document file to be uploaded.
        - **user_email**: The email of the user uploading the document.
        - **structured_json**: Whether to process the document as structured JSON.
    Returns the file name, processing status.
    """
    try:
        file_path = await upload_file_to_s3(file, user_email)
    except Exception as e:
        return {"error": f"Failed to upload file: {str(e)}"}

    validated = TaskStatusCreate(
        file_name=file.filename, user_email=user_email, file_path=file_path
    )
    existing_task = (
        db.query(models.TaskStatus)
        .filter(
            models.TaskStatus.file_path == file_path,
            models.TaskStatus.user_email == user_email,
        )
        .first()
    )
    if existing_task:
        existing_task.status = "processing"
        db_task = existing_task
    else:
        db_task = models.TaskStatus(
            file_name=validated.file_name,
            user_email=validated.user_email,
            status="processing",
            file_path=file_path,
        )
        db.add(db_task)
    db.commit()
    db.refresh(db_task)
    if development:
        # For local development, process the document synchronously
        process_document(task_id=db_task.task_id, structured_json=str(structured_json))
    else:
        sqs = boto3.client(
            "sqs",
        )
        try:
            sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(
                    {
                        "task_id": db_task.task_id,
                        "structured_json": str(structured_json),
                    }
                ),
            )
        except Exception as e:
            db_task.status = "failed"
            db_task.error_message = f"Failed to send message to SQS: {str(e)}"
            db.commit()
            db.refresh(db_task)
            return {"error": f"Failed to send message to SQS: {str(e)}"}
    return {
        "Status": "Processing",
        "task_id": db_task.task_id,
    }


@app.get("/health")
def test():
    """
    Health check endpoint

    Verifies the readiness of the Weaviate client.
    """
    with get_client() as client:
        ready = client.is_ready()
    return {"weaviate": ready}


@app.get("/task-status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the status of a document processing task.
    Whether the parsing and embedding of the document
    has been completed or is still in progress.
    - **task_id**: The task ID to check.

    Returns the task ID and its current status.
    """
    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == task_id).first()
    )
    if not task:
        return {"error": "Task not found"}
    return {"task_id": task.task_id, "status": task.status}


@app.get("/users/tasks/{user_email}")
def get_users_tasks(user_email: str, db: Session = Depends(get_db)):
    """
    Retrieve all tasks for a specific user.

    - **user_email**: The email of the user whose tasks are to be retrieved.

    Returns a list of tasks associated with the user.
    """
    tasks = (
        db.query(models.TaskStatus)
        .filter(models.TaskStatus.user_email == user_email)
        .all()
    )
    return tasks


@app.post("/users/task/json-aggregator", response_model=AggregationResponse)
def json_data_aggregator(
    task_id: str,
    field: str,
    db: Session = Depends(get_db),
):
    """
    Custom JSON data aggregator for Weaviate queries.
    Get sum, maximum, minimum, mean, and count of a specified field
    for a given task ID.
    - **task_id**: The ID of the task to query.
    - **field**: The field to aggregate (e.g., "score").
    Returns a dictionary with the aggregated results.
    """
    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == task_id).first()
    )
    if not task:
        return {"error": "Task not found"}
    try:
        with get_client() as client:
            agg_result = client.collections.get(
                "StructureJSONPlayer"
            ).aggregate.over_all(
                total_count=True,
                filters=Filter.by_property("document_name").like(task.file_path),
                return_metrics=wvc.query.Metrics(field).integer(
                    count=True,
                    maximum=True,
                    minimum=True,
                    mean=True,
                    sum_=True,
                ),
            )
            max_user_details = client.collections.get(
                "StructureJSONPlayer"
            ).query.fetch_objects(
                filters=(
                    Filter.by_property("document_name").like(task.file_path)
                    & Filter.by_property(field).equal(
                        agg_result.properties[field].maximum
                    )
                )
            )
            min_user_details = client.collections.get(
                "StructureJSONPlayer"
            ).query.fetch_objects(
                filters=(
                    Filter.by_property("document_name").like(task.file_path)
                    & Filter.by_property(field).equal(
                        agg_result.properties[field].minimum
                    )
                )
            )
            max_user_data = []
            if max_user_details and max_user_details.objects:
                for obj in max_user_details.objects:
                    max_user_data.append(obj.properties)
            min_user_data = []
            if min_user_details and min_user_details.objects:
                for obj in min_user_details.objects:
                    min_user_data.append(obj.properties)

        output = AggregationResult(
            count=agg_result.total_count,
            maximum=agg_result.properties[field].maximum,
            minimum=agg_result.properties[field].minimum,
            mean=agg_result.properties[field].mean,
            total=agg_result.properties[field].sum_,
            max_user_details=max_user_data,
            min_user_details=min_user_data,
        )

    except Exception as e:
        return {
            "task_id": task_id,
            "field": field,
            "error": f"Facing some issue with weaviate please try again later {str(e)}",
        }

    return {"task_id": task_id, "field": field, "output": output}


handler = Mangum(app)  # For AWS Lambda compatibility
