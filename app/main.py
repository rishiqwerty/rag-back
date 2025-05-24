from fastapi import FastAPI, UploadFile, File, Depends, Form, Request
from contextlib import asynccontextmanager
from mangum import Mangum
from .services.ingestion import process_document
from .services.weaviate_client import client, create_schema
from sqlalchemy.orm import Session
from .core.database import engine, get_db
from .core import models
from .core.validator import TaskStatusCreate, QuestionRequest
from .core.config import development, SQS_QUEUE_URL
from .utils.upload_files_to_s3 import upload_file_to_s3
from .services.embedding import generate_embedding
from weaviate.classes.query import Filter

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
    print(f"Processing task_id: {doc_id}, file_path: {task.file_path}")
    if not task:
        return {"error": "Task not found"}
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
    db: Session = Depends(get_db),
):
    """
    Upload a document to send queue message for parsing and embedding.

    - Accepts a document file and the user's email.
    - Stores file locally or uploads to S3 based on environment.
    - Creates a processing task in the database.
    - Sends a task to SQS queue (in production) or
    processes it directly (in development).

    Returns the file name, processing status.
    """
    # If development is True, we will store the file locally
    if development:
        upload_dir = "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        local_file_path = upload_dir / file.filename

        with open(local_file_path, "wb") as f:
            f.write(await file.read())

        file_path = str(local_file_path)
    else:
        file_path = await upload_file_to_s3(file, user_email)

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
        process_document(task_id=db_task.task_id)
    else:
        sqs = boto3.client(
            "sqs",
        )

        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "task_id": db_task.task_id,
                }
            ),
        )
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
    ready = client.is_ready()
    return {"weaviate": ready}


@app.get("/task-status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the status of a document processing task.

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


handler = Mangum(app)
