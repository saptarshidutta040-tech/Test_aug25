"""
main.py
────────
Entrypoint for the Zomato AI Restaurant Recommender.

Pipeline:
    1. Validate config (API keys, provider)
    2. Load & clean Zomato dataset
    3. Collect & validate user preferences (interactive CLI)
    4. Filter candidates via rule engine
    5. Build structured LLM prompt
    6. Call Groq LLM with retry
    7. Render recommendations to terminal

Run:
    python main.py
"""

from __future__ import annotations

import sys


def main() -> None:
    # ── Step 0: Validate environment at startup ───────────────────────────────
    from config.settings import validate_config
    try:
        validate_config()
    except EnvironmentError as e:
        print(f"\n[CONFIG ERROR]\n{e}\n")
        sys.exit(1)

    # ── Step 1: Load dataset ──────────────────────────────────────────────────
    from ui.output_renderer import (
        render_candidates_table,
        render_error,
        render_loading,
        render_llm_unavailable,
        render_no_results,
        render_query_summary,
        render_recommendations,
    )

    render_loading("Loading Zomato dataset")
    from data import get_clean_dataframe
    df = get_clean_dataframe()

    # ── Step 2: Collect user preferences ─────────────────────────────────────
    from ui.input_parser import collect_user_preferences, validate_preferences
    try:
        prefs = collect_user_preferences()
        prefs = validate_preferences(prefs)
    except (KeyboardInterrupt, EOFError):
        print("\n\nBye! 👋")
        sys.exit(0)
    except ValueError as e:
        render_error(str(e))
        sys.exit(1)

    # Show what the user searched for
    render_query_summary(prefs)

    # ── Step 3: Filter candidates ─────────────────────────────────────────────
    from engine.filter import FilterEngine
    render_loading("Filtering restaurants")
    engine = FilterEngine(df)
    candidates = engine.filter(prefs)

    if candidates.empty:
        render_no_results()
        sys.exit(0)

    # ── Step 4: Build prompt ──────────────────────────────────────────────────
    from engine.prompt_builder import build_prompt, estimate_token_count
    prompt = build_prompt(prefs, candidates)

    token_estimate = estimate_token_count(prompt)
    print(f"\n[dim]📝 Prompt ready (~{token_estimate} tokens, {len(candidates)} candidates)[/dim]")

    # ── Step 5: Call LLM ──────────────────────────────────────────────────────
    from engine.llm_client import call_llm_with_retry, get_llm_client
    from config.settings import LLM_MODEL, LLM_PROVIDER

    render_loading(f"Asking {LLM_PROVIDER}/{LLM_MODEL} for recommendations")

    try:
        llm = get_llm_client()
        response = call_llm_with_retry(llm, prompt, retries=3)
    except Exception as e:
        render_error(
            f"LLM call failed after 3 attempts.\n"
            f"Error: {e}\n\n"
            "Showing filtered candidates as fallback."
        )
        render_llm_unavailable(candidates)
        sys.exit(1)

    # ── Step 6: Display recommendations ──────────────────────────────────────
    render_recommendations(response, candidates)


if __name__ == "__main__":
    main()
