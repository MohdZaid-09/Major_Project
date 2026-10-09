import json
import httpx
from anthropic import Anthropic
from google import genai
from app.config import settings
from app.services.rag import retrieve_context_with_sources
from app.services.safety import emergency_response, is_emergency_message

_anthropic_client = None
_gemini_client = None

SYSTEM_PROMPT = """You are SwasthAI, a multilingual AI healthcare assistant for users in India.

CRITICAL RULES:
1. You are NOT a substitute for a licensed medical professional. Never give a definitive diagnosis.
2. ALWAYS respond in the language specified by the user's language code.
3. If symptoms are vague, ask a short follow-up question instead of guessing (location, duration, fever, existing conditions, medications, age, pregnancy) - in this case leave the remedy fields null.
4. Only flag a potential emergency for genuinely severe symptoms (chest pain, difficulty breathing, unconsciousness, stroke symptoms, heavy bleeding). A headache and mild fever alone is NOT an emergency.
5. When you have enough information, provide FOUR separate perspectives: allopathic (modern medicine), ayurvedic, unani, and homeopathic. For EACH, give:
   - summary: a short, practical suggestion (OTC options, home care, or traditional remedies as relevant - never prescription-only drugs)
   - evidence_level: one of "strong", "moderate", "limited", or "traditional/anecdotal" - be honest, especially for homeopathy and traditional systems, which generally have limited/anecdotal evidence for most conditions
   - precautions: brief safety notes or when to stop and see a doctor
6. Never recommend prescription-only medication without telling the user to consult a clinician first.
7. You may be given REFERENCE MATERIAL retrieved from a curated knowledge base before the user's message. Use it to ground your answer when relevant and consistent with the rules above. If the reference material doesn't cover the user's specific situation, or conflicts with safety rules 1-6, rely on your own general knowledge instead - the reference material is a helpful aid, not an override of your safety judgment.

Respond ONLY with valid JSON, nothing else, in exactly this shape:
{
  "conversational_reply": "short spoken-friendly text - either a follow-up question, or a one-line intro to the remedies below",
  "is_emergency": true or false,
  "allopathic": {"summary": "...", "evidence_level": "...", "precautions": "..."} or null,
  "ayurvedic": {"summary": "...", "evidence_level": "...", "precautions": "..."} or null,
  "unani": {"summary": "...", "evidence_level": "...", "precautions": "..."} or null,
  "homeopathic": {"summary": "...", "evidence_level": "...", "precautions": "..."} or null
}
"""


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


def _parse_response(raw_text: str) -> dict:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = raw_text.strip().strip("`").replace("json\n", "", 1)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = {
                "conversational_reply": raw_text,
                "is_emergency": False,
                "allopathic": None,
                "ayurvedic": None,
                "unani": None,
                "homeopathic": None,
            }
    if not isinstance(parsed, dict):
        parsed = {}
    parsed.setdefault("conversational_reply", "I could not prepare a response. Please try again.")
    parsed.setdefault("is_emergency", False)
    for system in ("allopathic", "ayurvedic", "unani", "homeopathic"):
        parsed.setdefault(system, None)
    return parsed


def _build_user_content(message: str, language: str, context: str, history: list[dict]) -> str:
    conversation = "\n".join(
        f"{entry['role'].title()}: {entry['content']}"
        for entry in history[-12:]
        if isinstance(entry, dict)
        and entry.get("role") in {"user", "assistant"}
        and entry.get("content")
    )
    history_section = f"CONVERSATION HISTORY:\n{conversation}\n\n" if conversation else ""
    if context:
        return (
            f"REFERENCE MATERIAL (use where relevant):\n{context}\n\n"
            f"{history_section}"
            f"[Respond in language code: {language}]\n"
            f"User message: {message}"
        )
    return f"{history_section}[Respond in language code: {language}]\n{message}"


async def _chat_anthropic(message: str, language: str, context: str, history: list[dict]) -> dict:
    client = _get_anthropic_client()
    user_content = _build_user_content(message, language, context, history)
    response = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    raw_text = "".join(b.text for b in response.content if b.type == "text")
    return _parse_response(raw_text)


async def _chat_gemini(message: str, language: str, context: str, history: list[dict]) -> dict:
    client = _get_gemini_client()
    user_content = _build_user_content(message, language, context, history)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_content,
        config={"system_instruction": SYSTEM_PROMPT},
    )
    return _parse_response(response.text)


async def _chat_ollama(message: str, language: str, context: str, history: list[dict]) -> dict:
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    user_content = _build_user_content(message, language, context, history)
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data.get("message", {}).get("content", "")
        return _parse_response(raw_text)


async def chat_completion(message: str, language: str = "en", history: list[dict] | None = None) -> dict:
    """
    Retrieves relevant reference material, then routes to the configured
    LLM provider with that context injected into the prompt.
    """
    if is_emergency_message(message):
        result = emergency_response(language)
        result["unani"] = None
        result["sources"] = []
        return result

    retrieval = retrieve_context_with_sources(message)
    context = retrieval["context"]
    history = history or []

    if settings.LLM_PROVIDER == "ollama":
        result = await _chat_ollama(message, language, context, history)
    elif settings.LLM_PROVIDER == "gemini":
        result = await _chat_gemini(message, language, context, history)
    else:
        result = await _chat_anthropic(message, language, context, history)

    if not isinstance(result, dict):
        raise RuntimeError("The configured LLM returned an invalid response object")
    result["language"] = language
    result["sources"] = retrieval["sources"]
    return result