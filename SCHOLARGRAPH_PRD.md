# ScholarGraph — Product Requirements Document

**Project:** ScholarGraph — Autonomous Citation Intelligence Engine
**Hackathon:** HackHazards 2026 (Submission deadline: June 30, 2026)
**Track:** Learning & Knowledge Systems (domain) · Neo4j/AuraDB + Sarvam AI (sponsor tracks)
**Status:** Core pipeline complete. Frontend migration in progress. 8 days remaining.

---

## 1. Problem Statement

Researchers need to understand the intellectual lineage of a paper — what ideas it builds on, what came before it, how concepts evolved over time. Existing tools (vector search, semantic similarity, LLM-based "research landscape" tools) answer "what is similar to this paper" using embedding distance — a probabilistic guess with no ground truth, no directionality, and no verifiability.

ScholarGraph answers a fundamentally different and more rigorous question: **what does this paper actually cite, and what citation path connects any two papers** — using real citation data stored in a graph database, not semantic approximation.

**Core differentiator:** Citation relationships are directed, dated, and factual (sourced from Semantic Scholar's citation graph). They are not LLM-inferred similarity judgments. This is the entire reason a graph database (Neo4j) is architecturally correct here, while a vector store is not.

---

## 2. Goals

1. Demonstrate that citation-graph traversal answers questions vector/semantic search structurally cannot (e.g., shortest path between two papers, ancestor lineage, reverse citation lookup).
2. Win the Neo4j/AuraDB sponsor track by showing deep, idiomatic use of graph traversal (not just using Neo4j as a key-value store).
3. Win or qualify for the Sarvam AI sponsor track by integrating Sarvam's LLM, OCR, and voice APIs meaningfully.
4. Ship a polished, demoable product with a custom UI (not a default Streamlit look) by June 30.

---

## 3. Non-Goals

- Not building a semantic/embedding-based research landscape tool (a different, already-explored competitor idea — explicitly rejected in favor of staying with the graph-based approach).
- Not supporting non-arXiv papers in v1 (PDF upload via Sarvam Vision is a stretch goal, not core path).
- Not building user accounts, persistence across sessions, or multi-user support — single-session demo tool only.

---

## 4. Current Architecture (Already Built — Do Not Rebuild)

### 4.1 Backend pipeline (Python) — COMPLETE & TESTED

```
agent/
├── ingestion_agent.py   — Fetches a paper by arXiv ID, stores as Paper node in Neo4j
├── crawler_agent.py     — Recursively crawls citation network (BFS), depth + max_papers configurable
├── orchestrator.py      — LangGraph state machine wiring ingestion → crawl
└── rag_agent.py         — GraphCypherQAChain: NL question → Cypher → graph query → LLM-synthesized answer

graph/
├── neo4j_client.py      — Neo4j driver wrapper, merge_paper(), merge_citation(), run_query()
└── schema.py            — Constraints + indexes on Paper.paperId, title, year

tools/
└── semantic_scholar.py  — Fetches paper metadata + references from Semantic Scholar API
```

**Graph schema (Neo4j):**
```cypher
(:Paper {paperId, title, year, abstract, authors, url, citationCount})
(:Paper)-[:CITES]->(:Paper)
```

**Status:** Fully working. Verified end-to-end: ingestion → crawl → Neo4j storage → RAG query → correct answer, including multi-hop shortest-path queries between connected papers (e.g., BERT → Attention Is All You Need).

**Known gotcha (already solved, do not reintroduce):** Semantic Scholar's reference list order is not guaranteed — a low `max_papers` limit during crawl can silently omit well-known citations. Always use `max_papers >= 60` for the two seed demo papers (BERT, Attention) to guarantee they're connected in the graph for the shortest-path demo.

### 4.2 API layer (FastAPI) — COMPLETE & TESTED

```
api/
├── server.py     — FastAPI app: /api/ingest, /api/ask, /api/graph, /api/status
└── schemas.py    — Pydantic request/response models
```

All four endpoints tested and working via `/docs` and via the frontend. Wraps the agent pipeline above with zero changes to agent logic.

**Run command:** `python -m uvicorn api.server:app --reload --port 8000`
(Note: always use `python -m uvicorn`, not bare `uvicorn` — bare command can resolve to wrong Python environment on Windows and cause `ModuleNotFoundError` for installed packages.)

### 4.3 Frontend (HTML/CSS/JS) — COMPLETE, NEEDS QA

```
static/
├── index.html    — Landing screen + workspace screen (two-screen SPA, no router)
├── style.css     — Dark academic theme: ink (#0F1419) background, sage (#8FB39B) + amber (#D9B888) accents
└── app.js        — Fetch calls to API, vis-network graph rendering, chat logic, canvas background animation
```

**Design language (must be preserved in any new work):**
- Colors: `--ink: #0F1419`, `--ink-raised: #141A1F`, `--sage: #8FB39B`, `--amber: #D9B888`, `--text-bright: #EDEAE0`
- Fonts: Fraunces (serif headlines), Inter (UI/body), JetBrains Mono (code/IDs/data)
- Landing page: animated canvas background (drifting nodes + occasional "citation flash" trace lines) behind a headline + arXiv ID input
- Workspace: sidebar (ingestion controls) + two-panel main area (graph left, chat right)
- Graph rendered via `vis-network` (CDN), root paper highlighted in amber and larger, all other nodes in sage

**Why this stack:** Originally built in Streamlit; migrated to FastAPI + raw HTML/CSS/JS because Streamlit's component CSS could not be reliably overridden (fights with internal `data-testid` selectors, especially for sliders and the agraph component, which renders in an isolated iframe). Full control was required for the dark theme to render correctly and consistently.

---

## 5. What Is Left To Build (8 Days Remaining)

This is the actual punch list. Work top to bottom — items are roughly ordered by priority.

### 5.1 CRITICAL — Verify frontend ↔ backend integration end-to-end
**Status: in progress, currently debugging.**
- Confirm the `max_papers` slider value is correctly sent in the `/api/ingest` request payload (check via browser DevTools → Network tab). There was a suspected bug where the slider UI showed one value but the request sent a stale/default value.
- Confirm re-ingestion with `MERGE` (not `CREATE`) correctly adds missing edges without duplicating existing nodes.
- Re-verify the BERT ↔ Attention Is All You Need shortest-path demo query works end-to-end through the actual UI (not just AuraDB Browser) after re-ingesting BERT with `max_papers=100`.

### 5.2 HIGH — Sarvam AI integration (required for second sponsor track)
**Status: not started. This is the single biggest remaining scope item.**

Add to `rag_agent.py`:
- LLM provider switch: `USE_SARVAM_LLM` flag in `config.py` already scaffolded — wire it to actually call Sarvam's chat completion endpoint (`sarvam-m` model via OpenAI-compatible endpoint: `https://api.sarvam.ai/v1`) instead of Groq, when flag is true. Keep Groq as the default dev-mode LLM to conserve the ₹1,000 Sarvam credit budget.
- Add `tools/tts.py` — Bulbul V3 text-to-speech wrapper. Wire a "read answer aloud" button in the chat panel (`app.js` + a new `/api/speak` FastAPI endpoint that returns audio bytes).
- Add `tools/stt.py` — Saaras V3 speech-to-text wrapper. Add a microphone button in the chat input row that records audio, sends to a new `/api/transcribe` endpoint, and fills the chat input with the transcribed question.
- Stretch (only if time allows): Sarvan Vision OCR for uploaded scanned PDFs — not required for core demo, core demo only needs arXiv ID flow.

**Budget discipline:** Keep `USE_SARVAM_LLM=false` and `USE_SARVAM_TTS=false` during all development/testing. Only flip both to `true` during final demo recording to conserve credits.

### 5.3 MEDIUM — Frontend polish pass
- Verify the slider styling (depth, max papers) renders cleanly with no overlapping tick labels — confirm in the actual browser, not just code review.
- Verify graph readability at default zoom — with 60+ nodes (after the higher `max_papers` re-ingestion), check whether labels overlap and whether vis-network's default physics produces a readable layout, or whether `physics.stabilization.iterations` needs tuning.
- Add a loading skeleton/spinner state on the graph panel while `/api/ingest` is running (currently the button shows "Crawling…" but the graph panel itself has no loading indicator).
- Confirm the "Back to landing" button correctly resets workspace state if the user starts a second session (or explicitly decide single-session-only is fine for a hackathon demo and skip this).

### 5.4 MEDIUM — Pre-seed demo data
- Before recording the final demo, pre-ingest and verify in AuraDB: (1) Attention Is All You Need (`1706.03762`), (2) BERT (`1810.04805`, with `max_papers=100` to guarantee the citation edge to Attention exists), (3) optionally RAG (`2005.11401`) as a third demo paper.
- Do NOT rely on live API calls during the actual demo recording — Semantic Scholar API has rate limits and can be slow; pre-seeding avoids any live-demo failure risk.

### 5.5 LOW — README and submission materials
- Write README with: problem statement, the graph-vs-vector-search argument, architecture diagram, setup instructions, example Cypher queries, and screenshots of the citation graph (single-hub and multi-cluster views already captured).
- Record 90-second demo video: arXiv ID input → graph builds → ask a multi-hop question → show generated Cypher on screen → (if Sarvam TTS is wired) play spoken answer.
- Write Devfolio submission text using the core pitch: *"Other tools tell you what a paper is similar to. ScholarGraph tells you what a paper actually descends from — and proves it with a traceable path through real citation data."*

---

## 6. Key Technical Decisions (Context for any new contributor/IDE agent)

| Decision | Reasoning |
|---|---|
| Neo4j AuraDB over a vector store | Citation relationships are factual, directed, and queryable via traversal (e.g. `shortestPath()`). Vector similarity cannot express this. |
| LangGraph for orchestration | The crawl is inherently a recursive loop with a depth guard — LangGraph's `StateGraph` with conditional edges models this more cleanly than a linear LangChain chain. |
| FastAPI + raw HTML/CSS/JS over Streamlit | Streamlit's component CSS (especially sliders and the `agraph` iframe) could not be reliably restyled. Full control was needed for the custom dark theme. |
| Groq as dev-mode LLM, Sarvam reserved for demo | Sarvam credit budget (₹1,000) is generous for inference cost but should not be burned on iterative dev-loop testing. |
| `MERGE` not `CREATE` for all graph writes | Makes re-ingestion idempotent — safe to re-run ingestion with higher limits without creating duplicate nodes/edges. |
| Pre-seeded demo papers, no live API during recording | Semantic Scholar API rate limits and latency are a demo-day risk; pre-seeding eliminates it entirely. |

---

## 7. Environment Notes (To Avoid Re-Solving Already-Solved Problems)

- Python 3.13 on Windows. `numpy` must be pinned to `2.2.6` or newer (older versions fail to build on this Python version without a modern GCC).
- `langchain` must be `0.3.x` (not `0.2.x`) — `0.2.x` pins `numpy<2.0.0`, which conflicts with the numpy version above.
- Always run Python module entry points with `python -m <module>` (e.g. `python -m agent.rag_agent`, `python -m uvicorn api.server:app`) — bare commands can resolve to the wrong Python interpreter on Windows when multiple installs exist.
- AuraDB database name is **not** `neo4j` by default on the free tier — check via `SHOW DATABASES` Cypher query and set `NEO4J_DATABASE` in `.env` explicitly. (Current project's database name: `9bd9a9cd` — already set.)
- `langchain_community.graphs.Neo4jGraph` is deprecated — use `langchain_neo4j.Neo4jGraph` and `langchain_neo4j.GraphCypherQAChain` instead (`pip install langchain-neo4j==0.10.0`).
- Clear `__pycache__` directories if you see stale import errors after editing files that uvicorn's `--reload` doesn't seem to pick up.

---

## 8. Definition of Done (for the 8-day window)

- [ ] Sarvam LLM, TTS, and STT all wired and demonstrable (flip the feature flags on, confirm working)
- [ ] Full flow works with zero errors: landing → arXiv ID → workspace → graph renders → chat answers multi-hop questions correctly
- [ ] BERT ↔ Attention shortest-path demo query confirmed working through the actual UI
- [ ] 90-second demo video recorded and uploaded
- [ ] README complete with architecture diagram and example queries
- [ ] Devfolio submission written and submitted before noon on June 30 (not the midnight deadline — buffer for last-minute technical issues)
