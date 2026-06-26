"""Offline tests for analyze()/_payload/on_analyze/test_connection.

No live server: `app.make_client` is patched to return a FakeClient that
mirrors the OpenAI shape — `.chat.completions.create(...)` returns an object
whose `choices[0].message` has `.content` and `.model_extra`, and
`.models.list()` returns an object with `.data` of items having `.id`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest
from openai import APIConnectionError
from pydantic import ValidationError

import app


# --------------------------------------------------------------------------- #
# Fakes mirroring the OpenAI object shape
# --------------------------------------------------------------------------- #
@dataclass
class FakeMessage:
    content: str | None
    model_extra: dict = field(default_factory=dict)


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]


@dataclass
class FakeModel:
    id: str


@dataclass
class FakeModelList:
    data: list[FakeModel]


class FakeCompletions:
    def __init__(self, message: FakeMessage, recorder: dict) -> None:
        self._message = message
        self._recorder = recorder

    def create(self, *args, **kwargs) -> FakeCompletion:
        self._recorder["create_kwargs"] = kwargs
        return FakeCompletion(choices=[FakeChoice(message=self._message)])


class FakeChat:
    def __init__(self, message: FakeMessage, recorder: dict) -> None:
        self.completions = FakeCompletions(message, recorder)


class FakeModels:
    def __init__(self, ids: list[str] | None, error: Exception | None) -> None:
        self._ids = ids
        self._error = error

    def list(self) -> FakeModelList:
        if self._error is not None:
            raise self._error
        return FakeModelList(data=[FakeModel(id=i) for i in (self._ids or [])])


class FakeClient:
    """Mirrors the parts of openai.OpenAI the app touches."""

    def __init__(
        self,
        *,
        message: FakeMessage | None = None,
        model_ids: list[str] | None = None,
        list_error: Exception | None = None,
        recorder: dict | None = None,
    ) -> None:
        self.recorder = recorder if recorder is not None else {}
        self.chat = FakeChat(message or FakeMessage(content=""), self.recorder)
        self.models = FakeModels(model_ids, list_error)


def _patch_make_client(monkeypatch: pytest.MonkeyPatch, client: FakeClient) -> dict:
    """Patch app.make_client; record the (base_url, api_key) it was called with."""
    calls: dict = {}

    def _factory(base_url: str | None, api_key: str | None) -> FakeClient:
        calls["base_url"] = base_url
        calls["api_key"] = api_key
        return client

    monkeypatch.setattr(app, "make_client", _factory)
    return calls


VALID_JSON = json.dumps(
    {
        "sentiment": "negative",
        "score": -0.8,
        "confidence": 0.92,
        "rationale": "The text expresses strong dissatisfaction.",
    }
)


# --------------------------------------------------------------------------- #
# analyze
# --------------------------------------------------------------------------- #
def test_content_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    """JSON in message.content -> validated SentimentResult."""
    client = FakeClient(message=FakeMessage(content=VALID_JSON))
    _patch_make_client(monkeypatch, client)

    result = app.analyze("The delivery was late and broken.")

    assert isinstance(result, app.SentimentResult)
    assert result.sentiment == "negative"
    assert result.score == -0.8
    assert result.confidence == 0.92


def test_reasoning_channel_with_prose(monkeypatch: pytest.MonkeyPatch) -> None:
    """content empty, JSON wrapped in prose inside reasoning_content -> still parses."""
    reasoning = (
        "Let me think about this. The wording is clearly enthusiastic.\n"
        + json.dumps(
            {
                "sentiment": "positive",
                "score": 0.9,
                "confidence": 0.95,
                "rationale": "Enthusiastic praise.",
            }
        )
        + "\nThat is my final answer."
    )
    client = FakeClient(
        message=FakeMessage(content="", model_extra={"reasoning_content": reasoning})
    )
    _patch_make_client(monkeypatch, client)

    result = app.analyze("I absolutely love this!")

    assert isinstance(result, app.SentimentResult)
    assert result.sentiment == "positive"
    assert result.score == 0.9


def test_analyze_uses_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Passed base_url/api_key reach make_client; model id passes through to create()."""
    client = FakeClient(message=FakeMessage(content=VALID_JSON))
    calls = _patch_make_client(monkeypatch, client)

    app.analyze(
        "whatever",
        base_url="https://api.example.com/v1",
        model="cloud-model-xyz",
        api_key="sk-secret",
    )

    assert calls["base_url"] == "https://api.example.com/v1"
    assert calls["api_key"] == "sk-secret"
    assert client.recorder["create_kwargs"]["model"] == "cloud-model-xyz"


def test_analyze_falls_back_to_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Blank model override falls back to the env default MODEL."""
    client = FakeClient(message=FakeMessage(content=VALID_JSON))
    _patch_make_client(monkeypatch, client)

    app.analyze("whatever", model="")

    assert client.recorder["create_kwargs"]["model"] == app.MODEL


# --------------------------------------------------------------------------- #
# on_analyze — never raises
# --------------------------------------------------------------------------- #
def test_on_analyze_connection_error_returns_notice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """APIConnectionError -> (notice_html, None), no raise."""

    def _boom(*args, **kwargs):
        raise APIConnectionError(request=None)  # type: ignore[arg-type]

    monkeypatch.setattr(app, "analyze", _boom)

    html, payload = app.on_analyze("some text")

    assert isinstance(html, str)
    assert "reach the endpoint" in html.lower()
    assert payload is None


def test_on_analyze_malformed_output_returns_notice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Schema-violating JSON -> notice, not a raised ValidationError."""
    bad_schema = json.dumps(
        {"sentiment": "ecstatic", "score": 5.0, "confidence": 0.5, "rationale": "x"}
    )
    client = FakeClient(message=FakeMessage(content=bad_schema))
    _patch_make_client(monkeypatch, client)

    html, payload = app.on_analyze("whatever")

    assert isinstance(html, str)
    assert "malformed" in html.lower()
    assert payload is None


def test_on_analyze_empty_text_returns_notice() -> None:
    """Blank input -> notice, no raise."""
    html, payload = app.on_analyze("   ")
    assert isinstance(html, str)
    assert payload is None


def test_on_analyze_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid result -> (rendered card html, dict payload)."""
    client = FakeClient(message=FakeMessage(content=VALID_JSON))
    _patch_make_client(monkeypatch, client)

    html, payload = app.on_analyze("The delivery was late and broken.")

    assert "NEGATIVE" in html
    assert isinstance(payload, dict)
    assert payload["sentiment"] == "negative"


# --------------------------------------------------------------------------- #
# test_connection — never raises
# --------------------------------------------------------------------------- #
def test_test_connection_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient(model_ids=["qwen/qwen3.6-35b-a3b", "other-model"])
    _patch_make_client(monkeypatch, client)

    status = app.test_connection(
        base_url="http://localhost:1234/v1",
        model="qwen/qwen3.6-35b-a3b",
        api_key="lm-studio",
    )

    assert isinstance(status, str)
    assert "Connected" in status
    assert "qwen/qwen3.6-35b-a3b" in status
    assert "available" in status.lower()


def test_test_connection_model_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient(model_ids=["other-model"])
    _patch_make_client(monkeypatch, client)

    status = app.test_connection(
        base_url="http://localhost:1234/v1",
        model="not-loaded",
        api_key="lm-studio",
    )

    assert isinstance(status, str)
    assert "not" in status.lower()


def test_test_connection_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """models.list raising -> status string, never raises."""
    client = FakeClient(list_error=APIConnectionError(request=None))  # type: ignore[arg-type]
    _patch_make_client(monkeypatch, client)

    status = app.test_connection(
        base_url="http://localhost:1234/v1",
        model="m",
        api_key="k",
    )

    assert isinstance(status, str)
    assert "can't reach" in status.lower()


# --------------------------------------------------------------------------- #
# _payload unit
# --------------------------------------------------------------------------- #
def test_payload_prefers_content() -> None:
    """_payload returns content when present, ignoring reasoning_content."""
    msg = FakeMessage(content=' {"a": 1} ', model_extra={"reasoning_content": "junk"})
    assert app._payload(msg) == '{"a": 1}'
