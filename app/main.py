from fastapi import FastAPI, UploadFile, File, Depends, Form, Request
from mangum import Mangum
from .services.ingestion import process_document
from .services.weaviate_client import client, create_schema
from sqlalchemy.orm import Session
from .core.database import engine, get_db
from .core import models
from .core.validator import TaskStatusCreate, QuestionRequest
from .core.config import development
from .utils.upload_files_to_s3 import upload_file_to_s3
from .services.embedding import generate_embedding
from weaviate.classes.query import Filter

import json
import boto3

# from slowapi import Limiter, _rate_limit_exceeded_handler

app = FastAPI()


@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)
    create_schema()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/document/questions")
def read_questions(request: QuestionRequest, db: Session = Depends(get_db)):
    question_vec = generate_embedding([{"text": request.question}])
    doc_id = request.task_id
    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == doc_id).first()
    )
    if not task:
        return {"error": "Task not found"}
    results = client.collections.get("DocumentChunk").query.near_vector(
        near_vector=question_vec[0].embedding,
        filters=Filter.by_property("document_name").like(task.file_path),
        limit=3,
    )
    answers = [obj.properties["text"] for obj in results.objects]
    return {"answers": answers}


@app.post("/upload")
async def doc_upload(
    file: UploadFile = File(...),
    user_email: str = Form(...),
    db: Session = Depends(get_db),
):
    file_path = await upload_file_to_s3(file, user_email)

    validated = TaskStatusCreate(
        file_name=file.filename, user_email=user_email, file_path=file_path
    )
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

        queue_url = (
            "https://sqs.us-east-1.amazonaws.com/576394207135/DocumentVectorQueue"
        )
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(
                {
                    "task_id": db_task.task_id,
                }
            ),
        )
    return {
        "filename": file.filename,
        "Status": "Processing",
        "task_id": db_task.task_id,
    }


@app.get("/health")
def test():
    """
    Health check endpoint
    """
    ready = client.is_ready()
    return {"weaviate": ready}


@app.get("/task-status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == task_id).first()
    )
    if not task:
        return {"error": "Task not found"}
    return {"task_id": task.task_id, "status": task.status}


handler = Mangum(app)
