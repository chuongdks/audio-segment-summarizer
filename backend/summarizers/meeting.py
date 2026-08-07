"""
Meeting note summarizer.

Extracts structured meeting notes with:
- Nested talking points and subsections
- Action items with owner and due date
- Timestamp references for audio seeking
"""
from config import get_config
from models import TranscriptSegment, MeetingSummary, TalkingPoint, SubSection, ActionItem
from .base import BaseSummarizer

class MeetingSummarizer(BaseSummarizer):

    def build_prompt(self, segments: list[TranscriptSegment]) -> str:
        transcript_block = self._format_transcript(segments)
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
          "title": "<name of this sub-group>",
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

Rules:
- Create a separate talking point for EVERY distinct topic. Do not merge topics.
- bullets: every specific fact, number, decision, or detail — not vague summaries.
- subsections: use when a topic has distinct sub-groups (e.g. phases, categories). Leave [] if not needed.
- ref_seg: integer segment ID from [seg:N] where the topic first appears.
- action_items: every task or commitment mentioned. Extract owner and due if spoken.
- Return valid JSON only."""

    def parse_result(self, data: dict, seg_index: dict) -> MeetingSummary:
        cfg = get_config()

        talking_points = []
        for tp in data.get("talking_points", []):
            subsections = [
                SubSection(
                    title=ss["title"],
                    bullets=ss.get("bullets", []),
                    ref_start=self._resolve(seg_index, ss.get("ref_seg", 0)),
                )
                for ss in tp.get("subsections", [])
            ]
            talking_points.append(
                TalkingPoint(
                    title=tp["title"],
                    bullets=tp.get("bullets", []),
                    subsections=subsections,
                    ref_start=self._resolve(seg_index, tp.get("ref_seg", 0)),
                )
            )

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
            model_used=cfg.ollama_model,
        )
