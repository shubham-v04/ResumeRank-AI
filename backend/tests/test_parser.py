"""
Tests for parser.py's non-LLM code paths only - the regex fallbacks and
file-type checks. get_candidate_profile() itself calls out to the LLM
(llm_extractor.py) and needs a live API key, so it's intentionally not
tested here; it's exercised manually via the running app instead.
Run with: cd backend && pytest
"""

from parser import _regex_email, _regex_years_of_experience, is_allowed_file


def test_regex_email_finds_first_email():
    text = "Contact me at jane.doe@example.com or jane@work.com"
    assert _regex_email(text) == "jane.doe@example.com"


def test_regex_email_returns_none_when_missing():
    assert _regex_email("No email address in this text at all.") is None


def test_regex_years_of_experience_plain_years():
    assert _regex_years_of_experience("5 years of experience in web development") == 5


def test_regex_years_of_experience_plus_and_abbreviation():
    assert _regex_years_of_experience("3+ yrs experience with Python") == 3


def test_regex_years_of_experience_takes_the_largest_mention():
    text = "2 years as an intern, then 6 years as a full-time engineer"
    assert _regex_years_of_experience(text) == 6


def test_regex_years_of_experience_ignores_obvious_junk():
    text = "Our company was founded 100 years ago. I have 4 years experience."
    assert _regex_years_of_experience(text) == 4


def test_regex_years_of_experience_no_match_returns_none():
    assert _regex_years_of_experience("No experience mentioned here.") is None


def test_is_allowed_file_accepts_pdf_and_docx():
    assert is_allowed_file("resume.pdf") is True
    assert is_allowed_file("resume.docx") is True
    assert is_allowed_file("RESUME.PDF") is True


def test_is_allowed_file_rejects_other_extensions():
    assert is_allowed_file("resume.txt") is False
    assert is_allowed_file("resume.exe") is False
    assert is_allowed_file("resume") is False
