"""Lightweight DistilBERT sentiment baseline for the LLM-vs-small-model lesson.

`transformers` + `torch` are heavy and optional. Imports are lazy and guarded so
the rest of the package (and its tests) work without them installed.
"""

from functools import lru_cache

from .models import BaselineResult, Sentiment

MODEL_ID = "distilbert-base-multilingual-cased-sentiments-student"

# The student model emits these labels; map them onto our three-way sentiment.
_LABEL_MAP: dict[str, Sentiment] = {
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}


class TransformersUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _pipeline():
    try:
        from transformers import pipeline  # noqa: PLC0415
    except ImportError as exc:  # torch/transformers not installed
        raise TransformersUnavailable(
            "transformers + torch are required for the DistilBERT baseline. "
            "Install package extras: pip install -r 04-fullstack-analyzer/requirements.txt"
        ) from exc
    return pipeline("sentiment-analysis", model=MODEL_ID)


def classify(review_text: str) -> BaselineResult:
    result = _pipeline()(review_text, truncation=True)[0]
    label = _LABEL_MAP.get(result["label"].lower(), "neutral")
    return BaselineResult(label=label, score=float(result["score"]))


def classify_batch(reviews: list[str]) -> list[BaselineResult]:
    pipe = _pipeline()
    out = pipe(reviews, truncation=True)
    return [
        BaselineResult(label=_LABEL_MAP.get(r["label"].lower(), "neutral"), score=float(r["score"]))
        for r in out
    ]
