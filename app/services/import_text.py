# Text Parsing and Chunking Service
from ..core.config import MAX_CHUNKS_PER_DOCUMENT

import re


def clean_text(text):
    """
    Clean the text by removing unwanted characters and formatting.
    """
    # Remove unwanted characters and formatting
    cleaned_text = re.sub(r"[\n\t]+", " ", text)
    cleaned_text = re.sub(r" +", " ", cleaned_text)
    cleaned_text = cleaned_text.lower()

    return cleaned_text


def simple_tokenize(text):
    return re.findall(r"\b\w+\b", text)


def chunk_by_tokens(
    document_name, text, max_tokens=300, max_chunks=MAX_CHUNKS_PER_DOCUMENT
):
    """Split text into chunks by merging adjacent paragraphs until max_tokens is reached.
    Optionally limit total number of chunks.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for idx, para in enumerate(paragraphs):
        para = para.strip()
        para = clean_text(para)
        if not para:
            continue

        para_tokens = simple_tokenize(para)
        if current_tokens + len(para_tokens) > max_tokens:
            if current_chunk:
                chunks.append(
                    {
                        "document_name": document_name,
                        "chunk_index": idx,
                        "text": para,
                        "tokenized_para": current_chunk.strip(),
                    }
                )

                if max_chunks and len(chunks) >= max_chunks:
                    break
            current_chunk = para
            current_tokens = len(para_tokens)
        else:
            current_chunk += " " + para
            current_tokens += len(para_tokens)

    if current_chunk and (not max_chunks or len(chunks) < max_chunks):
        chunks.append(
            {
                "document_name": document_name,
                "chunk_index": idx,
                "text": para,
                "tokenized_para": current_chunk.strip(),
            }
        )

    return chunks
