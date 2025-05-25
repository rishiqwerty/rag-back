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
    document_name, text, max_tokens=150, max_chunks=MAX_CHUNKS_PER_DOCUMENT
):
    """Efficiently split text into token-limited chunks by merging paragraphs.
    Large paragraphs are split into sub-chunks.
    Optionally limit number of chunks.
    """

    def add_chunk(chunks, text, idx):
        chunks.append(
            {
                "document_name": document_name,
                "chunk_index": idx,
                "text": text.strip(),
                "tokenized_para": text.strip(),
            }
        )

    if not text or not isinstance(text, str):
        raise ValueError("chunk_by_tokens: Text must be a non-empty string")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_idx = 0

    for para in paragraphs:
        para_tokens = simple_tokenize(para)
        num_tokens = len(para_tokens)

        # If paragraph itself exceeds max_tokens split it
        if num_tokens > max_tokens:
            for i in range(0, num_tokens, max_tokens):
                sub_tokens = para_tokens[i : i + max_tokens]
                sub_text = " ".join(sub_tokens)

                if current_chunk:
                    add_chunk(chunks, " ".join(current_chunk), chunk_idx)
                    chunk_idx += 1
                    if max_chunks and len(chunks) >= max_chunks:
                        return chunks
                    current_chunk = []
                    current_tokens = 0

                add_chunk(chunks, sub_text, chunk_idx)
                chunk_idx += 1
                if max_chunks and len(chunks) >= max_chunks:
                    return chunks
            continue  # move to next paragraph
        if current_tokens + num_tokens > max_tokens:
            add_chunk(chunks, " ".join(current_chunk), chunk_idx)
            chunk_idx += 1
            if max_chunks and len(chunks) >= max_chunks:
                return chunks
            current_chunk = [para]
            current_tokens = num_tokens
        else:
            current_chunk.append(para)
            current_tokens += num_tokens

    # Add any remaining chunk
    if current_chunk and (not max_chunks or len(chunks) < max_chunks):
        add_chunk(chunks, " ".join(current_chunk), chunk_idx)

    return chunks
