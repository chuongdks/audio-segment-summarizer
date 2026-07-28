import { useState, useCallback } from "react";

const API_BASE = "/api";

/**
 * Encapsulates all backend interaction for the summarizer.
 *
 * Makes two sequential calls so status reflects what the backend is
 * actually doing rather than guessing with a timer:
 *   1. POST /transcribe   → status "transcribing" → returns segments
 *   2. POST /summarize    → status "summarizing"  → returns summary
 *
 * Returns:
 *   result   — { transcription, summary } or null
 *   status   — "idle" | "transcribing" | "summarizing" | "done" | "error"
 *   error    — string or null
 *   run(file) — call with a File object to start the pipeline
 *   reset()   — clear everything back to idle
 */
export function useSummarizer() {
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error,  setError]  = useState(null);

  const run = useCallback(async (file) => {
    setResult(null);
    setError(null);

    try {
      // ── Step 1: Transcribe ──────────────────────────────────────────────────
      setStatus("transcribing");

      const formData = new FormData();
      formData.append("file", file);

      const transcribeRes = await fetch(`${API_BASE}/transcribe`, {
        method: "POST",
        body: formData,
      });

      if (!transcribeRes.ok) {
        const detail = await transcribeRes.json().catch(() => ({ detail: transcribeRes.statusText }));
        throw new Error(detail.detail || "Transcription failed.");
      }

      const transcription = await transcribeRes.json();

      // ── Step 2: Summarize ───────────────────────────────────────────────────
      setStatus("summarizing");

      const summarizeRes = await fetch(`${API_BASE}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(transcription.segments),
      });

      if (!summarizeRes.ok) {
        const detail = await summarizeRes.json().catch(() => ({ detail: summarizeRes.statusText }));
        throw new Error(detail.detail || "Summarization failed.");
      }

      const summary = await summarizeRes.json();

      setResult({ transcription, summary });
      setStatus("done");

    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setStatus("idle");
    setError(null);
  }, []);

  return { result, status, error, run, reset };
}