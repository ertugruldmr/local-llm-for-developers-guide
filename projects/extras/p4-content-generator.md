# Spec — P4: Survey-Question & Product-Description Generator (generation demo)

**Package:** `01-prompting/` extension (spec-only, not a numbered package) · **Concepts:** A3 few-shot, A6 structured output, A7 guardrails · **Difficulty:** ⭐⭐

## Goal
Turn structured product attributes into either **TR/EN product copy** or a
**balanced set of survey questions**, returning validated JSON the app can render
directly. It demonstrates few-shot steering (A3), output contracts (A6), and
content guardrails (A7) — no superlative claims without attribute support, hard
length caps, no fabricated attributes.

## User stories
- As a merchandiser, I paste product attributes and get a title + bullet copy
  (English and Turkish) I can drop into a listing.
- As a survey designer, I get a balanced set of questions (mix of rating, single-
  choice, open-ended) probing the product, with no leading phrasing.
- As a developer, every output is schema-validated, so the UI never has to parse
  free text.

## Data (synthetic, generic fashion-retail)
- `fixtures/products.jsonl` — ~20 synthetic product-attribute rows, each:
  `{category, fabric, fit, color, season}` (e.g. `{"category": "midi dress",
  "fabric": "viscose", "fit": "relaxed", "color": "ecru", "season": "SS"}`).
  Hand-authored, no source-dataset rows, no PII.
- A static few-shot set (2–3 attribute→copy and attribute→questions pairs) lives in
  the prompt, not the fixture.

## Output contract (structured output)
```python
from pydantic import BaseModel, Field
from typing import Literal

class ProductCopy(BaseModel):
    lang: Literal["en", "tr"]
    title: str = Field(max_length=70)
    bullets: list[str] = Field(min_length=3, max_length=5)   # each <= 120 chars
    meta: str = Field(max_length=160)                         # SEO meta description

class SurveyQuestion(BaseModel):
    kind: Literal["rating", "single_choice", "open"]
    text: str
    options: list[str] = Field(default_factory=list)          # only for single_choice

class SurveyQuestionSet(BaseModel):
    questions: list[SurveyQuestion] = Field(min_length=4, max_length=8)
```
Each bullet > the 120-char cap, or a `single_choice` with empty `options`, or copy
mentioning an attribute not present in the input → validation failure → retry once
→ quarantine, all via `common.llm.structured_call`.

## Guardrails (A7)
- **Attribute-grounded only:** the model may not introduce claims (e.g. "softest
  fabric ever") that aren't supported by the input attributes.
- **No superlatives** unsupported by attributes (post-validation check on the copy).
- **Length caps** enforced by the schema (`max_length` fields).
- **Balanced questions:** the set must include ≥1 of each `kind` (validator).

## Architecture
- **Backend (FastAPI):** `POST /generate-copy` → `ProductCopy` (per `lang`);
  `POST /generate-questions` → `SurveyQuestionSet`; `GET /health`.
- **Frontend (optional):** an attribute form with a mode toggle (copy / questions),
  rendering the validated JSON. Spec-only — frontend not required for done.

## Prompt sketch
```
SYSTEM: You write fashion-retail product copy / survey questions from attributes
        ONLY. Never claim an attribute not given. No superlatives. Honor length
        caps. Return ONLY JSON matching the requested schema.
FEW-SHOT: <2-3 attribute -> output pairs>     # A3, static prefix → cache-friendly (B3)
USER: <product attributes JSON> + mode
```

## Acceptance criteria
- Both modes return schema-valid JSON for the full fixture (≥95% first-try, rest
  recovered or quarantined).
- A copy request whose attributes don't justify a claim does **not** produce that
  claim (guardrail check passes on a small adversarial set).
- A question set always contains ≥1 rating, ≥1 single_choice (with options), ≥1 open.
- README documents the cloud swap and the few-shot example set.

## Stretch
- Turkish-first mode with `trnorm`-style normalization of the output.
- A/B two few-shot sets and compare adherence to the length/guardrail constraints.

## Swap to cloud
All generation goes through `common.llm.structured_call`; switching to a cloud
provider is the three-env-var change (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) —
no code edits.

## Build notes (for the agent)
This is a spec-only extension of `01-prompting/`; if implemented, follow the same
backend→fixture→pytest→frontend order. Implement `generate-questions` first (purely
structural guardrails are easy to test), then `generate-copy` with the
attribute-grounding check. Keep model config in `.env`.
