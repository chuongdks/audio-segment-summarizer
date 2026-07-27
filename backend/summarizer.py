import json
import os
import httpx

from models import TranscriptSegment, MeetingSummary, TalkingPoint, SubSection, ActionItem

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "360"))
MAX_SEGMENTS = int(os.getenv("MAX_SEGMENTS", "300"))


# ── Prompt ────────────────────────────────────────────────────────────────────

def _build_prompt(segments: list[TranscriptSegment]) -> str:
    lines = []
    for seg in segments:
        lines.append(f"[seg:{seg.id}] {seg.text}")
    transcript_block = "\n".join(lines)

    return f"""You are a professional meeting note-taker. Extract ALL information from the transcript below with high precision.

Return a single JSON object. No markdown fences, no explanation, nothing before or after the JSON.

TRANSCRIPT:
{transcript_block}

Return this exact JSON structure:
{{
  "meeting_date": "<date or time reference for this meeting, or null>",
  "summary": "<one concise paragraph covering the entire meeting>",
  "talking_points": [
    {{
      "title": "<name of this top-level topic or theme>",
      "bullets": ["<any top-level points that don't belong to a sub-group>"],
      "subsections": [
        {{
          "title": "<name of this sub-group, e.g. 'Training Phase' or 'Compensation'>",
          "bullets": ["<every specific fact, number, or detail in this sub-group>"],
          "ref_seg": <integer segment ID where this sub-group first appears>
        }}
      ],
      "ref_seg": <integer segment ID where this top-level topic first appears>
    }}
  ],
  "action_items": [
    {{
      "task": "<exactly what needs to be done>",
      "owner": "<name or role of person responsible, or null>",
      "due": "<deadline as stated, or null>",
      "completed": false
    }}
  ]
}}

Rules — follow ALL of them:

SECTIONS & SUBSECTIONS:
- Group related content into named top-level sections (e.g. "Work Authorization", "Program Structure", "Compensation").
- If a section has distinct sub-topics (e.g. "Training Phase" and "Client Assignment" under "Program Structure"), create subsections for them.
- If a section has no meaningful sub-groups, leave subsections as an empty array [] and put all bullets at the top level.
- Do NOT merge unrelated topics into one section.
- A 30-minute meeting should produce 5-10 top-level sections minimum.

BULLETS:
- Extract EVERY specific fact, number, name, date, condition, or decision.
- Each bullet is one concrete fact — not a vague summary.
- Preserve exact figures: dollar amounts, durations, percentages, counts.
- Aim for 3-8 bullets per section or subsection.

TIMESTAMPS:
- ref_seg must be the integer ID from [seg:N] where that topic or subsection first appears.
- Never use a mm:ss string — only the raw integer.

ACTION ITEMS:
- Include every task, follow-up, or commitment mentioned by anyone.
- If a name was spoken, set owner to that name — never leave it null if mentioned.
- If a deadline was spoken, set due to that — never leave it null if mentioned.
- completed is always false.

Return valid JSON only."""


# ── Segment index ─────────────────────────────────────────────────────────────

def _build_seg_index(segments: list[TranscriptSegment]) -> dict[int, float]:
    return {seg.id: seg.start for seg in segments}


# ── Ollama client ─────────────────────────────────────────────────────────────

def _call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 4096,
        },
    }

    # Explicit Timeout so the read phase (model generation) gets the full
    # OLLAMA_TIMEOUT budget, passing a bare float only sets the connect timeout.
    timeout = httpx.Timeout(
        connect=10.0,        # fail fast if Ollama is not running
        read=OLLAMA_TIMEOUT, # generation can be slow on large transcripts
        write=30.0,
        pool=5.0,
    )

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=timeout,
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

    # Truncate very long transcripts to keep the prompt within a manageable
    # context size for smaller models. The seg_index still uses ALL segments
    # so timestamp lookups stay accurate even for truncated runs.
    if len(segments) > MAX_SEGMENTS:
        print(f"[Summarizer] Truncating {len(segments)} segments to {MAX_SEGMENTS} "
              f"(increase MAX_SEGMENTS in .env for longer meetings)")
        segments_for_prompt = segments[:MAX_SEGMENTS]
    else:
        segments_for_prompt = segments

    seg_index = _build_seg_index(segments)
    prompt = _build_prompt(segments_for_prompt)
    raw = _call_ollama(prompt)
    data = _parse_response(raw)

    def resolve(ref_seg) -> float:
        """Resolve a model-returned segment ID to an exact timestamp."""
        try:
            return seg_index.get(int(ref_seg), 0.0)
        except (TypeError, ValueError):
            return 0.0

    # Map talking points with nested subsections
    talking_points = []
    for tp in data.get("talking_points", []):
        subsections = [
            SubSection(
                title=ss["title"],
                bullets=ss.get("bullets", []),
                ref_start=resolve(ss.get("ref_seg", 0)),
            )
            for ss in tp.get("subsections", [])
        ]
        talking_points.append(
            TalkingPoint(
                title=tp["title"],
                bullets=tp.get("bullets", []),
                subsections=subsections,
                ref_start=resolve(tp.get("ref_seg", 0)),
            )
        )

    # Map action items
    action_items = [
        ActionItem(
            task=ai["task"],
            owner=ai.get("owner"),
            due=ai.get("due"),
            completed=ai.get("completed", False),
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
