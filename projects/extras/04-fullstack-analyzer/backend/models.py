from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]
ChurnRisk = Literal["low", "medium", "high"]

# Fixed theme vocabulary the LLM must choose from (see prompt in app.py).
THEMES = ["sizing", "fabric", "fit", "color", "delivery", "price", "quality", "service"]


class Review(BaseModel):
    review_text: str
    rating: int = Field(ge=1, le=5)
    recommended: bool
    age: int = Field(ge=0, le=120)
    class_name: str


class ReviewInsight(BaseModel):
    sentiment: Sentiment
    themes: list[str]
    sizing_issue: bool
    churn_risk: ChurnRisk
    summary: str = Field(max_length=160)


class AnalyzeRequest(BaseModel):
    review_text: str


class AnalyzeBatchRequest(BaseModel):
    reviews: list[str]


class AnalyzeBatchResult(BaseModel):
    insights: list[ReviewInsight]
    quarantined: list[str]


class BaselineResult(BaseModel):
    label: Sentiment
    score: float


class CompareRow(BaseModel):
    review_text: str
    llm: Optional[ReviewInsight]
    baseline: Optional[BaselineResult]
