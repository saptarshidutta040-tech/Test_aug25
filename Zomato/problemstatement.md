# Problem Statement: AI-Powered Restaurant Recommendation System (Zomato Use Case)

## Overview

You are tasked with building an **AI-powered restaurant recommendation service** inspired by Zomato. The system should intelligently suggest restaurants based on user preferences by combining structured data with a Large Language Model (LLM).

---

## Objective

Design and implement an application that:

- Takes **user preferences** (such as location, budget, cuisine, and ratings)
- Uses a **real-world dataset** of restaurants
- Leverages an **LLM** to generate personalized, human-like recommendations
- Displays **clear and useful results** to the user

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:  
  [`ManikaSaini/zomato-restaurant-recommendation`](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract relevant fields such as:
  - Restaurant name
  - Location
  - Cuisine
  - Cost
  - Rating
  - And other metadata

---

### 2. User Input

Collect user preferences including:

| Preference | Example Values |
|---|---|
| **Location** | Delhi, Bangalore, Mumbai, etc. |
| **Budget** | Low, Medium, High |
| **Cuisine** | Italian, Chinese, Indian, etc. |
| **Minimum Rating** | e.g., 4.0 and above |
| **Additional Preferences** | Family-friendly, quick service, outdoor seating, etc. |

---

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM reason and rank options effectively

---

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants based on user preferences
- **Explain** why each recommendation fits the user's needs
- Optionally **summarize** the top choices in a narrative format

---

### 5. Output Display

Present top recommendations in a user-friendly format containing:

- 🍽️ **Restaurant Name**
- 🍜 **Cuisine**
- ⭐ **Rating**
- 💰 **Estimated Cost**
- 🤖 **AI-generated explanation**

---

## Architecture Diagram

```
User Input
    │
    ▼
┌─────────────────────┐
│   Preference Parser  │  ← location, budget, cuisine, rating, extras
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Data Ingestion     │  ← Hugging Face Zomato Dataset
│   & Filtering        │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Prompt Builder     │  ← Structured context + user query
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   LLM Engine         │  ← Ranks, explains, and summarizes
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Output Display     │  ← Top N recommendations with explanations
└─────────────────────┘
```

---

## Key Technical Components

| Component | Description |
|---|---|
| **Dataset** | Hugging Face Zomato restaurant dataset |
| **LLM** | Any compatible LLM (e.g., GPT-4, Gemini, LLaMA) |
| **Filtering Logic** | Rule-based pre-filtering before LLM ranking |
| **Prompt Engineering** | Structured prompts for reasoning and ranking |
| **Output Formatter** | Human-readable, structured recommendation display |

---

## Success Criteria

- [ ] Dataset is correctly loaded and preprocessed
- [ ] User input is collected and validated
- [ ] Relevant restaurants are filtered based on preferences
- [ ] LLM generates meaningful, explainable recommendations
- [ ] Output is displayed in a clean, user-friendly format
