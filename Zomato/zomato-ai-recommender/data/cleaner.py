"""
data/cleaner.py
───────────────
Cleans and normalizes the raw Zomato dataset into a consistent DataFrame.

Key transformations:
  - Parses 'rate' strings like "4.1/5", "NEW", "–" → float or None
  - Parses 'approx_cost(for two people)' strings like "1,200" → int
  - Normalises location and cuisine casing
  - Converts online_order / book_table "Yes"/"No" → bool
  - Deduplicates by (name, location)
  - Returns only the 8 REQUIRED_FIELDS columns

Real dataset shape: 51,717 rows × 17 columns
Expected output:    ~45,000+ rows × 8 columns (after dropping nulls & dupes)
"""

from __future__ import annotations

import re
import pandas as pd

from data.schema import REQUIRED_FIELDS


# ── Public API ────────────────────────────────────────────────────────────────

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize the raw Zomato DataFrame.

    Args:
        df: Raw DataFrame from load_zomato_dataset()

    Returns:
        Clean DataFrame with only REQUIRED_FIELDS columns.

    Raises:
        AssertionError: If the cleaned DataFrame is empty (corrupt data).
    """
    print(f"🧹 Cleaning dataset ({len(df):,} raw rows)...")

    # Step 1 ── Parse rating from 'rate' column
    df = df.copy()
    df["rating"] = df["rate"].apply(_parse_rating)

    # Step 2 ── Parse cost from 'approx_cost(for two people)'
    cost_col = "approx_cost(for two people)"
    df["cost_for_two"] = df[cost_col].apply(_parse_cost)

    # Step 3 ── Rename 'cuisines' → 'cuisine'
    df["cuisine"] = df["cuisines"].fillna("").str.strip()

    # Step 4 ── Normalise location (Title Case, strip whitespace)
    df["location"] = df["location"].fillna("").str.strip().str.title()

    # Step 5 ── Convert online_order / book_table "Yes"/"No" → bool
    df["online_order"] = _parse_bool_col(df["online_order"])
    df["book_table"]   = _parse_bool_col(df["book_table"])

    # Step 6 ── Ensure votes is int (it's already int64, but guard against NaN)
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    # Step 7 ── Normalise name
    df["name"] = df["name"].fillna("").str.strip()

    # Step 8 ── Drop rows missing critical fields
    df = df.dropna(subset=["rating", "cost_for_two"])
    df = df[df["name"] != ""]
    df = df[df["location"] != ""]

    # Step 9 ── Deduplicate by (name, location) — keep first occurrence
    df = df.drop_duplicates(subset=["name", "location"], keep="first")

    # Step 10 ── Reset index and return only required columns
    df = df[REQUIRED_FIELDS].reset_index(drop=True)

    assert len(df) > 0, (
        "Dataset is empty after cleaning. "
        "Check the source data or cache file."
    )

    print(f"✅ Cleaning complete: {len(df):,} usable rows retained")
    return df


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_rating(val: object) -> float | None:
    """
    Convert raw rating strings to float.

    Examples:
        "4.1/5"  → 4.1
        "NEW"    → None
        "–"      → None
        "-"      → None
        "3.8"    → 3.8
        " 4.2/5" → 4.2
        NaN      → None
    """
    if pd.isna(val):
        return None
    val = str(val).strip()
    if val in ("NEW", "–", "-", "nan", ""):
        return None
    val = val.replace("/5", "").strip()
    try:
        result = float(val)
        # Sanity check: ratings must be between 0 and 5
        return result if 0.0 <= result <= 5.0 else None
    except ValueError:
        return None


def _parse_cost(val: object) -> int | None:
    """
    Convert raw cost strings to integer INR value.

    Examples:
        "800"    → 800
        "1,200"  → 1200
        "₹800"   → 800
        "N/A"    → None
        NaN      → None
    """
    if pd.isna(val):
        return None
    # Remove currency symbols, commas, spaces
    cleaned = re.sub(r"[₹,\s]", "", str(val)).strip()
    if not cleaned or not cleaned.isdigit():
        return None
    cost = int(cleaned)
    # Sanity check: exclude obviously wrong values
    return cost if 0 < cost < 100_000 else None


def _parse_bool_col(series: pd.Series) -> pd.Series:
    """Convert a "Yes"/"No" string Series to bool (default False on unknown)."""
    return series.fillna("No").str.strip().str.upper().map(
        lambda v: True if v == "YES" else False
    )
