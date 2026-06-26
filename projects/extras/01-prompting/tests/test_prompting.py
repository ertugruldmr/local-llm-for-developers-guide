from demo import (
    FEW_SHOT,
    SentimentLabel,
    build_few_shot_messages,
    build_zero_shot_messages,
    classify,
)

from .conftest import VALID_PAYLOAD, install_fake_client


def test_zero_shot_has_system_and_user_only():
    msgs = build_zero_shot_messages("Runs small.")
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "user"]
    assert msgs[-1]["content"] == "Runs small."
    # Zero-shot must carry no example turns.
    assert all("sentiment" not in m["content"] for m in msgs if m["role"] == "assistant")


def test_few_shot_includes_example_turns():
    msgs = build_few_shot_messages("Runs small.")
    roles = [m["role"] for m in msgs]
    # system, then alternating user/assistant example pairs, then final user.
    assert roles[0] == "system"
    assert roles[-1] == "user"
    assert msgs[-1]["content"] == "Runs small."
    # The few-shot block must be present and ahead of the dynamic review.
    assert FEW_SHOT[0] in msgs
    assert "assistant" in roles
    assert len(msgs) == 2 + len(FEW_SHOT)


def test_few_shot_examples_cover_all_three_classes():
    labels = {
        m["content"].split('"sentiment": "')[1].split('"')[0]
        for m in FEW_SHOT
        if m["role"] == "assistant"
    }
    assert labels == {"positive", "neutral", "negative"}


def test_mocked_response_parses(monkeypatch):
    install_fake_client(monkeypatch, [VALID_PAYLOAD])
    result = classify("Late delivery and a broken zipper.", mode="zero")
    assert isinstance(result, SentimentLabel)
    assert result.sentiment == "negative"


def test_few_shot_mode_sends_example_turns_to_model(monkeypatch):
    client = install_fake_client(monkeypatch, [VALID_PAYLOAD])
    classify("Nice fabric.", mode="few")
    sent = client.calls[0]["messages"]
    assert len(sent) == 2 + len(FEW_SHOT)
    assert any(m["role"] == "assistant" for m in sent)
