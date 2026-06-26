# Local-LLM Hands-on Monorepo

A set of small, runnable, **provider-swappable** apps over a public, anonymized
retail-reviews dataset. Every example runs on a **local model** through the
OpenAI-compatible endpoint and switches to any cloud provider by changing three
environment variables — no code change.

Domain: a generic **fashion-retail customer survey & rewards panel** (surveys,
product feedback, vouchers). No company names, no PII — safe to publish.

Pairs with [Part 4 — Hands-on Projects](../article/part-4-projects.md). Specs:
[`PRD.md`](PRD.md), [`proposal.md`](proposal.md), and the per-package specs.

## Layout

The **flagship** is `sentiment-app/` — the published Phase-4 demo. Everything in
`extras/` is supplementary learning material to work through later.

```
projects/
├── sentiment-app/              # ★ FLAGSHIP — Gradio + OpenAI SDK + LM Studio,
│                               #   json_schema structured output. The published demo.
├── 00-serve-lmstudio/          # stand up + verify a local server, pick a model
├── common/llm.py               # the config contract — the ONLY place model config lives
├── requirements.txt            # shared deps (package extras live per-package)
├── pytest.ini                  # test discovery across packages
├── .env.example                # the three contract vars
└── extras/                     # supplementary learning demos (for later)
    ├── 01-prompting/               # anatomy, zero/few-shot, sample SKILL.md
    ├── 02-structured-output/       # pydantic / response_format, retry-then-quarantine
    ├── 03-rag-feedback/            # P3 · product-feedback RAG (chroma + local embeddings)
    ├── 04-fullstack-analyzer/      # P1 · FastAPI + React, LLM-vs-DistilBERT compare
    ├── 05-conversational-survey/   # P2 · multi-turn adaptive survey bot
    └── 06-agentic-capstone/        # P6 · rebuild P1 with an agent from AGENTS.md + SKILL.md
```

Model standings live in [`../model-table.md`](../model-table.md) — never hardcode
a model name or benchmark anywhere else.

## Run the flagship

`sentiment-app/` needs LM Studio serving on `:1234` (see `00-serve-lmstudio/`):

```bash
cd projects/sentiment-app
pip install -r requirements.txt
python app.py
```

## The config contract

Every package imports `common/llm.py` and nothing else touches model config:

```python
from common.llm import get_client, LLM_MODEL

resp = get_client().chat.completions.create(
    model=LLM_MODEL,
    messages=[{"role": "user", "content": "..."}],
)
```

Three environment variables drive it:

| Var | Local default (LM Studio) | Meaning |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:1234/v1` | OpenAI-compatible endpoint |
| `LLM_API_KEY`  | `lmstudio` | ignored locally; any non-empty string |
| `LLM_MODEL`    | `local-model` | model id from `GET /v1/models` |

### Swap to a cloud provider

Change **only these three** — the application code is untouched:

```bash
# OpenAI
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

Azure OpenAI and OpenRouter variants are in [`.env.example`](.env.example).

## Setup

```bash
cd projects
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit; .env is gitignored, never commit a key
```

Some extras add their own deps — `chromadb` for `extras/03-rag-feedback`,
`transformers` + `torch` for the DistilBERT comparison in
`extras/04-fullstack-analyzer`. Each package's README lists its extras and run steps.

## Run an extras package

`extras/` dirs are number-prefixed (`04-fullstack-analyzer`), so they aren't
importable Python module names — run from *inside* the package dir. Each
backend/demo walks up `sys.path` to the `projects/` root (the dir holding
`common/llm.py`) so the shared `common` package resolves; the package dir itself
supplies `backend`.

```bash
# FastAPI service
cd projects/extras/04-fullstack-analyzer
../../.venv/bin/uvicorn backend.app:app --reload --port 8000

# standalone concept demo
cd projects/extras/02-structured-output
../../.venv/bin/python demo.py
```

Run tests for one package from `projects/` (so `common` is importable) with the
package's relative path as the argument, or sweep all packages with
`./run_tests.sh`:

```bash
cd projects
.venv/bin/python -m pytest extras/04-fullstack-analyzer -q   # one package
./run_tests.sh                                               # all packages
```

Each package ships a README with its exact run steps and a swap-to-cloud note.

## Run tests

From `projects/` (discovery is configured in `pytest.ini`):

```bash
pytest              # all packages
pytest -x common    # one package, stop on first failure
```

Tests use the FastAPI `TestClient` (via `httpx`) and small fixtures — they do
**not** require a running LM Studio server unless a package's README says so.

## Structured-output rule

Every model call that feeds software returns a **validated Pydantic model**. On
schema-validation failure: retry once with the error appended, then quarantine
the row. `common.llm.structured_call` implements this (raises `QuarantineError`
after the failed retry); packages may use it or inline the same pattern.
