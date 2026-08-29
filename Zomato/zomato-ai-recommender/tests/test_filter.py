"""
tests/test_filter.py
─────────────────────
Unit tests for engine/filter.py — FilterEngine class.
Tests cover all 4 filter criteria, composite scoring, and fallback logic.
"""

from __future__ import annotations

import pandas as pd
import pytest

from engine.filter import FilterEngine


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def df():
    """Minimal clean DataFrame matching REQUIRED_FIELDS schema."""
    return pd.DataFrame([
        {
            "name": "Trattoria Italia", "location": "Koramangala",
            "cuisine": "Italian, Continental",
            "cost_for_two": 1200.0, "rating": 4.5, "votes": 900,
            "online_order": True, "book_table": True,
        },
        {
            "name": "Biryani Blues", "location": "Indiranagar",
            "cuisine": "North Indian, Biryani",
            "cost_for_two": 450.0, "rating": 4.2, "votes": 1500,
            "online_order": True, "book_table": False,
        },
        {
            "name": "Dragon Palace", "location": "Koramangala",
            "cuisine": "Chinese, Thai",
            "cost_for_two": 800.0, "rating": 3.8, "votes": 300,
            "online_order": False, "book_table": False,
        },
        {
            "name": "The Cafe", "location": "MG Road",
            "cuisine": "Cafe, Continental",
            "cost_for_two": 600.0, "rating": 4.0, "votes": 500,
            "online_order": True, "book_table": False,
        },
        {
            "name": "Spice Garden", "location": "Whitefield",
            "cuisine": "South Indian, Kerala",
            "cost_for_two": 350.0, "rating": 4.3, "votes": 800,
            "online_order": False, "book_table": False,
        },
    ])


# ── Location filter tests ──────────────────────────────────────────────────────

def test_filter_by_exact_location(df):
    result = FilterEngine(df).filter({"location": "Koramangala"})
    assert all("Koramangala" in loc for loc in result["location"])


def test_filter_by_partial_location(df):
    result = FilterEngine(df).filter({"location": "Korama"})
    assert len(result) == 2
    assert all("Koramangala" in loc for loc in result["location"])


def test_filter_empty_location_returns_all(df):
    result = FilterEngine(df).filter({"location": ""})
    assert len(result) == len(df)


def test_filter_location_case_insensitive(df):
    result = FilterEngine(df).filter({"location": "koramangala"})
    assert len(result) == 2


# ── Cuisine filter tests ───────────────────────────────────────────────────────

def test_filter_by_cuisine(df):
    result = FilterEngine(df).filter({"cuisine": "Italian"})
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Trattoria Italia"


def test_filter_cuisine_partial_match(df):
    """'Continental' appears in multiple rows."""
    result = FilterEngine(df).filter({"cuisine": "Continental"})
    assert len(result) == 2


def test_filter_empty_cuisine_returns_all(df):
    result = FilterEngine(df).filter({"cuisine": ""})
    assert len(result) == len(df)


def test_filter_cuisine_case_insensitive(df):
    result = FilterEngine(df).filter({"cuisine": "chinese"})
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Dragon Palace"


# ── Budget filter tests ────────────────────────────────────────────────────────

def test_filter_budget_low(df):
    result = FilterEngine(df).filter({"budget": "low"})
    assert all(row["cost_for_two"] < 500 for _, row in result.iterrows())


def test_filter_budget_medium(df):
    result = FilterEngine(df).filter({"budget": "medium"})
    assert all(500 <= row["cost_for_two"] <= 1500 for _, row in result.iterrows())


def test_filter_budget_high(df):
    """No fixture data costs > ₹1500, so fallback activates — should still return results."""
    result = FilterEngine(df).filter({"budget": "high"})
    # Fallback guarantees a non-empty result even when no exact match exists
    assert len(result) > 0


def test_filter_invalid_budget_returns_all(df):
    result = FilterEngine(df).filter({"budget": "ultra"})
    assert len(result) == len(df)


# ── Rating filter tests ────────────────────────────────────────────────────────

def test_filter_min_rating(df):
    result = FilterEngine(df).filter({"min_rating": 4.2})
    assert all(row["rating"] >= 4.2 for _, row in result.iterrows())


def test_filter_no_min_rating_returns_all(df):
    result = FilterEngine(df).filter({})
    assert len(result) == len(df)


def test_filter_min_rating_zero(df):
    result = FilterEngine(df).filter({"min_rating": 0.0})
    assert len(result) == len(df)


# ── Composite score sorting ────────────────────────────────────────────────────

def test_results_sorted_by_score(df):
    """Higher rating×log(votes) restaurant should come first."""
    result = FilterEngine(df).filter({})
    # Biryani Blues: 4.2 × log1p(1500) ≈ 30.5  — should rank high
    # Trattoria: 4.5 × log1p(900) ≈ 31.0        — should rank high
    # Dragon Palace: 3.8 × log1p(300) ≈ 21.8    — should rank lower
    scores = []
    import numpy as np
    for _, row in result.iterrows():
        scores.append(row["rating"] * np.log1p(row["votes"]))
    assert scores == sorted(scores, reverse=True)


# ── Fallback tests ─────────────────────────────────────────────────────────────

def test_fallback_on_impossible_combo(df):
    """Impossible combination → fallback → non-empty result."""
    result = FilterEngine(df).filter({
        "location": "Tokyo",
        "cuisine": "Mexican",
        "budget": "low",
        "min_rating": 5.0,
    })
    assert len(result) > 0


def test_fallback_location_only(df):
    """Unknown cuisine + valid location → fallback returns location matches."""
    result = FilterEngine(df).filter({
        "location": "Koramangala",
        "cuisine": "Ethiopian",
    })
    assert len(result) > 0


# ── TOP_K cap ─────────────────────────────────────────────────────────────────

def test_result_capped_at_top_k(df):
    from config.settings import TOP_K_CANDIDATES
    result = FilterEngine(df).filter({})
    assert len(result) <= TOP_K_CANDIDATES
