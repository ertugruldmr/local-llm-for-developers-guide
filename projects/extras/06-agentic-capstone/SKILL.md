---
name: scaffold-fastapi-from-spec
description: Scaffold a FastAPI service with a pydantic v2 output contract and an offline pytest, from a written spec. Use when an AGENTS.md points an agent at a per-project spec and asks for a backend that passes tests with no network.
---

# Skill — scaffold a FastAPI service from a spec

A reusable procedure for turning a per-project spec (problem, schema, endpoints,
acceptance) into a working, offline-tested FastAPI backend. This is the sample
skill the P6 capstone drives the agent with. (A9 — prompts/skills as files.)

## When to use

The repo's `AGENTS.md` names a spec file and the structured-output contract, and
asks for a backend whose tests pass offline. Don't use it for frontend work or for
anything that needs a live model in tests.

## Procedure

1. **Read the spec + AGENTS.md.** Extract: the output schema, the endpoints, the
   fixture shape, and the acceptance criteria. Note the fixed enums/vocabularies.
2. **Schema first.** Write `backend/models.py` — pydantic v2, type hints,
   `typing.Optional[...]`, `Field(max_length=...)` / `Literal[...]` constraints from
   the spec. No fields the spec doesn't name.
3. **Fixture.** Write a ~20-row synthetic fixture matching the spec's data contract.
   Synthetic only — no source-dataset rows, no PII, generic fashion-retail.
4. **Endpoints.** Write `backend/app.py` — FastAPI app, `/health`, plus the spec's
   endpoints. Every model call goes through `common.llm.structured_call` (JSON mode
   → validate → retry once → quarantine). Never reimplement model config; import
   from `common/llm.py`.
5. **Offline tests.** Write `tests/` that monkeypatch the OpenAI client to replay
   canned JSON. Assert: every fixture row → a valid schema instance; malformed JSON
   triggers the retry; a second failure raises `QuarantineError`; endpoints behave.
   No network, no live model.
6. **Run + green.** Run the package's pytest from the `projects/` root. Fix until
   green. Record any point where you needed human input as a steering moment.

## Output

A `generated/backend/` with `models.py`, `app.py`, a fixture, and `tests/` that pass
offline — plus the steering moments noted for the `AgentRunRecord`.

## Guardrails

- Structured output on every model-driven response; retry-once-then-quarantine.
- The three-env-var swap must hold (no hardcoded base_url / key / model).
- No PII, no company/internal names. Type hints on every signature.
