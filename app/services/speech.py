import os
import uuid
from threading import Lock
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool
from app.config import settings

_model = None
_model_lock = Lock()


def get_model():
    global _model
    with _model_lock:
        if _model is None:
            from faster_whisper import WhisperModel
            _model = WhisperModel(settings.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        return _model


def _transcribe_path(path: str) -> dict:
    segments, info = get_model().transcribe(
        path, beam_size=1, vad_filter=True, condition_on_previous_text=False,
    )
    # Whisper segments are lazy: iteration must also stay off the event loop.
    text = " ".join(segment.text.strip() for segment in segments)
    return {"text": text.strip(), "language": info.language}


async def transcribe_audio(file: UploadFile) -> dict:
    temp_path = os.path.join(settings.AUDIO_TEMP_DIR, f"{uuid.uuid4().hex}.audio")
    try:
        with open(temp_path, "wb") as output:
            while chunk := await file.read(1024 * 1024):
                await run_in_threadpool(output.write, chunk)
        return await run_in_threadpool(_transcribe_path, temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
