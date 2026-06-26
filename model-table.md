# model-table.md — authoritative model standings

> **Single source of truth for model names, sizes, and recommendations.** The local-model landscape
> moves monthly — no other file (article, artifact, project README) may hardcode model standings;
> they link here instead (CLAUDE.md guardrail #4).
>
> Status: **refreshed June 2026** from current model cards + leaderboards `[R-036]` `[R-037]` `[R-038]`
> and the author's own runs on M4 Pro 48GB + Colab H100. These are **practical picks, not benchmarked
> guarantees** — the landscape moves monthly, so re-verify the names/sizes/quants before any presentation.
> Newest open-weight frontier as of this refresh: **DeepSeek-V4** (deepseek-ai, MIT, Apr 2026) — a two-tier
> release: **V4-Pro** (1.6T MoE / ~49B active / 1M context) and **V4-Flash** (284B / 13B active). Full sizing
> landscape (open + closed, with per-GPU counts) lives in the artifact's **Hardware** tab.

## How to read this
- **VRAM ≈ params × bytes-per-param + KV-cache.** Rule of thumb: ~2 GB/B at FP16, ~0.5 GB/B at 4-bit `[R-024]`.
- Quant labels: `Q4_K_M` (≈0.5 GB/B, default daily driver), `Q5_K_M`, `Q8` (≈1 GB/B), `FP16` (≈2 GB/B).
- For MoE models (e.g. GLM-4.5-Air, Qwen3-30B-A3B) footprint tracks **total** params on disk/VRAM, but
  only the **active** params are computed per token — so they run fast for their size but still need RAM for the whole weight set.

## Recommendation by hardware (filled 2026-06-26)
| Unified RAM / VRAM | Practical pick | Quant | Good for |
|--------------------|----------------|-------|----------|
| 8 GB  | Qwen3-4B / Gemma 3 4B | Q4_K_M | light coding / chat, multilingual (~2.5 GB weights) |
| 16 GB | Qwen3-8B | Q4_K_M | coding + general use (~5 GB weights, room for KV-cache) |
| 48 GB (author Mac) | Qwen3.6-35B-A3B | Q4_K_M | the repo's `sentiment-app` model — 35B MoE / 3B active, fast for its size, structured output (~18–20 GB; room for context). For dense agentic coding swap to Devstral-Small-2507 (24B) |
| 80 GB (Colab H100) | Qwen3-32B | FP16 | heavy reasoning / serving (~64 GB); for agentic MoE use GLM-4.5-Air (106B-A12B) at Q4 (~55–60 GB). DeepSeek-V4-Flash (284B) needs heavier quant or ~2×48 GB |

## Recommendation by task (filled 2026-06-26; drives recommend_models.py)
| Task | Pick | Notes |
|------|------|-------|
| Coding (agentic) | Devstral-Small-2507 (24B) or Qwen3-Coder | purpose-built agentic coders, 128K+ context, strong tool-calling for their size `[R-055]` `[R-038]`; scale up to GLM-4.5-Air or DeepSeek-V4-Flash for harder agent loops `[R-056]` |
| Turkish language | Qwen3.6-35B-A3B (or Qwen3-8B) | English code leaderboards don't cover Turkish — Qwen3/Qwen3.6 train on 119 languages incl. Turkish `[R-054]`; verify on a Turkish eval before trusting it |
| RAG / embeddings | Embed: Qwen3-Embedding (0.6B / 4B) or BGE-M3 · Gen: Qwen3-8B | Qwen3-Embedding-8B topped MTEB-multilingual (Jun 2025); BGE-M3 is the multilingual hybrid-search default; pair with a small generator |
| Structured output | Qwen3.6-35B-A3B (or Qwen3-8B) | JSON-schema/function-calling reliability matters more than raw size — the `sentiment-app` runs this with `response_format=json_schema`; validate with Pydantic and retry on schema failure. Note reasoning models may emit JSON on the `reasoning_content` channel |

## Sources
Qwen3 report `[R-054]`, Devstral card `[R-055]`, GLM-4.5 report `[R-056]`; leaderboards `[R-036]` `[R-037]`,
"best local coding LLMs" `[R-038]`, VRAM/quant guide `[R-024]`.
Capture each as a dated `raw/` entry when relied on so the table stays traceable.
