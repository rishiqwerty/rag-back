import os
import boto3
from app.core.config import BUCKET_NAME
from app.core import models
from app.core.database import get_db
from app.services.embedding import generate_embedding
from app.services.import_text import chunk_by_tokens
from app.services.parser import parse_docx, parse_pdf, parse_text
from app.services.weaviate_client import (
    delete_existing_document_chunks,
    store_chunks_in_weaviate,
)


def get_file_from_s3(file_key: str):
    """
    Downloads a file from S3 to a local path.
    :param s3_key: S3 file key in the format 'path/to/file.txt'
    :return: Local file path
    """

    local_path = f"/tmp/{file_key}"
    local_dir = os.path.dirname(local_path)
    os.makedirs(local_dir, exist_ok=True)

    s3 = boto3.client("s3")
    try:
        s3.download_file(BUCKET_NAME, file_key, local_path)
    except Exception as e:
        raise RuntimeError(f"Failed to download file from S3: {e}")

    return local_path


def process_document(task_id: int):
    """
    THis function will contain pdf/doc file, will call chunk_text function
    and then call the embedding function to generate the embedding for each chunk.
    Process the document and store the chunks in Weaviate.
    """

    db = next(get_db())

    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == task_id).first()
    )
    print(f"Processing file_path: {task.file_path}")
    file_path = get_file_from_s3(task.file_path)

    delete_existing_document_chunks(task.file_name)
    chunks = parse_and_chunk_document(file_path, task.file_name)
    _embedded = batch_embedding_for_chunks(chunks)
    for i in _embedded:
        store_chunks_in_weaviate(i)

    task.status = "completed"
    db.commit()
    db.refresh(task)
    db.close()


def batch_embedding_for_chunks(chunks):
    """
    Generate an embedding for the given chunk of text.
    """

    embedding = generate_embedding(chunks)

    for i, embedding_info in enumerate(embedding):
        chunks[i]["embedding"] = embedding_info.embedding

    return chunks


def parse_and_chunk_document(file_path: str):
    """
    Chunk the text into smaller pieces for processing.

    Args:
        file_path (str): The path to the file.

    Returns:
        list: A list of text chunks.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = parse_pdf(file_path=file_path)
    elif ext == ".docx":
        text = parse_docx(file_path=file_path)
    elif ext == ".txt":
        text = parse_text(file_path=file_path)
    else:
        raise ValueError("Unsupported file type")
    chunks = chunk_by_tokens(file_path, text)

    return chunks
