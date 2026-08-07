import os
import tempfile
import shutil
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env before anything else

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from transcriber import Transcriber
from summarizer import summarize
from summarizers import SUMMARIZERS
from config import get_config, patch_config, AppConfig, ConfigPatch
from models import TranscriptionResult, MeetingSummary, TranscriptSegment, TranscribeAndSummarizeResult


# ── Lifespan: warm up Whisper at startup ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    Transcriber.get()
    yield


app = FastAPI(
    title="Meeting Summarizer API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # tighten when wiring up Electron
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _save_upload(file: UploadFile) -> tuple[str, str]:
    """Validate extension and save upload to a temp file. Returns (path, ext)."""
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        return tmp.name, ext


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    cfg = get_config()
    return {
        "status": "ok",
        "whisper_model":  cfg.whisper_model,
        "whisper_device": cfg.whisper_device,
        "ollama_model":   cfg.ollama_model,
        "ollama_url":     cfg.ollama_url,
    }


@app.get("/summarizers")
def list_summarizers():
    """List available summarizer styles and their descriptions."""
    descriptions = {
        "meeting": "Structured meeting notes with nested talking points and action items",
        "general": "Lightweight summary with flat talking points, no action items",
    }
    return {
        "styles": [
            {"id": k, "description": descriptions.get(k, "")}
            for k in SUMMARIZERS.keys()
        ]
    }


@app.get("/config", response_model=AppConfig)
def read_config():
    """Return the current active configuration (seeded from .env, may be patched)."""
    return get_config()


@app.patch("/config", response_model=AppConfig)
def update_config(patch: ConfigPatch):
    """
    Update one or more config values for this session.
    Changes take effect on the next request — .env is never modified.
    Changing whisper_model or whisper_device will cause the Whisper model
    to reload on the next transcription.
    """
    return patch_config(patch)


@app.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Upload audio → get back timed transcript segments.
    Use this if you want transcription only, without summarization.
    """
    tmp_path, _ = _save_upload(file)
    try:
        return Transcriber.get().transcribe(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        os.unlink(tmp_path)


@app.post("/summarize", response_model=MeetingSummary)
async def summarize_segments(
    segments: list[TranscriptSegment],
    style: str = Query(default="meeting", description="Summarizer style: meeting | general"),
):
    """
    Accept pre-transcribed segments → return structured summary.
    Use the `style` query param to select the summarizer:
    - **meeting** (default): nested talking points, action items, timestamps
    - **general**: lightweight summary with flat talking points, no action items
    """
    try:
        return summarize(segments, style=style)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Ollama unreachable / timeout — surface as 503
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")

# This api is prob for testing the transcribe and summarize functionality both at the same time, since front end call transcribe AND then summarize API
@app.post("/transcribe-and-summarize", response_model=TranscribeAndSummarizeResult)
async def transcribe_and_summarize(file: UploadFile = File(...)):
    """
    One-shot endpoint: upload audio → transcription + structured summary.
    Use transcription.segments to verify timestamps and language detection.
    Use summary for the structured meeting notes.
    """
    tmp_path, _ = _save_upload(file)
    try:
        transcription = Transcriber.get().transcribe(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        os.unlink(tmp_path)

    try:
        meeting_summary = summarize(transcription.segments)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")

    return TranscribeAndSummarizeResult(
        transcription=transcription,
        summary=meeting_summary,
    )
