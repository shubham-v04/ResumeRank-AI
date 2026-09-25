"""
Extracts a candidate's name, email, and phone from resume text using
an LLM - replacing the old spaCy/regex/keyword-list approach entirely.
An LLM genuinely understands that "Senior Backend Engineer" is a job
title and "Meera Nair" is a name, the way a human reading the resume
would, instead of needing hardcoded rules for every edge case.

PROVIDER-AGNOSTIC BY DESIGN: which provider and model get used is
controlled entirely by config.py (which reads .env). To add a new
provider:
  1. Write a _call_<provider>(text, model, api_key) function below,
     matching the same signature and return shape as _call_groq.
  2. Add it to the PROVIDERS dict.
  3. Set LLM_PROVIDER in .env to its name.
No other file in the app needs to change.
"""

import json
import re

from config import settings

EXTRACTION_PROMPT = """You are extracting structured data from a resume.

Read the resume text below and identify:
- name: the candidate's full name (a person's name, NOT a job title,
  NOT a company name, NOT a section header like "Curriculum Vitae")
- email: the candidate's email address, if present
- phone: the candidate's phone number, if present

Respond with ONLY a JSON object in this exact shape, nothing else:
{{"name": "...", "email": "...", "phone": "..."}}

If a field cannot be found, use null for that field.

Resume text:
---
{resume_text}
---
"""


def _extract_json(raw: str) -> dict:
    """Best-effort JSON parsing - handles the model wrapping the JSON
    in markdown fences or adding stray text around it."""
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def _call_groq(resume_text: str, model: str, api_key: str) -> dict:
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(resume_text=resume_text)}],
        temperature=0,
        max_tokens=200,
    )
    raw = response.choices[0].message.content
    return _extract_json(raw)


def _call_gemini(resume_text: str, model: str, api_key: str) -> dict:
    """Placeholder for adding Gemini later - same shape as _call_groq,
    just a different SDK underneath. Not wired up until you add
    google-generativeai to requirements.txt and set GEMINI_API_KEY."""
    raise NotImplementedError("Gemini provider not yet implemented - add it here when needed.")


# Maps a provider name (from .env) to the function that calls it,
# and to which API key from settings it should use.
PROVIDERS = {
    "groq": (_call_groq, lambda: settings.GROQ_API_KEY),
    "gemini": (_call_gemini, lambda: settings.GEMINI_API_KEY),
}


def extract_candidate_info(resume_text: str) -> dict:
    """
    Returns {"name": ..., "email": ..., "phone": ...}, any of which may
    be None if not found or if the LLM call fails for any reason. This
    never raises - a failure here should degrade gracefully, not break
    the whole analysis.
    """
    provider_entry = PROVIDERS.get(settings.LLM_PROVIDER)
    if provider_entry is None:
        print(f"[llm_extractor] Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}' - skipping extraction.")
        return {"name": None, "email": None, "phone": None}

    call_fn, get_api_key = provider_entry
    api_key = get_api_key()

    if not api_key:
        print(f"[llm_extractor] No API key set for provider '{settings.LLM_PROVIDER}' - skipping extraction.")
        return {"name": None, "email": None, "phone": None}

    try:
        # Only the header portion is needed - keeps requests fast and cheap.
        snippet = resume_text[:1500]
        result = call_fn(snippet, settings.LLM_MODEL, api_key)
        return {
            "name": result.get("name") or None,
            "email": result.get("email") or None,
            "phone": result.get("phone") or None,
        }
    except Exception as e:
        print(f"[llm_extractor] Extraction failed via {settings.LLM_PROVIDER}: {e}")
        return {"name": None, "email": None, "phone": None}