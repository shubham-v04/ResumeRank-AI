"""
Tests for llm_extractor.py's pure helper functions - no API key or
network needed. These two functions were the site of real bugs during
development (see README/commit history), so they're the highest-value
things to lock down with tests: a regression here silently breaks retry
timing or JSON parsing without ever raising an exception.
Run with: cd backend && pytest
"""

from llm_extractor import _parse_retry_wait, _extract_json


def test_parse_retry_wait_plain_seconds():
    error_message = "Rate limit reached. Please try again in 42.17s."
    # +1.0s buffer is intentional, see _parse_retry_wait's docstring
    assert _parse_retry_wait(error_message) == 43.17


def test_parse_retry_wait_minutes_and_seconds():
    # This is the exact format that exposed the original bug: a fixed
    # regex that only matched plain seconds silently fell back to a
    # useless 15s default on every TPD (daily quota) rate limit, which
    # actually needs several minutes of wait time.
    error_message = "Rate limit reached. Please try again in 7m9.4s."
    assert round(_parse_retry_wait(error_message), 2) == 430.4


def test_parse_retry_wait_falls_back_to_default_when_unmatched():
    error_message = "Some unrelated error with no wait time mentioned."
    assert _parse_retry_wait(error_message) == 15.0
    assert _parse_retry_wait(error_message, default=5.0) == 5.0


def test_parse_retry_wait_is_case_insensitive():
    error_message = "PLEASE TRY AGAIN IN 3.5S"
    assert _parse_retry_wait(error_message) == 4.5


def test_extract_json_plain_json():
    raw = '{"is_resume": true, "name": "Jane Doe"}'
    result = _extract_json(raw)
    assert result == {"is_resume": True, "name": "Jane Doe"}


def test_extract_json_wrapped_in_markdown_fences():
    raw = '```json\n{"is_resume": true, "name": "Jane Doe"}\n```'
    result = _extract_json(raw)
    assert result == {"is_resume": True, "name": "Jane Doe"}


def test_extract_json_with_surrounding_text():
    raw = 'Here is the profile:\n{"is_resume": false, "name": null}\nHope that helps!'
    result = _extract_json(raw)
    assert result == {"is_resume": False, "name": None}
