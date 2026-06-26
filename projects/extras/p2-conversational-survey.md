# Spec — P2: Conversational AI-Survey Bot (multi-turn demo)

**Package:** `05-conversational-survey/` · **Concepts:** C3 agent loop, C4 multi-turn, B5 memory, B6 compaction · **Difficulty:** ⭐⭐⭐

## Goal
A multi-turn survey bot that opens with a base question, asks **≥2 adaptive
follow-ups** driven by the respondent's answers, and closes by emitting a
**validated `SurveySummary`**. It demonstrates the agent loop (decide → act →
observe), short-term memory inside the context window, and **compaction** —
older turns are folded into a running summary so the window stays bounded across
a long conversation.

## User stories
- As a respondent, I answer a survey where each follow-up reacts to what I just said.
- As an analyst, every completed conversation yields a structured `SurveySummary`
  (topics, sentiment, verbatims, recommended next action) — no manual coding.
- As a developer, I see the agent decide "ask again vs. wrap up" and watch older
  turns compact into a summary instead of growing the prompt unbounded.

## Data (synthetic, generic fashion-retail)
No dataset needed to *drive* the bot — the respondent is the input. Two static
artifacts ship with the package:
- `backend/fixtures/survey_config.json` — the base question + the adaptive policy
  (`max_follow_ups`, the topic taxonomy to probe: `[sizing, fabric, fit, delivery,
  price, service]`, and a stop condition).
- `backend/fixtures/transcript.jsonl` — one canned synthetic conversation (a
  fashion-retail return scenario) used as the offline test fixture so the loop and
  the summary are exercised without a live model. Synthetic, no PII.

## Output contract (structured output)
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

Sentiment = Literal["positive", "neutral", "negative"]

class Turn(BaseModel):
    role: Literal["assistant", "user"]
    content: str

class FollowUpDecision(BaseModel):
    """One step of the agent loop: ask again or finish."""
    action: Literal["ask", "finish"]
    question: Optional[str] = None          # set when action == "ask"
    rationale: str = Field(max_length=200)  # why this follow-up / why stop

class SurveySummary(BaseModel):
    topics: list[str]                        # from the fixed taxonomy
    sentiment: Sentiment
    verbatims: list[str]                     # short quoted snippets, <= 5
    next_action: Literal["follow_up_call", "offer_voucher", "no_action", "escalate"]
    summary: str = Field(max_length=280)
```
Both `FollowUpDecision` and `SurveySummary` are produced via JSON-mode calls and
validated through `common.llm.structured_call` (retry-once-then-quarantine).

## Memory & compaction (B5/B6)
- **Short-term:** the live window holds the last `N` turns verbatim.
- **Compaction:** when turn count exceeds `N`, the oldest turns are summarized into
  a single `running_summary` string and dropped from the verbatim window. The
  prompt is then `[system, running_summary, ...last N turns]` — bounded regardless
  of conversation length. Threshold `N` lives in `survey_config.json`.

## Architecture
- **Backend (FastAPI):** session-scoped, in-memory store keyed by `session_id`.
  - `POST /session` → `{session_id, opening_question}`.
  - `POST /turn` → body `{session_id, answer}` → `FollowUpDecision` (next question)
    or, on `finish`, the `SurveySummary`. Drives one iteration of the agent loop and
    triggers compaction when the window is full.
  - `GET /session/{id}` → current transcript + running summary (for inspection).
  - `GET /health` → liveness.
- **Frontend (Next.js):** a chat panel that shows the running exchange, a side
  panel exposing the `running_summary` (so compaction is visible), and the final
  `SurveySummary` card when the loop finishes.

## Prompt sketch
```
SYSTEM: You run an adaptive fashion-retail survey. Probe topics from this fixed
        taxonomy: [sizing, fabric, fit, delivery, price, service]. After each
        answer, decide whether to ask one focused follow-up or finish. Ask at
        least 2 and at most {max_follow_ups} follow-ups. Return ONLY JSON
        (FollowUpDecision). When finishing, return a SurveySummary instead.
RUNNING_SUMMARY: <compacted older turns>     # static-ish prefix → cache-friendly (B3)
TURNS: <last N verbatim turns>
```

## Acceptance criteria
- A run over the canned fixture produces ≥2 distinct adaptive follow-ups that
  reference prior answers, then a **valid `SurveySummary`**.
- After the window threshold is crossed, the prompt contains a `running_summary`
  and the verbatim turn count stays ≤ `N` (compaction proven).
- README documents the cloud swap (three env vars) and the memory/compaction knobs.

## Stretch
- Persist sessions to SQLite instead of in-memory.
- Add a Turkish survey config variant (taxonomy + prompt localized).
- Token-budget guard (B1): refuse to grow the window; force compaction earlier.

## Swap to cloud
The bot only ever talks to the model through `common.llm` (the agent loop, the
follow-up decision, and the summary are all `structured_call`s). Switching to any
OpenAI-compatible cloud is the three-env-var change — `LLM_BASE_URL`,
`LLM_API_KEY`, `LLM_MODEL` — with no code edits.

## Build notes (for the agent)
Backend-first: implement the agent loop + compaction over the canned transcript
fixture, prove ≥2 follow-ups and a valid summary with a pytest, then add the
FastAPI session endpoints, then the chat frontend. Keep `N`, `max_follow_ups`, and
the taxonomy in `survey_config.json`, model config in `.env`.
