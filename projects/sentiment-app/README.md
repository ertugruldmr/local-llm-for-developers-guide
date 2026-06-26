---
title: Sentiment Analyzer
emoji: 🎯
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: "6.19.0"
app_file: app.py
pinned: false
---

# Sentiment Analyzer

Gradio app that classifies text sentiment using the **OpenAI SDK** against any
**OpenAI-compatible** endpoint (local **LM Studio** by default), with
**structured (JSON-schema) output** validated by Pydantic.

It works without a GPU: if the default endpoint is down, open **⚙️ Connection
settings** in the UI and point it at any working OpenAI-compatible endpoint
(another LM Studio, a tunnel, or a cloud provider). A wrong/unreachable provider
never crashes the app — it shows a clear notice and waits for a working one.

## Prerequisites
- Python >= 3.10
- LM Studio running with a chat model loaded, server on `localhost:1234`

## Setup

```bash
conda create -n sentiment python=3.11 -y
conda activate sentiment
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Opens `http://localhost:7860` and prints a temporary public `*.gradio.live`
link (sharing is on by default).

## Configuration (env vars)

| Variable             | Default                      | Purpose                              |
|----------------------|------------------------------|--------------------------------------|
| `LMSTUDIO_BASE_URL`  | `http://localhost:1234/v1`   | OpenAI-compatible endpoint           |
| `LMSTUDIO_MODEL`     | `qwen/qwen3.6-35b-a3b`       | Model id (see LM Studio)             |
| `LMSTUDIO_API_KEY`   | `lm-studio`                  | Ignored by LM Studio; real key for a cloud endpoint |
| `GRADIO_SHARE`       | `true`                       | Generate public share link (ignored on Spaces) |
| `GRADIO_SERVER_PORT` | `7860`                       | Local port                           |

See `.env.example` for a copy-paste template, including a block for pointing
at a remote endpoint.

### Connection settings (in the UI)

The env vars only set the **defaults**. At runtime, expand **⚙️ Connection
settings** to override **Base URL**, **Model**, and **API key** without
restarting — blank fields fall back to the env defaults. **Test connection**
lists the endpoint's available model ids so you can confirm the Model id. This
is the no-GPU path: when the local server isn't running, paste a working
endpoint here and analyze immediately.

## Notes

- **Public sharing** needs the one-time `frpc` binary at
  `~/.cache/huggingface/gradio/frpc/`. Gradio downloads it on first run; if your
  network blocks it, fetch it manually and `chmod +x`. On macOS clear quarantine
  with `xattr -dr com.apple.quarantine <binary>` if Gatekeeper blocks it.
- **Reasoning models** (e.g. Qwen3) emit the structured JSON into the
  `reasoning_content` channel and leave `content` empty under
  `response_format=json_schema`. `app.py` reads whichever field carries the
  payload — a plain `.parse()` would return nothing.

## Deploy to Hugging Face Spaces

The repo root is already a valid Gradio Space (the YAML header above is the
Space card). To deploy:

1. Create a new **Gradio** Space on Hugging Face.
2. Push `app.py`, `requirements.txt`, and this `README.md` to it.
3. A Space runs in the cloud and **cannot reach your laptop's `localhost`**.
   Point the app at a reachable endpoint via Space **secrets** (Settings →
   Variables and secrets):
   - `LMSTUDIO_BASE_URL` — a cloud OpenAI-compatible endpoint, or a public
     tunnel/Colab URL fronting your model (`https://…/v1`).
   - `LMSTUDIO_MODEL` — the model id that endpoint serves.
   - `LMSTUDIO_API_KEY` — the endpoint's real key (store as a secret, not a
     plain variable).
4. `GRADIO_SHARE` is irrelevant on Spaces — the platform serves the public URL,
   so leave it unset.

## Run tests

```bash
pip install pytest
PYTHONPATH=. python -m pytest tests -q
```

Tests run fully offline — they monkeypatch the OpenAI client and need no live
server.

## Structure

```
sentiment-app/
├── app.py            # Gradio app: client, schema, inference, UI
├── requirements.txt
├── .env.example      # env-var template (local + remote endpoint)
├── tests/            # offline tests (monkeypatched client, no server)
│   └── test_app.py
└── README.md
```
