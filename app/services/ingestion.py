import json
import os
from app.utils.json_helper import validate_player_json
import boto3
from app.core.config import BUCKET_NAME, development
from app.core import models
from app.core.database import get_db
from app.services.embedding import generate_embedding
from app.services.import_text import chunk_by_tokens
from app.services.parser import parse_docx, parse_json, parse_pdf, parse_text
from app.services.weaviate_client import (
    delete_existing_document_chunks,
    delete_existing_json_agg,
    store_chunks_in_weaviate,
    store_structure_json_player,
)
import datetime


def mark_task_as_failed(task: models.TaskStatus, error_message: str):
    """
    Mark the task as failed and update the error message.
    :param task: TaskStatus object
    :param error_message: Error message to be stored
    """
    task.status = "failed"
    task.error_message = error_message
    task.completed_at = datetime.datetime.now(datetime.timezone.utc)


def get_file_from_s3(file_key: str):
    """
    Downloads a file from S3 to a local path.
    :param s3_key: S3 file key in the format 'path/to/file.txt'
    :return: Local file path
    """
    error = ""
    local_path = f"/tmp/{file_key}"
    local_dir = os.path.dirname(local_path)
    os.makedirs(local_dir, exist_ok=True)

    s3 = boto3.client("s3")
    try:
        s3.download_file(BUCKET_NAME, file_key, local_path)
    except Exception as e:
        error = f"Error downloading file from S3: {e}"
        raise Exception(error)
    finally:
        s3.close()

    return local_path


def process_document(task_id: int, structured_json: str = None):
    """
    THis function will contain pdf/doc file, will call chunk_text function and
    then call the embedding function to generate the embedding for each chunk.
    Process the document and store the chunks in Weaviate.
    """

    db = next(get_db())

    task = (
        db.query(models.TaskStatus).filter(models.TaskStatus.task_id == task_id).first()
    )

    try:
        file_path = (
            get_file_from_s3(task.file_path) if not development else task.file_path
        )
        delete_existing_document_chunks(task.file_path)

        if structured_json and structured_json == "True":
            delete_existing_json_agg(task.file_path)
            structured_json_parse(file_path, s3_key=task.file_path)

        chunks = parse_and_chunk_document(file_path, s3_key=task.file_path)
        _embedded = batch_embedding_for_chunks(chunks)
        for i in _embedded:
            store_chunks_in_weaviate(i)

        task.status = "completed"
        task.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(task)

    except Exception as e:
        # Handle any errors by marking the task as failed
        mark_task_as_failed(task, str(e))
        db.commit()
        db.refresh(task)
        raise Exception(f"Error processing document: {e}")

    finally:
        db.close()


def batch_embedding_for_chunks(chunks):
    """
    Generate an embedding for the given chunk of text.
    """

    embedding = generate_embedding(chunks)

    for i, embedding_info in enumerate(embedding):
        chunks[i]["embedding"] = embedding_info.embedding

    return chunks


def parse_and_chunk_document(file_path: str, s3_key: str = None) -> list:
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
    elif ext == ".json":
        text = parse_json(file_path=file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    max_tokens = 100 if len(text) < 1000 else 200
    chunks = chunk_by_tokens(s3_key, text, max_tokens=max_tokens)

    return chunks


def structured_json_parse(file_path: str, s3_key: str):
    """
    Parse a structured JSON file and store the data in Weaviate.
    :param file_path: Path to the structured JSON file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                data["document_name"] = s3_key
                store_structure_json_player(data)
                validate_player_json(data)
            else:
                for item in data:
                    validate_player_json(item)
                    item["document_name"] = s3_key
                    store_structure_json_player(item)
    except Exception as e:
        raise Exception(f"Error parsing structured JSON: {e}")
