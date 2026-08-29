"""
ui/input_parser.py
───────────────────
Collects and validates user preferences via an interactive Rich CLI.

Collected preferences:
  - location   (str)   — e.g. "Bangalore"
  - cuisine    (str)   — e.g. "Italian" (empty = no preference)
  - budget     (str)   — "low" | "medium" | "high"
  - min_rating (float) — 0.0 – 5.0
  - extras     (str)   — free-text (e.g. "family-friendly, outdoor seating")

Usage:
    from ui.input_parser import collect_user_preferences, validate_preferences
    prefs = collect_user_preferences()
    prefs = validate_preferences(prefs)
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import FloatPrompt, Prompt
from rich.rule import Rule
from rich.text import Text

console = Console()

# ── Budget display hints ──────────────────────────────────────────────────────
BUDGET_HINTS = {
    "low":    "< ₹500 for two",
    "medium": "₹500 – ₹1,500 for two",
    "high":   "> ₹1,500 for two",
}


# ── Public API ────────────────────────────────────────────────────────────────

def collect_user_preferences() -> dict:
    """
    Interactively collect user preferences via a styled Rich CLI.

    Returns:
        Dict with keys: location, cuisine, budget, min_rating, extras.
    """
    _print_banner()

    # ── Location ─────────────────────────────────────────────────────────────
    location = Prompt.ask(
        "[bold yellow]📍 Location[/bold yellow]",
        default="Bangalore",
    )

    # ── Cuisine ───────────────────────────────────────────────────────────────
    cuisine_raw = Prompt.ask(
        "[bold yellow]🍜 Cuisine preference[/bold yellow]  "
        "[dim](e.g. Italian, Chinese — press Enter to skip)[/dim]",
        default="Any",
    )
    cuisine = "" if cuisine_raw.strip().lower() == "any" else cuisine_raw.strip()

    # ── Budget ────────────────────────────────────────────────────────────────
    console.print(
        "\n[dim]Budget options:[/dim] "
        "[green]low[/green] (< ₹500)  "
        "[yellow]medium[/yellow] (₹500–₹1,500)  "
        "[red]high[/red] (> ₹1,500)"
    )
    budget = Prompt.ask(
        "[bold yellow]💰 Budget[/bold yellow]",
        choices=["low", "medium", "high"],
        default="medium",
    )

    # ── Minimum rating ────────────────────────────────────────────────────────
    while True:
        min_rating = FloatPrompt.ask(
            "[bold yellow]⭐ Minimum rating[/bold yellow] [dim](0.0 – 5.0)[/dim]",
            default=4.0,
        )
        if 0.0 <= min_rating <= 5.0:
            break
        console.print("[red]⚠  Rating must be between 0.0 and 5.0. Please try again.[/red]")

    # ── Extra preferences ─────────────────────────────────────────────────────
    extras = Prompt.ask(
        "[bold yellow]✨ Any special requests?[/bold yellow]  "
        "[dim](e.g. family-friendly, outdoor seating — press Enter to skip)[/dim]",
        default="",
    )

    console.print()
    console.print(Rule("[dim]Searching restaurants...[/dim]"))
    console.print()

    return {
        "location":   location.strip(),
        "cuisine":    cuisine,
        "budget":     budget.strip(),
        "min_rating": float(min_rating),
        "extras":     extras.strip(),
    }


def validate_preferences(prefs: dict) -> dict:
    """
    Validate and normalise collected preferences.

    Args:
        prefs: Raw preferences dict from collect_user_preferences().

    Returns:
        Validated preferences dict (unchanged if valid).

    Raises:
        ValueError: If any preference is out of acceptable range.
    """
    if not (0.0 <= prefs.get("min_rating", 0) <= 5.0):
        raise ValueError(
            f"min_rating must be between 0.0 and 5.0, got {prefs['min_rating']}"
        )

    if prefs.get("budget") not in ("low", "medium", "high"):
        raise ValueError(
            f"budget must be one of: low | medium | high, got '{prefs.get('budget')}'"
        )

    # Normalise: empty strings → None where appropriate
    prefs["location"] = prefs.get("location", "").strip() or ""
    prefs["cuisine"]  = prefs.get("cuisine", "").strip() or ""
    prefs["extras"]   = prefs.get("extras", "").strip() or ""

    return prefs


# ── Private helpers ───────────────────────────────────────────────────────────

def _print_banner() -> None:
    """Print the styled application header."""
    title = Text()
    title.append("🍽️  ", style="bold")
    title.append("Zomato", style="bold red")
    title.append(" AI Restaurant Recommender", style="bold white")

    subtitle = Text(
        "Powered by Groq LLM  ·  51,000+ restaurants  ·  RAG-Lite",
        style="dim",
        justify="center",
    )

    console.print()
    console.print(Panel(
        f"{title}\n{subtitle}",
        border_style="bright_red",
        padding=(1, 4),
    ))
    console.print()
    console.print("[dim]Answer the prompts below to get personalised recommendations.[/dim]")
    console.print()
