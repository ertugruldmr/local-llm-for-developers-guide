from __future__ import annotations

import sys, pathlib
# walk up to the projects/ root (the dir that holds common/llm.py) so `common` resolves
for _cand in pathlib.Path(__file__).resolve().parents:
    if (_cand / "common" / "llm.py").exists():
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break

from typing import List, Optional

from chromadb.api.models.Collection import Collection
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.llm import QuarantineError, structured_call

from .index import build_collection, retrieve
from .models import Answer, AskRequest, Citation, FeedbackDoc

SYSTEM_PROMPT = (
    "You answer questions about product feedback using ONLY the provided context. "
    "Each context item has an id. Cite the ids you used. If the context does not "
    "contain the answer, say you don't know and return an empty citations list. "
    "Return ONLY a JSON object matching this schema:\n"
    '{"answer": string, "citations": [{"id": string, "snippet": string}], '
    '"confidence": "low|medium|high"}'
)


def _format_context(docs: List[FeedbackDoc]) -> str:
    return "\n".join(f"[{d.id}] ({d.product_category}) {d.text}" for d in docs)


def answer_question(
    question: str, collection: Collection, top_k: int = 4
) -> Answer:
    retrieved = retrieve(collection, question, top_k=top_k)
    retrieved_ids = {d.id for d in retrieved}

    if not retrieved:
        return Answer(
            answer="I don't know — no relevant feedback was found.",
            citations=[],
            confidence="low",
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CONTEXT:\n{_format_context(retrieved)}\n\nQUESTION: {question}"},
    ]
    try:
        result = structured_call(messages, Answer)
    except QuarantineError:
        return Answer(
            answer="I don't know — the model could not produce a grounded answer.",
            citations=[],
            confidence="low",
        )

    # Grounding guard: drop any citation the model invented that was not
    # actually retrieved. The answer may only cite from the supplied context.
    grounded = [c for c in result.citations if c.id in retrieved_ids]
    return Answer(answer=result.answer, citations=grounded, confidence=result.confidence)


app = FastAPI(title="Product-Feedback RAG Assistant", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_collection: Optional[Collection] = None


def get_collection() -> Collection:
    """Lazily build the (default-embedder) collection on first use.

    Tests override this via dependency_overrides with a stub-embedder
    collection so no embedding model is ever downloaded.
    """
    global _collection
    if _collection is None:
        _collection = build_collection()
    return _collection


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
def ask(req: AskRequest, collection: Collection = Depends(get_collection)) -> Answer:
    return answer_question(req.question, collection, top_k=req.top_k)
