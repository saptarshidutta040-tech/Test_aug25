"""
engine/prompt_builder.py
─────────────────────────
Builds structured Jinja2 prompts for the LLM by injecting:
  - User query (location, budget, cuisine, min_rating, extras)
  - Filtered candidate restaurants from the dataset

The prompt instructs the LLM to:
  1. Rank top 3–5 restaurants from the candidate list
  2. Explain why each fits the user's needs
  3. Provide an overall summary

Usage:
    from engine.prompt_builder import build_prompt
    prompt = build_prompt(query, candidates_df)
"""

from __future__ import annotations

import pandas as pd
from jinja2 import Template

from config.settings import BUDGET_MAP


# ── Prompt template ───────────────────────────────────────────────────────────

RECOMMENDATION_TEMPLATE = """\
You are an expert restaurant recommendation assistant for Zomato.

A user is looking for a restaurant with the following preferences:
- Location     : {{ location }}
- Budget       : {{ budget }} (approx ₹{{ budget_range }} for two)
- Cuisine      : {{ cuisine if cuisine else "No preference" }}
- Min Rating   : {{ min_rating }} / 5.0
- Special Ask  : {{ extras if extras else "None" }}

Here are the top candidate restaurants filtered from the Zomato dataset:
{% for r in restaurants %}
{{ loop.index }}. {{ r.name }}
   - Cuisine      : {{ r.cuisine }}
   - Rating       : {{ r.rating }} / 5.0  ({{ r.votes }} votes)
   - Cost for Two : ₹{{ r.cost_for_two | int }}
   - Location     : {{ r.location }}
   - Online Order : {{ "Yes" if r.online_order else "No" }}
   - Book Table   : {{ "Yes" if r.book_table else "No" }}
{% endfor %}
Please do the following:
1. Select and rank the TOP 3 to 5 restaurants from the list above that BEST match the user's preferences.
2. For each recommended restaurant, provide:
   - Restaurant Name
   - Cuisine, Rating, and Cost for Two
   - A 2 to 3 sentence explanation of why it is a great fit for this user.
3. End with a short 2 to 3 sentence overall summary of your recommendations.

Important rules:
- ONLY recommend restaurants from the list above. Do NOT invent or add any restaurant not listed.
- Be specific about WHY each restaurant matches the preferences (budget, cuisine, rating, extras).
- Be friendly, clear, and concise.
"""


# ── Public API ────────────────────────────────────────────────────────────────

def build_prompt(query: dict, candidates: pd.DataFrame) -> str:
    """
    Render the recommendation prompt template with user query and candidates.

    Args:
        query:      Dict with user preferences (location, budget, cuisine,
                    min_rating, extras).
        candidates: Filtered DataFrame from FilterEngine (≤ TOP_K rows).

    Returns:
        Fully rendered prompt string ready to send to the LLM.

    Raises:
        ValueError: If candidates DataFrame is empty.
    """
    if candidates.empty:
        raise ValueError(
            "Cannot build prompt: candidates DataFrame is empty. "
            "Ensure the filter engine returned at least one result."
        )

    budget = query.get("budget", "medium")
    low, high = BUDGET_MAP.get(budget, (0, float("inf")))
    if high == float("inf"):
        budget_range = f"{low}+"
    else:
        budget_range = f"{low}–{high}"

    template = Template(RECOMMENDATION_TEMPLATE)
    prompt = template.render(
        location=query.get("location") or "Any",
        budget=budget,
        budget_range=budget_range,
        cuisine=query.get("cuisine", ""),
        min_rating=query.get("min_rating", 3.5),
        extras=query.get("extras", ""),
        restaurants=candidates.to_dict(orient="records"),
    )
    return prompt


def estimate_token_count(prompt: str) -> int:
    """
    Rough token estimate: ~1 token per 4 characters.
    Use tiktoken for exact counts if needed.
    """
    return len(prompt) // 4
