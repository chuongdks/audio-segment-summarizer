from .meeting import MeetingSummarizer
from .general import GeneralSummarizer

# Registry — maps style key to summarizer class
# Add new styles here as you create them
SUMMARIZERS = {
    "meeting": MeetingSummarizer,
    "general": GeneralSummarizer,
}

def get_summarizer(style: str):
    """Return the summarizer class for the given style key."""
    if style not in SUMMARIZERS:
        raise ValueError(
            f"Unknown summarizer style '{style}'. "
            f"Available: {sorted(SUMMARIZERS.keys())}"
        )
    return SUMMARIZERS[style]()
