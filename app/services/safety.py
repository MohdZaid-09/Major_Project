import re


EMERGENCY_PATTERNS = (
    r"\bchest\s+pain\b",
    r"\b(can(?:not|'t)|cannot|unable to)\s+breathe\b",
    r"\b(shortness of breath|difficulty breathing|trouble breathing)\b",
    r"\b(unconscious|passed out|not responding)\b",
    r"\b(stroke|face drooping|slurred speech|one side.*(weak|numb))\b",
    r"\b(heavy bleeding|bleeding heavily|won't stop bleeding)\b",
)

NEGATION_PATTERN = re.compile(r"\b(no|not|without|never)\b[^.!?]{0,24}$", re.IGNORECASE)


def is_emergency_message(message: str) -> bool:
    """Flag high-risk symptoms before a model call; this is not a diagnosis."""
    normalized = " ".join(message.lower().split())
    for pattern in EMERGENCY_PATTERNS:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match and not NEGATION_PATTERN.search(normalized[max(0, match.start() - 30):match.start()]):
            return True
    return False


def emergency_response(language: str = "en") -> dict:
    messages = {
        "hi": "यह आपातकाल हो सकता है। अभी स्थानीय आपातकालीन नंबर पर कॉल करें या किसी पास के व्यक्ति से अस्पताल ले जाने के लिए कहें।",
        "en": "This may be an emergency. Call your local emergency number now or ask someone nearby to take you to a hospital.",
    }
    return {
        "conversational_reply": messages.get(language, messages["en"]),
        "is_emergency": True,
        "allopathic": None,
        "ayurvedic": None,
        "homeopathic": None,
        "language": language,
    }