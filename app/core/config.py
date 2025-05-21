import os

weaviate_api_key = os.environ["WEAVIATE_READONLY_KEY"]
weaviate_url = os.environ["WEAVIATE_URL"]
MAX_CHUNKS_PER_DOCUMENT = 200