from openai import OpenAI

def generate_embedding(text: list[dict]) -> list:
    """
    Generate an embedding for the given text using OpenAI's API.

    Args:
        text (list[dict]): A list of dictionaries containing text to be embedded.

    Returns:
        list: The generated embedding.
    """
    client = OpenAI()

    response = client.embeddings.create(
        input=[t["text"] for t in text],
        model="text-embedding-3-small"
    )
    embedding = response.data
    # model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return embedding