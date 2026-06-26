import json

import pytest
from pydantic import ValidationError

from common.llm import QuarantineError
from backend.app import analyze_review
from backend.models import Review, ReviewInsight

from .conftest import VALID_PAYLOAD, install_fake_client


def test_fixture_rows_match_dataset_schema(fixture_rows):
    assert len(fixture_rows) == 20
    for row in fixture_rows:
        model = Review.model_validate(row)
        assert model.review_text
        assert 1 <= model.rating <= 5
        assert isinstance(model.recommended, bool)
        assert model.class_name


def test_every_fixture_row_yields_valid_insight(monkeypatch, fixture_rows):
    install_fake_client(monkeypatch, [VALID_PAYLOAD])
    for row in fixture_rows:
        insight = analyze_review(row["review_text"])
        assert isinstance(insight, ReviewInsight)
        assert insight.sentiment in ("positive", "neutral", "negative")
        assert insight.churn_risk in ("low", "medium", "high")


def test_malformed_json_triggers_retry_then_succeeds(monkeypatch):
    # First response is junk, second is valid -> structured_call must recover.
    client = install_fake_client(monkeypatch, ["not json at all", VALID_PAYLOAD])
    insight = analyze_review("Runs small, returning it.")
    assert isinstance(insight, ReviewInsight)
    assert len(client.calls) == 2

    # The retry message must carry the validator error back to the model.
    retry_msgs = client.calls[1]["messages"]
    assert any("failed schema validation" in m["content"] for m in retry_msgs)


def test_two_consecutive_failures_quarantine(monkeypatch):
    bad = json.dumps({"sentiment": "ecstatic"})  # invalid Literal, missing fields
    client = install_fake_client(monkeypatch, [bad, bad])
    with pytest.raises(QuarantineError):
        analyze_review("anything")
    assert len(client.calls) == 2


def test_insight_rejects_bad_literal():
    with pytest.raises(ValidationError):
        ReviewInsight(
            sentiment="amazing",  # not in Literal
            themes=["fabric"],
            sizing_issue=False,
            churn_risk="low",
            summary="x",
        )
