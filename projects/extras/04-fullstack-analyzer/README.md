# 04 · Full-stack Review / Survey Analyzer (P1 — primary demo)

Batch customer reviews through a **local LLM**, extract a **validated structured
insight** per review, aggregate it, and **compare the LLM against a lightweight
DistilBERT classifier** — the "pick the smallest tool" lesson made concrete.

Concepts: A1 anatomy · A6 structured output · B7 result management.
Full spec: [`../p1-review-analyzer.md`](../p1-review-analyzer.md).

## What it does

- `POST /analyze` — one review → `ReviewInsight` (sentiment, themes, sizing_issue,
  churn_risk, summary), validated against a pydantic v2 schema.
- `POST /analyze-batch` — list of reviews → `{insights, quarantined}`. Rows whose
  model output fails validation twice are quarantined, not crashed.
- `POST /aggregate` — batch → sentiment / theme / churn-risk rollups for the dashboard.
- `POST /baseline` — DistilBERT sentiment-only baseline (503 if torch not installed).
- `GET /health` — liveness.

Every model call uses `common.llm.structured_call`: JSON-mode request → validate →
**retry once with the validator error appended → quarantine** (`QuarantineError`).

## Layout

```
04-fullstack-analyzer/
├── backend/
│   ├── app.py                 # FastAPI: /analyze /analyze-batch /aggregate /baseline /health
│   ├── models.py              # pydantic v2 schemas (ReviewInsight, ...)
│   ├── compare.py             # DistilBERT baseline (lazy, guarded import)
│   └── fixtures/reviews.jsonl # 20 synthetic rows matching the dataset schema
├── tests/                     # offline; the LLM client is mocked
├── frontend/                  # Next.js (App Router) scaffold
├── requirements.txt           # package extras: transformers + torch (optional, heavy)
└── .docs/001.spec-context.md
```

## Run the backend

From the package dir, so the top-level `backend` import resolves (the `app.py`
path bootstrap puts `projects/` on `sys.path` so `common` resolves too):

```bash
cd projects/04-fullstack-analyzer
../.venv/bin/uvicorn backend.app:app --reload --port 8000
```

Point it at a running local server (LM Studio etc.) via the three env vars below.

### DistilBERT baseline (optional)

`/baseline` and `backend/compare.py` need `transformers` + `torch`, which are
**not** in the shared venv (they're heavy). Install the package extras only if you
want the comparison:

```bash
pip install -r 04-fullstack-analyzer/requirements.txt
```

Model: `distilbert-base-multilingual-cased-sentiments-student` (sentiment only —
no themes, no churn, no summary — which is exactly the trade-off the demo shows).

## Run the frontend

```bash
cd 04-fullstack-analyzer/frontend
npm install
npm run dev        # http://localhost:3000  (talks to NEXT_PUBLIC_API_BASE)
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

## Run tests (offline — no LLM, no network)

```bash
cd projects
.venv/bin/python -m pytest 04-fullstack-analyzer -q
```

Tests monkeypatch `common.llm.get_client` to a fake that replays canned JSON, so
they assert: every fixture row → valid `ReviewInsight`; malformed JSON triggers the
retry; a second failure raises `QuarantineError`; the API endpoints behave.

## Data

Synthetic fixture (`backend/fixtures/reviews.jsonl`, 20 rows) mirrors the schema of
the **Women's E-Commerce Clothing Reviews** dataset [R-039]
(<https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews>):
`review_text`, `rating`, `recommended`, `age`, `class_name`. The fixture rows are
hand-authored and contain no rows from the source dataset and no PII — they exist so
the demo runs offline and publishably.
