from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]


class FeedbackDoc(BaseModel):
    """One row of the feedback corpus (backend/fixtures/feedback.jsonl)."""

    id: str
    text: str
    product_category: str


class Citation(BaseModel):
    """A single retrieved doc the answer is grounded in."""

    id: str
    snippet: str


class Answer(BaseModel):
    """Grounded RAG answer returned by POST /ask.

    `citations` must reference doc ids that were actually retrieved for the
    question — the grounding contract. The LLM may only cite from the supplied
    context; the API drops any hallucinated id before returning.
    """

    answer: str
    citations: List[Citation]
    confidence: Confidence


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=4, ge=1, le=10)
