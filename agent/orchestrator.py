from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from tools.semantic_scholar import get_paper, Paper
from agent.ingestion_agent import IngestionAgent
from agent.crawler_agent import CrawlerAgent


# ── State schema ──────────────────────────────────────────────
class ScholarState(TypedDict):
    arxiv_id:     str
    depth:        int
    max_papers:   int
    root_paper:   Optional[dict]   # Paper as dict for serialization
    crawl_result: Optional[dict]
    error:        Optional[str]
    status:       str              # "ingesting" | "crawling" | "done" | "error"


# ── Node functions ────────────────────────────────────────────
def ingest_node(state: ScholarState) -> ScholarState:
    """Node 1: Fetch root paper and store in Neo4j."""
    print(f"\n[Orchestrator] INGEST — arXiv:{state['arxiv_id']}")

    try:
        agent = IngestionAgent()
        paper = agent.ingest_paper(state["arxiv_id"])
        agent.close()

        if not paper:
            return {**state, "error": f"Paper not found: {state['arxiv_id']}", "status": "error"}

        return {
            **state,
            "root_paper": paper.model_dump(),
            "status": "crawling",
            "error": None,
        }

    except Exception as e:
        return {**state, "error": str(e), "status": "error"}


def crawl_node(state: ScholarState) -> ScholarState:
    """Node 2: Recursively crawl citation network."""
    print(f"\n[Orchestrator] CRAWL — depth={state['depth']}, max={state['max_papers']}")

    try:
        root = Paper(**state["root_paper"])

        crawler = CrawlerAgent(
            max_depth=state["depth"],
            max_papers=state["max_papers"]
        )
        # Root node already stored by ingest_node
        crawler.ingestion.client.merge_paper(
            crawler.ingestion._paper_to_dict(root)
        )
        result = crawler.run(root)
        crawler.close()

        return {
            **state,
            "crawl_result": result,
            "status": "done",
            "error": None,
        }

    except Exception as e:
        return {**state, "error": str(e), "status": "error"}


# ── Conditional edge ──────────────────────────────────────────
def should_crawl(state: ScholarState) -> str:
    if state["status"] == "error":
        return "error"
    return "crawl"


# ── Build graph ───────────────────────────────────────────────
def build_graph() -> StateGraph:
    graph = StateGraph(ScholarState)

    graph.add_node("ingest", ingest_node)
    graph.add_node("crawl",  crawl_node)

    graph.set_entry_point("ingest")

    graph.add_conditional_edges(
        "ingest",
        should_crawl,
        {"crawl": "crawl", "error": END}
    )
    graph.add_edge("crawl", END)

    return graph.compile()


def run_pipeline(arxiv_id: str, depth: int = 2, max_papers: int = 50) -> dict:
    """Main entry point for the full ScholarGraph pipeline."""
    app = build_graph()

    initial_state: ScholarState = {
        "arxiv_id":     arxiv_id,
        "depth":        depth,
        "max_papers":   max_papers,
        "root_paper":   None,
        "crawl_result": None,
        "error":        None,
        "status":       "ingesting",
    }

    final_state = app.invoke(initial_state)

    if final_state["status"] == "error":
        print(f"\n[Orchestrator] ❌ Error: {final_state['error']}")
    else:
        print(f"\n[Orchestrator] ✅ Pipeline complete")
        print(f"  Root   : {final_state['root_paper']['title']}")
        print(f"  Stored : {final_state['crawl_result']['papers_stored']} papers")

    return final_state


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    # BERT paper — fresh test with a different paper
    result = run_pipeline("1810.04805", depth=1, max_papers=25)