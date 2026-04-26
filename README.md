# 🧠 MeetingMind AI

> An AI-powered meeting intelligence platform that transcribes, summarises, and extracts action items from your meetings — so your team can focus on the conversation, not the notes.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7+-DC382D?style=flat-square&logo=redis&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF4458?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📌 Overview

MeetingMind AI is a full-stack intelligent meeting assistant that turns raw meeting audio or transcripts into structured, searchable knowledge. It automatically generates summaries, extracts action items with owners, answers questions about past meetings using semantic search, and stores everything in a queryable knowledge base.

**The problem it solves:** Teams spend hours in meetings and more hours writing notes afterward. MeetingMind AI handles everything post-meeting — structured summaries, assigned action items, and a searchable archive of every decision ever made.

---

## ✨ Features

- **🎙️ Meeting Transcription** — Upload audio files or paste raw transcripts for processing
- **📝 AI Summarisation** — Generates structured summaries with key discussion points and decisions
- **✅ Action Item Extraction** — Automatically identifies tasks, assigns owners, and sets due dates
- **🔍 Semantic Search** — Ask natural language questions across all past meetings using vector search
- **💬 Meeting Q&A** — Chat with your meeting history ("What did we decide about the product roadmap?")
- **📊 Meeting Analytics** — Track participation, recurring topics, and follow-through on action items
- **🔗 Integrations** — Pluggable architecture for Zoom, Google Meet, Slack, and calendar systems
- **🐳 Docker-ready** — Full containerised setup with one command
- **🔒 Secure** — Environment-based secrets, Redis session management, pre-commit hooks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MeetingMind AI                       │
├──────────────┬──────────────────────────────────────────────┤
│   UI Layer   │  React / Streamlit frontend (ui/)            │
├──────────────┼──────────────────────────────────────────────┤
│   API Layer  │  FastAPI — REST endpoints + WebSocket (src/) │
├──────────────┼──────────────────────────────────────────────┤
│   AI Core    │  Transcription → Summarisation → Extraction  │
│              │  LLM (OpenAI / Groq) + LangChain chains      │
├──────────────┼──────────────────────────────────────────────┤
│   Storage    │  PostgreSQL (structured data)                │
│              │  Qdrant (vector embeddings for search)       │
│              │  Redis (caching + session management)        │
├──────────────┼──────────────────────────────────────────────┤
│   Infra      │  Docker Compose · GitHub Actions CI/CD       │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
MeetingMindAI/
├── src/                        # Core application source
│   ├── api/                    # FastAPI routers and endpoints
│   ├── agents/                 # LLM agents (summariser, extractor, Q&A)
│   ├── models/                 # SQLAlchemy database models
│   ├── services/               # Business logic layer
│   ├── pipelines/              # End-to-end meeting processing pipelines
│   └── config.py               # App configuration and settings
│
├── ui/                         # Frontend interface
│
├── tests/                      # Unit and integration tests
│
├── docker/                     # Dockerfiles and compose configs
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/                       # Architecture diagrams and API docs
│
├── scripts/                    # Utility scripts (migrations, seeding)
│
├── requirements/               # Split requirements files
│   ├── base.txt                # Core dependencies
│   ├── dev.txt                 # Development dependencies
│   └── prod.txt                # Production dependencies
│
├── .github/workflows/          # CI/CD pipelines
├── .env.example                # Environment variable template
├── .pre-commit-config.yaml     # Code quality hooks
├── pyproject.toml              # Project metadata and tool config
├── test_env.py                 # Environment verification script
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16+ (or use Docker)
- Redis 7+ (or use Docker)
- An OpenAI API key (or compatible LLM provider)

### Option A — Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/DhrumilPrajapati03/MeetingMindAI.git
cd MeetingMindAI

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 3. Start all services
docker compose -f docker/docker-compose.yml up --build

# App will be available at http://localhost:8000
```

### Option B — Local Development

```bash
# 1. Clone the repository
git clone https://github.com/DhrumilPrajapati03/MeetingMindAI.git
cd MeetingMindAI

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements/dev.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Verify environment setup
python test_env.py

# 6. Run database migrations
python scripts/migrate.py

# 7. Start the application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Application
APP_NAME=MeetingMind AI
ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://meetingmind:password@localhost:5432/meetingmind
REDIS_URL=redis://localhost:6379/0

# Vector Database (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=meetings

# LLM Provider
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Embeddings
EMBEDDING_MODEL=text-embedding-3-small

# Optional integrations
SLACK_BOT_TOKEN=xoxb-...
ZOOM_API_KEY=...
```

---

## 🚀 Usage

### Process a Meeting

```python
from src.pipelines import MeetingPipeline

pipeline = MeetingPipeline()

# From audio file
result = pipeline.process_audio("meeting.mp3")

# From transcript text
result = pipeline.process_transcript("""
  Alice: Let's finalise the Q3 roadmap.
  Bob: I'll own the API redesign, targeting end of July.
  Alice: Great. Carol, can you handle user research by next Friday?
""")

print(result.summary)
print(result.action_items)
```

### Query Past Meetings

```python
from src.agents import MeetingQAAgent

agent = MeetingQAAgent()
answer = agent.ask("What did we decide about the pricing model last month?")
print(answer)
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/meetings/upload` | Upload audio or transcript |
| `GET` | `/meetings/{id}` | Get meeting details and summary |
| `GET` | `/meetings/{id}/actions` | Get extracted action items |
| `POST` | `/meetings/search` | Semantic search across meetings |
| `POST` | `/meetings/ask` | Q&A over meeting history |
| `GET` | `/meetings/analytics` | Meeting analytics dashboard |

Full API docs available at `http://localhost:8000/docs` (Swagger UI) once running.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test module
pytest tests/test_pipeline.py -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| API framework | FastAPI |
| AI / LLM | OpenAI GPT-4o, LangChain |
| Transcription | OpenAI Whisper |
| Vector database | Qdrant |
| Relational DB | PostgreSQL |
| Caching | Redis |
| Frontend | Streamlit / React (ui/) |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Code quality | pre-commit, ruff, black |
| Testing | pytest, pytest-cov |

---

## 🔄 CI/CD

The `.github/workflows/` directory contains automated pipelines for:

- **Lint & format check** on every pull request (ruff, black)
- **Test suite** runs on push to `master` and all PRs
- **Docker build validation** to ensure containers build cleanly
- **Dependency security scan** for known vulnerabilities

---

## 🗺️ Roadmap

- [x] Core transcription and summarisation pipeline
- [x] Action item extraction with owner assignment
- [x] Semantic search over meeting history
- [x] Docker Compose setup for local development
- [x] GitHub Actions CI/CD
- [ ] Zoom and Google Meet webhook integrations
- [ ] Slack bot for meeting summaries
- [ ] Real-time transcription via WebSocket streaming
- [ ] Calendar integration for automatic meeting scheduling
- [ ] Team dashboard and analytics UI
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes with tests
4. Ensure pre-commit hooks pass (`pre-commit run --all-files`)
5. Open a pull request with a clear description

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Dhrumil Prajapati**

GitHub: [@DhrumilPrajapati03](https://github.com/DhrumilPrajapati03)

---

<p align="center">Built with Python, LangChain, and a strong dislike for manually writing meeting notes.</p>
