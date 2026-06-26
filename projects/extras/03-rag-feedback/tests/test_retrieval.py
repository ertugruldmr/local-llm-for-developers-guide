from backend.index import HashingEmbeddingFunction, build_collection, load_fixture, retrieve
from backend.models import FeedbackDoc


def test_fixture_loads_twenty_docs(fixture_rows):
    assert len(fixture_rows) == 20
    for row in fixture_rows:
        doc = FeedbackDoc.model_validate(row)
        assert doc.id
        assert doc.text
        assert doc.product_category


def test_shrinkage_query_retrieves_planted_docs(stub_collection):
    # fb-001, fb-008, fb-015, fb-016 all describe items that shrank when washed.
    docs = retrieve(stub_collection, "cotton shrank warm wash", top_k=4)
    ids = {d.id for d in docs}
    assert "fb-001" in ids
    # the planted shrinkage docs should dominate the top-k
    shrinkage_ids = {"fb-001", "fb-008", "fb-015", "fb-016"}
    assert len(ids & shrinkage_ids) >= 2


def test_waterproof_query_retrieves_rain_jacket(stub_collection):
    docs = retrieve(stub_collection, "is the rain jacket waterproof in heavy rain", top_k=3)
    ids = {d.id for d in docs}
    assert "fb-012" in ids


def test_retrieve_respects_top_k(stub_collection):
    docs = retrieve(stub_collection, "fabric quality", top_k=2)
    assert len(docs) == 2


def test_empty_collection_returns_nothing():
    collection = build_collection([], embedding_function=HashingEmbeddingFunction())
    assert retrieve(collection, "anything", top_k=4) == []
