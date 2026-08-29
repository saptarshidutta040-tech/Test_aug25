"""
tests/test_data.py
───────────────────
Unit tests for data/cleaner.py and data/loader.py.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data.cleaner import _parse_rating, _parse_cost, _parse_bool_col, clean_dataset


# ── _parse_rating ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("val,expected", [
    ("4.1/5",   4.1),
    ("NEW",     None),
    ("–",       None),
    ("-",       None),
    ("nan",     None),
    ("",        None),
    ("3.8",     3.8),
    (" 4.2/5 ", 4.2),
    ("5.0/5",   5.0),
    ("0.0",     0.0),
    ("6.0",     None),   # out of range
    ("-1",      None),   # out of range
    (None,      None),
])
def test_parse_rating(val, expected):
    assert _parse_rating(val) == expected


# ── _parse_cost ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("val,expected", [
    ("800",     800),
    ("1,200",   1200),
    ("1,50,000",None),   # > 100_000 sanity cap
    ("0",       None),   # 0 is invalid
    ("N/A",     None),
    ("",        None),
    (None,      None),
    ("₹800",    800),
])
def test_parse_cost(val, expected):
    assert _parse_cost(val) == expected


# ── _parse_bool_col ───────────────────────────────────────────────────────────

def test_parse_bool_col_yes():
    s = pd.Series(["Yes", "YES", "yes"])
    result = _parse_bool_col(s)
    assert list(result) == [True, True, True]


def test_parse_bool_col_no():
    s = pd.Series(["No", "NO", "no"])
    result = _parse_bool_col(s)
    assert list(result) == [False, False, False]


def test_parse_bool_col_null():
    s = pd.Series([None, float("nan")])
    result = _parse_bool_col(s)
    assert list(result) == [False, False]


# ── clean_dataset ─────────────────────────────────────────────────────────────

@pytest.fixture
def raw_sample():
    """Minimal raw DataFrame mimicking real HuggingFace schema."""
    return pd.DataFrame([
        {
            "name": "Jalsa", "location": "banashankari",
            "cuisines": "North Indian, Chinese",
            "approx_cost(for two people)": "800",
            "rate": "4.1/5", "votes": 775,
            "online_order": "Yes", "book_table": "Yes",
        },
        {
            "name": "Pizza Hut", "location": "Koramangala",
            "cuisines": "Italian",
            "approx_cost(for two people)": "1,200",
            "rate": "3.9/5", "votes": 300,
            "online_order": "No", "book_table": "No",
        },
        {
            # Row with bad rating — should be dropped
            "name": "New Place", "location": "Indiranagar",
            "cuisines": "Continental",
            "approx_cost(for two people)": "600",
            "rate": "NEW", "votes": 0,
            "online_order": "Yes", "book_table": "No",
        },
        {
            # Row with bad cost — should be dropped
            "name": "Old Cafe", "location": "MG Road",
            "cuisines": "Cafe",
            "approx_cost(for two people)": "N/A",
            "rate": "4.0/5", "votes": 100,
            "online_order": "No", "book_table": "No",
        },
    ])


def test_clean_dataset_output_columns(raw_sample):
    cleaned = clean_dataset(raw_sample)
    from data.schema import REQUIRED_FIELDS
    assert list(cleaned.columns) == REQUIRED_FIELDS


def test_clean_dataset_drops_bad_rating(raw_sample):
    cleaned = clean_dataset(raw_sample)
    assert "New Place" not in cleaned["name"].values


def test_clean_dataset_drops_bad_cost(raw_sample):
    cleaned = clean_dataset(raw_sample)
    assert "Old Cafe" not in cleaned["name"].values


def test_clean_dataset_location_title_case(raw_sample):
    cleaned = clean_dataset(raw_sample)
    row = cleaned[cleaned["name"] == "Jalsa"]
    assert row.iloc[0]["location"] == "Banashankari"


def test_clean_dataset_rating_parsed(raw_sample):
    cleaned = clean_dataset(raw_sample)
    row = cleaned[cleaned["name"] == "Jalsa"]
    assert row.iloc[0]["rating"] == pytest.approx(4.1)


def test_clean_dataset_cost_parsed(raw_sample):
    cleaned = clean_dataset(raw_sample)
    row = cleaned[cleaned["name"] == "Pizza Hut"]
    assert row.iloc[0]["cost_for_two"] == 1200


def test_clean_dataset_bool_fields(raw_sample):
    cleaned = clean_dataset(raw_sample)
    row = cleaned[cleaned["name"] == "Jalsa"]
    assert row.iloc[0]["online_order"] == True
    assert row.iloc[0]["book_table"] == True


def test_clean_dataset_nonzero_rows(raw_sample):
    cleaned = clean_dataset(raw_sample)
    assert len(cleaned) > 0
