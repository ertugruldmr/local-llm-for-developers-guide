"""Trivially-green schema import test for the P2 scaffold.

Only asserts the pydantic models import and validate a minimal payload. The agent
loop / endpoints are unimplemented (NotImplementedError) — no behavior is tested
here yet. (Do not rely on this for coverage; it guards the schema contract only.)
"""

from backend.models import FollowUpDecision, SurveySummary, Turn


def test_models_import_and_validate():
    Turn(role="assistant", content="What did you think of the fit?")

    decision = FollowUpDecision(
        action="ask",
        question="Did the fabric feel as described?",
        rationale="probe the fabric topic, not yet covered",
    )
    assert decision.action == "ask"

    summary = SurveySummary(
        topics=["fit", "fabric"],
        sentiment="neutral",
        verbatims=["the fit ran small"],
        next_action="offer_voucher",
        summary="Respondent found the fit small but liked the fabric.",
    )
    assert summary.sentiment == "neutral"
