"""
Router — delegates to the correct summarizer style.

Import this module the same way as before:
  from summarizer import summarize

The `style` parameter selects the summarizer. Defaults to "meeting"
so existing calls without a style argument keep working unchanged.
"""
from models import TranscriptSegment, MeetingSummary
from summarizers import get_summarizer


def summarize(
    segments: list[TranscriptSegment],
    style: str = "meeting",
) -> MeetingSummary:
    """
    Summarize a transcript using the given style.

    Args:
        segments: timed transcript segments from Whisper
        style:    "meeting" | "general" (more styles can be added)

    Returns:
        MeetingSummary — same schema regardless of style
    """
    return get_summarizer(style).summarize(segments)
