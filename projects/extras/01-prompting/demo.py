"""Concept demo for Part 1, Pillar A — prompt anatomy + zero-shot vs few-shot.

Classifies a fashion-retail review's sentiment two ways:
  - zero-shot: instruction + role + output indicator, no examples (A2)
  - few-shot:  same, plus input->output demonstrations (A3)

Both call the local model through `common.structured_call`, so the response is
validated against a Pydantic schema (A6). Run with --mode zero|few.
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
from typing import Literal

from openai import APIConnectionError
from pydantic import BaseModel

from common.llm import LLM_MODEL, structured_call

Sentiment = Literal["positive", "neutral", "negative"]


class SentimentLabel(BaseModel):
    """The output contract (A6) — the only shape the model is allowed to return."""

    sentiment: Sentiment


# --- Prompt anatomy (A1) -----------------------------------------------------
# Role + instruction + output indicator live in the system message so they sit
# ahead of the dynamic review (static-first ordering, enables caching — B3).
SYSTEM_PROMPT = (
    "You are a precise labeling assistant for a fashion-retail review panel.\n"
    "Classify the sentiment of one customer review.\n"
    'Return ONLY a JSON object of the form {"sentiment": "positive|neutral|negative"}.\n'
    "Do not add fields, prose, or explanation."
)

# Few-shot demonstrations (A3). Static, so they precede the dynamic review.
FEW_SHOT: list[dict[str, str]] = [
    {"role": "user", "content": "Runs two sizes small and the fabric pilled after one wash."},
    {"role": "assistant", "content": '{"sentiment": "negative"}'},
    {"role": "user", "content": "True to size, soft fabric, arrived early. Ordering again."},
    {"role": "assistant", "content": '{"sentiment": "positive"}'},
    {"role": "user", "content": "It's fine. Nothing special, nothing wrong."},
    {"role": "assistant", "content": '{"sentiment": "neutral"}'},
]


def build_zero_shot_messages(review_text: str) -> list[dict[str, str]]:
    """Zero-shot (A2): instruction + the review, no examples."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": review_text},
    ]


def build_few_shot_messages(review_text: str) -> list[dict[str, str]]:
    """Few-shot (A3): same prompt, with example turns ahead of the input."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT,
        {"role": "user", "content": review_text},
    ]


def classify(review_text: str, *, mode: Literal["zero", "few"]) -> SentimentLabel:
    """Build the chosen prompt and return a validated SentimentLabel."""
    builder = build_zero_shot_messages if mode == "zero" else build_few_shot_messages
    messages = builder(review_text)
    return structured_call(messages, SentimentLabel)


SAMPLE_REVIEW = "Gorgeous color but it arrived a week late and the zipper jamms."


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-shot vs few-shot sentiment demo.")
    parser.add_argument("--mode", choices=["zero", "few"], default="few")
    parser.add_argument("--review", default=SAMPLE_REVIEW, help="Review text to classify.")
    args = parser.parse_args()

    print(f"model={LLM_MODEL} mode={args.mode}")
    print(f"review: {args.review}")
    try:
        result = classify(args.review, mode=args.mode)
    except APIConnectionError:
        print(
            "Could not reach a model at LLM_BASE_URL. Start LM Studio's local "
            "server, or point the three env vars at a cloud provider — see "
            "../00-serve-lmstudio/README.md."
        )
        raise SystemExit(1)
    print(f"sentiment: {result.sentiment}")


if __name__ == "__main__":
    main()
