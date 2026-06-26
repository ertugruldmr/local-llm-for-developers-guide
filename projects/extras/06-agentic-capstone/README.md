# 06 · Agentic Capstone — build P1 *with* an agent (P6)

Don't hand-write P1. **Regenerate P1's FastAPI backend from its spec using a coding
agent** driven by this package's [`AGENTS.md`](AGENTS.md) + [`SKILL.md`](SKILL.md),
on a local model. The artifact isn't the code (P1 already exists) — it's the
**documented run**: where the harness worked unattended, and the few moments a human
had to steer. Those moments are the teaching content.

Concepts: C1–C9 harness · A9 prompts-as-files.
Full spec: [`../p6-agentic-capstone.md`](../p6-agentic-capstone.md).

> **Status: skeleton.** `AGENTS.md` + `SKILL.md` + the `AgentRunRecord` schema exist;
> no agent run has been executed and `evaluate()` raises `NotImplementedError`. See
> [`.docs/001.spec-context.md`](.docs/001.spec-context.md) for the plan.
>
> **Design-goal framing:** "minimal steering" / self-improving is a **design goal of
> the workflow, not a benchmarked guarantee.** This README records what a run did; it
> makes no general claim that an agent beats a human.

## The two build paths

- **Best-practice path:** Claude Code pointed at a local model via the
  Anthropic-compatible endpoint, driven by `AGENTS.md` + `SKILL.md`.
- **Open path:** opencode on a local model in LM Studio — zero cloud dependency.

Both read the same `AGENTS.md` + `SKILL.md`.

## Run protocol

1. Start a local server (LM Studio) and confirm `GET /v1/models`.
2. Point the agent at this directory so it loads `AGENTS.md`.
3. Ask it to execute the `scaffold-fastapi-from-spec` skill against
   [`../p1-review-analyzer.md`](../p1-review-analyzer.md), writing to `generated/backend/`.
4. Let it run with **minimal steering**. Each time you intervene, note it.
5. Run the generated backend's offline pytest; capture the result.
6. Fill an `AgentRunRecord` (`backend/run_record.py`) with the steering moments and
   `backend_tests_pass`. Diff `generated/backend/` against `../04-fullstack-analyzer/backend/`.

## Layout

```
06-agentic-capstone/
├── AGENTS.md                  # agent brief: hard rules (config contract, structured output, build order)
├── SKILL.md                   # sample skill: scaffold-fastapi-from-spec
├── backend/
│   └── run_record.py          # AgentRunRecord schema + evaluate() stub
├── generated/                 # (created by the agent run) regenerated P1 backend
└── .docs/001.spec-context.md
```

## Config — three env vars (the whole contract)

| Var | Local default | Meaning |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:1234/v1` | OpenAI-compatible endpoint |
| `LLM_API_KEY`  | `lmstudio` | any non-empty string locally |
| `LLM_MODEL`    | `local-model` | model id from `GET /v1/models` |

**Swap to cloud — change only these three, no code changes:**

```bash
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

The generated backend inherits P1's contract (it talks to the model only through
`common.llm`), so the swap applies to it too. The *agent host* swaps by pointing the
harness at a cloud endpoint instead of the local one — same `AGENTS.md` + `SKILL.md`.

## Data

The agent generates P1's synthetic fixture (≥20 rows mirroring the Women's
E-Commerce Clothing Reviews schema [R-039]) — **synthetic, no PII, generic
fashion-retail**, same as the hand-built P1.
