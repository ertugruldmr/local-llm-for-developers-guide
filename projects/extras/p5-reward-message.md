# Spec — P5: Personalized Reward-Message Generator (guardrails demo)

**Package:** `01-prompting/` extension (spec-only, not a numbered package) · **Concepts:** A6 structured output, A7 guardrails · **Difficulty:** ⭐⭐

## Goal
From an **anonymized respondent profile + recent survey responses**, generate a
personalized reward (voucher) message **plus an auditable `reasoning` field** that
explains why this message/tone was chosen. The teaching point: when an LLM drives a
customer-facing action, the *reasoning* must be inspectable and the *guardrails*
must be enforced — no sensitive inferences, opt-out aware.

## User stories
- As a CRM owner, I get a short reward message tailored to the respondent's recent
  feedback, in a tone that fits their sentiment.
- As a compliance reviewer, I can read the `reasoning` field and see exactly which
  inputs drove the message — an audit trail, not a black box.
- As a developer, the output is validated JSON; opted-out profiles are refused
  before a message is ever generated.

## Data (synthetic, generic fashion-retail)
- `fixtures/profiles.jsonl` — ~20 synthetic, **anonymized** profiles:
  `{profile_id, tenure_months, recent_sentiment, last_categories[], opted_out}`.
  No names, no contact info, no demographics beyond a coarse `tenure_months`.
  Hand-authored, no PII.

## Output contract (structured output)
```python
from pydantic import BaseModel, Field
from typing import Literal

Tone = Literal["warm", "neutral", "apologetic", "celebratory"]

class RewardMessage(BaseModel):
    message: str = Field(max_length=240)
    tone: Tone
    reasoning: str = Field(max_length=300)   # auditable: which inputs drove this
    inputs_used: list[str]                   # explicit list of profile/response fields cited
```
Validated via `common.llm.structured_call` (retry-once-then-quarantine). The
`inputs_used` list makes the audit trail machine-checkable: every field named must
actually exist in the input (validator), so the `reasoning` can't cite phantom data.

## Guardrails (A7)
- **Opt-out aware:** if `opted_out` is true, the endpoint returns `204`/refusal
  **before** any model call — no message generated.
- **No sensitive inferences:** the prompt forbids inferring or referencing
  protected attributes (health, ethnicity, religion, exact age, etc.); a
  post-validation check rejects messages that do.
- **Grounded reasoning:** `inputs_used` must reference only real input fields
  (validator); the `reasoning` must be consistent with them.
- **Length caps** enforced by the schema.

## Architecture
- **Backend (FastAPI):** `POST /reward` → body `{profile}` → `RewardMessage`, or a
  refusal (`204` / `{refused: true, reason}`) when `opted_out`. `GET /health`.
- **Frontend (optional):** a profile picker that shows the generated message and an
  expandable "why this message" panel exposing `reasoning` + `inputs_used`.
  Spec-only — not required for done.

## Prompt sketch
```
SYSTEM: You write a short fashion-retail reward message from an anonymized profile
        ONLY. Never infer sensitive attributes. Cite the exact input fields you
        used in inputs_used. Pick a tone matching recent_sentiment. Return ONLY
        JSON (RewardMessage).
USER: <anonymized profile JSON + recent responses>
```

## Acceptance criteria
- Opted-out profiles are refused with no model call (verified by a test that fails
  if the client is invoked).
- For the fixture, every generated `RewardMessage` is schema-valid and every
  `inputs_used` entry maps to a real input field.
- A small adversarial profile set does not produce sensitive-inference language
  (guardrail check passes).
- README documents the cloud swap and the audit/guardrail design.

## Stretch
- Turkish tone variants.
- Log every generation with its `reasoning` to a JSONL audit file.

## Swap to cloud
Generation goes through `common.llm.structured_call`; the three-env-var change
(`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) switches to any cloud provider with no
code edits. The opt-out refusal is enforced in app code, before the client call, so
it holds regardless of provider.

## Build notes (for the agent)
Spec-only extension of `01-prompting/`. If implemented: backend→fixture→pytest
first. Write the opt-out refusal and the `inputs_used` grounding validator before
the prompt — they're the load-bearing guardrails and the easiest to test offline.
Keep model config in `.env`.
