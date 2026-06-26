# Spec — P1: Survey / Review Analyzer + Theme Miner (primary demo)

**Package:** `04-fullstack-analyzer/` · **Concepts:** A1, A6, B7 · **Difficulty:** ⭐⭐

## Goal
Batch customer reviews through a local LLM, extract structured insight per review, aggregate it into a dashboard, and **compare the LLM against a lightweight DistilBERT classifier** on cost/latency/quality.

## Dataset
[Women's E-Commerce Clothing Reviews](https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews) (23,486 rows, anonymized). Fields used: `Review Text`, `Rating`, `Recommended IND`, `Age`, `Class Name`.

## User stories
- As an analyst, I paste/upload reviews and see sentiment + themes per review and in aggregate.
- As an analyst, I see which themes correlate with low ratings / non-recommendation.
- As a developer, I see a side-by-side of LLM vs DistilBERT (accuracy, ms/req, $/1k).

## Output contract (structured output)
```python
from pydantic import BaseModel
from typing import Literal
class ReviewInsight(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    themes: list[str]            # e.g. ["sizing", "fabric", "delivery", "price"]
    sizing_issue: bool
    churn_risk: Literal["low", "medium", "high"]
    summary: str                 # <= 20 words
```
LLM call uses JSON mode / `response_format`; response is validated against `ReviewInsight`. On validation failure, retry once with the error appended, then quarantine the row.

## Architecture
- **Backend (FastAPI):** `POST /analyze` (batch) → list[ReviewInsight]; `GET /aggregate` → theme/sentiment rollups. Uses `common/llm.py`.
- **Classifier baseline:** `transformers` pipeline with `distilbert-base-multilingual-cased-sentiments-student`; same input, sentiment-only.
- **Frontend (Next.js):** upload/paste box, results table, theme bar chart, sentiment donut, and an LLM-vs-DistilBERT comparison panel.

## Prompt sketch
```
SYSTEM: You label retail product reviews. Return ONLY JSON matching the schema.
        Themes from this fixed list: [sizing, fabric, fit, color, delivery, price, quality, service].
FEW-SHOT: <2 labeled examples>            # A3; later can be RAG-retrieved (B4)
USER: <review text>
```
Static system + few-shot first (enables prompt caching, B3); the dynamic review last.

## Acceptance criteria
- Returns valid `ReviewInsight` for ≥95% of a 200-row sample.
- Dashboard renders aggregates and the comparison panel.
- README documents the cloud swap and the DistilBERT trade-off conclusion.

## Stretch
- Cache identical reviews; add a "dynamic few-shot" mode that retrieves nearest labeled examples (bridges to P3's vector store).
- .NET variant of the backend using the `OpenAI` NuGet SDK.

## Build notes (for the agent)
Implement backend first with a 20-row fixture, then the classifier, then the frontend. Keep all model config in `.env`. Write a pytest that asserts schema validity on the fixture.
