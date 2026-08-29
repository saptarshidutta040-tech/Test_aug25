# Architecture: AI-Powered Restaurant Recommendation System

> **Reference**: [problemstatement.md](./problemstatement.md)  
> **System**: Zomato-Inspired AI Recommendation Engine  
> **Pattern**: RAG-Lite (Retrieval + LLM Generation)

---

## 1. High-Level Architecture Overview

The system follows a **RAG-Lite (Retrieval-Augmented Generation)** pattern where structured restaurant data is retrieved and filtered before being passed to an LLM for intelligent, explainable ranking.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        AI RECOMMENDATION SYSTEM                          │
│                                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐                │
│  │  User Layer  │───▶│ Input Parser │───▶│ Data Layer   │                │
│  │  (CLI / UI)  │    │ & Validator  │    │ (HuggingFace)│                │
│  └─────────────┘    └──────────────┘    └──────┬───────┘                │
│                                                 │                        │
│                                         ┌───────▼────────┐              │
│                                         │ Filter & Rank   │              │
│                                         │ (Rule Engine)   │              │
│                                         └───────┬────────┘              │
│                                                 │                        │
│                                         ┌───────▼────────┐              │
│                                         │ Prompt Builder  │              │
│                                         │ (Context Inject)│              │
│                                         └───────┬────────┘              │
│                                                 │                        │
│                                         ┌───────▼────────┐              │
│                                         │   LLM Engine    │              │
│                                         │ (GPT/Gemini/    │              │
│                                         │  LLaMA)         │              │
│                                         └───────┬────────┘              │
│                                                 │                        │
│                                         ┌───────▼────────┐              │
│                                         │ Output Display  │              │
│                                         │ (Formatter)     │              │
│                                         └────────────────┘              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Breakdown

### Layer 1 — User Interface Layer

**Responsibility**: Collect and present information to/from the user.

| Sub-Component | Description |
|---|---|
| `InputCollector` | CLI prompts or UI form to gather user preferences |
| `InputValidator` | Validates fields (e.g., budget range, rating 0–5) |
| `OutputRenderer` | Formats and displays final recommendations |

**Inputs Collected**:
```
{
  "location":    "Bangalore",
  "budget":      "medium",          // low | medium | high
  "cuisine":     "Italian",
  "min_rating":  4.0,
  "extras":      "family-friendly"
}
```

---

### Layer 2 — Data Ingestion & Storage Layer

**Responsibility**: Load, clean, and make the Zomato dataset queryable.

| Sub-Component | Description |
|---|---|
| `DatasetLoader` | Fetches dataset from Hugging Face using `datasets` library |
| `DataCleaner` | Handles nulls, normalizes cost ranges, standardizes cuisines |
| `DataStore` | In-memory Pandas DataFrame or lightweight local DB (SQLite) |

**Dataset Source**:  
[`ManikaSaini/zomato-restaurant-recommendation`](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

**Key Fields Extracted**:

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Restaurant name |
| `location` | `string` | City / area |
| `cuisine` | `string` | Type of food served |
| `cost_for_two` | `int` | Average cost for two people |
| `rating` | `float` | Aggregate rating (0.0 – 5.0) |
| `votes` | `int` | Number of user votes |
| `online_order` | `bool` | Whether online ordering is available |
| `book_table` | `bool` | Whether table booking is available |

**Budget Mapping**:
```
low    → cost_for_two < 500
medium → cost_for_two between 500 and 1500
high   → cost_for_two > 1500
```

---

### Layer 3 — Filtering & Rule Engine

**Responsibility**: Narrow down the dataset to relevant candidates before handing off to the LLM.

```
Raw Dataset (N rows)
       │
       ▼  [Filter by Location]
  Location Match
       │
       ▼  [Filter by Cuisine]
  Cuisine Match
       │
       ▼  [Filter by Budget]
  Budget Match (cost_for_two range)
       │
       ▼  [Filter by Min Rating]
  Rating ≥ min_rating
       │
       ▼  [Sort by votes + rating]
  Top-K Candidates (e.g., top 10–20)
       │
       ▼
  Filtered Candidate List → Prompt Builder
```

**Why pre-filter?**
- Keeps LLM context window manageable
- Reduces hallucination risk (LLM works on real, verified data)
- Improves response speed and cost efficiency

---

### Layer 4 — Prompt Builder

**Responsibility**: Construct a structured, information-dense prompt for the LLM.

**Prompt Template**:
```
You are a restaurant recommendation expert.

A user is looking for a restaurant with the following preferences:
- Location: {location}
- Budget: {budget} (approx ₹{budget_range} for two)
- Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Special Preferences: {extras}

Here are the top candidate restaurants from the Zomato dataset:

{candidate_list_as_structured_text}

Based on the above, please:
1. Rank the top 3–5 restaurants that best match the user's preferences.
2. For each recommendation, provide:
   - Restaurant Name
   - Cuisine
   - Rating & Votes
   - Estimated Cost for Two
   - A 2–3 sentence explanation of why this restaurant is a good fit.
3. Provide a brief overall summary of your recommendations.

Respond in a clear, helpful, and friendly tone.
```

---

### Layer 5 — LLM Engine

**Responsibility**: Reason over the candidate data and produce ranked, explainable recommendations.

| Property | Detail |
|---|---|
| **Role** | Ranking + Explanation Generator |
| **Input** | Structured prompt with candidate restaurant data |
| **Output** | Ranked list with per-restaurant explanations + summary |
| **Compatible Models** | OpenAI GPT-4/3.5, Google Gemini, Meta LLaMA, Mistral |
| **API Pattern** | Standard chat completion (`messages` array) |
| **Temperature** | `0.3 – 0.7` (balanced between determinism and creativity) |
| **Max Tokens** | `800 – 1200` (enough for 5 recommendations + summary) |

**LLM Reasoning Flow**:
```
Candidate Data (structured text)
       │
       ▼
  Semantic Understanding
  (e.g., "family-friendly" → high votes, dine-in, good ambiance rating)
       │
       ▼
  Cross-reference with user preferences
       │
       ▼
  Rank candidates by holistic fit
       │
       ▼
  Generate natural language explanations
       │
       ▼
  Structured JSON or Markdown Output
```

---

### Layer 6 — Output Display Layer

**Responsibility**: Parse LLM output and render it cleanly for the user.

**Output Format per Recommendation**:
```
┌─────────────────────────────────────────────┐
│ 🏆 Rank #1 — Trattoria Italia               │
├─────────────────────────────────────────────┤
│ 🍜 Cuisine     : Italian                    │
│ ⭐ Rating      : 4.6 / 5.0  (1,240 votes)   │
│ 💰 Cost for 2  : ₹1,200                     │
│ 📍 Location    : Koramangala, Bangalore      │
├─────────────────────────────────────────────┤
│ 🤖 AI Insight:                              │
│ Trattoria Italia is a top match for your    │
│ preferences. With a stellar 4.6 rating and  │
│ a cozy family-friendly ambiance, it offers  │
│ authentic wood-fired pizza and pasta within │
│ your medium budget range.                   │
└─────────────────────────────────────────────┘
```

---

## 3. Component Interaction Diagram

```
                     ┌──────────────────────┐
                     │     User / Client     │
                     └──────────┬───────────┘
                                │  preferences dict
                                ▼
                     ┌──────────────────────┐
                     │    InputParser        │
                     │  (validate + normalize)│
                     └──────────┬───────────┘
                                │  validated_query
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
          ┌─────────────────┐    ┌──────────────────────┐
          │  DatasetLoader   │    │   Cache (optional)    │
          │  (HuggingFace)   │    │   Pre-loaded DF       │
          └────────┬────────┘    └──────────┬───────────┘
                   │                        │
                   └───────────┬────────────┘
                               │  raw dataframe
                               ▼
                     ┌──────────────────────┐
                     │    FilterEngine       │
                     │  location → cuisine   │
                     │  → budget → rating    │
                     └──────────┬───────────┘
                                │  top-K candidates
                                ▼
                     ┌──────────────────────┐
                     │    PromptBuilder      │
                     │  template + injection │
                     └──────────┬───────────┘
                                │  filled prompt
                                ▼
                     ┌──────────────────────┐
                     │     LLM API Client    │
                     │  (OpenAI / Gemini /   │
                     │   LLaMA / Mistral)    │
                     └──────────┬───────────┘
                                │  LLM response text
                                ▼
                     ┌──────────────────────┐
                     │    OutputRenderer     │
                     │  (parse + format)     │
                     └──────────┬───────────┘
                                │  final output
                                ▼
                     ┌──────────────────────┐
                     │     User / Client     │
                     └──────────────────────┘
```

---

## 4. Project Directory Structure

```
zomato-ai-recommender/
│
├── data/
│   ├── loader.py            # HuggingFace dataset loader
│   ├── cleaner.py           # Preprocessing & normalization
│   └── schema.py            # Field definitions & budget mapping
│
├── engine/
│   ├── filter.py            # Rule-based filtering logic
│   ├── prompt_builder.py    # Prompt template & injection
│   └── llm_client.py        # LLM API abstraction (OpenAI/Gemini etc.)
│
├── ui/
│   ├── input_parser.py      # Collect and validate user preferences
│   └── output_renderer.py   # Format and display recommendations
│
├── config/
│   └── settings.py          # API keys, model name, top-K, budget thresholds
│
├── main.py                  # Application entrypoint
├── requirements.txt
└── README.md
```

---

## 5. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core implementation |
| **Dataset** | HuggingFace `datasets` | Load Zomato data |
| **Data Manipulation** | Pandas | Filter, sort, process |
| **LLM Integration** | `openai` / `google-generativeai` / `transformers` | LLM API calls |
| **Prompt Management** | Jinja2 / f-strings | Prompt templating |
| **UI** | CLI (`argparse` / `rich`) or Streamlit | User interaction |
| **Configuration** | `python-dotenv` | Manage API keys |
| **Optional DB** | SQLite / DuckDB | Faster querying at scale |

---

## 6. Data Flow Summary

```
[HuggingFace Dataset]
        │
        │  load_dataset()
        ▼
[Pandas DataFrame]
        │
        │  filter(location, cuisine, budget, rating)
        ▼
[Filtered Candidates List]   ← Top 10–20 restaurants
        │
        │  inject into prompt template
        ▼
[LLM Prompt]
        │
        │  API call (chat completion)
        ▼
[LLM Response]
        │
        │  parse & render
        ▼
[Final Output to User]       ← Top 3–5 with explanations
```

---

## 7. Key Design Decisions

| Decision | Rationale |
|---|---|
| **Pre-filter before LLM** | Keeps context small, avoids hallucination, reduces cost |
| **Top-K selection** | Prevents overwhelming the LLM with irrelevant data |
| **LLM for ranking & explanation** | Humans prefer natural language reasoning over raw scores |
| **LLM-agnostic design** | Swap between GPT, Gemini, LLaMA without core code changes |
| **Budget as categories** | Simplifies UX; maps to cost ranges internally |
| **Sorted by votes + rating** | Ensures popular, well-reviewed restaurants are prioritized |

---

## 8. Scalability Considerations

| Concern | Solution |
|---|---|
| Large dataset | Use DuckDB or SQLite for faster filtering |
| High API latency | Cache LLM responses for identical queries |
| Multiple LLM providers | Abstract behind a `BaseLLMClient` interface |
| Multi-city support | Index by city for O(1) location lookups |
| Concurrent users | Async LLM calls using `asyncio` + `httpx` |

---

## 9. Error Handling Strategy

| Failure Point | Handling Approach |
|---|---|
| Dataset load failure | Retry with backoff; fallback to local CSV |
| No restaurants match filters | Relax filters progressively (remove extras → cuisine → budget) |
| LLM API error / timeout | Retry up to 3 times; return filtered list without LLM explanation |
| Empty LLM response | Validate response; prompt again with simplified query |
| Invalid user input | Validate at input layer; return descriptive error messages |

---

## 10. Future Enhancements

- [ ] **Semantic Search**: Use embeddings to match user intent beyond exact keyword filters
- [ ] **User History**: Personalize recommendations based on past interactions
- [ ] **Multi-modal Input**: Accept voice or image input for preferences
- [ ] **Feedback Loop**: Allow users to rate recommendations and retrain filters
- [ ] **Map Integration**: Show restaurants on an interactive map
- [ ] **Real-time Data**: Connect to live Zomato API for up-to-date restaurant info
