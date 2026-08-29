# Phase-Wise Implementation Plan
# AI-Powered Restaurant Recommendation System (Zomato)

> **Reference**: [architecture.md](./architecture.md) · [problemstatement.md](./problemstatement.md)  
> **Pattern**: RAG-Lite · **Language**: Python 3.10+  
> **Total Phases**: 6 · **Estimated Total Effort**: ~4–6 days

---

## Implementation Roadmap

```
Phase 1: Project Setup & Environment         [Day 1]
       │
       ▼
Phase 2: Data Ingestion & Preprocessing      [Day 1–2]
       │
       ▼
Phase 3: Filtering & Rule Engine             [Day 2]
       │
       ▼
Phase 4: Prompt Engineering & LLM Integration [Day 3]
       │
       ▼
Phase 5: User Interface & Output Display     [Day 4]
       │
       ▼
Phase 6: Testing, Error Handling & Polish    [Day 5–6]
```

---

## Phase 1 — Project Setup & Environment

> **Goal**: Establish a clean, reproducible project foundation.  
> **Estimated Time**: 2–3 hours  
> **Output**: Runnable project skeleton with all dependencies installed

### 1.1 Initialize Project Structure

Create the following directory and file layout:

```
zomato-ai-recommender/
│
├── data/
│   ├── __init__.py
│   ├── loader.py
│   ├── cleaner.py
│   └── schema.py
│
├── engine/
│   ├── __init__.py
│   ├── filter.py
│   ├── prompt_builder.py
│   └── llm_client.py
│
├── ui/
│   ├── __init__.py
│   ├── input_parser.py
│   └── output_renderer.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── tests/
│   ├── test_data.py
│   ├── test_filter.py
│   ├── test_prompt.py
│   └── test_llm.py
│
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

**Commands**:
```bash
mkdir -p zomato-ai-recommender/{data,engine,ui,config,tests}
cd zomato-ai-recommender
touch main.py requirements.txt .env.example .gitignore README.md
touch data/{__init__,loader,cleaner,schema}.py
touch engine/{__init__,filter,prompt_builder,llm_client}.py
touch ui/{__init__,input_parser,output_renderer}.py
touch config/{__init__,settings}.py
touch tests/{test_data,test_filter,test_prompt,test_llm}.py
```

---

### 1.2 Define Dependencies

**`requirements.txt`**:
```
datasets>=2.14.0          # HuggingFace dataset loader
pandas>=2.0.0             # DataFrame operations
openai>=1.0.0             # OpenAI GPT integration
google-generativeai>=0.3  # Gemini integration (optional)
python-dotenv>=1.0.0      # Environment variable management
rich>=13.0.0              # Beautiful CLI output
jinja2>=3.1.0             # Prompt templating
pytest>=7.4.0             # Unit testing
```

**Install**:
```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### 1.3 Environment Configuration

**`.env.example`**:
```
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=openai               # openai | gemini | llama
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=1200
TOP_K_CANDIDATES=15
```

**`config/settings.py`**:
```python
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
LLM_PROVIDER     = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL        = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE  = float(os.getenv("LLM_TEMPERATURE", 0.5))
LLM_MAX_TOKENS   = int(os.getenv("LLM_MAX_TOKENS", 1200))
TOP_K_CANDIDATES = int(os.getenv("TOP_K_CANDIDATES", 15))

BUDGET_MAP = {
    "low":    (0, 500),
    "medium": (500, 1500),
    "high":   (1500, float("inf")),
}
```

### ✅ Phase 1 Checklist
- [ ] Project directory structure created
- [ ] `requirements.txt` defined and installed
- [ ] Virtual environment active
- [ ] `.env` configured with API keys
- [ ] `config/settings.py` loads env vars correctly

---

## Phase 2 — Data Ingestion & Preprocessing

> **Goal**: Load the Zomato HuggingFace dataset, clean it, and make it queryable.  
> **Estimated Time**: 3–4 hours  
> **Output**: A clean Pandas DataFrame ready for filtering

### 2.1 Define the Data Schema

**`data/schema.py`**:
```python
# Canonical field names after cleaning
REQUIRED_FIELDS = [
    "name",          # str  — Restaurant name
    "location",      # str  — City / neighbourhood
    "cuisine",       # str  — Comma-separated cuisine types
    "cost_for_two",  # int  — Avg cost (INR) for two people
    "rating",        # float — Aggregate rating (0.0–5.0)
    "votes",         # int  — Number of ratings/votes
    "online_order",  # bool — Online ordering available
    "book_table",    # bool — Table reservation available
]

BUDGET_RANGES = {
    "low":    (0, 500),
    "medium": (500, 1500),
    "high":   (1500, float("inf")),
}
```

---

### 2.2 Implement Dataset Loader

**`data/loader.py`**:
```python
from datasets import load_dataset
import pandas as pd

DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"

def load_zomato_dataset() -> pd.DataFrame:
    """Load the Zomato dataset from HuggingFace and return as DataFrame."""
    dataset = load_dataset(DATASET_NAME, split="train")
    df = dataset.to_pandas()
    return df
```

---

### 2.3 Implement Data Cleaner

**`data/cleaner.py`**:
```python
import pandas as pd
from data.schema import REQUIRED_FIELDS

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize the raw Zomato dataset."""

    # 1. Normalize column names (lowercase, strip spaces)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # 2. Drop rows with critical missing values
    df = df.dropna(subset=["name", "location", "cuisine", "rate"])

    # 3. Parse rating — handle "NEW", "–", and "/5" formats
    df["rating"] = df["rate"].apply(_parse_rating)

    # 4. Parse cost_for_two — remove commas, cast to int
    df["cost_for_two"] = (
        df["approx_cost(for_two_people)"]
        .astype(str)
        .str.replace(",", "")
        .apply(lambda x: int(x) if x.isdigit() else None)
    )
    df = df.dropna(subset=["cost_for_two"])
    df["cost_for_two"] = df["cost_for_two"].astype(int)

    # 5. Normalize location and cuisine to lowercase stripped strings
    df["location"] = df["location"].str.strip().str.title()
    df["cuisine"]  = df["cuisines"].str.strip() if "cuisines" in df.columns else df["cuisine"].str.strip()

    # 6. Normalize boolean fields
    df["online_order"] = df["online_order"].str.strip().str.upper() == "YES"
    df["book_table"]   = df["book_table"].str.strip().str.upper() == "YES"

    # 7. Parse votes to int
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    return df[["name", "location", "cuisine", "cost_for_two",
               "rating", "votes", "online_order", "book_table"]]


def _parse_rating(val: str) -> float | None:
    """Convert rating strings like '4.1/5' or 'NEW' to float."""
    val = str(val).strip()
    if val in ["NEW", "–", "-", "nan"]:
        return None
    val = val.replace("/5", "").strip()
    try:
        return float(val)
    except ValueError:
        return None
```

---

### 2.4 Wire Up the Data Pipeline

**`data/__init__.py`**:
```python
from data.loader import load_zomato_dataset
from data.cleaner import clean_dataset

def get_clean_dataframe():
    raw_df = load_zomato_dataset()
    clean_df = clean_dataset(raw_df)
    return clean_df
```

### ✅ Phase 2 Checklist
- [ ] `loader.py` — fetches HuggingFace dataset successfully
- [ ] `cleaner.py` — handles all dirty data edge cases
- [ ] Rating parsing handles "NEW", "–", "4.1/5" formats
- [ ] Cost parsing handles comma-formatted strings
- [ ] Output DataFrame has all `REQUIRED_FIELDS` populated
- [ ] Run `test_data.py` — all tests pass

---

## Phase 3 — Filtering & Rule Engine

> **Goal**: Build rule-based logic to narrow down candidates before LLM processing.  
> **Estimated Time**: 2–3 hours  
> **Output**: A `FilterEngine` class that returns Top-K relevant restaurants

### 3.1 Implement the Filter Engine

**`engine/filter.py`**:
```python
import pandas as pd
from config.settings import BUDGET_MAP, TOP_K_CANDIDATES

class FilterEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def filter(self, query: dict) -> pd.DataFrame:
        """
        Apply sequential filters based on user query.
        Falls back gracefully if no results found.
        """
        df = self.df.copy()

        # Step 1: Filter by location (case-insensitive partial match)
        if query.get("location"):
            mask = df["location"].str.contains(query["location"], case=False, na=False)
            df = df[mask]

        # Step 2: Filter by cuisine (partial match across comma-separated list)
        if query.get("cuisine") and not df.empty:
            mask = df["cuisine"].str.contains(query["cuisine"], case=False, na=False)
            df = df[mask]

        # Step 3: Filter by budget range
        if query.get("budget") and not df.empty:
            low, high = BUDGET_MAP.get(query["budget"], (0, float("inf")))
            df = df[(df["cost_for_two"] >= low) & (df["cost_for_two"] <= high)]

        # Step 4: Filter by minimum rating
        if query.get("min_rating") and not df.empty:
            df = df[df["rating"] >= float(query["min_rating"])]

        # Step 5: Graceful fallback — relax filters if no results
        if df.empty:
            df = self._fallback_filter(query)

        # Step 6: Sort by composite score (rating × log(votes))
        import numpy as np
        df = df.copy()
        df["score"] = df["rating"] * np.log1p(df["votes"])
        df = df.sort_values("score", ascending=False)

        return df.head(TOP_K_CANDIDATES)

    def _fallback_filter(self, query: dict) -> pd.DataFrame:
        """Relax filters progressively to always return some results."""
        # Try without cuisine constraint
        relaxed = self.df.copy()
        if query.get("location"):
            relaxed = relaxed[relaxed["location"].str.contains(
                query["location"], case=False, na=False)]
        if query.get("min_rating"):
            relaxed = relaxed[relaxed["rating"] >= float(query["min_rating"]) - 0.5]
        return relaxed.head(TOP_K_CANDIDATES)
```

---

### 3.2 Filter Logic Flow

```
User Query dict
      │
      ▼  filter by location (str.contains)
      │
      ▼  filter by cuisine  (str.contains)
      │
      ▼  filter by budget   (cost range lookup)
      │
      ▼  filter by min_rating
      │
      ├─── Empty? ──▶ Fallback (relax constraints) ──┐
      │                                              │
      ▼◀─────────────────────────────────────────────┘
  Score = rating × log(1 + votes)
      │
      ▼  head(TOP_K_CANDIDATES)
      │
  Filtered DataFrame (≤15 rows)
```

### ✅ Phase 3 Checklist
- [ ] `FilterEngine` filters correctly by all 4 criteria
- [ ] Composite score `rating × log(votes)` ranks results well
- [ ] Fallback mechanism activates when 0 results returned
- [ ] Edge cases: empty cuisine, missing budget, no ratings
- [ ] Run `test_filter.py` — all tests pass

---

## Phase 4 — Prompt Engineering & LLM Integration

> **Goal**: Build prompt templates and a provider-agnostic LLM client.  
> **Estimated Time**: 4–5 hours  
> **Output**: A working end-to-end recommendation call with LLM response

### 4.1 Build the Prompt Builder

**`engine/prompt_builder.py`**:
```python
import pandas as pd
from jinja2 import Template

RECOMMENDATION_TEMPLATE = """
You are an expert restaurant recommendation assistant.

A user is looking for a restaurant with the following preferences:
- Location    : {{ location }}
- Budget      : {{ budget }} (approx ₹{{ budget_range }} for two)
- Cuisine     : {{ cuisine }}
- Min Rating  : {{ min_rating }} / 5.0
- Extras      : {{ extras if extras else "None specified" }}

Here are the top candidate restaurants filtered from the Zomato dataset:

{% for r in restaurants %}
{{ loop.index }}. {{ r.name }}
   - Cuisine      : {{ r.cuisine }}
   - Rating       : {{ r.rating }} / 5.0  ({{ r.votes }} votes)
   - Cost for Two : ₹{{ r.cost_for_two }}
   - Location     : {{ r.location }}
   - Online Order : {{ "Yes" if r.online_order else "No" }}
   - Book Table   : {{ "Yes" if r.book_table else "No" }}
{% endfor %}

Based on the above data, please:
1. Select and rank the top 3–5 restaurants that BEST match the user's preferences.
2. For each, provide:
   - Restaurant Name, Cuisine, Rating, Cost for Two
   - A 2–3 sentence explanation of why it is a great fit.
3. End with a brief 2–3 sentence overall summary.

Be friendly, clear, and concise. Do NOT invent any information not provided above.
"""

def build_prompt(query: dict, candidates: pd.DataFrame) -> str:
    """Inject user query and candidate data into the prompt template."""
    from config.settings import BUDGET_MAP
    budget_range = BUDGET_MAP.get(query.get("budget", "medium"), (0, 9999))
    budget_str = f"{budget_range[0]}–{budget_range[1]}" if budget_range[1] != float("inf") else f"{budget_range[0]}+"

    template = Template(RECOMMENDATION_TEMPLATE)
    return template.render(
        location=query.get("location", "Any"),
        budget=query.get("budget", "medium"),
        budget_range=budget_str,
        cuisine=query.get("cuisine", "Any"),
        min_rating=query.get("min_rating", 3.5),
        extras=query.get("extras", ""),
        restaurants=candidates.to_dict(orient="records"),
    )
```

---

### 4.2 Build the LLM Client (Provider-Agnostic)

**`engine/llm_client.py`**:
```python
from abc import ABC, abstractmethod
from config.settings import (
    LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, OPENAI_API_KEY, GEMINI_API_KEY
)

class BaseLLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        pass

class OpenAIClient(BaseLLMClient):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful restaurant recommendation assistant."},
                {"role": "user",   "content": prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()

class GeminiClient(BaseLLMClient):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)

    def complete(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()

def get_llm_client() -> BaseLLMClient:
    """Factory — returns the configured LLM client."""
    providers = {
        "openai": OpenAIClient,
        "gemini": GeminiClient,
    }
    cls = providers.get(LLM_PROVIDER)
    if not cls:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
    return cls()
```

---

### 4.3 Error Handling for LLM Calls

Wrap LLM calls with retry logic:
```python
import time

def call_llm_with_retry(client: BaseLLMClient, prompt: str, retries=3) -> str:
    for attempt in range(retries):
        try:
            return client.complete(prompt)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)   # Exponential backoff: 1s, 2s, 4s
    return ""
```

### ✅ Phase 4 Checklist
- [ ] Jinja2 prompt template renders correctly for all input combos
- [ ] `OpenAIClient.complete()` returns valid response
- [ ] `GeminiClient.complete()` returns valid response
- [ ] `get_llm_client()` factory switches providers via `.env`
- [ ] Retry logic handles `RateLimitError`, `Timeout` gracefully
- [ ] Run `test_prompt.py` and `test_llm.py` — all tests pass

---

## Phase 5 — User Interface & Output Display

> **Goal**: Build the input collection layer and the output rendering layer.  
> **Estimated Time**: 3–4 hours  
> **Output**: A polished CLI experience from input to final recommendations

### 5.1 Implement Input Parser

**`ui/input_parser.py`**:
```python
def collect_user_preferences() -> dict:
    """Interactively collect user preferences via CLI."""
    from rich.console import Console
    from rich.prompt import Prompt, FloatPrompt

    console = Console()
    console.print("\n[bold cyan]🍽️  Zomato AI Restaurant Recommender[/bold cyan]\n")

    location   = Prompt.ask("[yellow]📍 Enter your location[/yellow]", default="Bangalore")
    cuisine    = Prompt.ask("[yellow]🍜 Preferred cuisine[/yellow]",   default="Any")
    budget     = Prompt.ask(
        "[yellow]💰 Budget[/yellow]",
        choices=["low", "medium", "high"],
        default="medium"
    )
    min_rating = FloatPrompt.ask("[yellow]⭐ Minimum rating (0–5)[/yellow]", default=4.0)
    extras     = Prompt.ask("[yellow]✨ Any special preferences? (e.g. family-friendly)[/yellow]", default="")

    return {
        "location":   location.strip(),
        "cuisine":    cuisine.strip() if cuisine.lower() != "any" else "",
        "budget":     budget.strip(),
        "min_rating": min_rating,
        "extras":     extras.strip(),
    }

def validate_preferences(prefs: dict) -> dict:
    """Validate and normalize collected preferences."""
    if not (0.0 <= prefs["min_rating"] <= 5.0):
        raise ValueError("Minimum rating must be between 0.0 and 5.0")
    if prefs["budget"] not in ["low", "medium", "high"]:
        raise ValueError("Budget must be one of: low, medium, high")
    return prefs
```

---

### 5.2 Implement Output Renderer

**`ui/output_renderer.py`**:
```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

def render_recommendations(llm_response: str, candidates_df=None):
    """Display LLM recommendations in a rich, formatted layout."""
    console.print("\n")
    console.print(Panel(
        "[bold green]🤖 AI-Powered Recommendations[/bold green]",
        subtitle="Powered by LLM + Zomato Data",
        border_style="green"
    ))
    console.print("\n")
    console.print(llm_response)
    console.print("\n")

    if candidates_df is not None and not candidates_df.empty:
        _render_candidates_table(candidates_df)

def _render_candidates_table(df):
    """Show the filtered candidates as a reference table."""
    table = Table(title="📋 Filtered Candidates", box=box.ROUNDED, show_lines=True)
    table.add_column("Restaurant",   style="bold cyan",  no_wrap=True)
    table.add_column("Cuisine",      style="yellow")
    table.add_column("Rating",       style="green",  justify="center")
    table.add_column("Cost for 2",   style="magenta",justify="right")
    table.add_column("Location",     style="blue")

    for _, row in df.iterrows():
        table.add_row(
            row["name"],
            row["cuisine"][:30],
            f"⭐ {row['rating']}",
            f"₹{row['cost_for_two']}",
            row["location"],
        )
    console.print(table)

def render_error(message: str):
    console.print(Panel(f"[red]❌ {message}[/red]", border_style="red"))

def render_no_results():
    console.print(Panel(
        "[yellow]⚠️  No restaurants found matching your criteria.\nTry relaxing your filters.[/yellow]",
        border_style="yellow"
    ))
```

---

### 5.3 Wire Everything in `main.py`

**`main.py`**:
```python
from data import get_clean_dataframe
from engine.filter import FilterEngine
from engine.prompt_builder import build_prompt
from engine.llm_client import get_llm_client, call_llm_with_retry
from ui.input_parser import collect_user_preferences, validate_preferences
from ui.output_renderer import render_recommendations, render_error, render_no_results

def main():
    # Step 1: Load and clean dataset (once, at startup)
    print("⏳ Loading Zomato dataset...")
    df = get_clean_dataframe()

    # Step 2: Collect & validate user preferences
    prefs = collect_user_preferences()
    prefs = validate_preferences(prefs)

    # Step 3: Filter candidates
    engine = FilterEngine(df)
    candidates = engine.filter(prefs)

    if candidates.empty:
        render_no_results()
        return

    # Step 4: Build prompt
    prompt = build_prompt(prefs, candidates)

    # Step 5: Call LLM
    print("\n⏳ Generating recommendations...")
    llm = get_llm_client()
    try:
        response = call_llm_with_retry(llm, prompt)
    except Exception as e:
        render_error(f"LLM call failed: {e}")
        return

    # Step 6: Display output
    render_recommendations(response, candidates)

if __name__ == "__main__":
    main()
```

### ✅ Phase 5 Checklist
- [ ] `collect_user_preferences()` collects all 5 inputs correctly
- [ ] Input validation catches out-of-range ratings and invalid budgets
- [ ] `render_recommendations()` displays LLM output cleanly
- [ ] Candidates table renders with `rich` formatting
- [ ] `main.py` orchestrates all phases end-to-end
- [ ] Manual end-to-end test passes with valid LLM output

---

## Phase 6 — Testing, Error Handling & Polish

> **Goal**: Harden the system, handle all edge cases, and ensure reliability.  
> **Estimated Time**: 4–6 hours  
> **Output**: A robust, tested, production-ready application

### 6.1 Unit Tests

**`tests/test_data.py`**:
```python
import pytest
from data.cleaner import _parse_rating

def test_parse_rating_standard():
    assert _parse_rating("4.1/5") == 4.1

def test_parse_rating_new():
    assert _parse_rating("NEW") is None

def test_parse_rating_dash():
    assert _parse_rating("–") is None

def test_parse_rating_plain():
    assert _parse_rating("3.8") == 3.8
```

**`tests/test_filter.py`**:
```python
import pandas as pd
from engine.filter import FilterEngine

@pytest.fixture
def sample_df():
    return pd.DataFrame([
        {"name": "Pizza Place", "location": "Bangalore", "cuisine": "Italian",
         "cost_for_two": 800, "rating": 4.2, "votes": 500,
         "online_order": True, "book_table": False},
        {"name": "Biryani Hub", "location": "Delhi", "cuisine": "Indian",
         "cost_for_two": 400, "rating": 4.5, "votes": 1200,
         "online_order": False, "book_table": True},
    ])

def test_filter_by_location(sample_df):
    engine = FilterEngine(sample_df)
    result = engine.filter({"location": "Bangalore"})
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Pizza Place"

def test_filter_by_budget_low(sample_df):
    engine = FilterEngine(sample_df)
    result = engine.filter({"budget": "low"})
    assert all(result["cost_for_two"] < 500)
```

---

### 6.2 Error Handling Matrix

| Scenario | Detection Point | Response |
|---|---|---|
| Dataset fails to load | `loader.py` | Retry 3x → raise with message |
| All fields null after cleaning | `cleaner.py` | Skip row, log warning |
| Zero candidates after filter | `filter.py` | Activate fallback, relax constraints |
| LLM rate limit hit | `llm_client.py` | Exponential backoff, retry 3x |
| LLM returns empty string | `main.py` | Re-prompt with simplified query |
| Invalid rating input | `input_parser.py` | Re-prompt user with valid range |
| Missing API key | `settings.py` | Raise `EnvironmentError` at startup |

---

### 6.3 Logging

Add structured logging to track system behaviour:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

# Usage example in filter.py
logger.info(f"Filtered to {len(result)} candidates for query: {query}")
logger.warning("No results found; activating fallback filter")
```

---

### 6.4 Final Polish Checklist

- [ ] All `pytest` tests pass (`pytest tests/ -v`)
- [ ] `.env.example` has all required keys documented
- [ ] `README.md` has setup and usage instructions
- [ ] Logging is active across all modules
- [ ] No hardcoded API keys in source code
- [ ] Fallback triggers and recovers cleanly on empty results
- [ ] LLM retry logic tested with mocked failures
- [ ] Output renders correctly on both macOS Terminal and Windows CMD
- [ ] `main.py` exits cleanly with code 0 on success

---

## Summary: Phase Completion Matrix

| Phase | Description | Est. Time | Key Deliverable |
|:---:|---|---|---|
| **1** | Project Setup & Environment | 2–3 hrs | Skeleton, deps, config |
| **2** | Data Ingestion & Preprocessing | 3–4 hrs | Clean Pandas DataFrame |
| **3** | Filtering & Rule Engine | 2–3 hrs | `FilterEngine` class |
| **4** | Prompt Engineering & LLM Integration | 4–5 hrs | End-to-end LLM call |
| **5** | User Interface & Output Display | 3–4 hrs | Full CLI app |
| **6** | Testing, Error Handling & Polish | 4–6 hrs | Robust, tested system |
| | **Total** | **~18–25 hrs** | **Production-ready app** |

---

## Quick Start (After All Phases)

```bash
# 1. Clone and enter project
cd zomato-ai-recommender

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run the application
python main.py

# 5. Run tests
pytest tests/ -v
```
