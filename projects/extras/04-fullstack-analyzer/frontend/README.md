# Frontend — Review / Survey Analyzer

Minimal Next.js (App Router) UI. Posts a review to the FastAPI backend and renders
the structured LLM insight alongside the DistilBERT sentiment baseline.

## Run

```bash
cd 04-fullstack-analyzer/frontend
npm install          # not run during scaffolding
npm run dev          # http://localhost:3000
```

The backend base URL comes from `NEXT_PUBLIC_API_BASE` (default
`http://localhost:8000`). Start the backend first (see the package README).

## Files

- `app/page.tsx` — client page: textarea → `POST /analyze` (+ `POST /baseline`),
  renders the LLM-vs-DistilBERT comparison panel.
- `app/layout.tsx` — root layout.
- `next.config.mjs` — injects `NEXT_PUBLIC_API_BASE`.
