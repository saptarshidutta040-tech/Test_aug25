"""
data/loader.py
──────────────
Loads the Zomato restaurant dataset from HuggingFace.
Falls back to a local cached CSV if the network is unavailable.

Dataset: ManikaSaini/zomato-restaurant-recommendation
Shape:   51,717 rows × 17 columns
"""

from __future__ import annotations

import os
import pandas as pd

DATASET_NAME  = "ManikaSaini/zomato-restaurant-recommendation"
CACHE_CSV     = os.path.join(os.path.dirname(__file__), "zomato_cache.csv")
MAX_RETRIES   = 3


def load_zomato_dataset() -> pd.DataFrame:
    """
    Load the Zomato dataset from HuggingFace.
    On first run, downloads and caches locally to data/zomato_cache.csv.
    On subsequent runs, loads from cache for speed.

    Returns:
        Raw pandas DataFrame with all 17 original columns.

    Raises:
        RuntimeError: If the dataset cannot be loaded from HuggingFace
                      and no local cache exists.
    """
    # ── Fast path: use local cache if available ───────────────────────────────
    if os.path.exists(CACHE_CSV):
        print("📦 Loading dataset from local cache...")
        return pd.read_csv(CACHE_CSV, low_memory=False)

    # ── Slow path: download from HuggingFace ─────────────────────────────────
    print("⬇️  Downloading dataset from HuggingFace (first run)...")

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from datasets import load_dataset
            ds = load_dataset(DATASET_NAME, split="train")
            df = ds.to_pandas()

            # Save to cache so subsequent runs are instant
            _save_cache(df)
            print(f"✅ Dataset loaded: {len(df):,} rows × {len(df.columns)} columns")
            return df

        except Exception as e:
            last_error = e
            print(f"⚠️  Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                import time
                time.sleep(2 ** attempt)  # exponential backoff

    raise RuntimeError(
        f"Failed to load dataset after {MAX_RETRIES} attempts.\n"
        f"Last error: {last_error}\n"
        f"Tip: Check your internet connection or place a 'zomato_cache.csv' "
        f"in the data/ directory."
    )


def _save_cache(df: pd.DataFrame) -> None:
    """Persist the raw DataFrame to CSV for offline use."""
    try:
        df.to_csv(CACHE_CSV, index=False)
        print(f"💾 Dataset cached to: {CACHE_CSV}")
    except Exception as e:
        print(f"⚠️  Could not write cache: {e}")
