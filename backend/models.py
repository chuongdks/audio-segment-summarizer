from pydantic import BaseModel
from typing import Optional


# ── Step 1: Transcription ─────────────────────────────────────────────────────

class TranscriptSegment(BaseModel):
    """A single timed segment from Whisper transcription."""
    id: int
    text: str
    start: float        # seconds
    end: float          # seconds
    speaker: Optional[str] = None   # reserved for future diarization


class TranscriptionResult(BaseModel):
    """Full transcription output returned by the /transcribe endpoint."""
    segments: list[TranscriptSegment]
    full_text: str
    language: str
    duration_seconds: float


# ── Step 2: Summarization ─────────────────────────────────────────────────────

class ActionItem(BaseModel):
    """A single extracted task / follow-up."""
    task: str
    owner: Optional[str] = None     # person responsible, if mentioned
    due: Optional[str] = None       # deadline, if mentioned


class TalkingPoint(BaseModel):
    """
    A topic discussed in the meeting.
    ref_start points to the earliest segment where this topic appeared,
    so the frontend can seek the audio player to that moment.
    """
    title: str
    bullets: list[str]
    ref_start: float                # seconds into the audio


class MeetingSummary(BaseModel):
    """Full structured summary returned by the /summarize endpoint."""
    meeting_date: Optional[str] = None      # extracted from transcript or None
    summary: str                            # one-paragraph overview
    talking_points: list[TalkingPoint]
    action_items: list[ActionItem]
    model_used: str                         # which Ollama model produced this
