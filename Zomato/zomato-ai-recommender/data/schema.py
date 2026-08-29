"""
data/schema.py
──────────────
Canonical field definitions after cleaning, and budget mapping constants.
Based on the real HuggingFace dataset schema (51,717 rows, 17 columns).

Raw dataset columns:
    url, address, name, online_order, book_table, rate, votes, phone,
    location, rest_type, dish_liked, cuisines, approx_cost(for two people),
    reviews_list, menu_item, listed_in(type), listed_in(city)
"""

# Fields that must be present in the cleaned DataFrame
REQUIRED_FIELDS = [
    "name",           # str   — Restaurant name
    "location",       # str   — City / neighbourhood (e.g. "Banashankari")
    "cuisine",        # str   — Comma-separated cuisine types (from 'cuisines')
    "cost_for_two",   # int   — Avg cost (INR) for two (from 'approx_cost(for two people)')
    "rating",         # float — Aggregate rating 0.0–5.0 (parsed from 'rate')
    "votes",          # int   — Number of ratings/votes
    "online_order",   # bool  — Online ordering available
    "book_table",     # bool  — Table reservation available
]

# Raw dataset → cleaned field name mapping
RAW_TO_CLEAN = {
    "name":                          "name",
    "location":                      "location",
    "cuisines":                      "cuisine",
    "approx_cost(for two people)":   "cost_for_two",
    "rate":                          "rating",     # needs parsing
    "votes":                         "votes",
    "online_order":                  "online_order",
    "book_table":                    "book_table",
}

# Budget category → INR cost-for-two range
BUDGET_RANGES = {
    "low":    (0, 500),
    "medium": (500, 1500),
    "high":   (1500, float("inf")),
}
