# ResumeRank (AI-powered branch)

A local tool for recruiters: paste a job description, upload multiple resumes
(PDF or Word), and get a ranked, scored, downloadable shortlist.

**This is the `ai-resume-analyzer` branch.** It uses an LLM to extract
candidate names, instead of regex pattern-matching. For the simpler,
fully offline version with no external API dependency, see the `main`
branch.

## How it works

1. Paste/type a job description
2. Upload multiple resumes (PDF or .docx)
3. Click Analyze - the backend extracts text from each resume, calls an
   LLM to identify the candidate's name (and falls back to a regex for
   email), scores the resume against the job description using TF-IDF +
   cosine similarity and optional skill matching, and returns a ranked list
4. Download the results as Excel or PDF, or click through to view the
   original resume file

No login, no database - everything happens in memory/on disk for the
current run.

## Why this branch uses an LLM instead of regex/spaCy

Plain regex and even general-purpose NER models (like spaCy's small
English model) struggle with real resume formats:
- A job title appearing before the actual name ("Senior Backend
  Engineer" followed by "Meera Nair")
- Names written in ALL CAPS
- Names introduced with a label ("Name: Ananya Verma")
- Accented characters (José Hernández García)

An LLM reads the resume the way a person would, so it correctly tells
a job title apart from a name without needing hardcoded rules for
every format.

## Project structure

```
ResumeRank/
├── requirements.txt          (inside backend/)
├── README.md
├── .gitignore
├── backend/
│   ├── venv/                  # local virtual environment (not committed)
│   ├── .env                    # your real API key (YOU create this, gitignored)
│   ├── .env.example             # template showing the required format
│   ├── main.py                  # FastAPI app + routes
│   ├── config.py                  # settings loaded from .env - swap LLM provider/model here
│   ├── llm_extractor.py            # calls the LLM to extract name/email/phone
│   ├── parser.py                    # PDF/DOCX text extraction, delegates name extraction to llm_extractor
│   ├── scorer.py                      # TF-IDF + cosine similarity + skill-overlap scoring
│   ├── exporters.py                    # styled Excel and PDF generation
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/            # one component per feature
    └── package.json
```

## Setup

### 1. Get a free Groq API key

This branch needs an LLM API key to extract candidate names. Groq's
free tier requires no credit card:

1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key from the dashboard

### 2. Configure your environment

In `backend/`, copy `.env.example` to a new file named `.env`, then
fill in your key:
```
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your-actual-key-here
```
`.env` is gitignored and never gets committed - `.env.example` is the
safe-to-share template.

**Switching providers or models later** is a one-line change here -
no code edits needed elsewhere, as long as the provider is registered
in `llm_extractor.py`.

### 3. Backend
```
cd backend
venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs at http://localhost:8000

### 4. Frontend
```
cd frontend
npm install
npm run dev
```
Runs at http://localhost:5173

Open the frontend URL in your browser - it talks to the backend automatically.

## Features

1. Add a job description (with word-count guidance and a "Load Example" option)
2. Add required skills as tags - checked for exact presence in each resume
3. Set a minimum years-of-experience threshold (estimated from resume text)
4. Upload multiple resumes via drag-and-drop (PDF/Word)
5. One-click analysis
6. Ranked results table with match score, skill match breakdown, and experience flag
7. Candidate name extracted via LLM; email extracted via regex with LLM fallback
8. Click through to view the original resume file
9. Download results as a styled Excel or PDF
10. Loading indicator during analysis
11. Clear error messages for unreadable or unsupported files
12. Reset button to start over
13. Job description, skills, and experience threshold auto-saved as a draft (localStorage)

## Notes / known limitations

- Name extraction requires internet access and a valid API key - if
  the LLM call fails for any reason, the app degrades gracefully
  (email still resolves via regex; name shows "Unknown") rather than
  crashing, but you won't get a name for that resume.
- Years-of-experience is still a regex heuristic ("N years" phrases in
  the text) - not LLM-based, and treat it as approximate.
- Scoring is TF-IDF + optional skill-overlap based (keyword/skill
  presence), not semantic - a resume that says "led a team" won't
  automatically match a JD asking for "team leadership."
- Only .pdf and .docx are supported; scanned/image-only PDFs will be
  skipped since there's no OCR yet.
- Uploaded resumes are kept on disk only for the current batch
  (cleared automatically on the next analysis) - not committed to git.

## Relationship to `main`

| | `main` | `ai-resume-analyzer` (this branch) |
|---|---|---|
| Name extraction | Regex only | LLM (Groq), config-driven |
| External dependency | None - fully offline | Requires internet + API key |
| Setup complexity | Simpler | One extra step (.env + API key) |
| Accuracy on edge cases | Lower (job titles, labels, accents can confuse it) | Higher |

Both branches are maintained independently and are not intended to be
merged into each other.