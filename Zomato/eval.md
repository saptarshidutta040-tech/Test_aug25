# Evaluation Plan: AI-Powered Restaurant Recommendation System

> **Reference**: [architecture.md](./architecture.md) · [implementation.md](./implementation.md)  
> **System**: Zomato-Inspired AI Recommendation Engine (RAG-Lite)  
> **Evaluation Scope**: Data Pipeline · Filter Engine · Prompt Quality · LLM Output · End-to-End UX

---

## Evaluation Framework Overview

```
┌──────────────────────────────────────────────────────────┐
│                   EVALUATION LAYERS                       │
│                                                          │
│  L1: Unit Tests         → Individual component checks    │
│  L2: Integration Tests  → Layer-to-layer data flow       │
│  L3: LLM Output Eval    → Quality of recommendations     │
│  L4: End-to-End Tests   → Full pipeline, real queries    │
│  L5: Performance Tests  → Speed, memory, scalability     │
│  L6: User Experience    → Output clarity & usefulness    │
└──────────────────────────────────────────────────────────┘
```

---

## L1 — Unit Tests (Component Level)

> **Goal**: Verify each individual module works correctly in isolation.  
> **Tool**: `pytest`  
> **Run**: `pytest tests/ -v --tb=short`

---

### L1.1 — Data Cleaner (`data/cleaner.py`)

| Test ID | Test Description | Input | Expected Output |
|---|---|---|---|
| `T-DC-01` | Parse standard rating | `"4.1/5"` | `4.1` |
| `T-DC-02` | Parse "NEW" rating | `"NEW"` | `None` |
| `T-DC-03` | Parse dash rating | `"–"` | `None` |
| `T-DC-04` | Parse plain float | `"3.8"` | `3.8` |
| `T-DC-05` | Parse rating with spaces | `" 4.2/5 "` | `4.2` |
| `T-DC-06` | Parse cost with commas | `"1,200"` | `1200` |
| `T-DC-07` | Parse cost with currency | `"₹800"` | `800` |
| `T-DC-08` | Parse invalid cost | `"N/A"` | `None` |
| `T-DC-09` | Normalize location casing | `"bangalore"` | `"Bangalore"` |
| `T-DC-10` | Drop rows with null name | Row with `name=NaN` | Row excluded |
| `T-DC-11` | Deduplicate same name+location | 2 identical rows | 1 row retained |
| `T-DC-12` | Boolean online_order parse | `"Yes"` / `"No"` | `True` / `False` |

```python
# tests/test_data.py
import pytest
from data.cleaner import _parse_rating, clean_dataset
import pandas as pd

@pytest.mark.parametrize("val,expected", [
    ("4.1/5", 4.1),
    ("NEW",   None),
    ("–",     None),
    ("3.8",   3.8),
    (" 4.2/5 ", 4.2),
    ("nan",   None),
])
def test_parse_rating(val, expected):
    assert _parse_rating(val) == expected
```

---

### L1.2 — Filter Engine (`engine/filter.py`)

| Test ID | Test Description | Input | Expected Output |
|---|---|---|---|
| `T-FE-01` | Filter by exact location | `location="Bangalore"` | Only Bangalore rows |
| `T-FE-02` | Filter by partial location | `location="Bangal"` | Bangalore rows matched |
| `T-FE-03` | Filter by cuisine substring | `cuisine="Chinese"` | Rows where cuisine contains "Chinese" |
| `T-FE-04` | Filter by budget=low | `budget="low"` | `cost_for_two < 500` |
| `T-FE-05` | Filter by budget=medium | `budget="medium"` | `500 ≤ cost_for_two ≤ 1500` |
| `T-FE-06` | Filter by budget=high | `budget="high"` | `cost_for_two > 1500` |
| `T-FE-07` | Filter by min_rating | `min_rating=4.5` | All rows with `rating ≥ 4.5` |
| `T-FE-08` | Zero results → fallback | Impossible combo | Non-empty fallback result |
| `T-FE-09` | Result capped at TOP_K | Large dataset, no filters | `len(result) ≤ TOP_K` |
| `T-FE-10` | Composite score sorting | 2 rows: same rating, diff votes | Higher-voted row ranked first |
| `T-FE-11` | Empty location → no location filter | `location=""` | All locations included |
| `T-FE-12` | Case-insensitive cuisine match | `cuisine="italian"` | Matches "Italian" rows |

```python
# tests/test_filter.py
import numpy as np
import pandas as pd
import pytest
from engine.filter import FilterEngine

@pytest.fixture
def df():
    return pd.DataFrame([
        {"name": "A", "location": "Bangalore", "cuisine": "Italian, Continental",
         "cost_for_two": 800, "rating": 4.3, "votes": 500,
         "online_order": True, "book_table": False},
        {"name": "B", "location": "Delhi", "cuisine": "Chinese",
         "cost_for_two": 400, "rating": 4.6, "votes": 1500,
         "online_order": False, "book_table": True},
        {"name": "C", "location": "Bangalore", "cuisine": "Indian",
         "cost_for_two": 1200, "rating": 3.9, "votes": 200,
         "online_order": True, "book_table": False},
    ])

def test_filter_location(df):
    result = FilterEngine(df).filter({"location": "Bangalore"})
    assert all(result["location"] == "Bangalore")

def test_fallback_on_zero_results(df):
    result = FilterEngine(df).filter({
        "location": "Tokyo", "cuisine": "Mexican",
        "budget": "low", "min_rating": 5.0
    })
    assert len(result) > 0   # fallback must return something
```

---

### L1.3 — Prompt Builder (`engine/prompt_builder.py`)

| Test ID | Test Description | Expected |
|---|---|---|
| `T-PB-01` | All fields populated in output | Location, budget, cuisine present in rendered string |
| `T-PB-02` | Candidate restaurants appear in prompt | Each restaurant name appears once |
| `T-PB-03` | Empty extras renders gracefully | No `None` or `""` visible in prompt |
| `T-PB-04` | Special chars in restaurant name | No Jinja2 render error |
| `T-PB-05` | Prompt contains ranking instruction | String `"Rank"` present in output |
| `T-PB-06` | No hallucination instruction present | `"Do NOT invent"` in prompt |

```python
# tests/test_prompt.py
from engine.prompt_builder import build_prompt
import pandas as pd

def test_prompt_contains_location():
    candidates = pd.DataFrame([{
        "name": "Test Place", "cuisine": "Italian", "rating": 4.2,
        "votes": 300, "cost_for_two": 800, "location": "Bangalore",
        "online_order": True, "book_table": False
    }])
    prompt = build_prompt({"location": "Bangalore", "cuisine": "Italian",
                           "budget": "medium", "min_rating": 4.0, "extras": ""}, candidates)
    assert "Bangalore" in prompt
    assert "Test Place" in prompt
    assert "Do NOT invent" in prompt
```

---

### L1.4 — Input Validator (`ui/input_parser.py`)

| Test ID | Test Description | Input | Expected |
|---|---|---|---|
| `T-IV-01` | Valid rating accepted | `4.0` | Returns `4.0` |
| `T-IV-02` | Rating > 5.0 rejected | `6.0` | Raises `ValueError` |
| `T-IV-03` | Negative rating rejected | `-1.0` | Raises `ValueError` |
| `T-IV-04` | Invalid budget rejected | `"moderate"` | Raises `ValueError` |
| `T-IV-05` | Valid budget accepted | `"medium"` | Returns `"medium"` |

---

## L2 — Integration Tests (Layer-to-Layer)

> **Goal**: Verify data flows correctly between connected components.  
> **Tool**: `pytest` with real or mocked data

---

### L2.1 — Data → Filter Pipeline

| Test ID | Flow | Assertion |
|---|---|---|
| `T-INT-01` | `load_dataset → clean_dataset` | Output DataFrame has all `REQUIRED_FIELDS` |
| `T-INT-02` | `clean_dataset → FilterEngine` | FilterEngine accepts and filters clean DF without error |
| `T-INT-03` | `FilterEngine → build_prompt` | `build_prompt()` receives valid non-empty DataFrame |

---

### L2.2 — Filter → Prompt → LLM Pipeline

| Test ID | Flow | Assertion |
|---|---|---|
| `T-INT-04` | `build_prompt(candidates)` | Rendered prompt is a non-empty string |
| `T-INT-05` | `llm_client.complete(prompt)` (mocked) | Returns non-empty string without exception |
| `T-INT-06` | End-to-end with mocked LLM | `main()` runs without exception using mock LLM |

```python
# Mock LLM for integration testing
from unittest.mock import MagicMock, patch

def test_end_to_end_mocked_llm(sample_df):
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "Here are my top recommendations..."

    with patch("engine.llm_client.get_llm_client", return_value=mock_llm):
        from engine.filter import FilterEngine
        from engine.prompt_builder import build_prompt

        candidates = FilterEngine(sample_df).filter({"location": "Bangalore"})
        prompt = build_prompt({"location": "Bangalore", "cuisine": "Italian",
                               "budget": "medium", "min_rating": 4.0}, candidates)
        response = mock_llm.complete(prompt)

        assert len(response) > 0
```

---

## L3 — LLM Output Quality Evaluation

> **Goal**: Assess whether the LLM's recommendations are accurate, relevant, and well-reasoned.  
> **Method**: Human evaluation rubric + automated checks

---

### L3.1 — Evaluation Rubric (Per Recommendation)

Score each LLM recommendation on a **1–5 scale**:

| Criterion | 1 (Poor) | 3 (Acceptable) | 5 (Excellent) |
|---|---|---|---|
| **Relevance** | Restaurant doesn't match any preference | Matches some preferences | Perfectly matches all preferences |
| **Accuracy** | Recommends non-existent restaurant | Names exist but details wrong | Names and details match dataset exactly |
| **Explanation Quality** | No reason given | Generic reason given | Specific, personalised reasoning |
| **Ranking Logic** | Random order | Loosely ordered | Clearly ordered by preference fit |
| **Tone & Clarity** | Confusing or robotic | Readable | Friendly, clear, and helpful |

---

### L3.2 — Automated Output Checks

```python
def evaluate_llm_response(response: str, candidates_df, query: dict) -> dict:
    """
    Automated quality checks on LLM response.
    Returns a dict of check results.
    """
    results = {}

    # Check 1: Response is non-empty
    results["non_empty"] = bool(response.strip())

    # Check 2: No hallucinated restaurant names
    candidate_names = set(candidates_df["name"].str.lower().tolist())
    mentioned = [name for name in candidate_names if name in response.lower()]
    results["no_hallucination"] = all(
        name.lower() in candidate_names
        for name in extract_restaurant_names(response)
    )

    # Check 3: Location mentioned in response
    results["location_referenced"] = query["location"].lower() in response.lower()

    # Check 4: At least 1 restaurant recommended
    results["has_recommendations"] = any(
        name in response for name in candidates_df["name"]
    )

    # Check 5: Response length is reasonable
    results["adequate_length"] = 100 <= len(response) <= 3000

    return results
```

---

### L3.3 — Golden Test Set

Manually curated query-expectation pairs to verify LLM quality:

| Test ID | Query | Expected Behaviour |
|---|---|---|
| `T-LLM-01` | `{location: "Bangalore", cuisine: "Italian", budget: "medium", min_rating: 4.0}` | Top result is an Italian restaurant in Bangalore with rating ≥ 4.0 |
| `T-LLM-02` | `{location: "Delhi", cuisine: "Any", budget: "low", min_rating: 3.5}` | Results within budget `< ₹500`; no Italian/high-end picks |
| `T-LLM-03` | `{location: "Mumbai", cuisine: "Chinese", budget: "high", extras: "family-friendly"}` | Explanation references "family" or "ambiance" or "group" |
| `T-LLM-04` | `{location: "Bangalore", cuisine: "Ethiopian", budget: "medium", min_rating: 4.0}` | Fallback triggered; response notes alternative options |
| `T-LLM-05` | All defaults, no preferences | 3–5 well-explained results from varied cuisines |

---

### L3.4 — Hallucination Rate Metric

```
Hallucination Rate = (# LLM-mentioned names NOT in candidates) / (# total names mentioned)

Target: Hallucination Rate = 0%
Acceptable: < 5% (1 out of 20 runs may hallucinate)
```

---

## L4 — End-to-End Tests

> **Goal**: Validate the full pipeline from user input to final output with realistic data.

---

### L4.1 — Standard Scenario Tests

| Test ID | Scenario | Pass Criteria |
|---|---|---|
| `T-E2E-01` | Happy path: valid location + cuisine + budget + rating | Top 3–5 results displayed with AI explanation |
| `T-E2E-02` | Empty cuisine field | Results returned using only location + budget + rating |
| `T-E2E-03` | Unknown location (no matches) | Fallback activates; results displayed with note |
| `T-E2E-04` | Budget = "low" in a high-cost city | Fallback activates; results still shown |
| `T-E2E-05` | All defaults used | Non-empty output with ≥ 3 recommendations |
| `T-E2E-06` | LLM mocked to fail on first attempt | Retry logic triggers; response received on 2nd attempt |
| `T-E2E-07` | LLM mocked to always fail | Filtered candidates table shown; graceful degradation |

---

### L4.2 — End-to-End Test Runner

```bash
# Run full pipeline with a test query (non-interactive mode)
python main.py \
  --location "Bangalore" \
  --cuisine "Italian" \
  --budget "medium" \
  --min-rating 4.0 \
  --extras "family-friendly" \
  --non-interactive
```

> `--non-interactive` flag skips CLI prompts, reads from CLI args directly (add this mode in Phase 6).

---

## L5 — Performance & Scalability Tests

> **Goal**: Ensure the system remains fast and efficient under various data sizes and load conditions.

---

### L5.1 — Benchmark Targets

| Operation | Dataset Size | Target Latency | Acceptable Max |
|---|---|---|---|
| `load_dataset()` | ~50k rows | < 10s (first run) | 30s |
| `clean_dataset()` | ~50k rows | < 2s | 5s |
| `FilterEngine.filter()` | ~50k rows | < 0.5s | 1s |
| `build_prompt()` | 15 candidates | < 0.1s | 0.5s |
| LLM API call | N/A | < 10s | 30s |
| Full pipeline (with LLM) | ~50k rows | < 15s | 45s |

---

### L5.2 — Performance Test Script

```python
# tests/test_performance.py
import time
import pytest
from data import get_clean_dataframe
from engine.filter import FilterEngine

def test_cleaning_speed():
    start = time.time()
    df = get_clean_dataframe()
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Cleaning too slow: {elapsed:.2f}s"

def test_filter_speed(clean_df):
    engine = FilterEngine(clean_df)
    query = {"location": "Bangalore", "cuisine": "Italian",
             "budget": "medium", "min_rating": 4.0}
    start = time.time()
    result = engine.filter(query)
    elapsed = time.time() - start
    assert elapsed < 1.0, f"Filter too slow: {elapsed:.2f}s"

def test_filter_memory(clean_df):
    import tracemalloc
    tracemalloc.start()
    FilterEngine(clean_df).filter({"location": "Bangalore"})
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 50 * 1024 * 1024, f"Memory usage too high: {peak / 1e6:.1f} MB"
```

---

### L5.3 — LLM Cost Estimation

| Parameter | Value |
|---|---|
| Avg prompt tokens | ~600 tokens |
| Avg completion tokens | ~500 tokens |
| Total tokens / call | ~1,100 tokens |
| GPT-4o-mini cost | ~$0.0002 / 1K tokens |
| **Cost per query** | **~$0.00022** |
| Cost per 1,000 queries | **~$0.22** |

> Use `tiktoken` to count prompt tokens before sending:
> ```python
> import tiktoken
> enc = tiktoken.encoding_for_model("gpt-4o-mini")
> token_count = len(enc.encode(prompt))
> assert token_count < 3000, "Prompt too long"
> ```

---

## L6 — User Experience Evaluation

> **Goal**: Ensure the output is clear, useful, and delightful for the end user.

---

### L6.1 — Output Quality Checklist

Run this checklist manually for every major change:

- [ ] Top 3–5 restaurants are shown (never more than 5, never fewer than 1)
- [ ] Each entry shows: Name, Cuisine, Rating, Cost, Location, AI Explanation
- [ ] AI Explanation is 2–3 sentences, specific to user preferences
- [ ] Overall summary paragraph is present at the end
- [ ] No raw JSON or template artifacts visible in output
- [ ] Unicode renders correctly (emojis, ₹ symbol, box-drawing chars)
- [ ] `rich` table renders without wrapping issues on 80-char terminals
- [ ] Fallback message is shown when no results found (not a blank screen)
- [ ] Error messages are descriptive and actionable

---

### L6.2 — Qualitative Scoring Rubric (Manual Review)

After each major phase, run 5 diverse queries and score the output:

| Query Type | Evaluated Dimension |
|---|---|
| Highly specific (location + cuisine + budget + rating + extras) | Relevance + explanation quality |
| Only location provided | Breadth and variety of results |
| Unknown cuisine (fallback) | Fallback message clarity |
| LLM API unavailable (mocked) | Graceful degradation |
| High rating threshold (min 4.8) | Accuracy of rating filtering |

**Score**: Sum of 5 ratings (1–5 each) → Target: **≥ 20 / 25**

---

## Evaluation Summary Dashboard

| Evaluation Layer | Method | Metrics | Target |
|---|---|---|---|
| **L1 Unit Tests** | `pytest` | Pass rate | 100% |
| **L2 Integration Tests** | `pytest` + mocks | Pass rate | 100% |
| **L3 LLM Output Quality** | Rubric + auto-checks | Avg score | ≥ 4/5 |
| **L3 Hallucination Rate** | Name extraction check | Rate | 0% |
| **L4 End-to-End Tests** | Scenario scripts | Pass rate | ≥ 85% |
| **L5 Filter Performance** | `time` + `tracemalloc` | Latency | < 1s |
| **L5 Full Pipeline Latency** | Wall-clock timing | Latency | < 15s |
| **L5 LLM Cost** | Token estimation | Per query | < $0.001 |
| **L6 UX Checklist** | Manual review | Items passing | ≥ 90% |
| **L6 Qualitative Score** | 5-query review | Score | ≥ 20/25 |

---

## Running All Evaluations

```bash
# 1. All unit + integration tests
pytest tests/ -v --tb=short

# 2. Coverage report
pytest tests/ --cov=. --cov-report=term-missing

# 3. Performance benchmarks
pytest tests/test_performance.py -v -s

# 4. LLM golden test set (requires real API key)
pytest tests/test_llm_quality.py -v -s --run-llm

# 5. End-to-end scenario runner
python tests/run_e2e_scenarios.py
```

---

## Evaluation Cadence

| When | What to Run |
|---|---|
| After every code change | L1 Unit Tests (`pytest tests/`) |
| After completing each Phase | L1 + L2 Integration Tests |
| After Phase 4 (LLM integration) | L3 LLM Quality + Hallucination checks |
| After Phase 5 (full app) | L4 End-to-End + L6 UX checklist |
| Before final submission | All layers: L1 through L6 |

---

> **Total Test Cases**: 40+ (Unit: 22 · Integration: 7 · LLM Golden: 5 · E2E: 7)  
> **Evaluation References**: [architecture.md](./architecture.md) · [implementation.md](./implementation.md) · [edgecase.md](./edgecase.md)
