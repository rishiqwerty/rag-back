import os

use_local = False
weaviate_api_key = os.environ["WEAVIATE_READONLY_KEY"]
weaviate_admin_api_key = (
    os.environ["WEAVIATE_ADMIN_KEY"]
    if use_local
    else os.environ["WEAVIATE_OPENAI_ADMIN_KEY"]
)
weaviate_url = (
    os.environ["LOCAL_EMBEDDING_WEAVIATE_URL"]
    if use_local
    else os.environ["WEAVIATE_URL"]
)
DATABASE_URL = os.environ.get("PROD_DATABASE_URL", "sqlite:///./app.db")
MAX_CHUNKS_PER_DOCUMENT = 200

USE_S3 = os.environ.get("USE_S3", "False").lower() == "true"
BUCKET_NAME = os.environ.get("BUCKET_NAME", "rag_backend")
FILE_SIZE_LIMIT = 5 * 1024 * 1024  # 5MB
development = os.environ.get("DEVELOPMENT", "False").lower() == "true"
