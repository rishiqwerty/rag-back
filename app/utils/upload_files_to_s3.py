import io
import boto3
from fastapi import UploadFile
import os

from ..core.config import USE_S3, FILE_SIZE_LIMIT, BUCKET_NAME


async def upload_file_to_s3(file: UploadFile, user_email: str):
    contents = await file.read()
    if len(contents) > FILE_SIZE_LIMIT:
        raise ValueError("File size exceeds the limit of 5MB.")
    if USE_S3:
        s3 = boto3.client("s3")
        s3_key = f"{user_email}/{file.filename}"
        s3.upload_fileobj(io.BytesIO(contents), BUCKET_NAME, s3_key)
        file_location = s3_key
    else:
        # Local storage
        upload_dir = f"uploaded_files/{user_email}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        file_location = file_path
    return file_location
