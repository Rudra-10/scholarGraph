import sys
import os

# Allow imports from project root (agent/, graph/, tools/, config.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    IngestRequest, IngestResponse,
    AskRequest, AskResponse,
    GraphResponse, GraphNode, GraphEdge,
    SpeakRequest,
)
from agent.orchestrator import run_pipeline
from agent.rag_agent import RAGAgent
from graph.neo4j_client import Neo4jClient
from tools.tts import generate_speech
from tools.stt import transcribe_speech
import io

app = FastAPI(title="ScholarGraph API")

# ── CORS Middleware Configuration ─────────────────────────────
# NOTE: allow_origins=["*"] is used here to simplify local frontend integration 
# for the HackHazards 2026 hackathon demo. In production, this should be restricted
# to trusted, explicit domains to prevent Cross-Origin Resource Sharing vulnerabilities.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global state (simple, fine for a hackathon demo) ────────────
_state = {
    "rag_agent": None,
    "root_title": None,
    "root_id": None,
}


@app.on_event("startup")
def startup_event():
    """
    On server startup, check if Neo4j already contains paper nodes.
    If it does, pre-initialize the RAGAgent so that the chat assistant is 
    immediately queryable without requiring a new crawl session.
    """
    try:
        client = Neo4jClient()
        result = client.run_query("MATCH (p:Paper) RETURN count(p) AS count")
        client.close()
        if result and result[0]["count"] > 0:
            print(f"\n[Startup] Found {result[0]['count']} pre-seeded papers in Neo4j.")
            print("[Startup] Auto-initializing RAGAgent for instant chatbot availability...")
            _state["rag_agent"] = RAGAgent()
            _state["root_title"] = "Pre-seeded Citation Graph"
            _state["root_id"] = "preseeded"
    except Exception as e:
        print(f"\n[Startup] ⚠️ Failed to auto-initialize RAGAgent: {e}")


@app.post("/api/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    result = run_pipeline(req.arxiv_id.strip(), depth=req.depth, max_papers=req.max_papers)

    if result["status"] == "error":
        return IngestResponse(status="error", error=result["error"])

    _state["rag_agent"] = RAGAgent()
    _state["root_title"] = result["root_paper"]["title"]
    _state["root_id"] = result["root_paper"]["paperId"]

    return IngestResponse(
        status="success",
        root_title=result["root_paper"]["title"],
        papers_stored=result["crawl_result"]["papers_stored"],
    )


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not _state["rag_agent"]:
        raise HTTPException(status_code=400, detail="No paper ingested yet. Build a graph first.")

    res = _state["rag_agent"].ask(req.question)
    return AskResponse(answer=res["answer"], cypher=res["cypher"])


@app.get("/api/graph", response_model=GraphResponse)
def get_graph():
    client = Neo4jClient()
    records = client.run_query("""
        MATCH (a:Paper)-[:CITES]->(b:Paper)
        RETURN a.paperId AS from_id, a.title AS from_title, a.year AS from_year,
               b.paperId AS to_id,   b.title AS to_title,   b.year AS to_year
        LIMIT 300
    """)
    client.close()

    seen = set()
    nodes, edges = [], []
    root_id = _state.get("root_id")

    for r in records:
        if r["from_id"] not in seen:
            nodes.append(GraphNode(
                id=r["from_id"], title=r["from_title"], year=r["from_year"],
                is_root=(r["from_id"] == root_id)
            ))
            seen.add(r["from_id"])
        if r["to_id"] not in seen:
            nodes.append(GraphNode(
                id=r["to_id"], title=r["to_title"], year=r["to_year"],
                is_root=(r["to_id"] == root_id)
            ))
            seen.add(r["to_id"])
        edges.append(GraphEdge(source=r["from_id"], target=r["to_id"]))

    return GraphResponse(nodes=nodes, edges=edges)


@app.get("/api/status")
def status():
    return {
        "ready": _state["rag_agent"] is not None,
        "root_title": _state["root_title"],
    }


@app.post("/api/speak")
def speak(req: SpeakRequest):
    try:
        audio_bytes = generate_speech(req.text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        text = transcribe_speech(audio_bytes, filename=file.filename)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-sarvam")
def test_sarvam():
    results = {}
    
    # 1. Test LLM
    try:
        from langchain_openai import ChatOpenAI
        from config import SARVAM_API_KEY
        
        print("[TestSarvam] Testing ChatOpenAI integration with model 'sarvam-30b'...")
        llm = ChatOpenAI(
            model="sarvam-30b",
            openai_api_base="https://api.sarvam.ai/v1",
            openai_api_key=SARVAM_API_KEY,
            temperature=0,
        )
        response = llm.invoke("Say 'Hello!' and nothing else.")
        results["llm_status"] = "success"
        results["llm_response"] = response.content.strip()
    except Exception as e:
        results["llm_status"] = "failed"
        results["llm_error"] = str(e)
        
    # 2. Test TTS
    try:
        from tools.tts import generate_speech
        import config
        print("[TestSarvam] Testing TTS generation using bulbul:v3...")
        old_val = config.USE_SARVAM_TTS
        config.USE_SARVAM_TTS = True
        audio = generate_speech("Hi")
        config.USE_SARVAM_TTS = old_val
        results["tts_status"] = "success"
        results["tts_audio_len"] = len(audio)
    except Exception as e:
        results["tts_status"] = "failed"
        results["tts_error"] = str(e)
        
    return results


@app.get("/api/debug")
def debug():
    try:
        client = Neo4jClient()
        # Find BERT papers
        bert = client.run_query("MATCH (p:Paper) WHERE toLower(p.title) CONTAINS 'bert' RETURN p.title AS title, p.paperId AS id, p.year AS year LIMIT 5")
        # Find Attention papers
        attention = client.run_query("MATCH (p:Paper) WHERE toLower(p.title) CONTAINS 'attention' RETURN p.title AS title, p.paperId AS id, p.year AS year LIMIT 5")
        # Find shortest path between them (undirected)
        path = client.run_query("""
            MATCH (a:Paper), (b:Paper) 
            WHERE toLower(a.title) CONTAINS 'bert' AND toLower(b.title) CONTAINS 'attention is all you need'
            MATCH p = shortestPath((a)-[:CITES*]-(b)) 
            RETURN [n IN nodes(p) | n.title + ' (' + n.year + ')'] AS path
            LIMIT 1
        """)
        # Count total papers and citations
        counts = client.run_query("MATCH (p:Paper) OPTIONAL MATCH (p)-[r:CITES]->() RETURN count(p) AS papers, count(r) AS citations")
        client.close()
        return {
            "papers_in_db": counts[0] if counts else None,
            "bert_papers": bert,
            "attention_papers": attention,
            "path_found": path[0]["path"] if path else None
        }
    except Exception as e:
        return {"error": str(e)}


# ── Serve the frontend ───────────────────────────────────────
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

@app.get("/")
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

app.mount("/static", StaticFiles(directory=static_dir), name="static")