"""
ui/output_renderer.py
──────────────────────
Renders LLM recommendations and candidate data to the terminal using `rich`.

Public functions:
  - render_recommendations(llm_response, candidates_df) — main output
  - render_candidates_table(df)                         — filtered data table
  - render_error(message)                               — styled error panel
  - render_no_results()                                 — empty results notice
  - render_loading(step)                                — inline progress message

Usage:
    from ui.output_renderer import render_recommendations, render_error
"""

from __future__ import annotations

import pandas as pd
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()


# ── Main recommendation output ────────────────────────────────────────────────

def render_recommendations(
    llm_response: str,
    candidates_df: pd.DataFrame | None = None,
) -> None:
    """
    Display the LLM's recommendation text and the filtered candidates table.

    Args:
        llm_response:  Raw text response from the LLM.
        candidates_df: Optional filtered candidates DataFrame for reference table.
    """
    console.print()
    console.print(Rule("[bold green]🤖  AI Recommendations[/bold green]", style="green"))
    console.print()

    # Render LLM response as Markdown for nice formatting
    try:
        console.print(Markdown(llm_response))
    except Exception:
        # Fallback to plain text if markdown parsing fails
        console.print(llm_response)

    console.print()

    # Show filtered candidates reference table
    if candidates_df is not None and not candidates_df.empty:
        console.print(Rule("[dim]Reference: Filtered Candidates[/dim]", style="dim"))
        console.print()
        render_candidates_table(candidates_df)

    console.print()
    console.print(Rule("[dim]End of recommendations[/dim]", style="dim"))
    console.print()


def render_candidates_table(df: pd.DataFrame) -> None:
    """
    Render the filtered candidates as a rich formatted table.

    Args:
        df: Cleaned and filtered candidates DataFrame.
    """
    table = Table(
        title="📋  Filtered Candidates (from Zomato dataset)",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold cyan",
        header_style="bold white on dark_blue",
        border_style="bright_blue",
    )

    table.add_column("#",            style="dim",          width=3,  justify="right")
    table.add_column("Restaurant",   style="bold cyan",    min_width=20, no_wrap=False)
    table.add_column("Cuisine",      style="yellow",       min_width=16)
    table.add_column("Rating",       style="bold green",   width=8,  justify="center")
    table.add_column("Cost / 2",     style="bold magenta", width=10, justify="right")
    table.add_column("Location",     style="blue",         min_width=14)
    table.add_column("Order",        style="dim",          width=7,  justify="center")
    table.add_column("Book",         style="dim",          width=5,  justify="center")

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        cuisine_display = row["cuisine"]
        if len(cuisine_display) > 28:
            cuisine_display = cuisine_display[:26] + "…"

        table.add_row(
            str(i),
            row["name"],
            cuisine_display,
            f"⭐ {row['rating']:.1f}",
            f"₹{int(row['cost_for_two']):,}",
            row["location"],
            "✅" if row["online_order"] else "—",
            "✅" if row["book_table"] else "—",
        )

    console.print(table)


# ── Status / progress messages ────────────────────────────────────────────────

def render_loading(step: str) -> None:
    """Print a styled loading/progress message."""
    console.print(f"\n[dim]⏳  {step}...[/dim]")


def render_query_summary(prefs: dict) -> None:
    """Display a formatted summary of the user's search query."""
    from config.settings import BUDGET_MAP

    budget = prefs.get("budget", "medium")
    low, high = BUDGET_MAP.get(budget, (0, 9999))
    budget_range = f"₹{low}–₹{high}" if high != float("inf") else f"₹{low}+"

    lines = [
        f"[bold]📍 Location    :[/bold]  {prefs.get('location') or '[dim]Any[/dim]'}",
        f"[bold]🍜 Cuisine     :[/bold]  {prefs.get('cuisine') or '[dim]No preference[/dim]'}",
        f"[bold]💰 Budget      :[/bold]  {budget.title()} ({budget_range})",
        f"[bold]⭐ Min Rating  :[/bold]  {prefs.get('min_rating', 3.5)} / 5.0",
        f"[bold]✨ Special Ask :[/bold]  {prefs.get('extras') or '[dim]None[/dim]'}",
    ]

    content = "\n".join(lines)
    console.print(Panel(
        content,
        title="[bold]Your Search[/bold]",
        border_style="bright_yellow",
        padding=(1, 3),
    ))
    console.print()


# ── Error and empty state rendering ──────────────────────────────────────────

def render_error(message: str) -> None:
    """Display a styled error panel."""
    console.print()
    console.print(Panel(
        f"[bold red]❌  Error[/bold red]\n\n{message}",
        border_style="red",
        padding=(1, 3),
    ))
    console.print()


def render_no_results() -> None:
    """Display a styled no-results notice with helpful suggestions."""
    console.print()
    console.print(Panel(
        "[bold yellow]⚠️   No restaurants found[/bold yellow]\n\n"
        "No restaurants match your current filters. Try:\n"
        "  • [cyan]Relaxing your minimum rating[/cyan] (e.g. 3.5 instead of 4.5)\n"
        "  • [cyan]Broadening your cuisine[/cyan] (or leave it blank)\n"
        "  • [cyan]Adjusting your budget[/cyan] (try medium or high)\n"
        "  • [cyan]Checking the location spelling[/cyan]",
        border_style="yellow",
        padding=(1, 3),
    ))
    console.print()


def render_llm_unavailable(candidates_df: pd.DataFrame) -> None:
    """
    Graceful degradation: show filtered candidates when LLM is unavailable.
    """
    console.print()
    console.print(Panel(
        "[yellow]⚠️   AI explanation unavailable[/yellow]\n\n"
        "The LLM service could not be reached. Showing filtered results below.",
        border_style="yellow",
        padding=(1, 3),
    ))
    console.print()
    if not candidates_df.empty:
        render_candidates_table(candidates_df)
