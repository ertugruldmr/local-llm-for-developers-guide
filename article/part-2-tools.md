# Part 2 — The Tools

*Part 2 of 4 · [← Part 1](part-1-concepts.md) · [Part 3 →](part-3-serve-and-code.md)*

Part 1 was vocabulary. This part is the install chapter: get each tool on disk, know what it is and when to pick it, and hit the gotchas before they cost you an afternoon. Binding and serving config — provider blocks, base URLs, model IDs — lives in [Part 3](part-3-serve-and-code.md); here we install and orient.

The tools sort into four jobs:

- **The engine** runs and serves the model — **LM Studio** (with Ollama and vLLM named in passing).
- **Editor agents** live in VS Code — **Roo Code**, **Kilo Code**.
- **CLI harnesses** live in the terminal — **Claude Code**, **opencode**, **Hermes Agent**.
- **Reference repos** sharpen the agents — **ECC**, **claude-code-best-practice**.

Install order matters: stand up LM Studio first, because every other tool points at the endpoint it exposes.

---

## 2.1 · LM Studio — the engine

LM Studio is a desktop app (macOS / Windows / Linux) for discovering, downloading, and running local models through a GUI, and — the part that matters here — serving them behind an OpenAI-compatible (and now Anthropic-compatible) HTTP API. Install it first.

**1. Download.** Grab the installer for your platform from [lmstudio.ai](https://lmstudio.ai) [R-025].

**2. Download a model.** Open the **Search** (magnifying-glass) tab and pull a coding or general model from the Qwen or DeepSeek families — both ship strong [GGUF](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md) [R-053] builds (or [MLX](https://github.com/ml-explore/mlx) [R-052] on Apple Silicon). Pick a quantization that fits your VRAM/RAM; a 4-bit (`Q4`) build or higher is the usual starting point ([download-model docs](https://lmstudio.ai/docs/app/basics/download-model)) [R-067]. Which exact model to run on which hardware lives in [`model-table.md`](../model-table.md) — don't pick by reputation, pick by what fits.

**3. CRITICAL — expand the context window.** Open the **Local Server** tab and, in the model load / Hardware settings, raise the **Context Length** from its low default to at least **8192**, or **16384+** for agentic work. This is the single most common setup failure: coding assistants pack the whole workspace into context, and a too-small window makes the server reject requests with a token-overflow error. Set it before you wire up any harness.

**4. Start the server.** Select the model in the top dropdown and click **Start Server**. It defaults to `http://localhost:1234`, exposing `/v1/chat/completions`, `/completions`, `/embeddings`, and `/models` ([server docs](https://lmstudio.ai/docs/developer/core/server)) [R-025], plus an Anthropic-compatible `/v1/messages` for Claude Code ([LM Studio + Claude Code](https://lmstudio.ai/blog/claudecode)). Confirm with `curl http://localhost:1234/v1/models`.

Roo/Kilo Code, opencode, Claude Code, and your own apps all point at that one URL. Provider-by-provider wiring is in [Part 3](part-3-serve-and-code.md).

> **Security note, stated plainly:** the LM Studio server has **no authentication**. Keep it on `127.0.0.1` for local use; only bind `0.0.0.0` behind a firewall you control.

---

## 2.2 · Roo Code & Kilo Code — editor agents

Pick these when you live in VS Code and want the agent loop behind a GUI rather than a terminal. Both are marketplace extensions that drop an agentic assistant into the editor — code/architect/ask modes, multi-file edits, diff review. Kilo Code shares lineage with Roo/Cline, so demoing one teaches you the other; the setup is nearly identical.

Install: open the VS Code Extensions marketplace, search **Roo Code** (and/or **Kilo Code**), install, and open the sidebar panel. Both speak OpenAI-compatible providers, so they bind to the LM Studio endpoint directly — the actual provider/base-URL/model-ID config is in [Part 3](part-3-serve-and-code.md). Add a repo `AGENTS.md` [R-034] so the agent respects your conventions.

When to reach for them: you want the agent inline with the editor, with the diff right next to the code, and you'd rather click than type CLI flags. A typical turn — "create a paginated product-list component and a matching API hook" → review the diff → accept or steer.

> **Kilo Code config path:** if you configure via file rather than the UI, pre-create the directory so a global install doesn't leave it root-owned: `sudo mkdir -p ~/.config/kilo && sudo chown -R $(whoami) ~/.config/kilo`. Same ownership trap as opencode (§2.4).

---

## 2.3 · Claude Code — the CLI harness (subscription path)

Reach for Claude Code when you want the deepest, best-supported tooling around prompts-as-files. It's a terminal coding agent with a full harness — tool loop, plan/build, skills, hooks, slash commands, subagents, MCP — and the most mature ecosystem of the bunch.

Install via the native installer or npm:

```bash
curl -fsSL https://claude.ai/install.sh | bash   # macOS / Linux
#   Windows PowerShell:  irm https://claude.ai/install.ps1 | iex
#   or Homebrew:         brew install --cask claude-code
claude            # launch in a project
```

Add an `AGENTS.md` / `CLAUDE.md` [R-034][R-035] to teach it your repo. The recommended path is the **subscription** one — it authenticates against Anthropic's hosted models for best raw capability. Claude Code can also run fully local against LM Studio's Anthropic-compatible `/v1/messages` via environment variables; that wiring (base URL, token, model tiers) is in [Part 3](part-3-serve-and-code.md) [R-028]. Either way, give it a model with **≥64K context** — the harness is context-heavy.

Two repos turn a basic setup into a disciplined one:

- **[`affaan-m/ECC` (Everything Claude Code)](https://github.com/affaan-m/ECC)** [R-032] — hundreds of skills, 60+ subagents, slash commands, hooks, rules, and MCP configs, portable across Claude Code / Codex / opencode / Cursor. The advanced end-state of prompts-as-files.
- **[`shanraisshan/claude-code-best-practice`](https://github.com/shanraisshan/claude-code-best-practice)** [R-033] — "from vibe coding to agentic engineering," tighter and more didactic. Start here.

A representative run, given a decent `AGENTS.md`: "add unit tests for the orders service and fix anything red" → Claude Code plans, edits across files, runs tests, iterates.

---

## 2.4 · opencode — the fully open-source CLI harness

opencode is the answer when "no subscription, no cloud" is a hard requirement. It's an open-source terminal coding agent that speaks to 75+ providers including local Ollama and LM Studio, with LSP integration, plan/build modes, and session management ([opencode docs](https://opencode.ai/docs)) [R-026] — the same agent-loop power as Claude Code, running entirely on your local model.

Install globally with npm:

```bash
npm install -g @opencode/cli
```

> **Folder-permission gotcha — read this before you `sudo`.** Installing a global CLI under `sudo` can leave its app folders owned by `root`, after which normal runs fail with `PermissionDenied: FileSystem.open`. **Never run `sudo opencode .`.** If you hit the error, repair ownership once:
> ```bash
> sudo chown -R $(whoami) ~/.local/share/opencode ~/.config/opencode
> ```

Config lives at `~/.config/opencode/opencode.json` (macOS/Linux) or `$HOME\.config\opencode\opencode.json` (Windows); opencode also reads `JSONC` and merges a project-level `opencode.json` over the global one ([config docs](https://opencode.ai/docs/config)) [R-068]. The provider block that points it at LM Studio — `@ai-sdk/openai-compatible`, the `:1234/v1` base URL, the model ID — is in [Part 3](part-3-serve-and-code.md). Launch with `opencode` (or `opencode .`) in a repo; it reads the same `AGENTS.md` Claude Code does.

When to reach for it: you need to prove the whole workflow runs with zero cloud dependency — for example, "read this repo, propose a refactor of the data layer, apply it" on a local 24B model.

> **Related:** **Crush** (Charm) is another single-binary, BYOK terminal agent, with mid-session model switching across providers and any OpenAI/Anthropic-compatible endpoint ([Crush](https://github.com/charmbracelet/crush)) [R-030] — an alternative TUI worth knowing.

---

## 2.5 · Hermes Agent — persistent memory and a learning loop

Hermes is the one to study when you want to see where agents are heading. It's an open-source autonomous agent from Nous Research (released 2026) built around a learning loop — it creates skills from experience and persists them — plus memory that survives across sessions, asynchronous subagents, and operation over CLI, Telegram, Discord, Slack, WhatsApp, and email, all able to run locally and private ([hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/), [GitHub](https://github.com/nousresearch/hermes-agent)) [R-031].

It's the concrete instance of Part 1's frontier ideas — **C11 continuous learning** and **B5 long-term memory**.

One honest caveat: treat "self-improving" as a design goal, not a benchmarked guarantee. A technical audience will push on it, and rightly so.

---

## 2.6 · Reference repos at a glance

| Repo | What it gives you | Use it as |
|---|---|---|
| [ECC (Everything Claude Code)](https://github.com/affaan-m/ECC) [R-032] | Skills, subagents, hooks, commands, rules, MCP configs; cross-tool | The "power user" library |
| [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) [R-033] | Curated agentic-engineering practices | The on-ramp |

Pull ideas (an `AGENTS.md` structure, a useful `SKILL.md`, a slash command) into your own repo rather than adopting everything at once.

---

## 2.7 · Decision matrix — Ollama vs LM Studio vs Unsloth

These three names come up together and get mistaken for competitors. They solve different problems, and only two of them actually overlap.

| Dimension | **LM Studio** | **Ollama** | **Unsloth** |
|---|---|---|---|
| Primary job | Run & serve models with a **GUI** | Run & serve models from the **CLI** | **Fine-tune / train** models efficiently |
| Interface | Desktop app + local server | Terminal + local server | Python library / notebooks |
| OpenAI-compatible server | Yes | Yes | N/A (not its job) |
| Best for | Non-CLI users, quick demos, model discovery | Scripting, headless servers, automation | Teams customizing a model on their own data |
| Learning curve | Lowest | Low–medium | Medium–high |
| In this course | **Primary engine** | Named only | Named only |

**One-line recommendations:**
- **You want to develop apps / demo quickly and prefer a GUI →** use **LM Studio**.
- **You want to script, automate, or run headless on a server →** use **Ollama**.
- **You want to fine-tune a model on your own data (cheaply, on limited GPU) →** use **Unsloth** — it specializes in efficient fine-tuning built on techniques like *LoRA* ([Hu et al., 2021](https://arxiv.org/abs/2106.09685)) [R-021] and *QLoRA* ([Dettmers et al., 2023](https://arxiv.org/abs/2305.14314)) [R-022]. Then *serve* the result with LM Studio or Ollama. (**vLLM** belongs here too as the name to know for high-throughput production serving.)

The key insight: **Unsloth is upstream of the other two.** You fine-tune *with* Unsloth, then *serve* with LM Studio or Ollama. They're stages of a pipeline, not rivals.

---

## 2.8 · Section summary

- **LM Studio** is the engine; install it first because everything else plugs into its endpoint — and **expand the context window to 8192–16384+** before wiring any harness.
- **Roo / Kilo Code** bring the agent into VS Code; **Claude Code** (`curl … install.sh` / npm) and **opencode** (`npm install -g @opencode/cli`) bring it to the terminal — Claude Code for the best-supported subscription path, opencode for the fully open-source path on a local model. Never `sudo opencode`.
- **Hermes Agent** previews the self-improving, persistent-memory future (a design goal, not a guarantee).
- **ECC** and **claude-code-best-practice** are the libraries that turn a basic agent into a disciplined one.
- For the *Ollama vs LM Studio vs Unsloth* question: **serve with LM Studio or Ollama, fine-tune with Unsloth.**

Everything here is install + orientation. Next we wire these tools to the engine — provider blocks, base URLs, model IDs — and code against it.

---

*Next: [Part 3 — Serve & Code](part-3-serve-and-code.md) · [References](references.md) · [Interactive map](../artifact/index.html)*
