"""
engine/filter.py
────────────────
Rule-based filtering engine that narrows the Zomato dataset down to
Top-K relevant restaurant candidates before passing to the LLM.

Filter pipeline (sequential, each step is optional):
    1. Location  — case-insensitive partial match
    2. Cuisine   — case-insensitive partial match (comma-separated values)
    3. Budget    — cost_for_two within INR range
    4. Rating    — rating >= min_rating
    5. Fallback  — progressively relax constraints if 0 results
    6. Score     — rating × log1p(votes), descending
    7. Head      — top TOP_K_CANDIDATES rows

Usage:
    from engine.filter import FilterEngine
    engine = FilterEngine(df)
    candidates = engine.filter(query)
"""

from __future__ import annotations

import re
import numpy as np
import pandas as pd

from config.settings import BUDGET_MAP, TOP_K_CANDIDATES


class FilterEngine:
    """
    Applies sequential rule-based filters to narrow down restaurant candidates.

    Args:
        df: Clean DataFrame from get_clean_dataframe() — must have REQUIRED_FIELDS.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()

    # ── Public API ────────────────────────────────────────────────────────────

    def filter(self, query: dict) -> pd.DataFrame:
        """
        Filter restaurants based on user query and return Top-K candidates.

        Args:
            query: Dict with optional keys:
                - location   (str)   — e.g. "Bangalore"
                - cuisine    (str)   — e.g. "Italian"
                - budget     (str)   — "low" | "medium" | "high"
                - min_rating (float) — e.g. 4.0
                - extras     (str)   — free text (not used for filtering)

        Returns:
            DataFrame with ≤ TOP_K_CANDIDATES rows, sorted by composite score.
        """
        df = self.df.copy()

        # Step 1: Filter by location
        df = self._filter_location(df, query.get("location", ""))

        # Step 2: Filter by cuisine
        if not df.empty:
            df = self._filter_cuisine(df, query.get("cuisine", ""))

        # Step 3: Filter by budget
        if not df.empty:
            df = self._filter_budget(df, query.get("budget", ""))

        # Step 4: Filter by minimum rating
        if not df.empty:
            df = self._filter_rating(df, query.get("min_rating"))

        # Step 5: Fallback if empty — relax constraints progressively
        if df.empty:
            print("⚠️  No exact matches found. Activating fallback filter...")
            df = self._fallback_filter(query)

        # Step 6: Score and sort
        df = self._score_and_sort(df)

        # Step 7: Return top-K
        result = df.head(TOP_K_CANDIDATES).reset_index(drop=True)
        print(f"🔍 Filter returned {len(result)} candidates")
        return result

    # ── Filter steps ──────────────────────────────────────────────────────────

    @staticmethod
    def _filter_location(df: pd.DataFrame, location: str) -> pd.DataFrame:
        """Case-insensitive partial match on location column."""
        if not location or not location.strip():
            return df
        # Escape regex special chars from user input
        pattern = re.escape(location.strip())
        return df[df["location"].str.contains(pattern, case=False, na=False, regex=True)]

    @staticmethod
    def _filter_cuisine(df: pd.DataFrame, cuisine: str) -> pd.DataFrame:
        """Case-insensitive partial match on comma-separated cuisine field."""
        if not cuisine or not cuisine.strip():
            return df
        pattern = re.escape(cuisine.strip())
        return df[df["cuisine"].str.contains(pattern, case=False, na=False, regex=True)]

    @staticmethod
    def _filter_budget(df: pd.DataFrame, budget: str) -> pd.DataFrame:
        """Filter by cost_for_two within the budget range."""
        if not budget or budget not in BUDGET_MAP:
            return df
        low, high = BUDGET_MAP[budget]
        return df[(df["cost_for_two"] >= low) & (df["cost_for_two"] <= high)]

    @staticmethod
    def _filter_rating(df: pd.DataFrame, min_rating: float | None) -> pd.DataFrame:
        """Filter rows where rating >= min_rating."""
        if min_rating is None:
            return df
        try:
            threshold = float(min_rating)
        except (TypeError, ValueError):
            return df
        return df[df["rating"] >= threshold]

    @staticmethod
    def _score_and_sort(df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite score = rating × log1p(votes) and sort descending.
        This rewards highly rated AND highly reviewed restaurants.
        """
        df = df.copy()
        df["_score"] = df["rating"] * np.log1p(df["votes"])
        df = df.sort_values("_score", ascending=False)
        return df.drop(columns=["_score"])

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _fallback_filter(self, query: dict) -> pd.DataFrame:
        """
        Progressively relax constraints to always return some results.

        Cascade:
            1. Keep location + relax rating by 0.5
            2. Keep only location
            3. Return global top-K by score
        """
        relaxed = self.df.copy()

        # Try: location only + relaxed rating
        if query.get("location"):
            location_match = self._filter_location(relaxed, query["location"])
            if not location_match.empty:
                min_r = query.get("min_rating")
                if min_r is not None:
                    relaxed_r = self._filter_rating(location_match, float(min_r) - 0.5)
                    if not relaxed_r.empty:
                        print("   ↩ Fallback: location match + relaxed rating (−0.5)")
                        return relaxed_r
                print("   ↩ Fallback: location match only")
                return location_match

        # Final fallback: global top-K by score
        print("   ↩ Fallback: global top restaurants")
        return self._score_and_sort(relaxed).head(TOP_K_CANDIDATES)
