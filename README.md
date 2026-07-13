# 🎓 ScholarGraph — Autonomous Citation Intelligence Engine

> An autonomous citation exploration and Graph RAG engine that maps, crawls, and queries the academic ancestry of scientific research. Built using **Neo4j AuraDB**, **Sarvam AI**, and **LangGraph**.

Developed for **HackHazards 2026** (Learning & Knowledge Systems Track / Neo4j & Sarvam AI Sponsor Tracks).

---

## 🔗 Live Application & Demo

* **Deployed Web Application:** [https://scholargraph-mygi.onrender.com/](https://scholargraph-mygi.onrender.com/)
* **Neo4j Graph Database:** Cloud hosted via Neo4j AuraDB

---

## ✨ Key Features

* **Directed Citation Crawling (BFS):** Recursively traverses reference chains from any seed arXiv ID using a structured state machine orchestration built on **LangGraph**.
* **Neo4j Graph Database Integration:** Stores papers and their relationships structurally as `(:Paper)-[:CITES]->(:Paper)` to support deterministic graph traversals.
* **Hybrid Graph RAG:** Translates natural language questions to optimized Cypher queries via LangChain's `GraphCypherQAChain` for deterministic, hallucination-free graph analytics.
* **Sarvam AI Integration (Sponsor Track):**
  - **Voice Questions:** Powered by **Saaras V3** speech-to-text (STT) for hands-free querying.
  - **Audio Readback:** Powered by **Bulbul V3** text-to-speech (TTS) for natural narration of graph insights.
  - **LLM Reasoning:** Powered by `sarvam-30b` OpenAI-compatible chat model for QA completions.
* **Premium Dark Academic UI:** Fully responsive dashboard showing real-time BFS crawler status, live vis.network citation graph visualizations, and voice-enabled chatbot panel.

---

## 🛠️ Technology Stack

* **Frontend:** Vanilla HTML5, Modern HSL/CSS variables, JavaScript (ES6+), vis-network (node-graph visualization).
* **Backend:** FastAPI (Python 3.13), Uvicorn.
* **Orchestration & Agents:** LangGraph (StateGraph orchestration), LangChain (Neo4jGraph, GraphCypherQAChain).
* **Databases:** Neo4j AuraDB (Property Graph Database).
* **AI Model APIs:** Sarvam AI (LLM, TTS, STT APIs), Groq AI (Llama 3.3 70B for high-precision Cypher generation).

---

## 📂 Repository Structure

```text
scholarGraph/
├── agent/               # Autonomous agentic pipelines
│   ├── crawler_agent.py    # Recursive citation crawling agent
│   ├── ingestion_agent.py  # ArXiv ID resolver & single paper ingester
│   ├── orchestrator.py     # LangGraph agentic state coordinator
│   └── rag_agent.py        # GraphCypherQAChain Graph RAG implementation
├── api/                 # REST endpoints (FastAPI)
│   ├── server.py           # Backend routes & static file rendering
│   └── schemas.py          # Request / Response schemas
├── graph/               # Graph database configuration
│   ├── neo4j_client.py     # Neo4j client connection wrapper
│   └── schema.py           # Neo4j database constraints & indexes
├── tools/               # External APIs and SDKs
│   ├── semantic_scholar.py # Semantic Scholar API wrapper
│   ├── stt.py              # Sarvam AI STT API integration
│   └── tts.py              # Sarvam AI TTS API integration
├── static/              # Dark Academic UI Assets
│   ├── index.html          # Web dashboard layout
│   ├── style.css           # Glassmorphic Dark styling
│   └── app.js              # Live graph renderer & API orchestrator
├── config.py            # Environment configurations
├── requirements.txt     # Python requirements
├── .env.example         # Template for API credentials
└── README.md            # Hackathon documentation
```

---

## 🚀 Setup & Installation

### Prerequisites
* **Python 3.13+** (Windows users: Ensure `numpy >= 2.2.6` for compatibility)
* **Neo4j AuraDB Instance** (Free tier instance is sufficient)
* **Sarvam AI API Key**
* **Groq API Key**

### 1. Clone & Install
```bash
git clone <your-repository-url>
cd scholarGraph
python -m venv .venv
source .venv/Scripts/activate # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
NEO4J_URI=neo4j+s://<your-auradb-subdomain>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
NEO4J_PASSWORD=<your-auradb-password>

SARVAM_API_KEY=<your-sarvam-key>
GROQ_API_KEY=<your-groq-key>

USE_SARVAM_LLM=true
USE_SARVAM_TTS=true
```

### 3. Pre-seed the Database (Crucial for Demo Evaluation)
Because the Semantic Scholar API is rate-limited, judges should avoid triggering massive live BFS crawls during testing. Pre-seed your Neo4j instance with our pre-configured network of foundational papers (**Attention Is All You Need**, **BERT**, and **RAG**):
```bash
python agent/pre_seed.py
```
This script runs our crawlers in a controlled rate-limited loop and builds the primary citation graph containing **440+ papers** and **250+ citation edges**.

### 4. Run the Server
Start the FastAPI server:
```bash
python -m uvicorn api.server:app --reload
```
Open your browser at `http://127.0.0.1:8000` to interact with the application.

---

## 💬 Sample Graph RAG Queries to Try

Once the database is seeded or a graph is built, try these queries in the **Ask the Graph** chat panel:
1. **Citation Paths (Undirected/Directed Graph Traversals):**
   * *"what is the shortest citation path between BERT and Attention is all you need paper?"*
   * **Result:** Traces the exact historical citation path: `BERT (2019)` -> `U-Net (2018)` -> `Attention is All you Need (2017)`.
2. **Bibliographic Metrics:**
   * *"What is the most cited paper in the graph?"*
   * *"List all papers published in 2017."*
3. **Lineage Queries:**
   * *"Who are the authors of Attention is All you Need?"*
   * *"What papers does BERT cite?"*

---

## 🏆 Hackathon Sponsor Track Features

### Neo4j AuraDB Integration
* Models papers as nodes and citations as relationships: `(a:Paper)-[:CITES]->(b:Paper)`.
* Employs Graph RAG translating complex conversational queries into Cypher commands (`shortestPath()`, `IN-DEGREE` analytics).
* Utilizes a dual-LLM pipeline: Groq's `llama-3.3-70b` operates as the `cypher_llm` for 100% syntactically perfect Cypher generation, while Sarvam AI handles prompt response formatting (`qa_llm`).

### Sarvam AI Integration
* **Speech-to-Text (STT):** Integrates Sarvam's `Saaras V3` models enabling researchers to click the microphone icon and dictate queries directly into the search bar.
* **Text-to-Speech (TTS):** Generates high-fidelity audio readback of scientific insights using Sarvam's `bulbul:v3` text-to-speech model.
* **LLM:** Integrates `sarvam-30b` for natural language chat completion.
