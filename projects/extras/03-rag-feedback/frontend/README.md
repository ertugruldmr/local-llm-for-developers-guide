# Frontend — Product-Feedback RAG Assistant

Minimal Next.js (App Router) UI. Posts a question to the FastAPI backend and
renders the grounded answer with expandable cited sources.

## Run

```bash
cd 03-rag-feedback/frontend
npm install          # not run during scaffolding
npm run dev          # http://localhost:3000
```

The backend base URL comes from `NEXT_PUBLIC_API_BASE` (default
`http://localhost:8000`). Start the backend first (see the package README).

## Files

- `app/page.tsx` — client page: question box → `POST /ask`, renders the answer,
  confidence, and expandable citations.
- `app/layout.tsx` — root layout.
- `next.config.mjs` — injects `NEXT_PUBLIC_API_BASE`.
