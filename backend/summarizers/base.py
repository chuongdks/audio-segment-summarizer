"""
Shared base class for all summarizer styles.

Subclasses only need to implement:
  - build_prompt(segments) -> str
  - parse_result(data, seg_index) -> MeetingSummary

The Ollama call and JSON parsing are handled here.
"""
import json
from abc import ABC, abstractmethod

import httpx

from config import get_config
from models import TranscriptSegment, MeetingSummary


class BaseSummarizer(ABC):

    # ── Shared: Ollama call ───────────────────────────────────────────────────

    def _call_ollama(self, prompt: str) -> str:
        cfg = get_config()
        payload = {
            "model": cfg.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 4096,
            },
        }
        timeout = httpx.Timeout(
            connect=10.0,
            read=cfg.ollama_timeout,
            write=30.0,
            pool=5.0,
        )
        try:
            response = httpx.post(
                f"{cfg.ollama_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Could not reach Ollama at {cfg.ollama_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ollama timed out after {cfg.ollama_timeout}s. "
                "Try a smaller model or increase OLLAMA_TIMEOUT in settings."
            )
        return response.json()["response"]

    # ── Shared: JSON extraction ───────────────────────────────────────────────

    def _parse_json(self, raw: str) -> dict:
        """Strip markdown fences and extract the outermost JSON object."""
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```", 2)[-1]
            clean = clean.rsplit("```", 1)[0]
        start = clean.find("{")
        end   = clean.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object found in model response:\n{raw[:500]}")
        return json.loads(clean[start : end + 1])

    # ── Shared: segment index ─────────────────────────────────────────────────

    def _seg_index(self, segments: list[TranscriptSegment]) -> dict[int, float]:
        return {seg.id: seg.start for seg in segments}

    def _resolve(self, seg_index: dict, ref_seg) -> float:
        try:
            return seg_index.get(int(ref_seg), 0.0)
        except (TypeError, ValueError):
            return 0.0

    # ── Shared: transcript formatter ──────────────────────────────────────────

    def _format_transcript(self, segments: list[TranscriptSegment]) -> str:
        """Format segments as [seg:N] text lines for the prompt."""
        return "\n".join(f"[seg:{seg.id}] {seg.text}" for seg in segments)

    # ── Abstract: subclasses implement these ──────────────────────────────────

    @abstractmethod
    def build_prompt(self, segments: list[TranscriptSegment]) -> str:
        """Build the full prompt string to send to Ollama."""
        ...

    @abstractmethod
    def parse_result(self, data: dict, seg_index: dict[int, float]) -> MeetingSummary:
        """Map the parsed JSON dict into a MeetingSummary."""
        ...

    # ── Public entry point ────────────────────────────────────────────────────

    def summarize(self, segments: list[TranscriptSegment]) -> MeetingSummary:
        if not segments:
            raise ValueError("Cannot summarize an empty transcript.")

        cfg = get_config()

        # Truncate if needed
        if len(segments) > cfg.max_segments:
            print(
                f"[{self.__class__.__name__}] Truncating {len(segments)} "
                f"segments to {cfg.max_segments}"
            )
            segments = segments[: cfg.max_segments]

        seg_index = self._seg_index(segments)
        prompt    = self.build_prompt(segments)
        raw       = self._call_ollama(prompt)
        data      = self._parse_json(raw)

        return self.parse_result(data, seg_index)
