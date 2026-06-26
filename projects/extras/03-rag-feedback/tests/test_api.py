import json

from fastapi.testclient import TestClient

from backend.app import answer_question, app, get_collection
from backend.index import (
    HashingEmbeddingFunction,
    build_collection,
    load_fixture,
    retrieve,
)

from .conftest import install_fake_client


def _stub_collection():
    return build_collection(
        load_fixture(), embedding_function=HashingEmbeddingFunction()
    )


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ask_returns_grounded_answer(monkeypatch):
    # Override the collection dependency so no embedding model is downloaded.
    collection = _stub_collection()
    app.dependency_overrides[get_collection] = lambda: collection

    # The model cites fb-001 (real, retrieved) AND fb-999 (hallucinated).
    payload = json.dumps(
        {
            "answer": "Cotton items can shrink after a warm wash; wash cold.",
            "citations": [
                {"id": "fb-001", "snippet": "cotton t-shirt shrank"},
                {"id": "fb-999", "snippet": "hallucinated source"},
            ],
            "confidence": "high",
        }
    )
    install_fake_client(monkeypatch, [payload])

    try:
        resp = client.post(
            "/ask", json={"question": "cotton shrank warm wash", "top_k": 4}
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["confidence"] == "high"
    cited_ids = {c["id"] for c in body["citations"]}
    # Grounding contract: hallucinated id dropped, real retrieved id kept.
    assert "fb-001" in cited_ids
    assert "fb-999" not in cited_ids


def test_every_citation_references_a_retrieved_doc(monkeypatch, stub_collection):
    # Direct call: cite a mix and assert all surviving citations were retrieved.
    retrieved_ids = {
        d.id for d in retrieve(stub_collection, "shrinkage cotton wash", top_k=4)
    }
    payload = json.dumps(
        {
            "answer": "Yes, several cotton items shrink.",
            "citations": [{"id": rid, "snippet": "x"} for rid in retrieved_ids]
            + [{"id": "fb-000-fake", "snippet": "nope"}],
            "confidence": "medium",
        }
    )
    install_fake_client(monkeypatch, [payload])
    answer = answer_question("shrinkage cotton wash", stub_collection, top_k=4)
    assert answer.citations  # at least one survived
    for c in answer.citations:
        assert c.id in retrieved_ids


def test_quarantine_yields_honest_dont_know(monkeypatch, stub_collection):
    # Model returns junk twice -> structured_call quarantines -> honest fallback.
    install_fake_client(monkeypatch, ["nonsense", "still nonsense"])
    answer = answer_question("anything at all", stub_collection, top_k=4)
    assert answer.citations == []
    assert answer.confidence == "low"
    assert "don't know" in answer.answer.lower()
