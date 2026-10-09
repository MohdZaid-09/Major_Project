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
        "en": "Please get medical help now. Call your local emergency number or ask someone nearby to help you reach a hospital.",
        "hi": "कृपया तुरंत चिकित्सा सहायता लें. स्थानीय आपातकालीन नंबर पर कॉल करें या पास के किसी व्यक्ति से अस्पताल पहुँचने में मदद मांगें।",
        "bn": "এখনই চিকিৎসা সহায়তা নিন. স্থানীয় জরুরি নম্বরে ফোন করুন বা হাসপাতালে যেতে কাছের কারও সাহায্য নিন।",
        "mr": "कृपया त्वरित वैद्यकीय मदत घ्या. स्थानिक आपत्कालीन क्रमांकावर फोन करा किंवा रुग्णालयात जाण्यासाठी जवळच्या व्यक्तीची मदत घ्या.",
        "gu": "કૃપા કરીને તાત્કાલિક તબીબી મદદ લો. સ્થાનિક ઇમરજન્સી નંબર પર ફોન કરો અથવા હોસ્પિટલ પહોંચવા નજીકની વ્યક્તિની મદદ લો.",
        "pa": "ਕਿਰਪਾ ਕਰਕੇ ਤੁਰੰਤ ਡਾਕਟਰੀ ਮਦਦ ਲਵੋ. ਸਥਾਨਕ ਐਮਰਜੈਂਸੀ ਨੰਬਰ ਉੱਤੇ ਫ਼ੋਨ ਕਰੋ ਜਾਂ ਹਸਪਤਾਲ ਜਾਣ ਲਈ ਨੇੜਲੇ ਵਿਅਕਤੀ ਦੀ ਮਦਦ ਲਵੋ।",
        "ur": "براہ کرم فوراً طبی مدد لیں. مقامی ایمرجنسی نمبر پر کال کریں یا ہسپتال پہنچنے کے لیے کسی قریبی شخص سے مدد لیں۔",
        "ta": "உடனே மருத்துவ உதவி பெறுங்கள். உள்ளூர் அவசர எண்ணை அழைக்கவும் அல்லது மருத்துவமனை செல்ல அருகிலுள்ளவரின் உதவியைப் பெறவும்.",
        "te": "వెంటనే వైద్య సహాయం పొందండి. స్థానిక అత్యవసర నంబర్‌కు కాల్ చేయండి లేదా ఆసుపత్రికి వెళ్లడానికి దగ్గరలోని వారి సహాయం కోరండి.",
        "kn": "ದಯವಿಟ್ಟು ತಕ್ಷಣ ವೈದ್ಯಕೀಯ ಸಹಾಯ ಪಡೆಯಿರಿ. ಸ್ಥಳೀಯ ತುರ್ತು ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ ಅಥವಾ ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಲು ಹತ್ತಿರದವರ ಸಹಾಯ ಪಡೆಯಿರಿ.",
        "ml": "ഉടൻ വൈദ്യസഹായം തേടുക. പ്രാദേശിക അടിയന്തര നമ്പറിൽ വിളിക്കുക അല്ലെങ്കിൽ ആശുപത്രിയിലെത്താൻ സമീപത്തുള്ള ഒരാളുടെ സഹായം തേടുക."
}
    return {
        "conversational_reply": messages.get(language, messages["en"]),
        "is_emergency": True,
        "allopathic": None,
        "ayurvedic": None,
        "homeopathic": None,
        "unani": None,
        "language": language,
    }