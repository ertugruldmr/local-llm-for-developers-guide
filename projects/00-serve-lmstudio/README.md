# 00 · Serve a model with LM Studio (macOS / Apple Silicon)

Stand up a local OpenAI- and Anthropic-compatible server, verify it, wire it to
the config contract every project package uses, and pick which model to load.
This package is **scaffolded for the author to run on hardware** — sections
marked `TODO(author)` need a real screenshot or pasted output before publishing.

Pairs with the article: [Part 3 — Serve a Model and Code With It](../../article/part-3-serve-and-code.md).
Model standings live in [`model-table.md`](../../model-table.md) — never hardcode them here.

---

## 1 · Install LM Studio on macOS

1. Download LM Studio for **Apple Silicon** from <https://lmstudio.ai> and drag it to `/Applications`.
2. Open it. Go to the **Discover** (search) tab and pull one model:
   - **MLX build** if available — Apple's MLX runtime is the fastest on M-series.
   - Otherwise a **GGUF** `Q4_K_M` build (the default daily driver).
   - Size it to your RAM. Run `python3 recommend_models.py` (this folder) for a
     pick sized to this machine; it reads `model-table.md`.
3. Wait for the download, then open the **Chat** tab and **Load** the model. Confirm it answers a prompt.
4. Open the **Developer** tab (server icon), select the loaded model, set the
   port to **1234**, and press **Start Server**. Default endpoint:

   ```
   http://localhost:1234/v1
   ```

> TODO(author): screenshot of the Developer tab with the model loaded and the
> server running (status = Running, port 1234). Note the exact model id shown.

---

## 2 · Verify the server

List loaded models (grab the real model id from `data[].id`):

```bash
curl http://localhost:1234/v1/models
```

Expected shape:

```json
{
  "object": "list",
  "data": [
    { "id": "qwen3-coder-30b", "object": "model", "owned_by": "organization_owner" }
  ]
}
```

OpenAI-compatible chat completion (swap `model` for the id above):

```bash
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [{"role": "user", "content": "Say hi in one word."}]
  }'
```

Expected shape:

```json
{
  "choices": [
    { "index": 0, "message": { "role": "assistant", "content": "Hi" }, "finish_reason": "stop" }
  ],
  "model": "local-model",
  "usage": { "prompt_tokens": 12, "completion_tokens": 1, "total_tokens": 13 }
}
```

**Anthropic-compatible route.** LM Studio also serves `/v1/messages` (Messages
API shape) at `http://localhost:1234` — this is what Claude Code talks to via
`ANTHROPIC_BASE_URL` (see §4, path 2). Same loaded model, different envelope.

> TODO(author): paste the real `curl /v1/models` and `/v1/chat/completions`
> output from your run here, with the live model id.

---

## 3 · Wire it to the config contract

Every project package reads model config from **one** place — `common/llm.py` —
and nothing else touches it. It consumes three env vars:

```
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lmstudio          # ignored locally; any non-empty string
LLM_MODEL=local-model         # must match an id from GET /v1/models
```

Copy `.env.example` to `.env` and adjust. `.env` is gitignored — never commit a real key.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lmstudio")
resp = client.chat.completions.create(
    model="local-model",
    messages=[{"role": "user", "content": "Say hi in one word."}],
)
print(resp.choices[0].message.content)
```

**Swap to a cloud provider by changing only those three vars — nothing else.**
Point `LLM_BASE_URL` at OpenAI, Azure OpenAI, or OpenRouter, set the matching
`LLM_API_KEY` and `LLM_MODEL`, and the identical SDK code runs unchanged
(`.env.example` has ready-to-uncomment blocks). That is the whole portability
trick: the OpenAI wire format is the lingua franca, LM Studio speaks it locally.

---

## 4 · Three ways to code against it

Three editor/CLI paths, from most-capable to fully open. Pick by what you're optimizing for.

### Path 1 — Claude Code (subscription) · best-capability

Drive Claude Code against frontier Anthropic models. Best for hard, high-stakes
work where capability beats cost/privacy. This is the reference for *how to work
with an agentic coding tool* — repo `AGENTS.md`, skills, plan/build steering.
Best-practice references: **ECC — Everything Claude Code**
(<https://github.com/affaan-m/ECC>) and **claude-code-best-practice**
(<https://github.com/shanraisshan/claude-code-best-practice>).

### Path 2 — Claude Code + LM Studio · same harness, local engine

Keep the Claude Code workflow but point it at the local server's
Anthropic-compatible route:

```bash
export ANTHROPIC_BASE_URL=http://localhost:1234
export ANTHROPIC_AUTH_TOKEN=lmstudio
claude
```

Or per-workspace in VS Code `settings.json`:

```jsonc
"claudeCode.environmentVariables": [
  { "name": "ANTHROPIC_BASE_URL", "value": "http://localhost:1234" },
  { "name": "ANTHROPIC_AUTH_TOKEN", "value": "lmstudio" }
]
```

Same harness and conventions, no data leaving the machine. Capability is capped
by the local model.

> TODO(author): screenshot of Claude Code running a task against the local
> endpoint (note the model id in the status line).

### Path 3 — opencode + LM Studio · fully open-source (emphasized)

The end-to-end open path: **opencode** (open CLI harness) + **LM Studio** (open
engine) + an open-weight model. No subscription, nothing leaves the machine.
Point opencode at the local OpenAI-compatible endpoint
(`http://localhost:1234/v1`, model id from `GET /v1/models`) and run a full
agentic task:

```
> read the repo, propose a refactor of the data layer, then apply it with tests
```

You get the plan/build split, session persistence, and `AGENTS.md` honored —
the same agentic loop as Path 1, fully local. Use this for privacy, cost,
offline, and learning. Iterate here for the cheap 90%; switch the same toolchain
to the cloud for the hard 10%.

> TODO(author): paste a short opencode session transcript against the local
> model (the agentic plan→build→apply loop).

---

## 5 · Pick a model for this machine

```bash
python3 recommend_models.py                 # all tasks
python3 recommend_models.py --task coding    # coding | turkish | rag
python3 recommend_models.py --ram-gb 16      # size for a different box
```

It detects the chip + unified RAM (macOS `sysctl`, with a cross-platform
fallback) and reads `../../model-table.md` for candidate models per RAM tier and
task. `model-table.md` is the single source of truth — when it's still a
scaffold (`_TBD_` picks), the script reports that and still ranks the RAM tiers
your machine qualifies for.

> TODO(author): once `model-table.md` is filled during phase-3-v4, paste the
> real `recommend_models.py` output for your M4 Pro here.
