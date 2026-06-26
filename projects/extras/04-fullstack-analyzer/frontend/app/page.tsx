"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type ReviewInsight = {
  sentiment: "positive" | "neutral" | "negative";
  themes: string[];
  sizing_issue: boolean;
  churn_risk: "low" | "medium" | "high";
  summary: string;
};

type BaselineResult = { label: string; score: number };

export default function Home() {
  const [text, setText] = useState(
    "Runs two sizes small and the fabric pilled after one wash. Returning it."
  );
  const [insight, setInsight] = useState<ReviewInsight | null>(null);
  const [baseline, setBaseline] = useState<BaselineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    setLoading(true);
    setError(null);
    setBaseline(null);
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ review_text: text }),
      });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      setInsight((await res.json()) as ReviewInsight);

      // DistilBERT baseline (optional endpoint; ignored if backend lacks torch).
      const cmp = await fetch(`${API_BASE}/baseline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ review_text: text }),
      });
      if (cmp.ok) setBaseline((await cmp.json()) as BaselineResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "40px auto", padding: "0 16px" }}>
      <h1 style={{ fontFamily: "Georgia, serif" }}>Review / Survey Analyzer</h1>
      <p>Paste a customer review; the local LLM returns structured insight. A DistilBERT baseline is shown for comparison.</p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        style={{ width: "100%", padding: 12, fontSize: 16 }}
      />
      <button
        onClick={analyze}
        disabled={loading}
        style={{ marginTop: 12, padding: "10px 20px", background: "#C96442", color: "white", border: "none", borderRadius: 6, cursor: "pointer" }}
      >
        {loading ? "Analyzing…" : "Analyze"}
      </button>

      {error && <p style={{ color: "#b00" }}>Error: {error}</p>}

      {insight && (
        <section style={{ marginTop: 24, display: "grid", gap: 24, gridTemplateColumns: "1fr 1fr" }}>
          <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16 }}>
            <h2>LLM (structured)</h2>
            <p><strong>Sentiment:</strong> {insight.sentiment}</p>
            <p><strong>Churn risk:</strong> {insight.churn_risk}</p>
            <p><strong>Sizing issue:</strong> {insight.sizing_issue ? "yes" : "no"}</p>
            <p><strong>Themes:</strong> {insight.themes.join(", ")}</p>
            <p><strong>Summary:</strong> {insight.summary}</p>
          </div>
          <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16 }}>
            <h2>DistilBERT (baseline)</h2>
            {baseline ? (
              <>
                <p><strong>Label:</strong> {baseline.label}</p>
                <p><strong>Confidence:</strong> {(baseline.score * 100).toFixed(1)}%</p>
                <p style={{ color: "#666", fontSize: 14 }}>Sentiment only — no themes, no churn, no summary. That is the smallest-tool trade-off.</p>
              </>
            ) : (
              <p style={{ color: "#666" }}>Baseline unavailable (backend lacks transformers+torch, or /baseline not enabled).</p>
            )}
          </div>
        </section>
      )}
    </main>
  );
}
