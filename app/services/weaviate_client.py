from ..core.config import weaviate_url, weaviate_admin_api_key
import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
from weaviate.collections.classes.config import DataType, Property, Configure

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=wvc.init.Auth.api_key(weaviate_admin_api_key),
)


def create_schema():
    """
    Create the schema for the DocumentChunk class in Weaviate
    """
    # if "DocumentChunk" in client.collections.list_all():
    #     client.collections.delete("DocumentChunk")
    if "DocumentChunk" not in client.collections.list_all():
        client.collections.create(
            name="DocumentChunk",
            properties=[
                Property(
                    name="document_name", data_type=DataType.TEXT, index_searchable=True
                ),
                Property(name="chunk_index", data_type=DataType.INT),
                Property(name="text", data_type=DataType.TEXT),
                Property(name="page_number", data_type=DataType.TEXT),
            ],
            vectorizer_config=[
                Configure.NamedVectors.none(
                    name="custom_vector",
                    # vector_index_config=Configure.VectorIndex.hnsw()    # (Optional) Set vector index options
                )
            ],
        )
        client.close()


def store_chunks_in_weaviate(chunk_data):
    embedding = chunk_data.pop("embedding")
    client.collections.get("DocumentChunk").data.insert(
        properties=chunk_data,
        vector=embedding,
    )


def delete_existing_document_chunks(document_name):
    existing = client.collections.get("DocumentChunk").query.bm25(
        query=document_name, query_properties=["document_name"], limit=1
    )
    if existing and existing.objects:

        client.collections.get("DocumentChunk").data.delete_many(
            where=Filter.by_property("document_name").like(document_name), verbose=True
        )
