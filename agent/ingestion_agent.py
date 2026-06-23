from tools.semantic_scholar import get_paper, get_references, Paper
from graph.neo4j_client import Neo4jClient


class IngestionAgent:
    def __init__(self):
        self.client = Neo4jClient()

    def close(self):
        self.client.close()

    def _paper_to_dict(self, paper: Paper) -> dict:
        return {
            "paperId":      paper.paperId,
            "title":        paper.title,
            "year":         paper.year or 0,
            "abstract":     paper.abstract or "",
            "authors":      paper.authors or "",
            "url":          paper.url or "",
            "citationCount": paper.citationCount or 0,
        }

    def ingest_paper(self, arxiv_id: str) -> Paper | None:
        """
        Fetch a paper by arXiv ID and write it to Neo4j.
        Returns the Paper object or None if not found.
        Checks Neo4j first before making network requests.
        """
        print(f"\n[Ingestion] Fetching paper: arXiv:{arxiv_id}")
        
        # Check local DB first
        local_paper_data = self.client.get_paper_by_arxiv_id(arxiv_id)
        if local_paper_data:
            print(f"[Ingestion] ✓ Found paper in local database (Offline)")
            return Paper(
                paperId=local_paper_data.get("paperId"),
                title=local_paper_data.get("title", "Untitled"),
                year=local_paper_data.get("year"),
                abstract=local_paper_data.get("abstract"),
                authors=local_paper_data.get("authors"),
                url=local_paper_data.get("url"),
                citationCount=local_paper_data.get("citationCount"),
            )

        # Fallback to network
        paper = get_paper(arxiv_id)

        if not paper:
            print(f"[Ingestion] Paper not found: {arxiv_id}")
            return None

        self.client.merge_paper(self._paper_to_dict(paper))
        print(f"[Ingestion] ✓ Stored: {paper.title[:60]}")
        return paper

    def ingest_references(self, paper: Paper, depth: int = 1, current_depth: int = 0):
        """
        Recursively fetch and store references up to `depth` hops.
        """
        if current_depth >= depth:
            return

        print(f"\n[Ingestion] Fetching references for: {paper.title[:50]}... (depth {current_depth+1}/{depth})")
        references = get_references(paper.paperId, limit=20)
        print(f"[Ingestion] Found {len(references)} references")

        for ref in references:
            # Store the referenced paper node
            self.client.merge_paper(self._paper_to_dict(ref))
            # Store the CITES edge
            self.client.merge_citation(paper.paperId, ref.paperId)
            print(f"  ✓ {ref.year or '?'} — {ref.title[:55]}")

            # Recurse deeper if needed
            if current_depth + 1 < depth:
                self.ingest_references(ref, depth, current_depth + 1)

    def run(self, arxiv_id: str, depth: int = 1) -> Paper | None:
        """
        Full ingestion pipeline:
        1. Fetch + store root paper
        2. Recursively fetch + store references to given depth
        """
        paper = self.ingest_paper(arxiv_id)
        if not paper:
            return None

        self.ingest_references(paper, depth=depth)
        print(f"\n[Ingestion] ✅ Complete — graph written to AuraDB")
        return paper


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    agent = IngestionAgent()
    # Attention Is All You Need — depth 1 means root + its direct references
    agent.run("1706.03762", depth=1)
    agent.close()