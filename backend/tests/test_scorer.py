"""
Tests for scorer.py - pure functions, no API key or network needed.
Run with: cd backend && pytest
"""

from scorer import tfidf_scores, match_skills, score_resumes


def test_tfidf_scores_empty_job_description_returns_zero():
    scores = tfidf_scores("", ["some resume text"])
    assert scores == [0.0]


def test_tfidf_scores_empty_resume_list_returns_empty():
    scores = tfidf_scores("some job description", [])
    assert scores == []


def test_tfidf_scores_more_overlap_scores_higher():
    job = "Python FastAPI backend developer with PostgreSQL experience"
    strong_match = "Experienced Python FastAPI backend developer, PostgreSQL expert"
    weak_match = "Marketing specialist with social media and content writing skills"

    scores = tfidf_scores(job, [strong_match, weak_match])

    assert scores[0] > scores[1]


def test_match_skills_no_required_skills_returns_empty():
    matched, missing, percent = match_skills("some resume text", [])
    assert matched == []
    assert missing == []
    assert percent is None


def test_match_skills_case_insensitive_whole_word():
    resume_text = "Proficient in Python, FastAPI, and SQL. Familiar with Docker."
    required = ["python", "REACT", "SQL"]

    matched, missing, percent = match_skills(resume_text, required)

    assert matched == ["python", "SQL"]
    assert missing == ["REACT"]
    assert percent == round(2 / 3 * 100, 2)


def test_match_skills_avoids_partial_word_matches():
    # "Java" should NOT match inside "JavaScript"
    resume_text = "5 years of JavaScript and Node.js experience"
    matched, missing, percent = match_skills(resume_text, ["Java"])

    assert matched == []
    assert missing == ["Java"]


def test_score_resumes_falls_back_to_tfidf_when_no_skills_given():
    job = "Python backend developer"
    resumes = ["Python backend developer with 5 years experience"]

    results = score_resumes(job, resumes, required_skills=None)

    assert results[0]["skill_match_percent"] is None
    assert results[0]["final_score"] == results[0]["tfidf_score"]


def test_score_resumes_blends_tfidf_and_skills_when_skills_given():
    job = "Python backend developer with SQL experience"
    resumes = ["Python backend developer with SQL and FastAPI experience"]

    results = score_resumes(job, resumes, required_skills=["Python", "SQL"])

    assert results[0]["skill_match_percent"] == 100.0
    assert results[0]["final_score"] != results[0]["tfidf_score"]


def test_score_resumes_returns_all_expected_keys():
    results = score_resumes("job text", ["resume text"], required_skills=["Python"])
    row = results[0]

    for key in ("final_score", "tfidf_score", "skill_match_percent", "skills_matched", "skills_missing"):
        assert key in row
