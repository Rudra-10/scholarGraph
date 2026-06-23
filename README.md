# ScholarGraph — Autonomous Citation Intelligence Engine

ScholarGraph is an autonomous research tool designed to trace, crawl, and query the intellectual lineage of scientific papers. Sourced from real-world citation data via Semantic Scholar and powered by **Neo4j AuraDB** and **Sarvam AI**, it enables researchers to uncover exact citation paths (e.g., shortest paths, ancestor lineages) and query their graph database using natural language.

Developed for **HackHazards 2026** (Learning & Knowledge Systems Track / Neo4j & Sarvam AI Sponsor Tracks).

---

## 🚀 Key Features

- **Directed Citation Crawling:** Recursively crawls citation networks (BFS) from a seed arXiv ID using LangGraph orchestrations.
- **Neo4j Graph Database Integration:** Stores papers and their relationships structurally as `(:Paper)-[:CITES]->(:Paper)` to support deterministic graph traversals.
- **Graph RAG (Cypher QA Chain):** Translates natural language questions to Neo4j Cypher queries for factual, traceable, and hallucination-free answers.
- **Sarvam AI Integration:** 
  - Voice questions via **Saaras V3** speech-to-text (STT).
  - Audio playback of answers via **Bulbul V3** text-to-speech (TTS).
  - OpenAI-compatible chat completion using **sarvam-30b / sarvam-m** LLMs.
- **Dark Academic UI:** Custom responsive interface with an interactive citation graph visualization (rendered via `vis-network`).

---

## 📁 Repository Structure

```text
scholarGraph/
├── agent/               # Autonomous pipeline orchestrations
│   ├── crawler_agent.py    # Recursive BFS citation crawling
│   ├── ingestion_agent.py  # Seed paper arXiv resolver
│   ├── orchestrator.py     # LangGraph state machine flow
│   └── rag_agent.py        # GraphCypherQAChain RAG & LLM interfaces
├── api/                 # FastAPI backend endpoints
│   ├── server.py           # REST endpoints & static file mounting
│   └── schemas.py          # Pydantic schemas
├── graph/               # Graph database interfaces
│   ├── neo4j_client.py     # Neo4j driver wrapper
│   └── schema.py           # Database constraints & indexes
├── tools/               # External tool wrappers
│   ├── semantic_scholar.py # API client for metadata & reference fetching
│   ├── stt.py              # Sarvam AI Voice-to-Text wrapper
│   └── tts.py              # Sarvam AI Text-to-Voice wrapper
├── static/              # Vanilla HTML/CSS/JS frontend
│   ├── index.html          # Interactive application frontend
│   ├── style.css           # Custom dark academic design styling
│   └── app.js              # Network graph renderer & API client
├── config.py            # Environment variable configuration loading
├── requirements.txt     # Python dependencies list
├── .env.example         # Example environment template
└── .gitignore           # Standard git ignore definitions
```

---

## 🛠️ Prerequisites

- **Python 3.13+** (Windows environment notes: make sure `numpy` is pinned to `2.2.6+` for compatibility)
- **Neo4j AuraDB Instance** (Free tier database instance)
- **Sarvam AI API Key** (For TTS/STT and LLM sponsor track integrations)
- **Groq API Key** (Used as the default LLM provider for development to conserve credits)

---

## ⚙️ Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <your-repository-url>
   cd scholarGraph
   ```

2. **Set Up a Virtual Environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy the example file to `.env`:
   ```bash
   copy .env.example .env
   ```
   Fill in your actual API keys and database credentials in `.env`:
   - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
   - `SARVAM_API_KEY`
   - `GROQ_API_KEY`

---

## 🏃 Running the Application

Start the FastAPI application. Use `python -m uvicorn` on Windows to guarantee the correct Python path resolution:

```bash
python -m uvicorn api.server:app --reload --port 8000
```

Once running, access the user interface in your web browser:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🔒 Security & Git Best Practices

To prevent security risks and "red flags" before pushing to GitHub, the following precautions have been taken:
- **Ignored Secrets:** `.env` is explicitly declared in `.gitignore` and will **never** be pushed.
- **Mock Config Templates:** `.env.example` provides the keys structure without containing any real credentials.
- **Build Artifacts Excluded:** Python cache folders (`__pycache__/`, `*.pyc`), IDE configurations (`.vscode/`, `.idea/`), and the virtual environment directory (`.venv/`) are excluded from tracking.
- **Zero Hardcoded Keys:** All secret management is handled strictly through environment variables.
