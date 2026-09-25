"""
Handles turning uploaded resume files into plain text, and pulling out
a full candidate profile (name, email, phone, skills, education,
experience, and an AI-generated fit summary).

Extraction is delegated to llm_extractor.py (one LLM call per resume,
provider configured in .env). Email and years-of-experience have
simple regex fallbacks in case the LLM call fails or misses a field -
these are structured enough that regex alone is already reasonably
reliable, so the fallback costs nothing and adds robustness.
"""

import os
import re

from pypdf import PdfReader
from docx import Document

from llm_extractor import extract_candidate_profile as _llm_extract_profile

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


def _regex_email(text: str):
    matches = EMAIL_PATTERN.findall(text)
    return matches[0] if matches else None


def _regex_years_of_experience(text: str):
    matches = EXPERIENCE_PATTERN.findall(text)
    if not matches:
        return None
    years = [int(m) for m in matches if int(m) <= 50]
    return max(years) if years else None


async def get_candidate_profile(text: str, job_description: str = "") -> dict:
    """
    Returns a full candidate profile:
    {
        "name": str, "email": str, "phone": str|None,
        "skills": list[str], "education": str|None,
        "years_experience": int|None, "summary": str|None,
        "strengths": list[str], "concerns": list[str],
    }

    name/email/years_experience always have a usable value (falling
    back to "Unknown"/regex/None as appropriate); the AI-only fields
    (skills, education, summary, strengths, concerns) are empty/None
    if the LLM call didn't succeed, since there's no regex equivalent
    for those.
    """
    profile = await _llm_extract_profile(text, job_description)

    if not profile.get("email"):
        profile["email"] = _regex_email(text) or "Not found"

    if profile.get("years_experience") is None:
        profile["years_experience"] = _regex_years_of_experience(text)

    if not profile.get("name"):
        profile["name"] = "Unknown"

    return profile


def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in (".pdf", ".docx")