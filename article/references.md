# References

*All sources for the guide — academic papers, documentation, articles, repos, datasets, and tools. Verify model names/benchmarks before presenting; the landscape moves monthly.*

## Foundational papers (architecture & instruction-following)
- [R-001] Vaswani et al., 2017 — *Attention Is All You Need* — https://arxiv.org/abs/1706.03762
- [R-002] Ouyang et al., 2022 — *Training language models to follow instructions with human feedback (InstructGPT)* — https://arxiv.org/abs/2203.02155
- [R-003] Brown et al., 2020 — *Language Models are Few-Shot Learners (GPT-3)* — https://arxiv.org/abs/2005.14165
- [R-047] Kaplan et al., 2020 — *Scaling Laws for Neural Language Models* — https://arxiv.org/abs/2001.08361
- [R-048] Hoffmann et al., 2022 — *Training Compute-Optimal Large Language Models (Chinchilla)* — https://arxiv.org/abs/2203.15556
- [R-049] Touvron et al., 2023 — *LLaMA: Open and Efficient Foundation Language Models* — https://arxiv.org/abs/2302.13971

## Prompt engineering
- [R-004] Wei et al., 2022 — *Chain-of-Thought Prompting Elicits Reasoning in LLMs* — https://arxiv.org/abs/2201.11903
- [R-005] Zhou et al., 2022 — *Least-to-Most Prompting* — https://arxiv.org/abs/2205.10625
- [R-006] Yao et al., 2023 — *Tree of Thoughts* — https://arxiv.org/abs/2305.10601

## Context engineering & RAG
- [R-007] Lewis et al., 2020 — *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* — https://arxiv.org/abs/2005.11401
- [R-008] Karpukhin et al., 2020 — *Dense Passage Retrieval (DPR)* — https://arxiv.org/abs/2004.04906
- [R-009] Liu et al., 2023 — *Lost in the Middle: How Language Models Use Long Contexts* — https://arxiv.org/abs/2307.03172
- [R-010] Anthropic — *Prompt caching* (docs) — https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- [R-011] Awesome Context Engineering (survey/list) — https://github.com/Meirtz/Awesome-Context-Engineering

## Agents & harness
- [R-012] Yao et al., 2022 — *ReAct: Synergizing Reasoning and Acting in Language Models* — https://arxiv.org/abs/2210.03629
- [R-013] Schick et al., 2023 — *Toolformer: Language Models Can Teach Themselves to Use Tools* — https://arxiv.org/abs/2302.04761
- [R-014] Shinn et al., 2023 — *Reflexion: Language Agents with Verbal Reinforcement Learning* — https://arxiv.org/abs/2303.11366
- [R-015] Madaan et al., 2023 — *Self-Refine: Iterative Refinement with Self-Feedback* — https://arxiv.org/abs/2303.17651
- [R-016] Model Context Protocol (spec) — https://modelcontextprotocol.io
- [R-017] What Is an Agent Harness — https://www.firecrawl.dev/blog/what-is-an-agent-harness
- [R-018] Awesome Harness Engineering — https://github.com/ai-boost/awesome-harness-engineering
- [R-044] Packer et al., 2023 — *MemGPT: Towards LLMs as Operating Systems* — https://arxiv.org/abs/2310.08560
- [R-045] Wu et al., 2023 — *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation* — https://arxiv.org/abs/2308.08155
- [R-046] Wang et al., 2023 — *Voyager: An Open-Ended Embodied Agent with Large Language Models* — https://arxiv.org/abs/2305.16291

## Quantization & efficient training
- [R-019] Frantar et al., 2022 — *GPTQ* — https://arxiv.org/abs/2210.17323
- [R-020] Lin et al., 2023 — *AWQ* — https://arxiv.org/abs/2306.00978
- [R-021] Hu et al., 2021 — *LoRA: Low-Rank Adaptation* — https://arxiv.org/abs/2106.09685
- [R-022] Dettmers et al., 2023 — *QLoRA: Efficient Finetuning of Quantized LLMs* — https://arxiv.org/abs/2305.14314
- [R-023] Sanh et al., 2019 — *DistilBERT* — https://arxiv.org/abs/1910.01108
- [R-024] LLM quantization & VRAM guide — https://llmhardware.io/guides/llm-quantization-guide

## Tools & docs
- [R-025] LM Studio — https://lmstudio.ai · server docs https://lmstudio.ai/docs/developer/core/server · OpenAI-compat https://lmstudio.ai/docs/developer/openai-compat · Claude Code integration https://lmstudio.ai/blog/claudecode
- [R-026] opencode — https://opencode.ai/docs/
- [R-027] Claude Code (skills docs) — https://code.claude.com/docs/en/skills
- [R-028] Claude Code + local LLM (ANTHROPIC_BASE_URL) — https://renezander.com/guides/claude-code-local-llm-anthropic-base-url/
- [R-029] Roo Code + LM Studio — https://docs.roocode.com/providers/lmstudio
- [R-030] Crush (Charm) — https://github.com/charmbracelet/crush
- [R-031] Hermes Agent — https://hermes-agent.nousresearch.com/ · repo https://github.com/nousresearch/hermes-agent · async subagents https://www.marktechpost.com/2026/06/16/hermes-agent-adds-asynchronous-subagents-so-delegated-work-no-longer-blocks-the-parent-chat/
- [R-050] Kwon et al., 2023 — *Efficient Memory Management for LLM Serving with PagedAttention (vLLM)* — https://arxiv.org/abs/2309.06180 · docs https://docs.vllm.ai/
- [R-051] Chroma (vector database) — docs — https://docs.trychroma.com/docs/overview/introduction
- [R-052] Apple MLX — array framework for Apple silicon — https://github.com/ml-explore/mlx · docs https://ml-explore.github.io/mlx/
- [R-053] GGUF format specification (ggml) — https://github.com/ggml-org/ggml/blob/master/docs/gguf.md

## Reference repos (agentic best practice)
- [R-032] ECC — Everything Claude Code — https://github.com/affaan-m/ECC
- [R-033] claude-code-best-practice — https://github.com/shanraisshan/claude-code-best-practice

## Standards (prompts-as-files)
- [R-034] AGENTS.md guide — https://www.augmentcode.com/guides/how-to-build-agents-md
- [R-035] SKILL.md vs CLAUDE.md vs AGENTS.md — https://www.termdock.com/blog/skill-md-vs-claude-md-vs-agents-md

## Leaderboards & model landscape
- [R-036] LM Arena — Code leaderboard — https://lmarena.ai/leaderboard/code
- [R-037] LM Arena — WebDev (open-source filter) — https://arena.ai/leaderboard/code/webdev?license=open-source
- [R-038] Best local coding LLMs (2026) — https://www.promptquorum.com/local-llms/best-local-llms-for-coding
- [R-054] Qwen3 Technical Report (Qwen Team, 2025) — https://arxiv.org/abs/2505.09388 · HF org https://huggingface.co/Qwen
- [R-055] Devstral (Mistral coding model) — HF model card — https://huggingface.co/mistralai/Devstral-Small-2507
- [R-056] GLM-4.5 Technical Report (Zhipu / Z.ai, 2025) — https://arxiv.org/abs/2508.06471 · HF org https://huggingface.co/zai-org

## Tool & provider docs (Part 1–3 inline)
- [R-057] LM Studio — Structured Output — https://lmstudio.ai/docs/developer/openai-compat/structured-output
- [R-058] opencode — Rules (AGENTS.md) — https://opencode.ai/docs/rules
- [R-059] Claude Code — Memory (CLAUDE.md + auto memory) — https://code.claude.com/docs/en/memory
- [R-060] opencode — Skills (SKILL.md) — https://opencode.ai/docs/skills
- [R-061] LM Studio — Per-model load settings (context length) — https://lmstudio.ai/docs/app/advanced/per-model
- [R-062] opencode — Custom Tools — https://opencode.ai/docs/custom-tools
- [R-063] Claude Code — MCP — https://code.claude.com/docs/en/mcp
- [R-064] opencode — MCP servers — https://opencode.ai/docs/mcp-servers
- [R-065] Claude Code — Subagents — https://code.claude.com/docs/en/sub-agents
- [R-066] opencode — Agents — https://opencode.ai/docs/agents
- [R-067] LM Studio — Download a model — https://lmstudio.ai/docs/app/basics/download-model
- [R-068] opencode — Config — https://opencode.ai/docs/config
- [R-069] LM Studio — Anthropic-compatible endpoints — https://lmstudio.ai/docs/developer/anthropic-compat
- [R-070] LM Studio — Messages (POST /v1/messages) — https://lmstudio.ai/docs/developer/anthropic-compat/messages
- [R-071] LM Studio — Use Claude Code with LM Studio — https://lmstudio.ai/docs/integrations/claude-code
- [R-072] LM Studio — lms server start (CLI serve) — https://lmstudio.ai/docs/cli/serve/server-start
- [R-073] DeepSeek-V4 (Pro 1.6T / Flash 284B, MoE, MIT, Apr 2026) — https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash

## Datasets
- [R-039] Women's E-Commerce Clothing Reviews (Kaggle, anonymized) — https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews
- [R-040] Turkish sentiment dataset — https://huggingface.co/datasets/winvoker/turkish-sentiment-analysis-dataset
- [R-041] Turkish product reviews — https://huggingface.co/datasets/fthbrmnby/turkish_product_reviews

## Lightweight models
- [R-042] DistilBERT multilingual sentiment (student) — https://huggingface.co/lxyuan/distilbert-base-multilingual-cased-sentiments-student
- multilingual-sentiment-analysis — https://huggingface.co/tabularisai/multilingual-sentiment-analysis
- [R-043] Transformers.js — https://huggingface.co/docs/transformers.js/index

## Author artifacts (fill in after publishing)
- GitHub repo: `https://github.com/ertugruldmr/local-llm-for-developers-guide`
- Interactive overview map (GitHub Pages): `https://ertugruldmr.github.io/local-llm-for-developers-guide/`
- Published article base URL: `{{MEDIUM_URL}}`
