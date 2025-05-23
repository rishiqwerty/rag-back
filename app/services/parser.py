import pymupdf
import fitz
from docx import Document
import json

import pytesseract
from PIL import Image
import io


def is_usable_text_pdf(file_path, min_chars=100):
    total_text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text()
            total_text += text.strip()

    return len(total_text) > min_chars


def ocr_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(len(pdf)):
            pix = pdf[page_num].get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))
            page_text = pytesseract.image_to_string(img)
            text += f"\n\n--- Page {page_num+1} ---\n{page_text}"
    return text


def extract_text_with_pymupdf(file_path):
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def parse_pdf(file_path):
    if is_usable_text_pdf(file_path):
        text = extract_text_with_pymupdf(file_path)
    else:
        text = ocr_pdf(file_path)
    return text


def parse_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def parse_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def parse_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_json_field(file_path, field_name):
    data = parse_json(file_path)
    return data.get(field_name, "")
