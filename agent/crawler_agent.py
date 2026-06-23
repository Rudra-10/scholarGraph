import time
from tools.semantic_scholar import get_references, Paper
from graph.neo4j_client import Neo4jClient
from agent.ingestion_agent import IngestionAgent


class CrawlerAgent:
    def __init__(self, max_depth: int = 2, max_papers: int = 100):
        self.max_depth   = max_depth
        self.max_papers  = max_papers
        self.visited     = set()        # paperId → already processed
        self.ingestion   = IngestionAgent()
        self.client      = self.ingestion.client
        self.paper_count = 0

    def close(self):
        self.ingestion.close()

    def _should_stop(self) -> bool:
        return self.paper_count >= self.max_papers

    def _get_references_local_or_remote(self, paper_id: str) -> tuple[list[Paper], bool]:
        """
        Check Neo4j for cached references of the given paper first.
        Returns a list of Paper models and a boolean flag indicating if it was a remote fetch.
        """
        local_refs_data = self.client.get_local_references(paper_id)
        if local_refs_data:
            print(f"  [Crawler] Loaded {len(local_refs_data)} references from Neo4j (Offline)")
            papers = [
                Paper(
                    paperId=r.get("paperId"),
                    title=r.get("title", "Untitled"),
                    year=r.get("year"),
                    abstract=r.get("abstract"),
                    authors=r.get("authors"),
                    url=r.get("url"),
                    citationCount=r.get("citationCount"),
                )
                for r in local_refs_data
            ]
            return papers, False

        # Fallback to live API
        print(f"  [Crawler] Fetching references from Semantic Scholar API...")
        return get_references(paper_id, limit=15), True

    def crawl(self, paper: Paper, current_depth: int = 0):
        """
        Recursively crawl citations from a root paper.
        Stores every discovered paper + CITES edge in Neo4j.
        """
        if current_depth >= self.max_depth:
            return
        if self._should_stop():
            print(f"\n[Crawler] Reached max papers limit ({self.max_papers}). Stopping.")
            return
        if paper.paperId in self.visited:
            return

        self.visited.add(paper.paperId)

        print(f"\n[Crawler] Depth {current_depth+1}/{self.max_depth} — {paper.title[:55]}")
        print(f"          Papers crawled so far: {self.paper_count}/{self.max_papers}")

        references, is_remote = self._get_references_local_or_remote(paper.paperId)
        if is_remote:
            time.sleep(1)   # gentle rate limit buffer only for live API calls

        for ref in references:
            if self._should_stop():
                break
            if ref.paperId in self.visited:
                continue

            # Store node + edge
            self.ingestion.client.merge_paper(
                self.ingestion._paper_to_dict(ref)
            )
            self.ingestion.client.merge_citation(paper.paperId, ref.paperId)
            self.paper_count += 1
            print(f"  ✓ [{ref.year or '?'}] {ref.title[:60]}")

            # Recurse
            self.crawl(ref, current_depth + 1)

    def run(self, root_paper: Paper) -> dict:
        """
        Entry point. Takes an already-ingested root Paper
        and crawls its citation network.
        """
        print(f"\n[Crawler] Starting crawl from: {root_paper.title[:55]}")
        print(f"          Max depth: {self.max_depth} | Max papers: {self.max_papers}")

        self.crawl(root_paper, current_depth=0)

        result = {
            "root":          root_paper.title,
            "papers_stored": self.paper_count,
            "unique_visited": len(self.visited),
        }

        print(f"\n[Crawler] ✅ Crawl complete")
        print(f"          Papers stored : {result['papers_stored']}")
        print(f"          Nodes visited : {result['unique_visited']}")
        return result


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    from tools.semantic_scholar import get_paper

    # Fetch root paper first
    root = get_paper("1706.03762")   # Attention Is All You Need

    if root:
        # Store root node first
        agent = CrawlerAgent(max_depth=2, max_papers=40)
        agent.ingestion.client.merge_paper(
            agent.ingestion._paper_to_dict(root)
        )
        agent.run(root)
        agent.close()