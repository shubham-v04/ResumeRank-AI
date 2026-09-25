"""
Extracts a full candidate profile from resume text using an LLM - one
call returns everything: contact info, detected skills, education,
years of experience, an AI-generated fit assessment (summary,
strengths, concerns), and whether the document is actually a resume
at all (catches someone accidentally uploading unrelated documents,
which pure keyword-matching scoring can't detect on its own).

ASYNC BY DESIGN: this is async so main.py can fire off calls for many
resumes concurrently instead of waiting for each one to finish before
starting the next. See main.py / config.py's MAX_CONCURRENT_LLM_CALLS
for the concurrency cap - keep this LOW on a free tier, since token
budgets (not just request counts) are usually the real bottleneck.

PROVIDER-AGNOSTIC BY DESIGN: see config.py to switch providers/models.
"""

import asyncio
import json
import re

from config import settings

EXTRACTION_PROMPT = """You are analyzing a document that was uploaded as a candidate resume for a recruiter.

First, decide: is this document actually a resume/CV for a specific person (has a name, and describes their background, skills or experience)? Study notes, textbooks, articles, or any document that isn't about a specific candidate should be marked as NOT a resume.

Then extract (use null/empty for anything not applicable, especially if is_resume is false):
- is_resume: true or false
- name: the candidate's full name (a person's name, NOT a job title, NOT a company, NOT a header like "Curriculum Vitae")
- email: the candidate's email address, if present
- phone: the candidate's phone number, if present
- skills: an array of specific technical/professional skills actually mentioned (max 12, most relevant first)
- education: the highest degree and institution, as a short string (e.g. "B.Tech Computer Science, IIT Delhi")
- years_experience: total years of professional experience as a number (estimate if not stated directly; null if unclear)
- summary: a 1-2 sentence plain-English summary of this candidate's fit for the role described
- strengths: an array of 2-3 short specific strengths relevant to the job description (each under 12 words)
- concerns: an array of 0-2 short specific gaps or concerns relevant to the job description (each under 12 words; empty array if none)

Respond with ONLY a JSON object in this exact shape, nothing else:
{{"is_resume": true, "name": "...", "email": "...", "phone": "...", "skills": ["..."], "education": "...", "years_experience": 0, "summary": "...", "strengths": ["..."], "concerns": ["..."]}}

Job description:
---
{job_description}
---

Document text:
---
{resume_text}
---
"""

# The suggested wait time Groq includes in its rate-limit error message,
# e.g. "Please try again in 42.1725s" - parsed so retries actually wait
# long enough instead of retrying into the same wall immediately.
_RETRY_WAIT_PATTERN = re.compile(r"try again in (?:(\d+)m)?([\d.]+)s", re.IGNORECASE)


def _extract_json(raw: str) -> dict:
    """Best-effort JSON parsing - handles the model wrapping the JSON
    in markdown fences or adding stray text around it."""
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def _parse_retry_wait(error_message: str, default: float = 15.0) -> float:
    """Pulls the actual suggested wait time out of Groq's error text,
    since a fixed short backoff just retries into the same rate limit.
    Groq formats this as plain seconds ("42.17s") for short waits, or
    minutes+seconds combined ("7m9.4s") for longer ones - both are
    handled here."""
    match = _RETRY_WAIT_PATTERN.search(error_message)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = float(match.group(2))
        return minutes * 60 + seconds + 1.0  # small buffer on top
    return default


async def _call_groq(resume_text: str, job_description: str, model: str, api_key: str) -> dict:
    from groq import AsyncGroq
    try:
        from groq import RateLimitError
    except ImportError:
        RateLimitError = ()  # defensive fallback, matches nothing

    client = AsyncGroq(api_key=api_key)
    prompt = EXTRACTION_PROMPT.format(resume_text=resume_text, job_description=job_description)

    extra_kwargs = {}
    if "gpt-oss" in model:
        # Keeps hidden "reasoning" token usage low - both for speed and
        # to leave more of the tight free-tier token budget for the
        # actual JSON output.
        extra_kwargs["reasoning_effort"] = "low"

    # Free-tier token-per-minute budgets are tight and shared across ALL
    # requests, so a rate-limit hit here is common with more than a
    # couple of resumes in a batch - retry, but wait as long as Groq
    # actually asks for, not a short fixed backoff.
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_completion_tokens=900,
                **extra_kwargs,
            )
            raw = response.choices[0].message.content
            if not raw or not raw.strip():
                finish_reason = response.choices[0].finish_reason
                raise ValueError(
                    f"Empty response from model (finish_reason={finish_reason}) - "
                    f"likely ran out of tokens before producing output."
                )
            return _extract_json(raw)

        except RateLimitError as e:
            if attempt < max_attempts - 1:
                wait_seconds = _parse_retry_wait(str(e))
                print(f"[llm_extractor] Rate limited - waiting {wait_seconds:.1f}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(wait_seconds)
                continue
            raise


async def _call_gemini(resume_text: str, job_description: str, model: str, api_key: str) -> dict:
    """Placeholder for adding Gemini later - same shape as _call_groq."""
    raise NotImplementedError("Gemini provider not yet implemented - add it here when needed.")


PROVIDERS = {
    "groq": (_call_groq, lambda: settings.GROQ_API_KEY),
    "gemini": (_call_gemini, lambda: settings.GEMINI_API_KEY),
}

_EMPTY_PROFILE = {
    "is_resume": None, "name": None, "email": None, "phone": None, "skills": [],
    "education": None, "years_experience": None, "summary": None,
    "strengths": [], "concerns": [],
}


async def extract_candidate_profile(resume_text: str, job_description: str = "") -> dict:
    """
    Returns a full candidate profile dict (see _EMPTY_PROFILE for shape).
    Any field may be None/empty if not found or if the LLM call fails -
    this never raises, so a failure here degrades gracefully instead of
    breaking the whole analysis. is_resume is None (not False) if the
    LLM call itself failed - callers should treat None as "unknown,
    don't exclude" rather than "confirmed not a resume".
    """
    provider_entry = PROVIDERS.get(settings.LLM_PROVIDER)
    if provider_entry is None:
        print(f"[llm_extractor] Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}' - skipping extraction.")
        return dict(_EMPTY_PROFILE)

    call_fn, get_api_key = provider_entry
    api_key = get_api_key()

    if not api_key:
        print(f"[llm_extractor] No API key set for provider '{settings.LLM_PROVIDER}' - skipping extraction.")
        return dict(_EMPTY_PROFILE)

    try:
        # Kept modest on purpose - the free tier's token-per-minute
        # budget is the real constraint, not the model's context window.
        # This covers roughly the first 3-4 pages of a resume, which is
        # where the name/contact/skills/experience almost always are.
        snippet = resume_text[:8000]
        result = await call_fn(snippet, job_description[:1500], settings.LLM_MODEL, api_key)

        profile = dict(_EMPTY_PROFILE)
        profile.update({
            "is_resume": result.get("is_resume"),
            "name": result.get("name") or None,
            "email": result.get("email") or None,
            "phone": result.get("phone") or None,
            "skills": result.get("skills") or [],
            "education": result.get("education") or None,
            "years_experience": result.get("years_experience"),
            "summary": result.get("summary") or None,
            "strengths": result.get("strengths") or [],
            "concerns": result.get("concerns") or [],
        })
        return profile
    except Exception as e:
        print(f"[llm_extractor] Extraction failed via {settings.LLM_PROVIDER}: {e}")
        return dict(_EMPTY_PROFILE)