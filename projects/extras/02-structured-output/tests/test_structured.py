import json

import pytest
from pydantic import ValidationError

from common.llm import QuarantineError
from demo import ReviewRecord, extract_record

from .conftest import VALID_PAYLOAD, install_fake_client


def test_valid_response_parses_to_model(monkeypatch):
    install_fake_client(monkeypatch, [VALID_PAYLOAD])
    record = extract_record("Runs small and the seams frayed.")
    assert isinstance(record, ReviewRecord)
    assert record.sentiment == "negative"
    assert record.churn_risk == "high"
    assert record.sizing_issue is True


def test_call_requests_json_mode(monkeypatch):
    client = install_fake_client(monkeypatch, [VALID_PAYLOAD])
    extract_record("anything")
    assert client.calls[0]["response_format"] == {"type": "json_object"}


def test_malformed_json_triggers_retry_then_succeeds(monkeypatch):
    # First response is not JSON; structured_call must retry and recover.
    client = install_fake_client(monkeypatch, ["totally not json", VALID_PAYLOAD])
    record = extract_record("Late delivery, broken zipper.")
    assert isinstance(record, ReviewRecord)
    assert len(client.calls) == 2
    # The retry must feed the validator error back to the model.
    retry_msgs = client.calls[1]["messages"]
    assert any("failed schema validation" in m["content"] for m in retry_msgs)


def test_two_consecutive_failures_quarantine(monkeypatch):
    bad = json.dumps({"sentiment": "ecstatic"})  # invalid Literal + missing fields
    client = install_fake_client(monkeypatch, [bad, bad])
    with pytest.raises(QuarantineError):
        extract_record("anything")
    assert len(client.calls) == 2


def test_record_rejects_out_of_contract_value():
    with pytest.raises(ValidationError):
        ReviewRecord(
            sentiment="amazing",  # not in Literal
            themes=["fabric"],
            sizing_issue=False,
            churn_risk="low",
            summary="x",
        )
