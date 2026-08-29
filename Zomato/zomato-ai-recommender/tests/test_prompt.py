"""
tests/test_prompt.py
─────────────────────
Unit tests for engine/prompt_builder.py — build_prompt() and template rendering.
"""

from __future__ import annotations

import pandas as pd
import pytest

from engine.prompt_builder import build_prompt, estimate_token_count


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def candidates():
    """Minimal candidate DataFrame for prompt building tests."""
    return pd.DataFrame([
        {
            "name": "Trattoria Italia", "location": "Koramangala",
            "cuisine": "Italian, Continental",
            "cost_for_two": 1200.0, "rating": 4.5, "votes": 900,
            "online_order": True, "book_table": True,
        },
        {
            "name": "Pizza Hut", "location": "Koramangala",
            "cuisine": "Italian, Fast Food",
            "cost_for_two": 800.0, "rating": 4.0, "votes": 600,
            "online_order": True, "book_table": False,
        },
    ])


@pytest.fixture
def query():
    return {
        "location": "Koramangala",
        "cuisine": "Italian",
        "budget": "medium",
        "min_rating": 4.0,
        "extras": "family-friendly",
    }


# ── Core rendering tests ───────────────────────────────────────────────────────

def test_prompt_is_non_empty(candidates, query):
    prompt = build_prompt(query, candidates)
    assert isinstance(prompt, str)
    assert len(prompt.strip()) > 0


def test_prompt_contains_location(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "Koramangala" in prompt


def test_prompt_contains_cuisine(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "Italian" in prompt


def test_prompt_contains_budget_label(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "medium" in prompt


def test_prompt_contains_budget_range(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "500" in prompt and "1500" in prompt


def test_prompt_contains_min_rating(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "4.0" in prompt


def test_prompt_contains_extras(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "family-friendly" in prompt


def test_prompt_contains_all_restaurant_names(candidates, query):
    prompt = build_prompt(query, candidates)
    for name in candidates["name"]:
        assert name in prompt, f"Restaurant '{name}' not found in prompt"


def test_prompt_contains_no_hallucination_instruction(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "Do NOT invent" in prompt or "ONLY recommend" in prompt


def test_prompt_contains_ranking_instruction(candidates, query):
    prompt = build_prompt(query, candidates)
    assert "rank" in prompt.lower() or "Rank" in prompt


# ── Budget range edge cases ────────────────────────────────────────────────────

def test_prompt_budget_high_shows_plus(candidates):
    q = {"location": "Koramangala", "budget": "high", "min_rating": 4.0}
    prompt = build_prompt(q, candidates)
    assert "1500+" in prompt


def test_prompt_budget_low_range(candidates):
    q = {"location": "Koramangala", "budget": "low", "min_rating": 4.0}
    prompt = build_prompt(q, candidates)
    assert "0" in prompt and "500" in prompt


# ── Empty/missing fields ───────────────────────────────────────────────────────

def test_prompt_no_cuisine_shows_no_preference(candidates):
    q = {"location": "Koramangala", "budget": "medium", "min_rating": 4.0, "cuisine": ""}
    prompt = build_prompt(q, candidates)
    assert "No preference" in prompt


def test_prompt_no_extras_shows_none(candidates):
    q = {"location": "Koramangala", "budget": "medium", "min_rating": 4.0, "extras": ""}
    prompt = build_prompt(q, candidates)
    assert "None" in prompt


def test_prompt_no_location_shows_any(candidates):
    q = {"location": "", "budget": "medium", "min_rating": 4.0}
    prompt = build_prompt(q, candidates)
    assert "Any" in prompt


# ── Error case ─────────────────────────────────────────────────────────────────

def test_prompt_raises_on_empty_candidates(query):
    with pytest.raises(ValueError, match="empty"):
        build_prompt(query, pd.DataFrame())


# ── Token estimator ────────────────────────────────────────────────────────────

def test_token_estimate_reasonable(candidates, query):
    prompt = build_prompt(query, candidates)
    tokens = estimate_token_count(prompt)
    # Prompt with 2 restaurants should be between 100 and 2000 tokens
    assert 100 < tokens < 2000
