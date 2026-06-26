"""Offline test harness — mirrors 04-fullstack-analyzer's FakeClient approach.

Monkeypatches `common.llm.get_client` so `structured_call` never touches the
network or a live LLM. Tests run fully offline.
"""

import json


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
    def __init__(self, responses: list) -> None:
        self._responses = list(responses)
        self.calls: list = []

    def create(self, **kwargs) -> _Completion:
        self.calls.append(kwargs)
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return _Completion(self._responses[idx])


class FakeClient:
    """Stand-in for openai.OpenAI; replays a scripted list of message contents."""

    def __init__(self, responses: list) -> None:
        self.chat = type("Chat", (), {"completions": _Completions(responses)})()

    @property
    def calls(self) -> list:
        return self.chat.completions.calls


VALID_PAYLOAD = json.dumps({"sentiment": "negative"})


def install_fake_client(monkeypatch, responses: list) -> FakeClient:
    """Patch common.llm.get_client so structured_call hits the fake."""
    client = FakeClient(responses)
    import common.llm as llm

    monkeypatch.setattr(llm, "get_client", lambda: client)
    return client
