from fastapi import FastAPI, UploadFile, File, Depends, Form, Request
from mangum import Mangum
from .services.ingestion import process_document, async_process_document
from .services.weaviate_client import client, create_schema
from sqlalchemy.orm import Session
from .core.database import engine, get_db
from .core import models
from .core.validator import TaskStatusCreate
from .core.config import development
from .utils.upload_files_to_s3 import upload_file_to_s3

# from slowapi import Limiter, _rate_limit_exceeded_handler

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
handler = Mangum(app)


create_schema()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/questions")
def read_questions():
    a = "Name of the Cheif ethics counciler"

    from .services.embedding import generate_embedding

    # 1. Embed the question
    question_vec = generate_embedding([{"text": a}])

    # 2. Query Weaviate for similar chunks
    results = client.collections.get("DocumentChunk").query.near_vector(
        near_vector=question_vec[0].embedding,
        limit=3,  # Return top 3 relevant chunks
    )
    # 3. Collect the most relevant texts
    answers = [obj.properties["text"] for obj in results.objects]
    print(len(answers))
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
        async_process_document(task_id=db_task.task_id)
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
    return {"status": ready}


@app.get("/task-status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == task_id).first()
    )
    if not task:
        return {"error": "Task not found"}
    return {"task_id": task.task_id, "status": task.status}
