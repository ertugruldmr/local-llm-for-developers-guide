from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]
NextAction = Literal["follow_up_call", "offer_voucher", "no_action", "escalate"]

# Fixed topic taxonomy the bot probes (see survey_config.json / app prompt).
TAXONOMY = ["sizing", "fabric", "fit", "delivery", "price", "service"]


class Turn(BaseModel):
    role: Literal["assistant", "user"]
    content: str


class FollowUpDecision(BaseModel):
    """One step of the agent loop: ask another follow-up or finish."""

    action: Literal["ask", "finish"]
    question: Optional[str] = None  # set when action == "ask"
    rationale: str = Field(max_length=200)


class SurveySummary(BaseModel):
    topics: list[str]
    sentiment: Sentiment
    verbatims: list[str] = Field(max_length=5)
    next_action: NextAction
    summary: str = Field(max_length=280)


class StartSessionResult(BaseModel):
    session_id: str
    opening_question: str


class TurnRequest(BaseModel):
    session_id: str
    answer: str


class SessionState(BaseModel):
    session_id: str
    running_summary: str = ""
    turns: list[Turn] = Field(default_factory=list)
    follow_ups_asked: int = 0
    summary: Optional[SurveySummary] = None
