import os
import uuid
from fastapi import UploadFile
from faster_whisper import WhisperModel
from app.config import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(settings.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model

async def transcribe_audio(file: UploadFile) -> dict:
    """Saves the upload, transcribes it, cleans up, returns {"text", "language"}."""
    temp_path = os.path.join(settings.AUDIO_TEMP_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:
        model = get_model()
        segments, info = model.transcribe(
            temp_path,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return {"text": text.strip(), "language": info.language}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)