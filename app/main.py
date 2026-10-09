import json
import logging

from fastapi.staticfiles import StaticFiles
from app.config import settings

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.services.llm import chat_completion
from app.services.speech import transcribe_audio
from app.services.tts import synthesize_speech
from app.config import settings

app = FastAPI(title="Voice AI Backend MVP", version="0.1.0")
logger = logging.getLogger(__name__)
app.mount("/audio", StaticFiles(directory=settings.AUDIO_TEMP_DIR), name="audio")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _parse_history(raw_history: str) -> list[dict]:
    parsed_history = json.loads(raw_history)
    if not isinstance(parsed_history, list):
        raise ValueError("history must be a list")
    return [
        entry for entry in parsed_history
        if isinstance(entry, dict)
        and entry.get("role") in {"user", "assistant"}
        and isinstance(entry.get("content"), str)
        and entry["content"].strip()
    ]

@app.get("/")
def home() -> FileResponse:
    return FileResponse(
        "app/static/index.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "Voice AI backend is running"}

@app.get("/debug-config")
def debug_config():
    return {"llm_provider": settings.LLM_PROVIDER}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> JSONResponse:
    result = await transcribe_audio(file)
    return JSONResponse(content=result)


@app.post("/chat")
async def chat(
    message: str = Form(...),
    language: str = Form("en"),
    history: str = Form("[]"),
) -> JSONResponse:
    try:
        parsed_history = _parse_history(history)
        result = await chat_completion(message, language=language, history=parsed_history)
        return JSONResponse(content=result)
    except (json.JSONDecodeError, ValueError):
        return JSONResponse(status_code=400, content={"error": "Conversation history was invalid."})
    except Exception:
        logger.exception("Chat request failed with provider %s", settings.LLM_PROVIDER)
        return JSONResponse(
            status_code=502,
            content={"error": f"The {settings.LLM_PROVIDER} AI service is temporarily unavailable. Check that it is running and configured correctly."},
        )


@app.post("/speak")
async def speak(text: str = Form(...)) -> JSONResponse:
    result = await synthesize_speech(text)
    return JSONResponse(content=result)

@app.post("/voice-chat")
async def voice_chat(
    file: UploadFile = File(...),
    context: str = Form(""),
    history: str = Form("[]"),
) -> JSONResponse:
    try:
        transcription = await transcribe_audio(file)
    except Exception:
        logger.exception("Voice transcription failed")
        return JSONResponse(
            status_code=422,
            content={"error": "I could not understand that recording. Please try speaking again or type your question."},
        )

    user_text = transcription["text"]
    detected_language = transcription["language"]

    if not user_text:
        return JSONResponse(
            status_code=400,
            content={"error": "Could not detect any speech in the audio."},
        )

    try:
        parsed_history = _parse_history(history)
        prompt = user_text if parsed_history or not context else f"{context}\nUser: {user_text}"
        result = await chat_completion(prompt, language=detected_language, history=parsed_history)
    except (json.JSONDecodeError, ValueError):
        return JSONResponse(status_code=400, content={"error": "Conversation history was invalid."})
    except Exception:
        logger.exception("Voice chat request failed with provider %s", settings.LLM_PROVIDER)
        return JSONResponse(
            status_code=502,
            content={"error": f"The {settings.LLM_PROVIDER} AI service is temporarily unavailable. Check that it is running and configured correctly."},
        )

    return JSONResponse(content={
        "transcribed_text": user_text,
        "detected_language": detected_language,
        **result,
    })