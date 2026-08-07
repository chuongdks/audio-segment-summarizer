"""
General audio summarizer.

Produces a lightweight summary with:
- A concise overview paragraph
- Simple flat talking points (no subsections, no action items)
- Timestamp references for audio seeking

Good for: podcasts, lectures, interviews, voice memos - any audio
where you want a quick digest without meeting-specific structure.
"""
from config import get_config
from models import TranscriptSegment, MeetingSummary, TalkingPoint, ActionItem
from .base import BaseSummarizer


class GeneralSummarizer(BaseSummarizer):

    def build_prompt(self, segments: list[TranscriptSegment]) -> str:
        transcript_block = self._format_transcript(segments)
        return f"""You are a concise summarizer. Your job is to produce a clean, readable summary of the audio transcript below.

Return a single JSON object. No markdown fences, no explanation, nothing before or after the JSON.

TRANSCRIPT:
{transcript_block}

Return this exact JSON structure:
{{
  "meeting_date": "<any date or time reference mentioned, or null>",
  "summary": "<two to three sentences capturing the core topic and main takeaway of the entire audio>",
  "talking_points": [
    {{
      "title": "<short label for this topic>",
      "bullets": ["<one clear sentence per key point - be specific, include names and numbers>"],
      "subsections": [],
      "ref_seg": <integer segment ID from [seg:N] where this topic first appears>
    }}
  ],
  "action_items": []
}}

Rules:
- summary: cover the whole audio in 2-3 sentences. What is it about? What is the main conclusion?
- talking_points: one entry per distinct topic or theme. Aim for 4-8 topics.
- bullets: 2-4 bullets per topic. Each bullet is one specific, concrete point - not a vague summary.
- subsections: always an empty array [] - no nesting for general summaries.
- action_items: always an empty array [] - general summaries do not extract tasks.
- ref_seg: the integer segment ID where this topic first appears in the transcript.
- Return valid JSON only."""

    def parse_result(self, data: dict, seg_index: dict) -> MeetingSummary:
        cfg = get_config()

        talking_points = [
            TalkingPoint(
                title=tp["title"],
                bullets=tp.get("bullets", []),
                subsections=[],        # general summaries never have subsections
                ref_start=self._resolve(seg_index, tp.get("ref_seg", 0)),
            )
            for tp in data.get("talking_points", [])
        ]

        return MeetingSummary(
            meeting_date=data.get("meeting_date"),
            summary=data.get("summary", ""),
            talking_points=talking_points,
            action_items=[],           # general summaries never have action items
            model_used=cfg.ollama_model,
        )
