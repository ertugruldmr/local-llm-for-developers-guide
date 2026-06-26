"""Concept demo for Part 1, A6 — output contracts / structured output.

This is the lesson that makes an LLM "safe to wire into software": instead of
free text, the model must return JSON matching a Pydantic schema. We call it
through `common.structured_call`, which uses JSON mode (`response_format`),
validates the response, and on failure applies the documented
retry-once-then-quarantine policy.

Domain: extract a structured record from one fashion-retail review.
"""

from __future__ import annotations

import sys, pathlib
# walk up to the projects/ root (the dir that holds common/llm.py) so `common` resolves
for _cand in pathlib.Path(__file__).resolve().parents:
    if (_cand / "common" / "llm.py").exists():
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break

import argparse
from typing import List, Literal

from openai import APIConnectionError
from pydantic import BaseModel, Field

from common.llm import LLM_MODEL, QuarantineError, structured_call

Sentiment = Literal["positive", "neutral", "negative"]
ChurnRisk = Literal["low", "medium", "high"]

# Fixed vocabulary the model must choose themes from — closed sets are easier to
# validate and keep downstream analytics clean.
THEMES = ["sizing", "fabric", "fit", "color", "delivery", "price", "quality", "service"]


class ReviewRecord(BaseModel):
    """The output contract. Every field is the model's promise to the software."""

    sentiment: Sentiment
    themes: List[str]
    sizing_issue: bool
    churn_risk: ChurnRisk
    summary: str = Field(max_length=160)


SYSTEM_PROMPT = (
    "You extract structured records from fashion-retail product reviews.\n"
    "Return ONLY a JSON object matching this schema:\n"
    '{"sentiment": "positive|neutral|negative", "themes": [string], '
    '"sizing_issue": boolean, "churn_risk": "low|medium|high", "summary": string}\n'
    f"Pick themes only from this fixed list: {THEMES}. "
    "summary must be <= 20 words. Do not add fields or prose."
)


def extract_record(review_text: str) -> ReviewRecord:
    """Extract a validated ReviewRecord from one review.

    `structured_call` enforces the contract: it requests JSON mode, validates
    against ReviewRecord, and on a validation failure retries ONCE with the
    validator error appended. A second failure raises QuarantineError so the
    caller can set the row aside instead of crashing the batch.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": review_text},
    ]
    return structured_call(messages, ReviewRecord)


SAMPLE_REVIEW = (
    "Beautiful color but it runs at least one size small and the stitching came "
    "loose after a couple of wears. Doubt I'll order from here again."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Structured-output (A6) demo.")
    parser.add_argument("--review", default=SAMPLE_REVIEW, help="Review text to extract.")
    args = parser.parse_args()

    print(f"model={LLM_MODEL}")
    print(f"review: {args.review}")
    try:
        record = extract_record(args.review)
    except QuarantineError as exc:
        # In a batch you'd append exc.raw to a quarantine list and continue.
        print(f"QUARANTINED (validation failed twice): {exc}")
        return
    except APIConnectionError:
        print(
            "Could not reach a model at LLM_BASE_URL. Start LM Studio's local "
            "server, or point the three env vars at a cloud provider — see "
            "../00-serve-lmstudio/README.md."
        )
        raise SystemExit(1)
    print("validated record:")
    print(record.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
