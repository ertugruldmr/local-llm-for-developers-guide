from fastapi.testclient import TestClient

from backend.app import app

from .conftest import VALID_PAYLOAD, install_fake_client

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_returns_validated_insight(monkeypatch):
    install_fake_client(monkeypatch, [VALID_PAYLOAD])
    resp = client.post("/analyze", json={"review_text": "Runs small, fabric pilled."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sentiment"] == "negative"
    assert body["churn_risk"] == "high"
    assert "sizing" in body["themes"]


def test_analyze_batch_quarantines_bad_rows(monkeypatch):
    # All calls return junk -> every row is quarantined, none crash the batch.
    install_fake_client(monkeypatch, ["nonsense", "nonsense"])
    resp = client.post("/analyze-batch", json={"reviews": ["a", "b"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["insights"] == []
    assert set(body["quarantined"]) == {"a", "b"}


def test_aggregate_rolls_up(monkeypatch):
    install_fake_client(monkeypatch, [VALID_PAYLOAD])
    resp = client.post("/aggregate", json={"reviews": ["one", "two", "three"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["n"] == 3
    assert body["sentiment"]["negative"] == 3
    assert body["themes"]["sizing"] == 3
