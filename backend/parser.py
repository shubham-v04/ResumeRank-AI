"""
Handles turning uploaded resume files into plain text, and pulling out
structured fields (name, email, years of experience).

Name/email extraction is delegated to llm_extractor.py (an LLM call,
provider configured in .env) - it genuinely understands resume context
instead of relying on regex patterns and hardcoded keyword lists. A
simple email regex is kept as a fallback in case the LLM doesn't find
one or the call fails for any reason.
"""

import os
import re

from pypdf import PdfReader
from docx import Document

from llm_extractor import extract_candidate_info

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
EXPERIENCE_PATTERN = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b", re.IGNORECASE)


def extract_text_from_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def extract_text_from_docx(path: str) -> str:
    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text(path: str) -> str:
    """Dispatches to the right extractor based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".docx":
        return extract_text_from_docx(path)
    return ""


def extract_entities(text: str):
    """
    Returns (name, email). Name comes from the LLM extractor. Email
    also comes from the LLM first, but falls back to a plain regex if
    the LLM didn't find one or the call failed - an email address is
    structured enough that regex alone is already reliable, so this
    fallback costs nothing and adds robustness.
    """
    result = extract_candidate_info(text)

    email = result.get("email")
    if not email:
        regex_emails = EMAIL_PATTERN.findall(text)
        email = regex_emails[0] if regex_emails else "Not found"

    name = result.get("name") or "Unknown"

    return name, email


def extract_years_of_experience(text: str):
    """
    Heuristic only: looks for the largest "N years" mention in the resume.
    Not reliable for every resume format - treat as an estimate, not a fact.
    Returns an int, or None if nothing matched.
    """
    matches = EXPERIENCE_PATTERN.findall(text)
    if not matches:
        return None
    years = [int(m) for m in matches if int(m) <= 50]
    return max(years) if years else None


def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in (".pdf", ".docx")