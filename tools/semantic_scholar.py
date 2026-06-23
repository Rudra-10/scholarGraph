import time
import requests
from pydantic import BaseModel

BASE_URL = "https://api.semanticscholar.org/graph/v1"

FIELDS = "paperId,title,year,abstract,authors,url,citationCount,references"


class Paper(BaseModel):
    paperId:       str
    title:         str
    year:          int | None   = None
    abstract:      str | None   = None
    authors:       str | None   = None  # stored as comma-separated string
    url:           str | None   = None
    citationCount: int | None   = None


def _parse_paper(data: dict) -> Paper | None:
    """Safely convert raw API dict to Paper. Returns None if paperId missing."""
    if not data.get("paperId"):
        return None
    return Paper(
        paperId       = data["paperId"],
        title         = data.get("title") or "Untitled",
        year          = data.get("year"),
        abstract      = data.get("abstract"),
        authors       = ", ".join(
            a["name"] for a in (data.get("authors") or [])
        ),
        url           = data.get("url"),
        citationCount = data.get("citationCount"),
    )


def get_paper(arxiv_id: str) -> Paper | None:
    """
    Fetch a single paper by arXiv ID.
    Example: get_paper("2305.14314")
    """
    url = f"{BASE_URL}/paper/arXiv:{arxiv_id}"
    params = {"fields": FIELDS}

    response = requests.get(url, params=params)

    if response.status_code == 404:
        print(f"[SemanticScholar] Paper not found: {arxiv_id}")
        return None
    if response.status_code == 429:
        print("[SemanticScholar] Rate limited — waiting 10s...")
        time.sleep(10)
        return get_paper(arxiv_id)

    response.raise_for_status()
    return _parse_paper(response.json())


def get_references(paper_id: str, limit: int = 50) -> list[Paper]:
    """
    Fetch all references (papers this paper cites) by Semantic Scholar paperId.
    """
    url = f"{BASE_URL}/paper/{paper_id}/references"
    params = {"fields": "paperId,title,year,abstract,authors,url,citationCount", "limit": limit}

    response = requests.get(url, params=params)

    if response.status_code == 429:
        print("[SemanticScholar] Rate limited — waiting 10s...")
        time.sleep(10)
        return get_references(paper_id, limit)

    response.raise_for_status()
    data = response.json()

    papers = []
    for item in (data.get("data") or []):
        cited = item.get("citedPaper", {})
        paper = _parse_paper(cited)
        if paper:
            papers.append(paper)

    return papers


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching 'Attention Is All You Need'...")
    paper = get_paper("1706.03762")

    if paper:
        print(f"\nTitle:    {paper.title}")
        print(f"Year:     {paper.year}")
        print(f"Authors:  {paper.authors}")
        print(f"Citations:{paper.citationCount}")

        print(f"\nFetching references...")
        refs = get_references(paper.paperId, limit=10)
        print(f"Found {len(refs)} references. First 3:")
        for r in refs[:3]:
            print(f"  - [{r.year}] {r.title}")
    else:
        print("Paper not found.")