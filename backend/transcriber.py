import os
from faster_whisper import WhisperModel
from models import TranscriptSegment, TranscriptionResult

# Model size tradeoffs:
#   "tiny"   — fastest, least accurate  (~39M params)
#   "base"   — good for clear audio     (~74M params)
#   "medium" — sweet spot               (~769M params)  ← recommended
#   "large-v3" — best accuracy          (~1550M params)
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "medium")

# "cpu" works everywhere; use "cuda" if you have an Nvidia GPU
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = "int8" if DEVICE == "cpu" else "float16"


class Transcriber:
    _instance: "Transcriber | None" = None

    def __init__(self):
        print(f"[Transcriber] Loading Whisper '{WHISPER_MODEL_SIZE}' on {DEVICE}...")
        self.model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )
        print("[Transcriber] Model ready.")

    @classmethod
    def get(cls) -> "Transcriber":
        """Singleton — model loads once and stays in memory."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe an audio file and return timed segments.

        faster-whisper returns a generator of Segment objects, each with:
          .id, .text, .start, .end, .words (word-level timestamps)
        """
        segments_gen, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,   # enables word-level refs later
            vad_filter=True,        # skips silence automatically
        )

        segments: list[TranscriptSegment] = []
        full_text_parts: list[str] = []

        for seg in segments_gen:
            clean_text = seg.text.strip()
            segments.append(
                TranscriptSegment(
                    id=seg.id,
                    text=clean_text,
                    start=round(seg.start, 2),
                    end=round(seg.end, 2),
                )
            )
            full_text_parts.append(clean_text)

        return TranscriptionResult(
            segments=segments,
            full_text=" ".join(full_text_parts),
            language=info.language,
            duration_seconds=round(info.duration, 2),
        )
