# Spec — P3: Product-Feedback RAG Assistant (RAG demo)

**Package:** `03-rag-feedback/` · **Concepts:** B4 RAG, B8 grounding, B1 budget · **Difficulty:** ⭐⭐⭐

## Goal
Answer natural-language questions about products using **retrieval over a local corpus** of product specs + prior tester feedback, with **citations**, running fully offline on local embeddings + a local LLM.

## Corpus (anonymized, synthetic + public)
- Product spec sheets (synthetic markdown: fabric, care, sizing notes) — generate ~30.
- Tester feedback excerpts derived from the [Women's E-Commerce Clothing Reviews](https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews) set, grouped by category.

## Pipeline
1. **Chunk** docs (≈500 tokens, 50 overlap).
2. **Embed** via `POST /v1/embeddings` on LM Studio (load an embedding model).
3. **Store** in `chromadb` (persistent local dir).
4. **Retrieve** top-k (k=4) for a query; optional rerank.
5. **Generate** a grounded answer that **cites chunk ids**; refuse if retrieval is empty.

## Output contract
```python
class GroundedAnswer(BaseModel):
    answer: str
    citations: list[str]     # chunk/source ids actually used
    confidence: Literal["low", "medium", "high"]
```

## Architecture
- **Backend (FastAPI):** `POST /ingest` (build/refresh index), `POST /ask` → `GroundedAnswer`.
- **Frontend:** a simple ask box that shows the answer with expandable cited sources.

## Prompt sketch
```
SYSTEM: Answer ONLY from the provided context. Cite source ids. If the context
        doesn't contain the answer, say you don't know. Return JSON (GroundedAnswer).
CONTEXT: <retrieved chunks with ids>      # static-ish block → cache-friendly (B3)
USER: <question>
```

## Acceptance criteria
- "What do testers say about shrinkage on cotton items?" returns an answer with ≥1 real citation.
- Empty/irrelevant retrieval yields an honest "I don't know" (grounding works).
- Runs with no network access once models are downloaded.

## Stretch
- Hybrid retrieval (keyword + dense).
- Swap the embedding/LLM to a cloud provider via `.env` and show identical behavior.

## Build notes (for the agent)
Start with the ingest + retrieve path and a CLI `ask`, prove grounding, then add the FastAPI + frontend. Keep `k`, chunk size, and model ids in `.env`.
