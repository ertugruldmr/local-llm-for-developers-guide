import sys, pathlib
# walk up to the projects/ root (the dir that holds common/llm.py) so `common` resolves
for _cand in pathlib.Path(__file__).resolve().parents:
    if (_cand / "common" / "llm.py").exists():
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break

from collections import Counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from common.llm import QuarantineError, structured_call

from .models import (
    AnalyzeBatchRequest,
    AnalyzeBatchResult,
    AnalyzeRequest,
    BaselineResult,
    ReviewInsight,
    THEMES,
)

SYSTEM_PROMPT = (
    "You label retail product reviews. Return ONLY a JSON object matching this schema:\n"
    '{"sentiment": "positive|neutral|negative", "themes": [string], '
    '"sizing_issue": boolean, "churn_risk": "low|medium|high", "summary": string}\n'
    f"Pick themes only from this fixed list: {THEMES}. "
    "summary must be <= 20 words. Do not add fields."
)

# Few-shot examples kept static so they sit ahead of the dynamic review,
# which enables prompt caching (article B3).
FEW_SHOT: list[dict[str, str]] = [
    {
        "role": "user",
        "content": "Runs two sizes small and the seams frayed after one wash. Returning it.",
    },
    {
        "role": "assistant",
        "content": (
            '{"sentiment": "negative", "themes": ["sizing", "quality"], '
            '"sizing_issue": true, "churn_risk": "high", '
            '"summary": "Sizing off and poor build quality, customer returning the item."}'
        ),
    },
    {
        "role": "user",
        "content": "Lovely fabric, true to size, arrived quickly. Will order again.",
    },
    {
        "role": "assistant",
        "content": (
            '{"sentiment": "positive", "themes": ["fabric", "fit", "delivery"], '
            '"sizing_issue": false, "churn_risk": "low", '
            '"summary": "Happy with fabric, fit and fast delivery; intends to reorder."}'
        ),
    },
]


def analyze_review(review_text: str) -> ReviewInsight:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT,
        {"role": "user", "content": review_text},
    ]
    return structured_call(messages, ReviewInsight)


app = FastAPI(title="Review / Survey Analyzer", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=ReviewInsight)
def analyze(req: AnalyzeRequest) -> ReviewInsight:
    return analyze_review(req.review_text)


@app.post("/analyze-batch", response_model=AnalyzeBatchResult)
def analyze_batch(req: AnalyzeBatchRequest) -> AnalyzeBatchResult:
    insights: list[ReviewInsight] = []
    quarantined: list[str] = []
    for text in req.reviews:
        try:
            insights.append(analyze_review(text))
        except QuarantineError:
            quarantined.append(text)
    return AnalyzeBatchResult(insights=insights, quarantined=quarantined)


@app.post("/baseline", response_model=BaselineResult)
def baseline(req: AnalyzeRequest) -> BaselineResult:
    # DistilBERT sentiment baseline. 503 if transformers+torch aren't installed
    # (the import is lazy and guarded — see backend/compare.py).
    from .compare import TransformersUnavailable, classify

    try:
        return classify(req.review_text)
    except TransformersUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/aggregate")
def aggregate(req: AnalyzeBatchRequest) -> dict[str, object]:
    batch = analyze_batch(req)
    sentiment_counts: Counter[str] = Counter(i.sentiment for i in batch.insights)
    theme_counts: Counter[str] = Counter(t for i in batch.insights for t in i.themes)
    churn_counts: Counter[str] = Counter(i.churn_risk for i in batch.insights)
    return {
        "n": len(batch.insights),
        "quarantined": len(batch.quarantined),
        "sentiment": dict(sentiment_counts),
        "themes": dict(theme_counts),
        "churn_risk": dict(churn_counts),
    }
