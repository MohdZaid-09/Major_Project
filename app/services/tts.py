import uuid, os
from gtts import gTTS
from app.config import settings

SUPPORTED = {"hi", "en", "bn", "ta", "te", "kn", "ml", "mr", "gu", "ur", "pa"}

async def synthesize_speech(text: str, language: str = "en") -> dict:
    lang_code = language if language in SUPPORTED else "en"
    filename = f"{uuid.uuid4().hex}.mp3"
    file_path = os.path.join(settings.AUDIO_TEMP_DIR, filename)
    gTTS(text=text, lang=lang_code).save(file_path)
    return {"audio_url": f"/audio/{filename}", "filename": filename}