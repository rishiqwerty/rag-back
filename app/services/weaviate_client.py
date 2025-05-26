from ..core.config import weaviate_url, weaviate_admin_api_key
import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
from weaviate.collections.classes.config import (
    DataType,
    Property,
    Configure,
)


def get_client():
    # Connect to Weaviate Cloud
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=wvc.init.Auth.api_key(weaviate_admin_api_key),
    )


def create_schema():
    """
    Create the schema for the DocumentChunk class in Weaviate
    """
    client = get_client()
    # if "StructureJSONPlayer" in client.collections.list_all():
    #     print("Deleting existing StructureJSONPlayer collection...")
    #     client.collections.delete("StructureJSONPlayer")
    try:
        if "DocumentChunk" not in client.collections.list_all():
            client.collections.create(
                name="DocumentChunk",
                properties=[
                    Property(
                        name="document_name",
                        data_type=DataType.TEXT,
                        index_searchable=True,
                    ),
                    Property(name="chunk_index", data_type=DataType.INT),
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="page_number", data_type=DataType.TEXT),
                ],
                vectorizer_config=[Configure.NamedVectors.none(name="custom_vector")],
            )
        if "StructureJSONPlayer" not in client.collections.list_all():
            client.collections.create(
                name="StructureJSONPlayer",
                properties=[
                    Property(
                        name="document_name",
                        data_type=DataType.TEXT,
                        index_searchable=True,
                    ),
                    Property(name="customer_id", data_type=DataType.NUMBER),
                    Property(name="name", data_type=DataType.TEXT),
                    Property(name="age", data_type=DataType.NUMBER),
                    Property(name="membership", data_type=DataType.TEXT),
                    Property(name="purchases_last_6_months", data_type=DataType.NUMBER),
                    Property(name="preferred_category", data_type=DataType.TEXT),
                    Property(name="last_purchase_date", data_type=DataType.TEXT),
                    Property(name="nearest_store", data_type=DataType.TEXT),
                    Property(name="total_spent", data_type=DataType.NUMBER),
                ],
                vectorizer_config=[Configure.NamedVectors.none(name="custom_vector")],
            )

    except Exception as e:
        raise Exception(f"Error creating Weaviate schema: {e}")
    finally:
        client.close()


def store_chunks_in_weaviate(chunk_data: dict):
    """
    Store a document chunk in Weaviate.
    :param chunk_data: Dictionary containing the chunk data
        with 'embedding' key.
    """
    client = get_client()
    try:
        embedding = chunk_data.pop("embedding")
        client.collections.get("DocumentChunk").data.insert(
            properties=chunk_data,
            vector=embedding,
        )
    except Exception as e:
        raise Exception(f"Error storing chunk in Weaviate: {e}")
    finally:
        client.close()


def store_structured_json_in_weaviate(data: dict):
    """
    Store a StructureJSONPlayer in Weaviate.
    :param data: Dictionary containing the player data.
    """
    client = get_client()
    try:
        client.collections.get("StructureJSONPlayer").data.insert_many(
            data,
        )
    except Exception as e:
        raise Exception(f"Error storing StructureJSONPlayer in Weaviate: {e}")
    finally:
        client.close()


def delete_existing_document_chunks(document_name: str):
    """
    Delete existing document chunks in Weaviate for a given document name.
    """
    client = get_client()
    try:
        existing = client.collections.get("DocumentChunk").query.bm25(
            query=document_name, query_properties=["document_name"], limit=1
        )
        if existing and existing.objects:

            client.collections.get("DocumentChunk").data.delete_many(
                where=Filter.by_property("document_name").like(document_name),
                verbose=True,
            )

    except Exception as e:
        raise Exception(f"Error deleting existing document chunks: {e}")
    finally:
        client.close()


def delete_existing_json_agg(document_name: str):
    """
    Delete existing json player object in Weaviate for a given document name.
    """
    client = get_client()
    try:
        existing = client.collections.get("StructureJSONPlayer").query.bm25(
            query=document_name, query_properties=["document_name"], limit=1
        )
        if existing and existing.objects:

            client.collections.get("StructureJSONPlayer").data.delete_many(
                where=Filter.by_property("document_name").like(document_name),
                verbose=True,
            )

    except Exception as e:
        raise Exception(f"Error deleting existing document chunks: {e}")
    finally:
        client.close()
