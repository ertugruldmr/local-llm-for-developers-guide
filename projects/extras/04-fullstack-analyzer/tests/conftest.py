import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).resolve().parents[1] / "backend" / "fixtures" / "reviews.jsonl"


@pytest.fixture
def fixture_rows() -> list[dict]:
    with FIXTURE.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Completion:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs) -> _Completion:
        self.calls.append(kwargs)
        # Replay scripted responses; repeat the last one if over-called.
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return _Completion(self._responses[idx])


class FakeClient:
    """Stand-in for openai.OpenAI; replays a scripted list of message contents."""

    def __init__(self, responses: list[str]) -> None:
        self.chat = type("Chat", (), {"completions": _Completions(responses)})()

    @property
    def calls(self) -> list[dict]:
        return self.chat.completions.calls


# A canned, schema-valid ReviewInsight payload reused across tests.
VALID_PAYLOAD = json.dumps(
    {
        "sentiment": "negative",
        "themes": ["sizing", "quality"],
        "sizing_issue": True,
        "churn_risk": "high",
        "summary": "Item runs small and quality is poor; customer is returning it.",
    }
)


def install_fake_client(monkeypatch, responses: list[str]) -> FakeClient:
    """Patch common.llm.get_client so structured_call hits the fake."""
    client = FakeClient(responses)
    import common.llm as llm

    monkeypatch.setattr(llm, "get_client", lambda: client)
    return client
