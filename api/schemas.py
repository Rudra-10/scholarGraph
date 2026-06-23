from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    arxiv_id: str
    depth: int = 1
    max_papers: int = 30


class IngestResponse(BaseModel):
    status: str               # "success" | "error"
    root_title: Optional[str] = None
    papers_stored: Optional[int] = None
    error: Optional[str] = None


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    cypher: Optional[str] = None


class GraphNode(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    is_root: bool = False


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SpeakRequest(BaseModel):
    text: str