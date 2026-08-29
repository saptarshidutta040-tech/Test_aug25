"""
config/settings.py
──────────────────
Central configuration module. Loads all settings from environment variables
defined in the .env file. Raises clear errors at startup if required keys
are missing.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, Tuple
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()

# ─── Python version guard ────────────────────────────────────────────────────
if sys.version_info < (3, 9):
    raise RuntimeError(
        f"Python 3.9+ required. You are running {sys.version}. "
        "Please upgrade your Python version."
    )

# ─── LLM Configuration ───────────────────────────────────────────────────────
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
GROK_API_KEY    = os.getenv("GROK_API_KEY")   # kept for backwards compat
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
LLM_PROVIDER    = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL       = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.5"))
LLM_MAX_TOKENS  = int(os.getenv("LLM_MAX_TOKENS", "1200"))

# ─── Filter Configuration ────────────────────────────────────────────────────
TOP_K_CANDIDATES = int(os.getenv("TOP_K_CANDIDATES", "15"))

# ─── Budget Mapping ──────────────────────────────────────────────────────────
# Maps user-facing budget labels to INR cost-for-two ranges
BUDGET_MAP: Dict[str, Tuple[int, float]] = {
    "low":    (0, 500),
    "medium": (500, 1500),
    "high":   (1500, float("inf")),
}

# ─── Startup Validation ──────────────────────────────────────────────────────
def validate_config() -> None:
    """
    Validate that required configuration is present.
    Call this once at application startup before accepting any user input.
    Raises EnvironmentError with actionable message if anything is missing.
    """
    provider = LLM_PROVIDER.lower()

    if provider == "openai" and not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your OpenAI API key\n"
            "  3. Re-run the application"
        )

    if provider == "gemini" and not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your Gemini API key\n"
            "  3. Re-run the application"
        )

    if provider == "grok" and not GROK_API_KEY:
        raise EnvironmentError(
            "GROK_API_KEY is not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your Grok (xAI) API key\n"
            "  3. Re-run the application"
        )

    if provider == "groq" and not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your Groq API key from console.groq.com\n"
            "  3. Re-run the application"
        )

    if provider not in ("openai", "gemini", "grok", "groq"):
        raise EnvironmentError(
            f"Unsupported LLM_PROVIDER: '{provider}'.\n"
            "  Supported values: openai | gemini | groq"
        )
