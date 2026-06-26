# 02 · Structured Output — the output contract

A runnable concept demo for **Part 1, A6** of the guide: making an LLM return a
machine-readable shape so it's safe to wire into software.

It extracts a structured `ReviewRecord` (sentiment, themes, sizing flag, churn
risk, summary) from one fashion-retail review using JSON mode + Pydantic
validation, and demonstrates the retry-once-then-quarantine policy.

## What it teaches

- **Output contract (A6)** — a Pydantic `ReviewRecord` is the model's promise to
  the software; closed `Literal`/vocabulary fields keep downstream analytics clean.
- **JSON mode** — `common.structured_call` requests
  `response_format={"type": "json_object"}` and validates the response.
- **Retry once, then quarantine** — on a validation failure the call retries once
  with the validator error appended; a second failure raises `QuarantineError` so
  a batch can set the row aside instead of crashing.

## Run

A local OpenAI-compatible server (e.g. LM Studio, default `http://localhost:1234/v1`)
must be serving a model. From the package dir (the `demo.py` path bootstrap puts
`projects/` on `sys.path` so `common` resolves):

```bash
cd projects/02-structured-output
../.venv/bin/python demo.py
```

It prints the validated record as JSON, or a `QUARANTINED` line if the model
failed the contract twice.

## Test (offline — no LLM needed)

From `projects/`:

```bash
.venv/bin/python -m pytest 02-structured-output -q
```

The tests mock the client (`tests/conftest.py`): valid JSON parses, malformed JSON
retries then recovers, and two failures raise `QuarantineError`. No network call.

## Config — the three env vars

Model config is owned entirely by `common/llm.py`. Override via environment only:

| Var            | Default                     |
| -------------- | --------------------------- |
| `LLM_BASE_URL` | `http://localhost:1234/v1`  |
| `LLM_API_KEY`  | `lmstudio`                  |
| `LLM_MODEL`    | `local-model`               |

**Swap to cloud:** set those three to your provider (e.g. OpenAI:
`LLM_BASE_URL=https://api.openai.com/v1`, `LLM_API_KEY=sk-...`,
`LLM_MODEL=gpt-4o-mini`). Nothing in this package changes.
