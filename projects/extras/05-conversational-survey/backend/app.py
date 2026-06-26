"""P2 · Conversational AI-Survey Bot — backend stub.

SKELETON ONLY. The agent loop, memory window, and compaction (article B5/B6) are
not implemented yet; endpoint bodies raise NotImplementedError. See
../.docs/001.spec-context.md and ../../p2-conversational-survey.md for the plan.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    SessionState,
    StartSessionResult,
    SurveySummary,
    TurnRequest,
)

SYSTEM_PROMPT = (
    "You run an adaptive fashion-retail survey. Probe topics from this fixed "
    "taxonomy: [sizing, fabric, fit, delivery, price, service]. After each answer, "
    "decide whether to ask one focused follow-up or finish. Ask at least 2 and at "
    "most max_follow_ups follow-ups. Return ONLY JSON (FollowUpDecision). When "
    "finishing, return a SurveySummary instead."
)

app = FastAPI(title="Conversational AI-Survey Bot", version="0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/session", response_model=StartSessionResult)
def start_session() -> StartSessionResult:
    raise NotImplementedError("open a session and return the base question")


@app.post("/turn")
def turn(req: TurnRequest) -> object:
    # Drives one agent-loop iteration: record the answer, decide ask-vs-finish,
    # compact older turns when the window threshold is crossed. Returns a
    # FollowUpDecision or, on finish, a SurveySummary.
    raise NotImplementedError("run one agent-loop step (decide -> ask / finish)")


@app.get("/session/{session_id}", response_model=SessionState)
def get_session(session_id: str) -> SessionState:
    raise NotImplementedError("return transcript + running_summary for inspection")


def summarize(state: SessionState) -> SurveySummary:
    raise NotImplementedError("produce the final validated SurveySummary")
