"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Citation = { id: string; snippet: string };
type Answer = {
  answer: string;
  citations: Citation[];
  confidence: "low" | "medium" | "high";
};

export default function Home() {
  const [question, setQuestion] = useState(
    "What do testers say about shrinkage on cotton items?"
  );
  const [result, setResult] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 4 }),
      });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      setResult((await res.json()) as Answer);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "40px auto", padding: "0 16px" }}>
      <h1 style={{ fontFamily: "Georgia, serif" }}>Product-Feedback RAG Assistant</h1>
      <p>Ask a question about products; the local LLM answers <strong>only</strong> from retrieved feedback and cites its sources.</p>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={3}
        style={{ width: "100%", padding: 12, fontSize: 16 }}
      />
      <button
        onClick={ask}
        disabled={loading}
        style={{ marginTop: 12, padding: "10px 20px", background: "#C96442", color: "white", border: "none", borderRadius: 6, cursor: "pointer" }}
      >
        {loading ? "Asking…" : "Ask"}
      </button>

      {error && <p style={{ color: "#b00" }}>Error: {error}</p>}

      {result && (
        <section style={{ marginTop: 24 }}>
          <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16 }}>
            <p><strong>Confidence:</strong> {result.confidence}</p>
            <p style={{ fontSize: 17 }}>{result.answer}</p>
          </div>
          <h2 style={{ marginTop: 24 }}>Cited sources ({result.citations.length})</h2>
          {result.citations.length === 0 ? (
            <p style={{ color: "#666" }}>No sources cited — the assistant declined to answer beyond the retrieved feedback.</p>
          ) : (
            result.citations.map((c) => (
              <details key={c.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: 10, marginBottom: 8 }}>
                <summary style={{ cursor: "pointer", fontWeight: 600 }}>{c.id}</summary>
                <p style={{ marginTop: 8 }}>{c.snippet}</p>
              </details>
            ))
          )}
        </section>
      )}
    </main>
  );
}
