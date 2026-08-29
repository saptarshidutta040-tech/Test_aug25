# Edge Cases: AI-Powered Restaurant Recommendation System

> **Reference**: [architecture.md](./architecture.md) · [implementation.md](./implementation.md)  
> **Coverage**: All 6 architecture layers + cross-cutting concerns  
> **Format**: Edge Case → Detection Point → Expected Behaviour → Handling Strategy

---

## Overview

Edge cases are organized layer-by-layer, mirroring the architecture:

```
Layer 1 — User Input Layer
Layer 2 — Data Ingestion & Storage Layer
Layer 3 — Filtering & Rule Engine
Layer 4 — Prompt Builder
Layer 5 — LLM Engine
Layer 6 — Output Display Layer
Cross-Cutting — Environment, Config, Performance
```

---

## Layer 1 — User Input Edge Cases

### EC-1.1: Empty Location Input

| Field | Detail |
|---|---|
| **Scenario** | User presses Enter without typing a location |
| **Detection** | `input_parser.py` — post-strip empty string |
| **Risk** | Filter engine receives `""`, matches ALL locations → too many candidates |
| **Expected Behaviour** | Treat as "any location"; skip location filter step |
| **Handling** | `if not query["location"]: skip location filter` |

---

### EC-1.2: Location with Typo or Partial Match

| Field | Detail |
|---|---|
| **Scenario** | User types `"Bangalor"` instead of `"Bangalore"` |
| **Risk** | `str.contains()` returns 0 results → triggers unnecessary fallback |
| **Expected Behaviour** | Fuzzy/partial match should still find results |
| **Handling** | Use `str.contains(location, case=False)` — partial match handles most typos. Consider `difflib.get_close_matches()` for stricter inputs |

---

### EC-1.3: Invalid Rating Value

| Field | Detail |
|---|---|
| **Scenario** | User enters `6.5` or `-1` for minimum rating |
| **Risk** | Filter produces zero results (no restaurant has rating > 5) |
| **Expected Behaviour** | Reject input immediately, prompt again with valid range |
| **Handling** | Validate: `0.0 <= min_rating <= 5.0` at input layer before passing downstream |

---

### EC-1.4: Invalid Budget Value

| Field | Detail |
|---|---|
| **Scenario** | User types `"moderate"` instead of `"low"`, `"medium"`, or `"high"` |
| **Risk** | `BUDGET_MAP.get()` returns `None` → runtime error in filter |
| **Expected Behaviour** | Re-prompt with valid choices |
| **Handling** | Enforce `choices=["low", "medium", "high"]` at CLI level; fallback to `"medium"` if programmatic |

---

### EC-1.5: Special Characters in Input

| Field | Detail |
|---|---|
| **Scenario** | User enters `"Café & Bistro"`, `"Peña's"`, SQL-like `"'; DROP TABLE"` |
| **Risk** | Regex errors in `str.contains()`, prompt injection into LLM |
| **Expected Behaviour** | Sanitize inputs; strip SQL-like patterns; escape for prompt |
| **Handling** | Strip leading/trailing whitespace; escape `{`, `}` in Jinja2 templates; never pass raw input directly into SQL |

---

### EC-1.6: Cuisine Not Available in Dataset

| Field | Detail |
|---|---|
| **Scenario** | User requests `"Ethiopian"` cuisine, which doesn't exist in the dataset |
| **Risk** | Zero candidates after cuisine filter |
| **Expected Behaviour** | Inform user no results for that cuisine; suggest top-rated nearby alternatives |
| **Handling** | Fallback: remove cuisine constraint, return results with note: `"No Ethiopian restaurants found. Showing top-rated options in your area."` |

---

### EC-1.7: All Fields Left as Default/Blank

| Field | Detail |
|---|---|
| **Scenario** | User hits Enter for every prompt, using all defaults |
| **Risk** | Filter may return hundreds of unfiltered rows → context overload in LLM |
| **Expected Behaviour** | Cap candidates to `TOP_K` even with no filters |
| **Handling** | `FilterEngine` always applies `.head(TOP_K_CANDIDATES)` as a hard limit |

---

## Layer 2 — Data Ingestion & Preprocessing Edge Cases

### EC-2.1: HuggingFace Dataset Unavailable

| Field | Detail |
|---|---|
| **Scenario** | Network error, HuggingFace API down, or dataset removed |
| **Risk** | Application crashes at startup |
| **Expected Behaviour** | Retry 3 times with exponential backoff; fall back to local cached CSV |
| **Handling** | Wrap `load_dataset()` in try/except; maintain a `data/zomato_cache.csv` as fallback |

```python
try:
    df = load_dataset(DATASET_NAME, split="train").to_pandas()
except Exception:
    df = pd.read_csv("data/zomato_cache.csv")   # fallback
```

---

### EC-2.2: Rating Field in Unexpected Format

| Field | Detail |
|---|---|
| **Scenario** | Rating column contains: `"4.1/5"`, `"NEW"`, `"–"`, `"-"`, `"3.8 "` (trailing space), `NaN` |
| **Risk** | `float()` conversion fails → unhandled exception |
| **Expected Behaviour** | Parse all known formats; unknown formats → `None` (row excluded from rating filter) |
| **Handling** | `_parse_rating()` function handles all variants; rows with `None` rating are excluded only when `min_rating` is specified |

---

### EC-2.3: Cost Field with Commas or Currency Symbols

| Field | Detail |
|---|---|
| **Scenario** | `"1,200"`, `"₹800"`, `"500.0"`, `"N/A"` |
| **Risk** | `int()` cast fails → row dropped or wrong value used |
| **Expected Behaviour** | Strip non-numeric chars, cast to int; `"N/A"` → `None` |
| **Handling** | `str.replace(",", "").replace("₹", "").strip()` before `int()` cast |

---

### EC-2.4: Duplicate Restaurant Entries

| Field | Detail |
|---|---|
| **Scenario** | Same restaurant appears multiple times (different branches or data errors) |
| **Risk** | LLM prompt gets duplicate entries; redundant recommendations |
| **Expected Behaviour** | Deduplicate by `(name, location)` composite key |
| **Handling** | `df.drop_duplicates(subset=["name", "location"], keep="first")` |

---

### EC-2.5: Dataset is Empty After Cleaning

| Field | Detail |
|---|---|
| **Scenario** | All rows fail validation (corrupt dataset file) |
| **Risk** | Application proceeds with empty DataFrame → misleading output |
| **Expected Behaviour** | Raise a clear startup error and halt |
| **Handling** | `assert len(df) > 0, "Dataset is empty after cleaning. Check source data."` |

---

### EC-2.6: Missing Columns in Dataset

| Field | Detail |
|---|---|
| **Scenario** | Dataset schema changes upstream; `votes` or `cuisine` column missing |
| **Risk** | `KeyError` during cleaning or filtering |
| **Expected Behaviour** | Validate required columns at load time; raise descriptive error |
| **Handling** | Check `REQUIRED_FIELDS ⊆ df.columns` immediately after loading |

```python
missing = set(REQUIRED_FIELDS) - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in dataset: {missing}")
```

---

### EC-2.7: Extremely Large Dataset

| Field | Detail |
|---|---|
| **Scenario** | Dataset grows to 100k+ rows; in-memory Pandas becomes slow |
| **Risk** | Slow startup, high memory usage |
| **Expected Behaviour** | Filtering remains fast (< 1s) |
| **Handling** | Pre-index by city on load; use DuckDB for SQL-based filtering at scale |

---

## Layer 3 — Filtering & Rule Engine Edge Cases

### EC-3.1: Zero Results After All Filters

| Field | Detail |
|---|---|
| **Scenario** | No restaurant matches location + cuisine + budget + rating simultaneously |
| **Risk** | Empty candidates list → prompt with no data → LLM hallucinates |
| **Expected Behaviour** | Progressively relax constraints until results are found |
| **Handling Strategy** | Fallback cascade: |

```
Full filter → 0 results?
  → Drop "extras" filter → still 0?
    → Drop cuisine filter → still 0?
      → Drop budget filter → still 0?
        → Drop min_rating constraint → return top-K by score
```

---

### EC-3.2: Only 1–2 Candidates Found

| Field | Detail |
|---|---|
| **Scenario** | Strict filters yield only 1 or 2 restaurants |
| **Risk** | LLM asked to rank "top 3–5" but only 2 exist → LLM fabricates extra ones |
| **Expected Behaviour** | LLM prompt dynamically states the actual count; LLM recommends only what exists |
| **Handling** | Adjust prompt: `"Here are {{ count }} candidate restaurants. Recommend all {{ count }} with explanations."` |

---

### EC-3.3: All Candidates Have the Same Rating

| Field | Detail |
|---|---|
| **Scenario** | All filtered restaurants share an identical rating (e.g., 4.0) |
| **Risk** | Composite score `rating × log(votes)` still differentiates by votes — works correctly |
| **Expected Behaviour** | Higher-voted restaurants ranked first |
| **Handling** | Composite score naturally resolves ties; no special handling needed |

---

### EC-3.4: Location Matches Multiple Cities

| Field | Detail |
|---|---|
| **Scenario** | User types `"Koramangala"` which is a neighbourhood, not a city |
| **Risk** | `str.contains("Koramangala")` may match rows from multiple cities |
| **Expected Behaviour** | Return results from all matching rows (neighbourhood-level matching is valid) |
| **Handling** | Accepted behaviour; partial match is intentional |

---

### EC-3.5: Cuisine Field Contains Multiple Cuisines

| Field | Detail |
|---|---|
| **Scenario** | Dataset has `"North Indian, Chinese, Fast Food"` as a single cuisine string; user requests `"Chinese"` |
| **Risk** | Exact match fails; `str.contains()` needed |
| **Expected Behaviour** | Restaurant is included in results |
| **Handling** | Always use `str.contains()` not `==` for cuisine matching |

---

### EC-3.6: Rating is NaN for All Candidates

| Field | Detail |
|---|---|
| **Scenario** | All matching restaurants have `"NEW"` or missing ratings |
| **Risk** | `min_rating` filter drops everything |
| **Expected Behaviour** | When rating is missing, treat as "unknown" and include if user hasn't explicitly set `min_rating` |
| **Handling** | In fallback: `df[df["rating"].isna() | (df["rating"] >= relaxed_min)]` |

---

## Layer 4 — Prompt Builder Edge Cases

### EC-4.1: Candidate List Too Long for Context Window

| Field | Detail |
|---|---|
| **Scenario** | `TOP_K = 20` and each restaurant has long cuisine/name strings; total prompt exceeds model's token limit |
| **Risk** | API error: `context_length_exceeded` |
| **Expected Behaviour** | Truncate candidate list to fit within safe token budget |
| **Handling** | Estimate tokens: `~50 tokens/restaurant`; for 4096-token models, keep `TOP_K ≤ 15` |

---

### EC-4.2: Special Characters in Restaurant Names Breaking Template

| Field | Detail |
|---|---|
| **Scenario** | Restaurant named `"Café {{ specials }}"` or `"Bar & Grill"` |
| **Risk** | Jinja2 interprets `{{ }}` as template variable → render error |
| **Expected Behaviour** | Names rendered as literal strings |
| **Handling** | Use `{{ r.name | e }}` (Jinja2 escape filter) or pass data as variables, not raw strings |

---

### EC-4.3: Missing Extras / All Fields Optional

| Field | Detail |
|---|---|
| **Scenario** | User provides no `extras` preference |
| **Risk** | Prompt shows `"Special Preferences: None"` — looks unnatural |
| **Expected Behaviour** | Gracefully omit or rephrase the extras line |
| **Handling** | `{{ extras if extras else "No special preferences" }}` |

---

### EC-4.4: Currency Symbol Rendering Issues

| Field | Detail |
|---|---|
| **Scenario** | `₹` symbol may not render in all terminals or LLM contexts |
| **Risk** | Garbled output in some environments |
| **Expected Behaviour** | Consistent symbol display |
| **Handling** | Use `INR` or `Rs.` as fallback if terminal encoding is detected as non-UTF-8 |

---

## Layer 5 — LLM Engine Edge Cases

### EC-5.1: LLM API Rate Limit Exceeded

| Field | Detail |
|---|---|
| **Scenario** | Too many requests in a short window (HTTP 429) |
| **Risk** | Unhandled exception crashes the app |
| **Expected Behaviour** | Retry with exponential backoff up to 3 times |
| **Handling** | Catch `RateLimitError`; wait `2^attempt` seconds before retry |

---

### EC-5.2: LLM Returns Empty or Whitespace-Only Response

| Field | Detail |
|---|---|
| **Scenario** | API call succeeds but `response.choices[0].message.content` is `""` or `"   "` |
| **Risk** | Empty output rendered to user |
| **Expected Behaviour** | Detect empty response; retry once with simplified prompt |
| **Handling** | `if not response.strip(): retry_with_simplified_prompt()` |

---

### EC-5.3: LLM Hallucinates Restaurant Names

| Field | Detail |
|---|---|
| **Scenario** | LLM recommends a restaurant not in the candidate list |
| **Risk** | User gets a fake recommendation they cannot find |
| **Expected Behaviour** | Only names from the provided candidate list should appear in output |
| **Handling** | Add to prompt: `"IMPORTANT: Only recommend restaurants explicitly listed above. Do NOT invent new restaurants."` Post-process: validate mentioned names against candidate list |

---

### EC-5.4: LLM Response Not in Expected Format

| Field | Detail |
|---|---|
| **Scenario** | LLM returns a paragraph instead of a structured ranked list |
| **Risk** | Output renderer cannot parse structured fields |
| **Expected Behaviour** | Render raw LLM text as-is (graceful degradation) |
| **Handling** | Structured parsing is optional; always fall back to raw `console.print(llm_response)` |

---

### EC-5.5: LLM Context Window Exceeded

| Field | Detail |
|---|---|
| **Scenario** | Prompt + completion exceeds model's max token limit (e.g., 4096 tokens for GPT-3.5) |
| **Risk** | `InvalidRequestError: maximum context length exceeded` |
| **Expected Behaviour** | Reduce `TOP_K` and retry |
| **Handling** | Catch error → reduce `TOP_K` by 5 → rebuild prompt → retry once |

---

### EC-5.6: LLM Timeout

| Field | Detail |
|---|---|
| **Scenario** | LLM API takes > 30 seconds to respond |
| **Risk** | App appears frozen |
| **Expected Behaviour** | Timeout after 30s; show filtered candidates without LLM explanation |
| **Handling** | Set `timeout=30` in API call; on `TimeoutError`, show candidates table with message: `"AI explanation unavailable. Showing filtered results."` |

---

### EC-5.7: LLM API Key Invalid or Expired

| Field | Detail |
|---|---|
| **Scenario** | `OPENAI_API_KEY` is wrong, expired, or missing from `.env` |
| **Risk** | `AuthenticationError` at runtime |
| **Expected Behaviour** | Clear error message at startup, not mid-execution |
| **Handling** | Validate API key format at startup; perform a lightweight test call before accepting user input |

---

### EC-5.8: LLM Returns Biased or Inappropriate Content

| Field | Detail |
|---|---|
| **Scenario** | LLM outputs offensive language or discriminatory suggestions |
| **Risk** | Poor user experience, reputational damage |
| **Expected Behaviour** | Content safety filter applied |
| **Handling** | Use provider's moderation endpoint (e.g., OpenAI moderation API) before displaying response |

---

## Layer 6 — Output Display Edge Cases

### EC-6.1: Terminal Does Not Support Unicode / Emoji

| Field | Detail |
|---|---|
| **Scenario** | Running on Windows CMD or a restricted terminal that can't display `🍽️`, `⭐`, `₹` |
| **Risk** | Garbled or missing characters in output |
| **Expected Behaviour** | Degrade gracefully to ASCII equivalents |
| **Handling** | Detect `sys.stdout.encoding`; if not UTF-8, use plain-text fallback: `[FOOD]`, `[STAR]`, `Rs.` |

---

### EC-6.2: Restaurant Name Exceeds Column Width

| Field | Detail |
|---|---|
| **Scenario** | Restaurant name is 80+ characters (e.g., `"The Grand International Hotel & Spa Multi-Cuisine Restaurant"`) |
| **Risk** | `rich` table row wraps awkwardly or overflows |
| **Expected Behaviour** | Truncate with `…` at display limit |
| **Handling** | Set `no_wrap=True` + `max_width=40` on the name column in `rich.Table` |

---

### EC-6.3: Candidates DataFrame is Empty at Render Time

| Field | Detail |
|---|---|
| **Scenario** | Fallback filter also returned 0 rows (extreme case) |
| **Risk** | `for _, row in df.iterrows()` on empty DF renders nothing — but no error message either |
| **Expected Behaviour** | Show a clear "no results" panel |
| **Handling** | Check `candidates.empty` before calling `render_recommendations()`; call `render_no_results()` instead |

---

### EC-6.4: Very Large Number of Votes

| Field | Detail |
|---|---|
| **Scenario** | A restaurant has `votes = 50000` — displayed as a raw integer |
| **Risk** | Long numbers are hard to read in the table |
| **Expected Behaviour** | Format as `50,000` |
| **Handling** | `f"{row['votes']:,}"` — Python's built-in thousands separator |

---

## Cross-Cutting Edge Cases

### EC-X.1: Concurrent / Repeated Calls

| Field | Detail |
|---|---|
| **Scenario** | Multiple users or processes run the CLI simultaneously |
| **Risk** | Shared in-memory DataFrame mutated (if not copied); LLM rate limits hit |
| **Expected Behaviour** | Each call operates on an isolated copy of the DataFrame |
| **Handling** | `FilterEngine.filter()` always operates on `self.df.copy()` |

---

### EC-X.2: Environment Variables Not Loaded

| Field | Detail |
|---|---|
| **Scenario** | `.env` file missing or not in working directory |
| **Risk** | `OPENAI_API_KEY = None` → silent failure until API call |
| **Expected Behaviour** | Fail fast at startup with actionable message |
| **Handling** | Startup check: `if not OPENAI_API_KEY: raise EnvironmentError("OPENAI_API_KEY not set. Copy .env.example to .env")` |

---

### EC-X.3: Python Version Incompatibility

| Field | Detail |
|---|---|
| **Scenario** | User runs with Python 3.8; code uses `float | None` union syntax (3.10+) |
| **Risk** | `SyntaxError` at import |
| **Expected Behaviour** | Clear version error |
| **Handling** | Add version guard in `main.py`: `assert sys.version_info >= (3, 10)` |

---

### EC-X.4: Dependency Version Conflicts

| Field | Detail |
|---|---|
| **Scenario** | `openai>=1.0.0` uses a different API from `openai==0.28` |
| **Risk** | `AttributeError: module 'openai' has no attribute 'OpenAI'` |
| **Expected Behaviour** | Clear import error with fix instructions |
| **Handling** | Pin exact versions in `requirements.txt`; document in README |

---

### EC-X.5: First Run — Dataset Not Yet Cached

| Field | Detail |
|---|---|
| **Scenario** | Very first run downloads the full HuggingFace dataset (can be slow) |
| **Risk** | User sees a frozen terminal with no feedback |
| **Expected Behaviour** | Show progress indicator during download |
| **Handling** | `print("⏳ Loading Zomato dataset (first run may take a moment)...")` before `load_dataset()` |

---

## Edge Case Severity Matrix

| ID | Edge Case | Severity | Likelihood | Priority |
|:---:|---|:---:|:---:|:---:|
| EC-1.3 | Invalid rating input | 🔴 High | High | P0 |
| EC-2.1 | HuggingFace dataset unavailable | 🔴 High | Medium | P0 |
| EC-2.6 | Missing columns in dataset | 🔴 High | Low | P0 |
| EC-5.1 | LLM rate limit exceeded | 🔴 High | High | P0 |
| EC-5.7 | Invalid/missing API key | 🔴 High | High | P0 |
| EC-3.1 | Zero filter results | 🟠 Medium | High | P1 |
| EC-5.3 | LLM hallucinates names | 🟠 Medium | Medium | P1 |
| EC-5.6 | LLM timeout | 🟠 Medium | Medium | P1 |
| EC-2.2 | Unexpected rating format | 🟠 Medium | High | P1 |
| EC-4.1 | Context window exceeded | 🟠 Medium | Medium | P1 |
| EC-1.5 | Special chars / injection | 🟠 Medium | Low | P1 |
| EC-5.2 | Empty LLM response | 🟡 Low | Low | P2 |
| EC-6.1 | Terminal encoding issues | 🟡 Low | Low | P2 |
| EC-3.2 | Too few candidates | 🟡 Low | Medium | P2 |
| EC-2.4 | Duplicate entries | 🟡 Low | High | P2 |
| EC-6.2 | Long restaurant names | 🟡 Low | Medium | P2 |

---

## Testing Edge Cases

Recommended pytest parameterize patterns:

```python
import pytest
from engine.filter import FilterEngine

@pytest.mark.parametrize("location,cuisine,budget,rating,expected_min", [
    ("Bangalore", "Italian", "medium", 4.0, 0),   # Normal case
    ("",          "",        "medium", 4.0, 0),   # EC-1.1: Empty location
    ("Xyz123",    "Italian", "medium", 4.0, 0),   # EC-1.2: Unknown location (fallback)
    ("Bangalore", "Ethiopian","medium",4.0, 0),   # EC-1.6: Unknown cuisine (fallback)
    ("Bangalore", "Italian", "medium", 5.5, None),# EC-1.3: Invalid rating
])
def test_filter_edge_cases(location, cuisine, budget, rating, expected_min, sample_df):
    ...
```

---

> **Last Updated**: Based on [architecture.md](./architecture.md) v1.0  
> **Total Edge Cases Documented**: 30  
> **Priority Breakdown**: P0 (5) · P1 (8) · P2 (7)
