# AGENTS.md — agentic capstone build conventions

This file is the agent's brief for regenerating the **P1 backend**
(`04-fullstack-analyzer/backend/`) from its spec. Both build paths (Claude Code,
opencode) read it. Keep it tight — these are hard rules, not suggestions.

> The "minimal steering" / self-improving behavior is a **design goal of this
> workflow, not a benchmarked guarantee.** Document what happened on the run; make
> no general claim.

## Target

Regenerate the FastAPI backend specified in
[`../p1-review-analyzer.md`](../p1-review-analyzer.md) into `generated/backend/`,
with offline-passing tests. The hand-built reference is
`../04-fullstack-analyzer/` — do not edit it; diff against it at the end.

## Hard rules

1. **Config contract.** All model config lives in `common/llm.py` (imported, never
   reimplemented): `get_client()` reads `LLM_BASE_URL`, `LLM_API_KEY`; `LLM_MODEL`
   is the model id. Local default is `http://localhost:1234/v1`. The cloud swap is
   exactly those three env vars — no other code knows local-vs-cloud.
2. **Structured output everywhere.** Every model call that feeds software returns a
   pydantic v2 model. Use JSON mode (`response_format={"type": "json_object"}`).
3. **Retry-once-then-quarantine.** On schema-validation failure, retry once with the
   validator error appended; a second failure raises `QuarantineError` and the row
   is set aside — never crash the batch. Use `common.llm.structured_call`.
4. **Build order:** backend with a 20-row fixture → pytest asserting schema validity
   → expand → (frontend last, out of scope here).
5. **Tests pass offline.** Mock the LLM client (no network, no live model in tests).
6. **No PII, no company names, no internal project names.** Domain is a generic
   fashion-retail customer survey & rewards panel. Public/synthetic data only.
7. **Type hints on every signature.** pydantic v2. `typing.Optional[...]` (host is
   on Python 3.9). No speculative abstractions — solve the spec, nothing more.

## Skills

Use [`SKILL.md`](SKILL.md): "scaffold a FastAPI service with a pydantic output
contract + offline pytest from a spec." Follow its procedure step by step.

## Done when

`generated/backend/` exists, its offline pytest is green, and the run is recorded as
an `AgentRunRecord` (`backend/run_record.py`) — including every human steering moment.
