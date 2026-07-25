import json
import os
import httpx

from models import TranscriptSegment, MeetingSummary, TalkingPoint, ActionItem

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))   # seconds


# ── Prompt ────────────────────────────────────────────────────────────────────

def _build_prompt(segments: list[TranscriptSegment]) -> str:
    """
    Format timed transcript segments into a prompt that instructs the LLM
    to return structured JSON with timestamp references.

    Each line looks like:
        [00:42] And the Q3 budget is currently 10% over target.
    """
    lines = []
    for seg in segments:
        minutes = int(seg.start // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        lines.append(f"[{timestamp}] {seg.text}")

    transcript_block = "\n".join(lines)

    return f"""You are a professional meeting note-taker. Analyze the transcript below and return a JSON object — nothing else, no markdown fences, no explanation.

TRANSCRIPT:
{transcript_block}

Return this exact JSON structure:
{{
  "meeting_date": "<date mentioned in transcript, or null>",
  "summary": "<one concise paragraph summarising the whole meeting>",
  "talking_points": [
    {{
      "title": "<short topic title>",
      "bullets": ["<key point>", "<key point>"],
      "ref_start": <earliest timestamp in SECONDS (float) where this topic appears>
    }}
  ],
  "action_items": [
    {{
      "task": "<what needs to be done>",
      "owner": "<person responsible or null>",
      "due": "<deadline or null>"
    }}
  ]
}}

Rules:
- ref_start must be a number in seconds (e.g. 42.0), not a mm:ss string.
- Extract every distinct topic as a separate talking point.
- Only include action items that are explicitly stated.
- If no date is mentioned, set meeting_date to null.
- Return valid JSON only. No prose before or after."""


# ── Ollama client ─────────────────────────────────────────────────────────────

def _call_ollama(prompt: str) -> str:
    """Send prompt to Ollama and return raw text response."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,     # low temp = more consistent structured output
            "num_predict": 2048,
        },
    }

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_BASE_URL}. "
            "Make sure Ollama is running: `ollama serve`"
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            f"Ollama request timed out after {OLLAMA_TIMEOUT}s. "
            "Try a smaller model or increase OLLAMA_TIMEOUT."
        )

    return response.json()["response"]


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_response(raw: str) -> dict:
    """
    Safely extract JSON from the LLM response.
    Models sometimes wrap output in ```json fences despite instructions,
    so we locate the first { and last } as a fallback.
    """
    # Strip markdown fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```", 2)[-1]          # drop opening fence line
        clean = clean.rsplit("```", 1)[0]           # drop closing fence

    # Find outermost JSON object
    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model response:\n{raw[:500]}")

    return json.loads(clean[start : end + 1])


# ── Public interface ──────────────────────────────────────────────────────────

def summarize(segments: list[TranscriptSegment]) -> MeetingSummary:
    """
    Take a list of timed transcript segments → return a structured MeetingSummary.

    Flow:
      1. Format segments into a timestamped prompt
      2. Call Ollama
      3. Parse the JSON response
      4. Map into Pydantic models (validates types and required fields)
    """
    if not segments:
        raise ValueError("Cannot summarize an empty transcript.")

    prompt = _build_prompt(segments)
    raw = _call_ollama(prompt)
    data = _parse_response(raw)

    # Map talking points
    talking_points = [
        TalkingPoint(
            title=tp["title"],
            bullets=tp.get("bullets", []),
            ref_start=float(tp.get("ref_start", 0.0)),
        )
        for tp in data.get("talking_points", [])
    ]

    # Map action items
    action_items = [
        ActionItem(
            task=ai["task"],
            owner=ai.get("owner"),
            due=ai.get("due"),
        )
        for ai in data.get("action_items", [])
    ]

    return MeetingSummary(
        meeting_date=data.get("meeting_date"),
        summary=data.get("summary", ""),
        talking_points=talking_points,
        action_items=action_items,
        model_used=OLLAMA_MODEL,
    )
