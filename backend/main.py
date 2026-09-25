"""
ResumeRank backend.

Endpoints:
  POST /analyze           - job description + resumes (+ optional skills/min experience) -> ranked results
  GET  /analyze/progress   - current progress of an in-flight /analyze call, for a live "X of Y" counter
  GET  /download/excel      - downloads the most recent results as an .xlsx
  GET  /download/pdf        - downloads the most recent results as a .pdf
  GET  /resumes/<file>       - serves an uploaded resume so it can be viewed in-browser

No database, no auth - everything lives in memory / on disk for the
current server run, which is fine for a local, single-user tool.
"""

import asyncio
import os
import shutil

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from werkzeug.utils import secure_filename

from config import settings
from parser import extract_text, get_candidate_profile, is_allowed_file
from scorer import score_resumes
from exporters import generate_excel, generate_pdf

app = FastAPI(title="ResumeRank")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/resumes", StaticFiles(directory=UPLOAD_DIR), name="resumes")

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

latest_results: list[dict] = []

# Tracks progress of whatever /analyze call is currently running, so the
# frontend can poll GET /analyze/progress and show "Analyzing X of Y".
# This is a single global since this app is single-user/single-request
# at a time by design - it isn't meant to track multiple concurrent
# analyses.
analysis_progress = {"total": 0, "completed": 0, "active": False}


def reset_upload_dir():
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def parse_skills(raw: str) -> list[str]:
    """Turns a comma-separated skills string into a clean list."""
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


async def _profile_with_progress(sem: asyncio.Semaphore, text: str, job_description: str) -> dict:
    """Wraps get_candidate_profile with a concurrency cap AND updates
    the shared progress counter the moment this one resume finishes -
    not when the whole batch finishes, so the counter moves live."""
    async with sem:
        result = await get_candidate_profile(text, job_description)
        analysis_progress["completed"] += 1
        return result


@app.post("/analyze")
async def analyze(
    job_description: str = Form(...),
    resume_files: list[UploadFile] = File(...),
    required_skills: str = Form(""),          # comma-separated, optional
    min_experience: int | None = Form(None),   # years, optional
):
    global latest_results

    if not job_description.strip():
        return JSONResponse(status_code=400, content={"error": "Job description is empty."})

    if not resume_files:
        return JSONResponse(status_code=400, content={"error": "No resume files were uploaded."})

    skills_list = parse_skills(required_skills)
    reset_upload_dir()

    parsed = []       # (stored_filename, original_filename, text)
    skipped = []

    for idx, f in enumerate(resume_files):
        if not f.filename or not is_allowed_file(f.filename):
            skipped.append(f.filename or "unknown file")
            continue

        contents = await f.read()
        if len(contents) > MAX_FILE_SIZE_BYTES:
            skipped.append(f"{f.filename} (too large - over 10MB)")
            continue

        stored_filename = f"{idx}_{secure_filename(f.filename)}"
        stored_path = os.path.join(UPLOAD_DIR, stored_filename)
        with open(stored_path, "wb") as out:
            out.write(contents)

        text = extract_text(stored_path)
        if not text.strip():
            skipped.append(f.filename)
            continue

        parsed.append((stored_filename, f.filename, text))

    if not parsed:
        return JSONResponse(
            status_code=400,
            content={"error": "None of the uploaded files could be read.", "skipped": skipped},
        )

    # Reset and start tracking progress for this batch - the frontend
    # starts polling /analyze/progress as soon as it sees "active".
    analysis_progress["total"] = len(parsed)
    analysis_progress["completed"] = 0
    analysis_progress["active"] = True

    try:
        sem = asyncio.Semaphore(settings.MAX_CONCURRENT_LLM_CALLS)
        profile_tasks = [_profile_with_progress(sem, text, job_description) for (_, _, text) in parsed]
        profiles = await asyncio.gather(*profile_tasks)
    finally:
        # Always clear "active", even if something above raised, so the
        # frontend's polling loop doesn't spin forever on a dead batch.
        analysis_progress["active"] = False

    score_results = score_resumes(job_description, [p[2] for p in parsed], skills_list)

    results = []
    non_resume_files = []

    for (stored_filename, original_filename, _), profile, score in zip(parsed, profiles, score_results):
        years_exp = profile["years_experience"]
        meets_experience = None
        if min_experience is not None:
            meets_experience = (years_exp is not None) and (years_exp >= min_experience)

        row = {
            "filename": original_filename,
            "name": profile["name"],
            "email": profile["email"],
            "phone": profile["phone"],
            "score": score["final_score"],
            "tfidf_score": score["tfidf_score"],
            "skill_match_percent": score["skill_match_percent"],
            "skills_matched": score["skills_matched"],
            "skills_missing": score["skills_missing"],
            "skills_detected": profile["skills"],
            "education": profile["education"],
            "years_experience": years_exp,
            "meets_experience": meets_experience,
            "ai_summary": profile["summary"],
            "ai_strengths": profile["strengths"],
            "ai_concerns": profile["concerns"],
            "resume_url": f"/resumes/{stored_filename}",
        }

        if profile.get("is_resume") is False:
            non_resume_files.append(original_filename)
        else:
            results.append(row)

    results.sort(key=lambda r: r["score"], reverse=True)
    latest_results = results

    return {"results": results, "skipped": skipped, "non_resume_files": non_resume_files}


@app.get("/analyze/progress")
def get_progress():
    return analysis_progress


@app.get("/download/excel")
def download_excel(limit: int | None = None):
    if not latest_results:
        return JSONResponse(status_code=400, content={"error": "No results to export yet."})
    data = latest_results[:limit] if limit else latest_results
    buffer = generate_excel(data)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ranked_resumes.xlsx"},
    )


@app.get("/download/pdf")
def download_pdf(limit: int | None = None):
    if not latest_results:
        return JSONResponse(status_code=400, content={"error": "No results to export yet."})
    data = latest_results[:limit] if limit else latest_results
    buffer = generate_pdf(data)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=ranked_resumes.pdf"},
    )