# 03 · Product-Feedback RAG Assistant (RAG demo)

Answer natural-language questions about products by **retrieving over a local
corpus** of tester feedback in `chromadb`, then having a **local LLM** produce a
**grounded, validated answer with citations** — and refusing honestly when the
corpus has nothing to say.

Concepts: B4 retrieval-augmented generation · B8 grounding · B1 context budget.
Full spec: [`../p3-feedback-rag.md`](../p3-feedback-rag.md).

## What it does

- `POST /ask` — `{question, top_k}` → `Answer` (`answer`, `citations[]`,
  `confidence`), validated against a pydantic v2 schema. Retrieval runs over a
  Chroma collection; the prompt feeds only the retrieved chunks as context.
- `GET /health` — liveness.

Two contracts make this a RAG demo rather than a chatbot:

1. **Structured output** — every model call goes through
   `common.llm.structured_call`: JSON-mode request → validate against `Answer` →
   **retry once with the validator error appended → quarantine** (`QuarantineError`).
   On quarantine the API returns an honest "I don't know" instead of crashing.
2. **Grounding guard** — after the model answers, the API **drops any citation id
   the model invented** that was not in the retrieved set. The answer may only
   cite from the supplied context. Empty retrieval → honest "I don't know" with no
   citations.

## Layout

```
03-rag-feedback/
├── backend/
│   ├── app.py                  # FastAPI: /ask /health + grounding guard
│   ├── index.py                # Chroma build/retrieve + offline HashingEmbeddingFunction
│   ├── models.py               # pydantic v2 schemas (Answer, Citation, FeedbackDoc, AskRequest)
│   └── fixtures/feedback.jsonl # 20 synthetic feedback rows (id, text, product_category)
├── tests/                      # offline; LLM client mocked, deterministic stub embedder
├── frontend/                   # Next.js (App Router) scaffold
├── requirements.txt            # package extra: chromadb (heavy-ish, local vector store)
└── .docs/001.spec-context.md
```

## Run the backend

From the package dir, so the top-level `backend` import resolves (the `app.py`
path bootstrap puts `projects/` on `sys.path` so `common` resolves too):

```bash
cd projects/03-rag-feedback
../.venv/bin/uvicorn backend.app:app --reload --port 8000
```

On first `/ask` the backend lazily builds the Chroma collection from the fixture
using Chroma's **bundled default embedder** (local ONNX MiniLM — downloaded once,
then offline, no API calls). Point the LLM at a running local server (LM Studio
etc.) via the three env vars below.

### chromadb note

`chromadb` is a **package-local** extra (not in the shared venv). Install it on top
of the shared `projects/requirements.txt`:

```bash
../.venv/bin/pip install -r requirements.txt
```

The corpus is in-memory (`EphemeralClient`) and rebuilt from the fixture on
startup — nothing is written to disk, so the demo runs offline and leaves no state.

## Run the frontend

```bash
cd 03-rag-feedback/frontend
npm install
npm run dev        # http://localhost:3000  (talks to NEXT_PUBLIC_API_BASE)
```

See [`frontend/README.md`](frontend/README.md).

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
config lives in `common/llm.py` and nowhere else. (The embedder is independent —
the local Chroma default is used regardless of which chat model serves `/ask`.)

## Run tests (offline — no LLM, no network)

```bash
cd projects
.venv/bin/python -m pytest 03-rag-feedback -q
```

Tests monkeypatch `common.llm.get_client` to a fake that replays canned JSON, and
inject a deterministic `HashingEmbeddingFunction` so no embedding model is ever
downloaded. They assert: the fixture loads 20 valid docs; planted "shrinkage" and
"waterproof" queries retrieve the right docs; `top_k` is respected; the
**grounding guard drops hallucinated citation ids**; and two malformed model
responses quarantine into an honest "I don't know".

## Data

Synthetic fixture (`backend/fixtures/feedback.jsonl`, 20 rows): `{id, text,
product_category}`. The rows are hand-authored tester-feedback excerpts in the
spirit of the **Women's E-Commerce Clothing Reviews** dataset
[R-039] (<https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews>),
plus the public Turkish dataset family [R-040], [R-041] referenced across the
guide. No source-dataset rows and no PII — the fixture exists so the RAG +
grounding contract runs offline and publishably (generic fashion-retail domain).
