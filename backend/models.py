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
    completed: bool = False         # checkbox state, toggled in frontend


class SubSection(BaseModel):
    """
    A named sub-group within a section.
    e.g. 'Training Phase' inside 'FDM Program Structure'
    """
    title: str
    bullets: list[str]
    ref_start: float                # seconds into the audio


class TalkingPoint(BaseModel):
    """
    A top-level section discussed in the meeting.
    May contain flat bullets, nested subsections, or both.
    ref_start points to where this section first appears in the audio.
    """
    title: str
    bullets: list[str]              # top-level bullets for this section
    subsections: list[SubSection]   # optional nested sub-groups
    ref_start: float                # seconds into the audio


class MeetingSummary(BaseModel):
    """Full structured summary returned by the /summarize endpoint."""
    meeting_date: Optional[str] = None      # extracted from transcript or None
    summary: str                            # one-paragraph overview
    talking_points: list[TalkingPoint]
    action_items: list[ActionItem]
    model_used: str                         # which Ollama model produced this


# ── Step 3: Combined response ─────────────────────────────────────────────────

class TranscribeAndSummarizeResult(BaseModel):
    """Combined response for the /transcribe-and-summarize endpoint."""
    transcription: TranscriptionResult
    summary: MeetingSummary
