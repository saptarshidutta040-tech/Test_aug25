# Zomato AI Restaurant Recommender

An AI-powered restaurant recommendation system that combines structured Zomato data with an LLM to generate personalized, explainable restaurant suggestions.

## Architecture

```
User Input → Filter Engine → Prompt Builder → LLM → Output Display
```

> See [architecture.md](../architecture.md) for the full system design.

## Quick Start

### 1. Set up environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or GEMINI_API_KEY
```

### 3. Run the application

```bash
python main.py
```

### 4. Run tests

```bash
pytest tests/ -v
```

## Project Structure

```
zomato-ai-recommender/
├── data/           # Dataset loading & cleaning (Phase 2)
├── engine/         # Filter, prompt builder, LLM client (Phase 3–4)
├── ui/             # CLI input & output rendering (Phase 5)
├── config/         # Settings & environment config (Phase 1)
├── tests/          # Unit & integration tests (Phase 6)
└── main.py         # Application entrypoint
```

## Dataset

[ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) on HuggingFace.

## Implementation Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Project Setup & Environment | ✅ Complete |
| 2 | Data Ingestion & Preprocessing | 🔲 Pending |
| 3 | Filtering & Rule Engine | 🔲 Pending |
| 4 | Prompt Engineering & LLM Integration | 🔲 Pending |
| 5 | User Interface & Output Display | 🔲 Pending |
| 6 | Testing, Error Handling & Polish | 🔲 Pending |

## References

- [Problem Statement](../problemstatement.md)
- [Architecture](../architecture.md)
- [Implementation Plan](../implementation.md)
- [Edge Cases](../edgecase.md)
- [Evaluation Plan](../eval.md)
