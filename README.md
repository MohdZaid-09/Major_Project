# SwasthAI

SwasthAI is a multilingual healthcare assistant built with Python and FastAPI. It lets users describe symptoms in text or voice, retrieves relevant local medical context from a knowledge base, and uses an LLM to provide general health guidance in a structured format.

The app focuses on safety, multilingual support, and a simple browser-based conversational interface.

## Features

- Multilingual health guidance in multiple Indian languages
- Text-based and voice-based symptom input
- Local retrieval-augmented generation (RAG) using ChromaDB
- Structured medical response format with:
  - conversational reply
  - emergency flag
  - allopathic, ayurvedic, unani, and homeopathic perspectives
  - evidence level and precautions
- Text-to-speech output for assistant responses
- Emergency detection for severe symptoms
- Static browser frontend for quick interaction

## Tech Stack

- Python 3
- FastAPI
- ChromaDB
- SentenceTransformers
- gTTS
- Faster Whisper (optional transcription backend)
- Anthropic / Gemini / Ollama LLM support
- HTML, CSS, and JavaScript frontend

## Project Structure

```text
Major_Project/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── models/
│   ├── services/
│   └── static/
├── knowledge_base/
│   ├── common_cold.md
│   ├── cough.md
│   ├── fever.md
│   ├── headache.md
│   └── ...
├── scripts/
│   ├── create_progress_pdf.py
│   └── ingest_knowledge_base.py
├── audio_temp/
├── chroma_store/
├── .gitignore
├── requirements.txt
├── .env.example
└── README.md
```

## Important Notes

This project is intended as a general-purpose health guidance assistant, not a replacement for a licensed medical professional.

It is designed to:

- ask follow-up questions when symptoms are vague
- avoid definitive diagnosis
- flag emergency symptoms early
- provide general information only
- encourage professional medical consultation when needed

## Setup

1. Clone the repository

```bash
git clone https://github.com/MohdZaid-09/Major_Project.git
cd Major_Project
```

2. Create a virtual environment

```bash
python -m venv .venv
```

3. Activate the environment

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

4. Install dependencies

```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the project root

Example:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_gemini_key_here
CLAUDE_MODEL=claude-sonnet-5
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
WHISPER_MODEL_SIZE=small
```

## Build the Knowledge Base

The project uses ChromaDB with local medical markdown documents. To build the vector index:

```bash
python scripts/ingest_knowledge_base.py
```

This reads all markdown files in the `knowledge_base/` folder and stores retrievable chunks in `chroma_store/`.

## Run the App

Start the FastAPI backend:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

## API Endpoints

### Health

```http
GET /health
```

### Chat

```http
POST /chat
```

Form fields:

- `message`
- `language`
- `history`

### Transcribe audio

```http
POST /transcribe
```

Multipart file upload for audio.

### Voice chat

```http
POST /voice-chat
```

Audio file upload plus optional context/history.

### Text-to-speech

```http
POST /speak
```

Form field:

- `text`

## Example Response Shape

```json
{
  "conversational_reply": "You may have a mild viral illness...",
  "is_emergency": false,
  "allopathic": {
    "summary": "Rest, hydration, and symptom relief...",
    "evidence_level": "strong",
    "precautions": "Seek care if symptoms worsen."
  },
  "ayurvedic": {
    "summary": "Warm fluids and ginger tea...",
    "evidence_level": "traditional/anecdotal",
    "precautions": "Use with caution if symptoms are severe."
  },
  "unani": null,
  "homeopathic": null,
  "language": "en",
  "sources": []
}
```

## Safety Rules Built Into the App

The assistant is designed to:

- avoid giving a definitive diagnosis
- respond in the requested language
- ask clarifying questions when needed
- avoid recommending prescription-only drugs without clinician guidance
- escalate to emergency handling for severe symptoms like chest pain, difficulty breathing, stroke symptoms, heavy bleeding, or unconsciousness

## License

This project is available for educational and personal use.

## Author

Mohd Zaid

## Knowledge, latency and interface update

- The corpus now has **13 symptom topics** (the original four plus diarrhoea/vomiting,
  dehydration, constipation, reflux, sore throat, nasal allergies, heat illness,
  sprains/strains and insect bites), plus a complementary-care safety document.
- New material includes source URLs and editorial review dates. Summaries are
  general information, **not clinician-reviewed**. The original four documents
  remain legacy material without verified source metadata. Source links appear
  below care cards when available; retrieved sources are not a guarantee that
  every generated sentence is supported by them.
- Rebuild the index after updating, then restart the server:

  ```bash
  python scripts/ingest_knowledge_base.py
  uvicorn app.main:app --reload
  ```

- Provider requests use async SDKs. Embedding/retrieval, transcription (including
  lazy segment iteration) and gTTS run off the request event loop. Ollama reuses
  HTTP connections and keeps its model loaded for `OLLAMA_KEEP_ALIVE=15m`.
- `WARMUP_RAG=true` moves the first embedding/model load into startup. This makes
  startup slower but avoids that cold-start work on the first chat. Set
  `WARMUP_SPEECH=true` to also load Whisper at startup (requires faster-whisper).
  Model downloads still need network access on first use.
- Answers are prompted to be concise while retaining safety instructions.
  `LLM_MAX_TOKENS=1500` is a configurable output ceiling, not a speed guarantee;
  do not set it so low that multilingual JSON is truncated.
  `LLM_TIMEOUT_SECONDS=90` bounds each provider request. Anthropic permits one retry.
- INFO logs report retrieval and generation milliseconds without logging symptom
  text. Actual response time depends on the configured model, hardware and network;
  no live provider speedup has been measured in this update.
- All 11 language choices translate app-owned interface text immediately, including
  statuses, errors, care labels and accessibility labels. Urdu uses RTL layout.
  Language choice persists locally. Existing conversation text and generated care
  content retain their original language; future requests use the selected language.
  Noto fonts are bundled for Indian scripts and Urdu with their SIL Open Font
  Licenses in `app/static/fonts/`. Language names stay in their own scripts. Browser-native audio controls follow
  the browser's locale. Translations should receive native-speaker review.
- Voice chat accepts an optional `language` form field: when supplied it controls
  the response language; otherwise detected speech language is used. `/speak`
  accepts `language` too. Browser speech voices depend on the device.
- The microphone uses an SVG icon and changes to a stop symbol during capture.
  Duplicate submission and switching chats while requests are active are blocked.
  Failed text requests restore the draft for retry. Enter sends; Shift+Enter adds a line.

### Verification

```bash
pip install pytest pytest-asyncio
python -m pytest tests/test_chat_flow.py -q
```

The regression suite uses mocked providers/retrieval: no credentials or model
weights are required. Browser checks additionally require Playwright:

```bash
pip install playwright
playwright install chromium
# With the app running on port 8765, set SWASTHAI_TEST_URL=http://127.0.0.1:8765
python -m pytest tests/test_ui.py -q
```

The deterministic emergency keyword gate still covers English phrases only.
Emergency replies are localized in all UI languages; multilingual symptom
recognition still depends on the model and needs a separate clinical safety review.
