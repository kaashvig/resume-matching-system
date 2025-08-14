import os
import io
import pdfplumber
from docx import Document

def extract_text_from_pdf(file_obj):
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def extract_text_from_docx(file_obj):
    doc = Document(file_obj)
    return "\n".join([para.text for para in doc.paragraphs]).strip()

def extract_text(*args):
    """
    Flexible extract_text:
    - extract_text(path)
    - extract_text(file_bytes, filename)
    """
    # Handle extract_text(path)
    if len(args) == 1 and isinstance(args[0], str):
        path = args[0]
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            with open(path, "rb") as f:
                return extract_text_from_pdf(f)
        elif ext == ".docx":
            with open(path, "rb") as f:
                return extract_text_from_docx(f)
        else:
            raise ValueError(f"Unsupported file format: '{ext}' — only .pdf and .docx are supported.")

    # Handle extract_text(file_bytes, filename)
    elif len(args) == 2:
        file_content, filename = args
        ext = os.path.splitext(filename)[1].lower()
        file_obj = io.BytesIO(file_content)
        if ext == ".pdf":
            return extract_text_from_pdf(file_obj)
        elif ext == ".docx":
            return extract_text_from_docx(file_obj)
        else:
            raise ValueError(f"Unsupported file format: '{ext}' — only .pdf and .docx are supported.")

    else:
        raise TypeError("extract_text() must be called with either (path) or (file_bytes, filename)")


