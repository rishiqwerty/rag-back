import openai
from openai import OpenAI


def generate_embedding(text: list[dict]) -> list:
    """
    Generate an embedding for the given text using OpenAI's API.

    Args:
        text (list[dict]): A list of dictionaries containing
            text to be embedded.

    Returns:
        list: The generated embedding.
    """
    # model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    client = OpenAI()
    try:
        response = client.embeddings.create(
            input=[t["text"] for t in text], model="text-embedding-3-small"
        )
        embedding = response.data
        return embedding

    except openai.APIConnectionError as e:
        raise Exception(f"API connection error: {e}")
    except openai.RatelimitError as e:
        raise Exception(f"API connection error: {e}")
    except Exception as e:
        raise Exception(f"API connection error: {e}")
