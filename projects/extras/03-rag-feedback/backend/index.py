from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import List, Optional, Sequence

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from .models import FeedbackDoc

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "feedback.jsonl"


def load_fixture(path: Path = FIXTURE) -> List[FeedbackDoc]:
    with path.open() as fh:
        return [FeedbackDoc.model_validate_json(line) for line in fh if line.strip()]


def build_collection(
    docs: Optional[Sequence[FeedbackDoc]] = None,
    *,
    embedding_function: Optional[EmbeddingFunction] = None,
) -> Collection:
    """Build an EPHEMERAL (in-memory) Chroma collection from feedback docs.

    `embedding_function` is injectable: production leaves it `None` so Chroma
    uses its bundled default (local ONNX MiniLM, no API calls); tests pass a
    deterministic stub so retrieval is reproducible with zero network.
    """
    if docs is None:
        docs = load_fixture()

    client = chromadb.EphemeralClient()
    kwargs = {} if embedding_function is None else {"embedding_function": embedding_function}
    # Unique name per build: EphemeralClient shares one in-process system, so a
    # fixed name would collide when more than one collection is built (e.g.
    # across tests). The collection is still in-memory and discarded with the client.
    collection = client.create_collection(name=f"feedback_{uuid.uuid4().hex}", **kwargs)  # type: ignore[arg-type]
    if not docs:
        return collection
    collection.add(
        ids=[d.id for d in docs],
        documents=[d.text for d in docs],
        metadatas=[{"product_category": d.product_category} for d in docs],
    )
    return collection


def retrieve(collection: Collection, question: str, top_k: int = 4) -> List[FeedbackDoc]:
    """Return the top-k feedback docs for a question, most-relevant first."""
    n = min(top_k, collection.count())
    if n == 0:
        return []
    res = collection.query(query_texts=[question], n_results=n)
    ids = res["ids"][0]
    documents = res["documents"][0]
    metadatas = res["metadatas"][0]
    return [
        FeedbackDoc(
            id=doc_id,
            text=text,
            product_category=str(meta.get("product_category", "")),
        )
        for doc_id, text, meta in zip(ids, documents, metadatas)
    ]


_STOPWORDS = frozenset(
    """a an and the of to in on at for is are was were be been it its this that these
    those i you he she they we my your me as but or if so no not too very only just
    after before with without about over under into from up down out off than then
    all any few more most some such own same other each both did do does
    """.split()
)


class HashingEmbeddingFunction(EmbeddingFunction):
    """Deterministic, network-free embedder for tests and offline demos.

    A bag-of-words hashing vectorizer with stopword removal: each content token
    is hashed into one of `dim` buckets, then L2-normalized. No model download,
    fully reproducible. Documents sharing content vocabulary land near each
    other, which is enough to prove the retrieval + grounding contract without a
    real embedding model. (It is exact-token, not semantic — the production path
    uses Chroma's bundled MiniLM embedder; see build_collection.)
    """

    def __init__(self, dim: int = 256) -> None:
        self._dim = dim

    @staticmethod
    def name() -> str:
        return "hashing-stub"

    def get_config(self) -> dict:
        return {"dim": self._dim}

    @classmethod
    def build_from_config(cls, config: dict) -> "HashingEmbeddingFunction":
        return cls(dim=config.get("dim", 256))

    def __call__(self, input: Documents) -> Embeddings:
        vectors: Embeddings = []
        for text in input:
            vec = [0.0] * self._dim
            for token in text.lower().split():
                token = token.strip(".,!?;:\"'()")
                if not token or token in _STOPWORDS:
                    continue
                digest = hashlib.md5(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "big") % self._dim
                vec[bucket] += 1.0
            norm = sum(v * v for v in vec) ** 0.5
            if norm > 0:
                vec = [v / norm for v in vec]
            vectors.append(vec)
        return vectors
