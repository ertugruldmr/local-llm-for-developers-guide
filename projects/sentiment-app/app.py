"""Sentiment analysis demo — OpenAI SDK against an OpenAI-compatible endpoint.

Defaults to a local LM Studio model but the endpoint, model, and key are
editable at runtime via the Connection settings panel, so when LM Studio is
down or you have no GPU you can point it at any OpenAI-compatible endpoint
(cloud provider, Colab tunnel, …) without a restart.

The model (Qwen3) is a reasoning model: under `response_format=json_schema`
LM Studio emits the structured JSON into the `reasoning_content` channel and
leaves `content` empty, so we read whichever field carries the payload.
"""

from __future__ import annotations

import json
import os
from typing import Literal

import gradio as gr
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessage
from pydantic import BaseModel, Field, ValidationError

# --------------------------------------------------------------------------- #
# Config (env defaults — overridable at runtime via the UI)
# --------------------------------------------------------------------------- #
BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
MODEL = os.getenv("LMSTUDIO_MODEL", "qwen/qwen3.6-35b-a3b")
API_KEY = os.getenv(
    "LMSTUDIO_API_KEY", "lm-studio"
)  # LM Studio ignores the value

SHARE = os.getenv("GRADIO_SHARE", "true").lower() in {"1", "true", "yes"}
SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))


def make_client(base_url: str | None, api_key: str | None) -> OpenAI:
    """Build a client from runtime values, falling back to env defaults."""
    return OpenAI(
        base_url=(base_url or "").strip() or BASE_URL,
        api_key=(api_key or "").strip() or API_KEY,
        timeout=60.0,
    )


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
class SentimentResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    score: float = Field(
        ge=-1.0, le=1.0, description="-1 very negative .. +1 very positive"
    )
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(
        description="One short sentence justifying the call."
    )


RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "sentiment_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                },
                "score": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "rationale": {"type": "string"},
            },
            "required": ["sentiment", "score", "confidence", "rationale"],
            "additionalProperties": False,
        },
    },
}

SYSTEM_PROMPT = (
    "You are a precise sentiment classifier. Classify the user's text.\n"
    "- sentiment: positive | negative | neutral\n"
    "- score: signed float in [-1, 1]; NEGATIVE text must get a negative score, "
    "positive text a positive score, neutral near 0.\n"
    "- confidence: float in [0, 1] for how sure you are.\n"
    "- rationale: one short sentence.\n"
    "Return only the structured object."
)


# --------------------------------------------------------------------------- #
# Inference
# --------------------------------------------------------------------------- #
def _payload(message: ChatCompletionMessage) -> str:
    """Return the JSON string, reading the reasoning channel as a fallback."""
    if message.content and message.content.strip():
        return message.content.strip()
    reasoning = (message.model_extra or {}).get("reasoning_content", "") or ""
    text = reasoning.strip()
    if (
        "{" in text and "}" in text
    ):  # reasoning channel may wrap the JSON in prose
        text = text[text.find("{") : text.rfind("}") + 1]
    return text


def analyze(
    text: str,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> SentimentResult:
    client = make_client(base_url, api_key)
    completion = client.chat.completions.create(
        model=(model or "").strip() or MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text.strip()},
        ],
        response_format=RESPONSE_FORMAT,
        temperature=0,
    )
    return SentimentResult.model_validate_json(
        _payload(completion.choices[0].message)
    )


# --------------------------------------------------------------------------- #
# Connection test
# --------------------------------------------------------------------------- #
def test_connection(
    base_url: str | None, model: str | None, api_key: str | None
) -> str:
    """Cheap reachability check via models.list(). Never raises."""
    resolved_url = (base_url or "").strip() or BASE_URL
    resolved_model = (model or "").strip() or MODEL
    try:
        client = make_client(base_url, api_key)
        ids = [m.id for m in client.models.list().data]
    except (APIConnectionError, APITimeoutError):
        return (
            f"❌ Can't reach the endpoint at <code>{resolved_url}</code> — "
            "check the Base URL and that the server is running."
        )
    except AuthenticationError:
        return "❌ Auth failed — check the API key."
    except Exception as exc:  # noqa: BLE001 — surface anything as a friendly line
        return f"❌ Connection failed: {_trim(str(exc))}"

    if not ids:
        return (
            f"⚠️ Connected to <code>{resolved_url}</code>, but the endpoint "
            "reports no models."
        )

    preview = ", ".join(f"<code>{i}</code>" for i in ids[:5])
    more = f" (+{len(ids) - 5} more)" if len(ids) > 5 else ""
    if resolved_model in ids:
        match = f"Model <code>{resolved_model}</code> is available. ✅"
    else:
        match = (
            f"⚠️ Model <code>{resolved_model}</code> is <b>not</b> in the list — "
            "pick one of the ids above."
        )
    return f"✅ Connected. {len(ids)} model(s): {preview}{more}.<br>{match}"


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
THEME = {"positive": "#16a34a", "negative": "#dc2626", "neutral": "#64748b"}
EMOJI = {"positive": "😊", "negative": "😠", "neutral": "😐"}


def _bar(value: float, lo: float, hi: float, color: str) -> str:
    pct = max(0.0, min(100.0, (value - lo) / (hi - lo) * 100.0))
    return (
        f'<div class="bar-track"><div class="bar-fill" '
        f'style="width:{pct:.1f}%;background:{color}"></div></div>'
    )


def render(result: SentimentResult) -> str:
    color = THEME[result.sentiment]
    return f"""
<div class="card result" style="--accent:{color}">
  <div class="headline">
    <span class="emoji">{EMOJI[result.sentiment]}</span>
    <span class="label">{result.sentiment.upper()}</span>
  </div>
  <div class="metric">
    <div class="metric-label"><span>Score</span><span>{result.score:+.2f}</span></div>
    {_bar(result.score, -1.0, 1.0, color)}
  </div>
  <div class="metric">
    <div class="metric-label"><span>Confidence</span><span>{result.confidence:.0%}</span></div>
    {_bar(result.confidence, 0.0, 1.0, color)}
  </div>
  <p class="rationale">{result.rationale}</p>
</div>
"""


def _trim(msg: str, limit: int = 200) -> str:
    msg = " ".join(msg.split())
    return msg if len(msg) <= limit else msg[: limit - 1] + "…"


def _notice(title: str, detail: str) -> str:
    return f"""
<div class="card notice">
  <div class="notice-head"><span class="notice-icon">⚠️</span>{title}</div>
  <p class="notice-detail">{detail}</p>
  <p class="notice-hint">Open <b>Connection settings</b> below and use
     <b>Test connection</b> to check the endpoint and list available models.</p>
</div>
"""


def on_analyze(
    text: str,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> tuple[str, dict | None]:
    """Run analysis. Never raises — provider failures become an in-card notice."""
    if not text or not text.strip():
        return (
            _notice("Nothing to analyze", "Enter some text first."),
            None,
        )
    try:
        result = analyze(text, base_url, model, api_key)
    except (APIConnectionError, APITimeoutError):
        return (
            _notice(
                "Can't reach the endpoint",
                "Check the Base URL and that the server is running.",
            ),
            None,
        )
    except AuthenticationError:
        return (
            _notice("Authentication failed", "Check the API key."),
            None,
        )
    except NotFoundError:
        return (
            _notice(
                "Model not found",
                "Check the Model id (use Test connection to list available ids).",
            ),
            None,
        )
    except (BadRequestError, RateLimitError, APIError) as exc:
        return (
            _notice("The provider rejected the request", _trim(str(exc))),
            None,
        )
    except (ValidationError, json.JSONDecodeError):
        return (
            _notice(
                "Malformed model output",
                "The model returned malformed output — try again.",
            ),
            None,
        )
    except Exception as exc:  # noqa: BLE001 — keep the app alive on anything
        return (
            _notice("Something went wrong", _trim(str(exc))),
            None,
        )
    return render(result), result.model_dump()


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
CSS = """
/* Minimal layout on top of Gradio's DEFAULT theme. No theme overrides — the
   native components keep Gradio's styling and adapt to light/dark on their own.
   The custom result/notice/empty cards read Gradio's OWN theme variables, so
   they match whatever theme is active (this is also what fixes the half-dark
   mismatch: everything now reads the same variables). */
.gradio-container { max-width: 1060px !important; margin: 0 auto !important; }

/* header */
#app-header { text-align: center; padding: 18px 16px 14px; }
#app-header h1 { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -.02em; }
#app-header p { margin: 6px 0 0; color: var(--body-text-color-subdued); font-size: 14px; }
#app-header .rule {
  width: 54px; height: 3px; border-radius: 999px;
  background: var(--button-primary-background-fill, #4f46e5); margin: 12px auto 0; opacity: .9;
}

/* layout */
#main-row { align-items: flex-start; gap: 20px; }
#conn-status { font-size: 13px; color: var(--body-text-color-subdued); line-height: 1.55; padding: 4px 2px; min-height: 20px; }

/* custom cards — driven by Gradio theme variables so they adapt to light/dark */
.card {
  border: 1px solid var(--border-color-primary);
  border-radius: var(--radius-lg, 12px);
  padding: 22px 24px;
  background: var(--block-background-fill);
  color: var(--body-text-color);
  min-height: 280px; box-sizing: border-box;
}
.card.empty {
  border-style: dashed;
  display: flex; align-items: center; justify-content: center;
  color: var(--body-text-color-subdued); font-size: 15px; text-align: center;
}

/* result card (sentiment color comes from inline --accent set by render()) */
.card.result { border-top: 3px solid var(--accent, #4f46e5); }
.card.result .headline {
  font-size: 24px; font-weight: 800; display: flex; align-items: center; gap: 12px;
  color: var(--accent, #4f46e5);
}
.card.result .emoji { font-size: 32px; }
.metric { margin-top: 18px; }
.metric-label {
  display: flex; justify-content: space-between;
  font-weight: 600; font-size: 13px; margin-bottom: 6px;
}
.bar-track {
  height: 10px; border-radius: 999px;
  background: var(--background-fill-secondary); overflow: hidden;
}
.bar-fill { height: 100%; border-radius: 999px; width: 0; animation: grow .5s ease forwards; }
@keyframes grow { from { width: 0 !important; } }
.rationale { margin-top: 18px; font-style: italic; color: var(--body-text-color-subdued); line-height: 1.6; font-size: 15px; }

/* notice (needs-attention) — amber accent, theme-driven body */
.card.notice { border-top: 3px solid #d97706; }
.notice-head { display: flex; align-items: center; gap: 10px; font-size: 17px; font-weight: 700; }
.notice-icon { font-size: 20px; }
.notice-detail { margin: 12px 0 0; line-height: 1.55; font-size: 15px; }
.notice-hint { margin: 12px 0 0; color: var(--body-text-color-subdued); font-size: 13px; line-height: 1.5; }

/* responsive: stack to one column on mobile */
@media (max-width: 768px) {
  #main-row { flex-direction: column; }
  .card { min-height: 0; }
}
"""

EMPTY_CARD = (
    '<div class="card empty">Results will appear here after you '
    "click <b>&nbsp;Analyze</b>.</div>"
)

EXAMPLES = [
    "I absolutely love this product, it exceeded all my expectations!",
    "The delivery was late and the package arrived damaged. Very disappointed.",
    "The meeting is scheduled for 3pm in conference room B.",
    "Great battery life, but the camera is mediocre and the price is too high.",
]


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Sentiment Analyzer") as demo:
        gr.HTML(
            """
            <div id="app-header">
              <h1>🎯 Sentiment Analyzer</h1>
              <p>Structured JSON output via the OpenAI SDK against any
                 OpenAI-compatible endpoint.</p>
              <div class="rule"></div>
            </div>
            """
        )

        with gr.Row(elem_id="main-row"):
            with gr.Column(scale=1):
                text_input = gr.Textbox(
                    label="Text",
                    placeholder="Type or paste text to analyze…",
                    lines=8,
                    max_lines=8,
                )
                with gr.Row():
                    clear_btn = gr.ClearButton(value="Clear")
                    analyze_btn = gr.Button("Analyze", variant="primary")
                gr.Examples(
                    examples=EXAMPLES,
                    inputs=text_input,
                    label="Try an example",
                )
            with gr.Column(scale=1):
                card = gr.HTML(value=EMPTY_CARD)
                with gr.Accordion("Raw JSON", open=False):
                    raw = gr.JSON()

        with gr.Accordion(
            "⚙️ Connection settings", open=False, elem_id="settings-acc"
        ):
            base_url_in = gr.Textbox(
                label="Base URL",
                value=BASE_URL,
                placeholder="http://localhost:1234/v1",
            )
            model_in = gr.Textbox(
                label="Model",
                value=MODEL,
                placeholder="model id served by the endpoint",
            )
            api_key_in = gr.Textbox(
                label="API key",
                value=API_KEY,
                type="password",
                placeholder="endpoint API key (LM Studio ignores it)",
            )
            with gr.Row():
                test_btn = gr.Button("Test connection", variant="secondary")
            conn_status = gr.HTML(
                value="Endpoint not tested yet.", elem_id="conn-status"
            )

        provider_inputs = [base_url_in, model_in, api_key_in]

        clear_btn.add([text_input, raw])
        clear_btn.click(fn=lambda: EMPTY_CARD, outputs=card)

        test_btn.click(
            fn=test_connection,
            inputs=provider_inputs,
            outputs=conn_status,
        )

        gr.on(
            triggers=[analyze_btn.click, text_input.submit],
            fn=on_analyze,
            inputs=[text_input, *provider_inputs],
            outputs=[card, raw],
        )
    return demo


if __name__ == "__main__":
    build_ui().queue().launch(
        share=SHARE,
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        show_error=True,
        theme=gr.themes.Soft(),
        css=CSS,
    )
