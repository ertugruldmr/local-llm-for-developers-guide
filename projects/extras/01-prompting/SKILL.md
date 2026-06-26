---
name: classify-review-sentiment
description: Classify a fashion-retail customer review as positive, neutral, or negative. Use when a task needs a single sentiment label for one review and a strict JSON output.
---

# Classify Review Sentiment

A capability file in the `SKILL.md` format (article A9 ↔ C11). An agentic tool
reads only the `description` above and lazy-loads this body when a task matches —
keeping the context window lean (B1).

## When to use

A task asks for the sentiment of exactly one fashion-retail review and expects a
machine-readable label, not a paragraph.

## Contract

Return only:

```json
{"sentiment": "positive" | "neutral" | "negative"}
```

No extra fields, no prose.

## How to apply

1. Put the role + instruction + output indicator in the `system` message (A1).
2. For ambiguous or mixed reviews, prepend three labeled examples — one per class
   — as `user`/`assistant` turns (few-shot, A3). Keep them static and ahead of the
   input so the prefix stays cacheable (B3).
3. Validate the response against the `SentimentLabel` Pydantic model; on failure,
   retry once then quarantine (A6). `common.structured_call` does this for you.

## Reference implementation

See `demo.py` in this package: `build_zero_shot_messages`, `build_few_shot_messages`,
and `classify`.
