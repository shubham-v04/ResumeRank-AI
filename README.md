# ResumeRank AI

A local tool for recruiters: paste a job description, upload multiple resumes
(PDF or Word), and get a ranked, AI-scored, downloadable shortlist.

Unlike a plain keyword/TF-IDF matcher, this version uses an LLM to actually
read each resume, extracting structured candidate details and a genuine fit
assessment instead of just counting overlapping words.

## How it works

1. Paste or type a job description (with word-count guidance for better matching)
2. Optionally add required skills as tags and a minimum years-of-experience threshold
3. Drag and drop multiple resumes (PDF or .docx)
4. Click Analyze. For each file, the backend extracts the raw text, sends it to an LLM in one call to get the candidate's name, email, phone, detected skills, education, years of experience, an AI-written fit summary, strengths, concerns, and whether the document is even a resume at all, then scores it against the job description using TF-IDF and cosine similarity blended with skill-overlap matching
5. Non-resume documents (study notes, unrelated PDFs, and so on) are automatically excluded from the ranked list, and reported separately rather than silently dropped
6. Watch a live "Analyzing X of Y" progress bar while it works
7. Browse the ranked table, expand any candidate's "AI Insights" panel for the full assessment, and click straight through to view their original file
8. Filter to just the top 5, 10, 20, 50, or a custom number of candidates
9. Download the (filtered) results as a styled Excel or PDF

No login, no database. Everything runs locally and lives in memory or on disk for the current session.

## Why an LLM instead of regex or spaCy

Plain regex and general-purpose NER models, such as spaCy's small English
model, struggle with real resume formats: a job title appearing before the
actual name ("Senior Backend Engineer" then "Meera Nair"), names written in
ALL CAPS, label-prefixed names ("Name: Ananya Verma"), or accented
characters (Jose Hernandez Garcia). An LLM reads a resume the way a person
would, so it tells a job title apart from a name without needing hardcoded
rules for every format, and the same call produces skills, education,
experience, and a fit assessment essentially for free instead of needing
separate keyword logic for each.

## Project structure

```
resumerank-ai/
├── README.md
├── .gitignore
├── backend/
│   ├── .env.example          # template - copy to .env and fill in your key
│   ├── main.py                # FastAPI app + routes
│   ├── config.py               # settings loaded from .env - swap LLM provider/model here
│   ├── llm_extractor.py         # single LLM call: profile extraction + fit assessment
│   ├── parser.py                 # PDF/DOCX text extraction, regex fallback for email/experience
│   ├── scorer.py                  # TF-IDF + cosine similarity + skill-overlap scoring
│   ├── exporters.py                # styled Excel and PDF generation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/           # one component per feature
│   └── package.json
└── sample-data/                    # 15 sample resumes (PDF/DOCX) + a sample job description
```

## Setup

### 1. Get a free Groq API key

This app needs an LLM API key to analyze resumes. Groq's free tier requires no credit card.

1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key from the dashboard

### 2. Configure your environment

In `backend/`, copy `.env.example` to a new file named `.env`, then fill in your key:

```
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your-actual-key-here
MAX_CONCURRENT_LLM_CALLS=2
```

`.env` is gitignored and never gets committed. `.env.example` is the safe-to-share template.

Switching providers or models later is a one-line change here, no code
edits needed elsewhere, as long as the provider is registered in
`llm_extractor.py`.

`MAX_CONCURRENT_LLM_CALLS` trades speed for rate-limit safety: Groq's free
tier has a tight tokens-per-minute budget shared across every request. `2`
is a reasonable default. Drop to `1` if you see frequent "Rate limited,
waiting..." lines in the terminal, or raise it if you're on a paid tier.

### 3. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs at http://localhost:8000

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at http://localhost:5173

Open the frontend URL in your browser. It talks to the backend automatically.

## Features

1. Job description input with word-count guidance
2. Required skills as tags, checked for exact presence in each resume
3. Minimum years-of-experience threshold (estimated from resume text)
4. Drag-and-drop multi-file upload (PDF/Word) with a collapsible summary
5. Live progress bar during analysis ("Analyzing X of Y resumes...")
6. Ranked results table with match score, skill match breakdown, and experience flag
7. Expandable "AI Insights" panel per candidate: summary, strengths, concerns, detected skills, education
8. Automatic exclusion of non-resume documents from ranking, reported separately rather than silently dropped
9. Click straight through to view the original resume file
10. Top-N filter (5, 10, 20, 50, or custom) to focus on just the best candidates
11. Download results as a styled Excel or PDF, matching whatever Top-N filter is active
12. Job description, skills, and experience threshold auto-saved as a draft (localStorage), so a refresh doesn't lose your work
13. Reset button to start over

## Notes and known limitations

- Requires internet access and a valid API key. If an LLM call fails for a given resume, that resume degrades gracefully (email and experience still resolve via regex fallback where possible) rather than crashing the batch.
- Free-tier rate limits mean larger batches take a little while. The app retries automatically with the wait time Groq actually asks for.
- Scoring blends TF-IDF keyword overlap with skill matching, not a fully semantic match. A resume that says "led a team" won't automatically match a job description asking for "team leadership."
- Only .pdf and .docx are supported. Scanned or image-only PDFs are skipped since there's no OCR yet.
- Uploaded resumes are kept on disk only for the current batch (cleared automatically on the next analysis) and are never committed to git.