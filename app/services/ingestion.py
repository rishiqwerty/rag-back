
from app.services.import_text import parse_pdf, chunk_by_tokens


def process_document(document):
    """
    Process the document and extract relevant information.
    """
    # Placeholder for document processing logic
    # This could involve text extraction, summarization, etc.
    # processed_data = {
    #     "title": document.get("title"),
    #     "content": document.get("content"),
    #     "metadata": document.get("metadata"),
    # }
    # return processed_data
    pass

def chunk_text():
    """
    Chunk the text into smaller pieces for processing.
    
    Args:
        text (str): The text to chunk.
        chunk_size (int): The size of each chunk.
    
    Returns:
        list: A list of text chunks.
    """
    # Placeholder for text chunking logic
    # chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    # return chunks
    text = parse_pdf()
    chunks = chunk_by_tokens(text, max_tokens=150)
    return chunks
    print(f"Ingesting {len(chunks)} chunks for this document.")


