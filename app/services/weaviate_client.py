from ..core.config import weaviate_url, weaviate_api_key
import weaviate
from weaviate.classes.init import Auth
from weaviate.vectorizer import Configure

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    vectorizer_config=[
        Configure.NamedVectors.text2vec_openai(
            name="title_vector",
            source_properties=["title"]
        )
    ]
)

print(client.is_ready())