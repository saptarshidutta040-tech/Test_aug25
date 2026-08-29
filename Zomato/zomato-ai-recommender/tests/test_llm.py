"""
tests/test_llm.py
──────────────────
Integration tests for engine/llm_client.py.

Uses unittest.mock to avoid real API calls in CI/test environments.
A separate `--run-llm` marker is used for live Groq API tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from engine.llm_client import (
    BaseLLMClient,
    GroqClient,
    call_llm_with_retry,
    get_llm_client,
)


# ── Mock LLM helper ───────────────────────────────────────────────────────────

def make_mock_client(return_value: str = "Mocked LLM response") -> BaseLLMClient:
    mock = MagicMock(spec=BaseLLMClient)
    mock.complete.return_value = return_value
    return mock


# ── get_llm_client factory tests ──────────────────────────────────────────────

def test_get_llm_client_groq():
    with patch("engine.llm_client.LLM_PROVIDER", "groq"), \
         patch("engine.llm_client.GROQ_API_KEY", "fake-key"):
        with patch("groq.Groq"):
            client = get_llm_client()
            assert isinstance(client, GroqClient)


def test_get_llm_client_invalid_provider():
    with patch("engine.llm_client.LLM_PROVIDER", "unknown_provider"):
        with pytest.raises(ValueError, match="Unsupported"):
            get_llm_client()


# ── call_llm_with_retry tests ─────────────────────────────────────────────────

def test_retry_succeeds_on_first_attempt():
    mock = make_mock_client("Great recommendation!")
    result = call_llm_with_retry(mock, "test prompt", retries=3)
    assert result == "Great recommendation!"
    assert mock.complete.call_count == 1


def test_retry_succeeds_on_second_attempt():
    mock = MagicMock(spec=BaseLLMClient)
    mock.complete.side_effect = [Exception("Rate limit"), "Success on retry"]
    result = call_llm_with_retry(mock, "test prompt", retries=3)
    assert result == "Success on retry"
    assert mock.complete.call_count == 2


def test_retry_raises_after_all_attempts_fail():
    mock = MagicMock(spec=BaseLLMClient)
    mock.complete.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        call_llm_with_retry(mock, "test prompt", retries=2)
    assert mock.complete.call_count == 2


def test_retry_raises_on_empty_response():
    mock = make_mock_client("")  # empty response
    with pytest.raises(Exception):
        call_llm_with_retry(mock, "test prompt", retries=2)


def test_retry_raises_on_whitespace_response():
    mock = make_mock_client("   ")  # whitespace only
    with pytest.raises(Exception):
        call_llm_with_retry(mock, "test prompt", retries=2)


def test_retry_passes_prompt_to_client():
    mock = make_mock_client("response")
    call_llm_with_retry(mock, "my specific prompt", retries=1)
    mock.complete.assert_called_once_with("my specific prompt")


# ── Integration test (mocked): filter → prompt → LLM ─────────────────────────

def test_e2e_filter_prompt_llm_mocked():
    """
    End-to-end test using mocked LLM.
    Verifies that FilterEngine + build_prompt + LLM client chain works.
    """
    import pandas as pd
    from engine.filter import FilterEngine
    from engine.prompt_builder import build_prompt

    sample_df = pd.DataFrame([
        {
            "name": "Test Restaurant", "location": "Bangalore",
            "cuisine": "Italian", "cost_for_two": 800.0,
            "rating": 4.3, "votes": 500,
            "online_order": True, "book_table": False,
        }
    ])

    query = {
        "location": "Bangalore",
        "cuisine": "Italian",
        "budget": "medium",
        "min_rating": 4.0,
        "extras": "",
    }

    # Step 1: Filter
    candidates = FilterEngine(sample_df).filter(query)
    assert not candidates.empty

    # Step 2: Build prompt
    prompt = build_prompt(query, candidates)
    assert "Test Restaurant" in prompt

    # Step 3: Mock LLM call
    mock_client = make_mock_client("Here are my top recommendations for Bangalore...")
    response = call_llm_with_retry(mock_client, prompt)

    assert "Bangalore" in response or len(response) > 10
    mock_client.complete.assert_called_once_with(prompt)
