import os
from pydantic import BaseModel
from typing import Literal

# ── Types ─────────────────────────────────────────────────────────────────────
# Model size tradeoffs:
#   "tiny"   — fastest, least accurate  (~39M params)
#   "base"   — good for clear audio     (~74M params)
#   "medium" — sweet spot               (~769M params)  ← recommended
#   "large-v3" — best accuracy          (~1550M params)
WhisperModel  = Literal["tiny", "base", "medium", "large-v3"]

# "cpu" works everywhere; use "cuda" if you have an Nvidia GPU
WhisperDevice = Literal["cpu", "cuda"]

class AppConfig(BaseModel):
    whisper_model:  WhisperModel
    whisper_device: WhisperDevice
    ollama_model:   str
    ollama_url:     str
    ollama_timeout: float
    max_segments:   int

class ConfigPatch(BaseModel):
    """All fields optional — only provided fields are updated."""
    whisper_model:  WhisperModel  | None = None
    whisper_device: WhisperDevice | None = None
    ollama_model:   str           | None = None
    ollama_url:     str           | None = None
    ollama_timeout: float         | None = None
    max_segments:   int           | None = None


# ── Singleton in-memory config ─────────────────────────────────────────────────
# Seeded from .env on startup. Changes via PATCH /config apply for the
# current server session only — .env is never written to.

_config: AppConfig | None = None

def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig(
            whisper_model  = os.getenv("WHISPER_MODEL",  "medium"),
            whisper_device = os.getenv("WHISPER_DEVICE", "cpu"),
            ollama_model   = os.getenv("OLLAMA_MODEL",   "llama3.1:8b"),
            ollama_url     = os.getenv("OLLAMA_URL",     "http://localhost:11434"),
            ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT", "360")),
            max_segments   = int(os.getenv("MAX_SEGMENTS", "300")),
        )
    return _config

def patch_config(patch: ConfigPatch) -> AppConfig:
    """Apply only the non-None fields from the patch."""
    cfg = get_config()
    updated = cfg.model_copy(update={
        k: v for k, v in patch.model_dump().items() if v is not None
    })
    global _config
    _config = updated
    return _config
