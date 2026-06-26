# 01 · Prompting — zero-shot vs few-shot

A runnable concept demo for **Part 1, Pillar A** of the guide (prompt anatomy A1,
zero-shot A2, few-shot A3, output contracts A6, prompts-as-files A9).

It classifies the sentiment of a single fashion-retail review two ways and lets you
compare the prompt structures side by side.

## What it teaches

- **Prompt anatomy (A1)** — role + instruction + output indicator in the `system`
  message; the review as the `user` turn.
- **Zero-shot (A2)** — no examples; the model relies on pretraining.
- **Few-shot (A3)** — three labeled examples (one per class) prepended as
  `user`/`assistant` turns, ahead of the dynamic input so the prefix stays
  cacheable (B3).
- **Output contract (A6)** — the response is validated against a Pydantic
  `SentimentLabel` via `common.structured_call`.
- **`SKILL.md` (A9)** — `SKILL.md` shows the capability-file format an agentic
  tool lazy-loads on demand.

## Run

A local OpenAI-compatible server (e.g. LM Studio, default `http://localhost:1234/v1`)
must be serving a model. From the package dir (the `demo.py` path bootstrap puts
`projects/` on `sys.path` so `common` resolves):

```bash
cd projects/01-prompting
../.venv/bin/python demo.py --mode few
../.venv/bin/python demo.py --mode zero --review "Lovely dress, true to size."
```

## Test (offline — no LLM needed)

From `projects/`:

```bash
.venv/bin/python -m pytest 01-prompting -q
```

The tests mock the client (`tests/conftest.py`), so they assert prompt structure
and parsing without any network call.

## Config — the three env vars

Model config is owned entirely by `common/llm.py`. Override via environment only:

| Var            | Default                     |
| -------------- | --------------------------- |
| `LLM_BASE_URL` | `http://localhost:1234/v1`  |
| `LLM_API_KEY`  | `lmstudio`                  |
| `LLM_MODEL`    | `local-model`               |

**Swap to cloud:** set those three to your provider (e.g. OpenAI:
`LLM_BASE_URL=https://api.openai.com/v1`, `LLM_API_KEY=sk-...`,
`LLM_MODEL=gpt-4o-mini`). Nothing in this package changes.
