from app.services.import_text import chunk_by_tokens
import pytest


def test_chunk_by_tokens_basic():
    """
    Test basic functionality of chunk_by_tokens.
    """
    document_name = "test_document"
    text = "This is a test paragraph.\n\nThis is another test paragraph."
    max_tokens = 5
    max_chunks = 2

    chunks = chunk_by_tokens(document_name, text, max_tokens, max_chunks)

    assert len(chunks) == 2
    assert chunks[0]["document_name"] == document_name
    assert "test paragraph" in chunks[0]["text"]
    assert "another test paragraph" in chunks[1]["text"]


def test_chunk_by_tokens_empty_text():
    """
    Test chunk_by_tokens with empty text.
    """
    document_name = "empty_document"
    text = ""
    max_tokens = 5
    max_chunks = 2

    with pytest.raises(ValueError, match="Text must be a non-empty string"):
        chunk_by_tokens(document_name, text, max_tokens, max_chunks)


def test_chunk_by_tokens_large_text():
    """
    Test chunk_by_tokens with a large text that exceeds max_tokens.
    """
    document_name = "large_document"
    text = "Word " * 1000  # A large text with 1000 words
    max_tokens = 100
    max_chunks = 5

    chunks = chunk_by_tokens(document_name, text, max_tokens, max_chunks)

    assert len(chunks) == max_chunks
    for chunk in chunks:
        assert len(chunk["tokenized_para"].split()) <= max_tokens


def test_chunk_by_tokens_error_handling():
    """
    Test chunk_by_tokens error handling.
    """
    document_name = "error_document"
    text = None  # Invalid input
    max_tokens = 5
    max_chunks = 2

    with pytest.raises(ValueError, match="Text must be a non-empty string"):
        chunk_by_tokens(document_name, text, max_tokens, max_chunks)
