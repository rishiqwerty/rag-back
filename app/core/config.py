import os

use_local = False  # Set to True if running locally non openai
weaviate_api_key = os.environ.get("WEAVIATE_READONLY_KEY")
weaviate_admin_api_key = (
    os.environ.get("WEAVIATE_ADMIN_KEY")
    if use_local
    else os.environ.get("WEAVIATE_OPENAI_ADMIN_KEY")
)
weaviate_url = (
    os.environ.get("LOCAL_EMBEDDING_WEAVIATE_URL")
    if use_local
    else os.environ.get("WEAVIATE_URL")
)
DATABASE_URL = os.environ.get("PROD_DATABASE_URL", "sqlite:///./app.db")
MAX_CHUNKS_PER_DOCUMENT = 200

USE_S3 = os.environ.get("USE_S3", "False").lower() == "true"
BUCKET_NAME = os.environ.get("BUCKET_NAME", "rag_backend")
FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB
development = os.environ.get("DEVELOPMENT", "False").lower() == "true"
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
