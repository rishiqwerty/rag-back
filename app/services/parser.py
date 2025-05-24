import pymupdf
import fitz
from docx import Document
import json

import pytesseract
from PIL import Image
import io
import boto3
from botocore.exceptions import ClientError
from ..core.config import BUCKET_NAME, development


def is_usable_text_pdf(file_path, min_chars=100):
    total_text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text()
            total_text += text.strip()

    return len(total_text) > min_chars


def ocr_pdf(file_path):
    """
    Uses Tesseract OCR to extract text from a PDF file for development.
    :param file_path: Path to the PDF file
    :return: Extracted text from the PDF
    """
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(len(pdf)):
            pix = pdf[page_num].get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))
            page_text = pytesseract.image_to_string(img)
            text += f"\n\n--- Page {page_num+1} ---\n{page_text}"
    return text


def aws_ocr_pdf(file_path):
    """
    Uses AWS Textract to perform OCR on a PDF file stored in S3.
    :param file_path: Path to the PDF file in S3
    :return: Extracted text from the PDF
    """
    client = boto3.client("textract")

    try:
        response = client.detect_document_text(
            Document={"S3Object": {"Bucket": BUCKET_NAME, "Name": file_path}}
        )

        text = ""
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                text += item["Text"] + "\n"

        return text.strip()
    except ClientError as e:
        raise Exception(f"Error processing document with AWS Textract: {e}")


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
        if development:
            text = ocr_pdf(file_path)
        else:
            aws_ocr_pdf(file_path)
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
