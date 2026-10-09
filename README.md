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
