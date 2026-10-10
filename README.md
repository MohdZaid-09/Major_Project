# MedSaathi

MedSaathi is a multilingual health guidance assistant built with Python and FastAPI. It helps users describe symptoms in text or voice, retrieves relevant local medical context from a curated knowledge base, and answers with general, safety-focused guidance in a structured format.

The project is designed for low-friction symptom checking in Indian contexts, with multilingual support, follow-up questioning, and emergency escalation when appropriate.

## What MedSaathi does

- Accepts symptom queries in text or voice
- Supports multiple Indian languages in the browser UI
- Uses a local knowledge base for grounded retrieval
- Helps users with a follow-up flow when symptoms are vague
- Returns four care perspectives:
  - allopathic
  - ayurvedic
  - unani
  - homeopathic
- Adds safety notes, evidence levels, and precautions to each recommendation
- Flags urgent symptoms and gives emergency guidance when needed
- Offers a browser-based experience with dark mode and animated remedy cards

## Key features

- Multilingual assistant interface
- Local RAG using ChromaDB and sentence embeddings
- Optional local model support through Ollama
- Anthropic and Gemini model support
- Voice transcription and text-to-speech support
- Fallback logic when the LLM is unavailable
- Emergency detection for severe symptoms
- Simple front-end using HTML, CSS, and JavaScript

## Current app flow

The app follows a guided conversational pattern:

1. User enters a symptom question
2. The assistant responds with a concise answer
3. If needed, it asks one focused follow-up question
4. It displays four remedy options after the conversation context is sufficient
5. The user can continue the chat or start a new one

This is the conversational flow the app is designed to support.

## Tech stack

- Python 3.12
- FastAPI
- ChromaDB
- SentenceTransformers
- Ollama
- Anthropic / Gemini / Ollama model providers
- Faster Whisper and speech utilities
- HTML, CSS, and JavaScript front-end

## Project structure

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
│   ├── acid_reflux.md
│   ├── allergic_rhinitis.md
│   ├── common_cold.md
│   ├── cough.md
│   ├── dehydration.md
│   ├── diarrhoea.md
│   ├── fever.md
│   ├── headache.md
│   ├── heat_illness.md
│   ├── insect_bites.md
│   ├── sore_throat.md
│   └── sprains_strains.md
├── scripts/
│   ├── create_progress_pdf.py
│   └── ingest_knowledge_base.py
├── tests/
│   ├── test_chat_flow.py
│   └── test_ui.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── audio_temp/
├── chroma_store/
└── app/static/fonts/
```

## Important safety note

This project is not a replacement for a licensed healthcare professional.

It is intended to provide general information only and to:

- ask clarifying questions when symptoms are vague
- avoid making a definitive diagnosis
- flag emergency symptoms early
- encourage medical consultation when needed
- avoid recommending prescription-only medication without clinician guidance

## Local setup

1. Clone the repository

```bash
git clone https://github.com/MohdZaid-09/Major_Project.git
cd Major_Project
```

2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root

Example configuration:

```env
LLM_PROVIDER=ollama
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_gemini_key_here
CLAUDE_MODEL=claude-sonnet-5
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
WHISPER_MODEL_SIZE=small
WARMUP_RAG=true
WARMUP_SPEECH=false
LLM_MAX_TOKENS=1500
LLM_TIMEOUT_SECONDS=90
OLLAMA_KEEP_ALIVE=15m
```

If you want to use Ollama locally, make sure it is installed and the model is available:

```bash
ollama pull qwen2.5:7b
```

## Build the knowledge base

The app uses a local Markdown knowledge base and ChromaDB to retrieve relevant context before generating an answer.

```bash
python scripts/ingest_knowledge_base.py
```

This creates or refreshes the vector store under the local `chroma_store` directory.

## Run the app

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/
```

## Main API routes

### Health check

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

### Voice transcription

```http
POST /transcribe
```

Multipart file upload for audio.

### Voice chat

```http
POST /voice-chat
```

Audio upload plus conversation context/history.

### Text to speech

```http
POST /speak
```

Form field:

- `text`

## Example response shape

```json
{
  "conversational_reply": "It may be a mild viral illness. Please tell me more about fever and cough duration.",
  "follow_up_question": "How long have your symptoms lasted and are you having fever, chest pain, or breathing difficulty?",
  "is_emergency": false,
  "allopathic": {
    "summary": "Rest, hydration, and OTC symptom relief as appropriate.",
    "evidence_level": "strong",
    "precautions": "Do not exceed dosage instructions and seek medical care if symptoms worsen."
  },
  "ayurvedic": {
    "summary": "Warm fluids and ginger tea may help soothe throat discomfort.",
    "evidence_level": "traditional/anecdotal",
    "precautions": "Use cautiously and consult a qualified practitioner if unsure."
  },
  "unani": {
    "summary": "Warm drinks and steam inhalation can help with cough and congestion.",
    "evidence_level": "traditional/anecdotal",
    "precautions": "Use with caution and avoid self-medicating if symptoms are severe."
  },
  "homeopathic": {
    "summary": "Some people use symptom-based homeopathic remedies, but evidence is limited.",
    "evidence_level": "traditional/anecdotal",
    "precautions": "This should not replace conventional care."
  },
  "language": "en",
  "sources": []
}
```

## Safety rules built into the app

The assistant is designed to:

- respond in the user-requested language
- avoid making a definitive diagnosis
- ask one focused follow-up question when details are missing
- distinguish between general health guidance and emergency symptoms
- avoid prescribing medications without qualified clinical context
- prioritize urgent medical help for severe symptoms such as chest pain, breathing difficulty, fainting, stroke signs, or heavy bleeding

## Screenshots

Add screenshots of the main workflow here to document the product experience:

- Home screen / welcome state
- Chat conversation with symptom input
- Follow-up question flow
- Remedy card grid with four care perspectives
- Dark mode toggle on the interface

Example image layout:

```md
![Home screen](docs/screenshots/home.png)
![Conversation flow](docs/screenshots/chat-flow.png)
![Care perspectives](docs/screenshots/remedies.png)
![Dark mode](docs/screenshots/dark-mode.png)
```

Store screenshots in a `docs/screenshots/` folder for consistent documentation.

## Deployment

This application can be run locally or deployed to a remote server.

### Local deployment

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production deployment options

Common options for hosting this FastAPI app include:

- Azure App Service
- Azure Container Apps
- Docker container on a VPS or cloud host
- Any server that supports Python web apps

### Recommended production settings

- Set environment variables in your hosting platform
- Enable a working LLM backend: Ollama, Anthropic, or Gemini
- Keep the `knowledge_base/` and `chroma_store/` directory available on the deployed instance
- Configure `WARMUP_RAG` and `WARMUP_SPEECH` depending on your deployment environment
- Use a reverse proxy or managed platform if needed for TLS and HTTP routing

Example production command:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## License

This project is available for educational and personal use.

## Author

Mohd Zaid
