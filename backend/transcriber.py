from faster_whisper import WhisperModel
from config import get_config
from models import TranscriptSegment, TranscriptionResult


class Transcriber:
    _instance: "Transcriber | None" = None
    _loaded_model:  str | None = None
    _loaded_device: str | None = None

    def __init__(self, model_size: str, device: str):
        compute_type = "int8" if device == "cpu" else "float16"
        print(f"[Transcriber] Loading Whisper '{model_size}' on {device} ({compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[Transcriber] Model ready.")

    @classmethod
    def get(cls) -> "Transcriber":
        """
        Singleton that reloads if whisper_model or whisper_device changed in config.
        This means changing the model in the UI takes effect on the next transcription
        without restarting the server.
        """
        cfg = get_config()
        if (
            cls._instance is None
            or cls._loaded_model  != cfg.whisper_model
            or cls._loaded_device != cfg.whisper_device
        ):
            cls._instance      = cls(cfg.whisper_model, cfg.whisper_device)
            cls._loaded_model  = cfg.whisper_model
            cls._loaded_device = cfg.whisper_device
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
