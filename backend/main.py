import os
import tempfile
import shutil
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env before anything else

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from transcriber import Transcriber
from summarizer import summarize
from models import TranscriptionResult, MeetingSummary, TranscriptSegment


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
    return {
        "status": "ok",
        "whisper_model": os.getenv("WHISPER_MODEL", "medium"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        "ollama_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
    }


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
async def summarize_segments(segments: list[TranscriptSegment]):
    """
    Accept pre-transcribed segments → return structured meeting summary.
    Use this if you already have a transcript and just want summarization.
    """
    try:
        return summarize(segments)
    except RuntimeError as e:
        # Ollama unreachable / timeout — surface as 503
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")


@app.post("/transcribe-and-summarize", response_model=MeetingSummary)
async def transcribe_and_summarize(file: UploadFile = File(...)):
    """
    One-shot endpoint: upload audio → get back a full structured summary.
    This is what the Electron frontend will call.
    """
    tmp_path, _ = _save_upload(file)
    try:
        result = Transcriber.get().transcribe(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        os.unlink(tmp_path)

    try:
        return summarize(result.segments)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")
