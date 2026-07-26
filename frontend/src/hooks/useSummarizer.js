import { useState, useCallback } from "react";

const API_BASE = "/api";

/**
 * Encapsulates all backend interaction for the summarizer.
 *
 * Returns:
 *   result   — { transcription, summary } or null
 *   status   — "idle" | "transcribing" | "summarizing" | "done" | "error"
 *   error    — string or null
 *   run(file) — call with a File object to start the pipeline
 *   reset()  — clear everything back to idle
 */
export function useSummarizer() {
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);

  const run = useCallback(async (file) => {
    setResult(null);
    setError(null);
    setStatus("transcribing");

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Single call — backend handles both transcription and summarization.
      // We show "transcribing" then switch to "summarizing" after a short delay
      // so the user sees progress rather than a single frozen spinner.
      const transcribeTimer = setTimeout(() => setStatus("summarizing"), 4000);

      const res = await fetch(`${API_BASE}/transcribe-and-summarize`, {
        method: "POST",
        body: formData,
      });

      clearTimeout(transcribeTimer);

      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(detail.detail || "Unknown error from server.");
      }

      const data = await res.json();
      setResult(data);
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
