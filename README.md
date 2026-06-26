# Local LLMs for Developers — Complete Education Package

A practical, vendor-neutral guide to **running and building with local LLMs**: from the core concepts (prompt / context / harness engineering) to serving models with **LM Studio**, coding with **VS Code agents** and **CLI agents** (Claude Code, opencode), and shipping **OpenAI-compatible full-stack apps** you can swap to any provider by changing two lines.

> Designed as a 1–2 hour training + a long-form article + an interactive map + a hands-on monorepo. Everything is anonymized and reusable by anyone.

---

## Contents

```
local-llm-course/
├── CHECKPOINT.md                 # resume/state file (read first if continuing in a new chat)
├── README.md                     # you are here
├── article/                      # the long-form ("Medium") article, one file per part
│   ├── 00-introduction.md
│   ├── part-1-concepts.md        # Prompt / Context / Harness — with academic references
│   ├── part-2-tools.md           # Tools + install + decision matrix
│   ├── part-3-serve-and-code.md  # Serving + coding workflows + model sizing
│   ├── part-4-projects.md        # Hands-on full-stack projects
│   └── references.md             # full bibliography (papers, articles, repos, datasets)
├── artifact/
│   └── index.html                # interactive overview map (host on GitHub Pages)
└── projects/                     # build specs for the hands-on monorepo
    ├── PRD.md
    ├── proposal.md
    ├── p1-review-analyzer.md
    ├── p3-feedback-rag.md
    └── backlog.md
```

## How the pieces fit together

1. **Read / publish the article** (`article/*.md`) — the full narrative with every term and reference.
2. **Host the interactive map** (`artifact/index.html`) — a hover/click mind-map that *navigates* the article and doubles as a spaced-repetition review tool. Each node links back to the relevant article section.
3. **Build the projects** (`projects/*.md`) — PRD-first specs you implement as a monorepo (with Claude Code and/or opencode + a local model).

The article and the artifact are cross-linked. The artifact uses a placeholder `{{MEDIUM_URL}}` for the published article base URL — find-and-replace it once after publishing.

## Publish the interactive map on GitHub Pages (free URL)

```bash
# from a repo that contains artifact/index.html
git add artifact/index.html && git commit -m "add overview map"
git push origin main
# GitHub → Settings → Pages → Source: "Deploy from a branch"
#   Branch: main   Folder: /artifact   (or move index.html to /docs and pick /docs)
# Your URL: https://<user>.github.io/<repo>/
```

For a project-page root, either put `index.html` at repo root, use the `/docs` folder option, or add a GitHub Actions Pages workflow. The file is fully self-contained (no build step, no external JS dependencies), so it works the moment Pages serves it.

## Author setup (for the live session)

- **Local:** macOS Apple Silicon (M4 Pro / 48 GB). Install LM Studio, pull a coding model, start the server. See `article/part-3-serve-and-code.md`.
- **Cloud heavy demo:** Google Colab Pro (H100 80 GB) — serve a larger model and tunnel the endpoint. (Notebook to be added in v2.)
- **Agent paths:** Claude Code (subscription, "best-practice" build) and opencode + LM Studio (fully open-source build).

## License & reuse

Content is anonymized and intended for free educational reuse. Verify model names/benchmarks against `projects` notes before presenting — the local-model landscape moves monthly.
