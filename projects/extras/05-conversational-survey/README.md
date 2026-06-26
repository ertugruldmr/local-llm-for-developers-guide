# 05 · Conversational AI-Survey Bot (P2)

A multi-turn survey bot that opens with a base question, asks **≥2 adaptive
follow-ups** driven by the answers, and emits a **validated `SurveySummary`**. It's
the agent-loop + memory + compaction demo: older turns compact into a running
summary so the context window stays bounded across a long conversation.

Concepts: C3 agent loop · C4 multi-turn · B5 memory · B6 compaction.
Full spec: [`../p2-conversational-survey.md`](../p2-conversational-survey.md).

> **Status: skeleton.** Schemas + fixtures + a `/health` endpoint exist; the agent
> loop and `/session` / `/turn` endpoints raise `NotImplementedError`. See
> [`.docs/001.spec-context.md`](.docs/001.spec-context.md) for the build plan.

## What it will do

- `POST /session` — open a session → `{session_id, opening_question}`.
- `POST /turn` — `{session_id, answer}` → next `FollowUpDecision` (adaptive
  follow-up) or, on finish, a `SurveySummary`. Runs one agent-loop iteration and
  compacts older turns when the window fills.
- `GET /session/{id}` — current transcript + `running_summary` (compaction visible).
- `GET /health` — liveness (implemented).

Every model call goes through `common.llm.structured_call` (JSON mode → validate →
retry once with the error → quarantine).

## Layout

```
05-conversational-survey/
├── backend/
│   ├── app.py                      # FastAPI: /health (live), /session /turn /session/{id} (stubs)
│   ├── models.py                   # pydantic v2 schemas (FollowUpDecision, SurveySummary, ...)
│   └── fixtures/
│       ├── survey_config.json      # base question, taxonomy, follow-up bounds, window size
│       └── transcript.jsonl        # one canned synthetic conversation (offline fixture)
├── tests/test_schema.py            # trivially-green model-import test
└── .docs/001.spec-context.md
```

## Run the backend (placeholder)

From the `projects/` root (so `common` resolves as a package):

```bash
cd projects/05-conversational-survey
../.venv/bin/uvicorn backend.app:app --reload --port 8000
# /health returns ok; /session and /turn raise NotImplementedError until built
```

## Config — three env vars (the whole contract)

| Var | Local default | Meaning |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:1234/v1` | OpenAI-compatible endpoint |
| `LLM_API_KEY`  | `lmstudio` | any non-empty string locally |
| `LLM_MODEL`    | `local-model` | model id from `GET /v1/models` |

**Swap to cloud — change only these three, no code changes:**

```bash
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

Azure / OpenRouter variants are in [`../.env.example`](../.env.example). All model
config lives in `common/llm.py` and nowhere else.

## Data

All fixtures are **synthetic, generic fashion-retail, no PII**. The canned
`transcript.jsonl` is a hand-authored return scenario used to exercise the loop and
the summary fully offline.
