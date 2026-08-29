"""
data/__init__.py
─────────────────
Public entry point for the data package.

Usage:
    from data import get_clean_dataframe
    df = get_clean_dataframe()
"""

from __future__ import annotations

import pandas as pd

from data.loader import load_zomato_dataset
from data.cleaner import clean_dataset

# Module-level cache — dataset is loaded once per process
_cached_df: pd.DataFrame | None = None


def get_clean_dataframe(force_reload: bool = False) -> pd.DataFrame:
    """
    Load and clean the Zomato dataset.

    Caches the result in memory so repeated calls are instant.

    Args:
        force_reload: If True, bypass in-memory cache and reload from scratch.

    Returns:
        Clean pandas DataFrame with REQUIRED_FIELDS columns.
    """
    global _cached_df

    if _cached_df is not None and not force_reload:
        return _cached_df

    raw_df    = load_zomato_dataset()
    _cached_df = clean_dataset(raw_df)
    return _cached_df
