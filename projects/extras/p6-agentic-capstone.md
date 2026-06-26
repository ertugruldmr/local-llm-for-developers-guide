# Spec — P6: Agentic Capstone — build P1 *with* an agent (harness demo)

**Package:** `06-agentic-capstone/` · **Concepts:** C1–C9 harness, A9 prompts-as-files · **Difficulty:** ⭐⭐⭐⭐

## Goal
Don't hand-write P1. **Regenerate P1's FastAPI backend from its spec using a coding
agent** driven by a repo `AGENTS.md` + a custom `SKILL.md`, running against a local
model. The artifact of this project isn't the code (P1 already exists) — it's the
**documented agent run**: where the harness got it right unattended, and the few
moments a human had to steer. Those steering moments are the teaching content.

> **Design-goal framing (guardrail):** the "self-improving" / minimal-steering
> behavior of the agent is a **design goal of the workflow, not a benchmarked
> guarantee**. We document what the harness did on *this* run; we make no claim it
> reproduces identically or beats a human in general.

## User stories
- As a learner, I run one agent invocation and watch it scaffold a working,
  tested FastAPI service from a spec — the harness builds the app.
- As a developer, I read `AGENTS.md` + `SKILL.md` and understand how to encode my
  own project conventions so an agent can execute them (A9, prompts-as-files).
- As a reviewer, I read the run log and see exactly which steps were autonomous and
  which needed a human nudge.

## The two build paths
- **Best-practice path:** Claude Code (subscription) pointed at a local model via
  the Anthropic-compatible endpoint, driven by `AGENTS.md` + `SKILL.md`.
- **Open path:** opencode on a local model in LM Studio — proves the workflow has
  zero cloud dependency.

Both consume the same `AGENTS.md` + `SKILL.md`; the run log notes which path produced
which result.

## Inputs (what the agent reads)
- `AGENTS.md` — repo conventions: the `common/llm.py` config contract, the
  structured-output / retry-once-then-quarantine pattern, the
  backend→fixture→pytest→frontend build order, "no PII / generic fashion-retail",
  and "tests must pass offline (mock the client)".
- `SKILL.md` — a reusable skill: **"scaffold a FastAPI service with a pydantic
  output contract + offline pytest from a spec"** (the procedure the agent follows).
- The target spec: `../p1-review-analyzer.md`.

## Output (success contract)
There is no new *runtime* schema — the agent's deliverable is a regenerated P1
backend. The capstone's own contract is the **run record**:
```python
from pydantic import BaseModel
from typing import Literal

class SteeringMoment(BaseModel):
    step: str
    issue: str
    human_action: str           # what the human did to unblock
    autonomous: Literal[False]  # by definition, steering = not autonomous

class AgentRunRecord(BaseModel):
    path: Literal["claude-code", "opencode"]
    model: str
    steps_total: int
    steps_autonomous: int
    steering_moments: list[SteeringMoment]
    backend_tests_pass: bool    # did the generated backend's pytest go green?
```
`backend/run_record.py` provides this model + a tiny `evaluate(generated_dir)`
helper that runs the generated backend's tests and fills `backend_tests_pass`.

## Acceptance criteria
- The agent, driven only by `AGENTS.md` + `SKILL.md` + the P1 spec, produces a
  FastAPI backend whose offline pytest **passes**, with minimal human steering.
- The run is documented as an `AgentRunRecord` (the steering moments captured).
- README contrasts the agent-built backend with the hand-built P1 (where they
  diverged, what the harness missed) — **without** claiming a benchmarked win.

## Stretch
- Run both paths (Claude Code and opencode) and diff the steering-moment counts.
- Have the agent also regenerate the frontend scaffold.
- Feed the steering moments back into `SKILL.md` and re-run (the "self-improving"
  *design goal* — documented as an experiment, not a guarantee).

## Swap to cloud
The generated backend inherits P1's contract: it talks to the model only through
`common.llm`, so the three-env-var swap applies. The *agent itself* swaps host by
pointing the harness at a cloud endpoint instead of the local one — same
`AGENTS.md` + `SKILL.md`.

## Build notes (for the agent / author)
This package ships the *inputs* (`AGENTS.md`, `SKILL.md`, `run_record.py` stub) and
a README that is the run protocol. The "build" is executing the agent run and
filling the README + `AgentRunRecord`. Keep the generated output in a sibling
`generated/` dir so it's diffable against `../04-fullstack-analyzer/`.
