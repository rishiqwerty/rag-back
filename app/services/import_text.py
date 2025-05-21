# Text Parsing and Chunking Service
import pymupdf
import fitz
from docx import Document
import json

import pytesseract
from PIL import Image
import io
from ..core.config import MAX_CHUNKS_PER_DOCUMENT

import nltk
nltk.download('punkt_tab') # Need to download the punkt tokenizer models
from nltk.tokenize import word_tokenize

def chunk_by_tokens(text, max_tokens=300, max_chunks=MAX_CHUNKS_PER_DOCUMENT):
    """Split text into chunks by merging adjacent paragraphs until max_tokens is reached.
    Optionally limit total number of chunks.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_tokens = word_tokenize(para)
        if current_tokens + len(para_tokens) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                if max_chunks and len(chunks) >= max_chunks:
                    break
            current_chunk = para
            current_tokens = len(para_tokens)
        else:
            current_chunk += " " + para
            current_tokens += len(para_tokens)

    if current_chunk and (not max_chunks or len(chunks) < max_chunks):
        chunks.append(current_chunk.strip())

    return chunks



def is_usable_text_pdf(file_path, min_chars=100):
    total_text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text()
            total_text += text.strip()

    return len(total_text) > min_chars

def extract_text_with_pymupdf(file_path):
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def ocr_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(len(pdf)):
            pix = pdf[page_num].get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))
            page_text = pytesseract.image_to_string(img)
            text += f"\n\n--- Page {page_num+1} ---\n{page_text}"
    return text

def parse_pdf(file_path="/Users/rishavsharma/Downloads/whistleblower-policy-ba-revised.pdf"):
    if is_usable_text_pdf(file_path):
        text = extract_text_with_pymupdf(file_path)
    else:
        text = ocr_pdf(file_path)
    return text


def parse_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_json_field(file_path, field_name):
    data = parse_json(file_path)
    return data.get(field_name, "")
