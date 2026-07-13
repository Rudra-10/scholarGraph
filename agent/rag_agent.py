# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
# pyrefly: ignore [missing-import]
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain.prompts import PromptTemplate
from config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE,
    GROQ_API_KEY, SARVAM_API_KEY, USE_SARVAM_LLM
)


CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
You are an expert Neo4j Cypher query generator for a research citation graph.

Graph schema:
{schema}

Node labels: Paper
Node properties: paperId, title, year, abstract, authors, citationCount, url
Relationship: (Paper)-[:CITES]->(Paper) means "this paper cites that paper"

Rules:
- For title matching, ALWAYS use case-insensitive matching. Use toLower(p.title) CONTAINS 'lowercase_term' or case-insensitive regex to avoid missing papers due to capitalization.
- For short acronyms or titles (e.g., 'BERT', 'RAG'), ALWAYS use case-insensitive regex word boundaries to prevent matching sub-strings in other words. Example: WHERE p.title =~ '(?i).*\\\\bBERT\\\\b.*'
- For "foundational" or "must read" → find papers with highest in-degree (most cited)
- For "path" questions → use shortestPath() and find start/end nodes using a case-insensitive WHERE clause. Example: MATCH (a:Paper), (b:Paper) WHERE toLower(a.title) CONTAINS 'bert' AND toLower(b.title) CONTAINS 'attention is all you need' MATCH path = shortestPath((a)-[:CITES*]-(b)) RETURN [n IN nodes(path) | n.title + ' (' + n.year + ')'] AS citation_chain
- For "influenced by" → traverse [:CITES] outward from the paper
- For "what cites X" → traverse [:CITES] inward to the paper
- Always RETURN paper titles and years
- LIMIT results to 10 unless asked otherwise
- Never use APOC procedures

Question: {question}
Cypher query (no explanation, just the query):
"""
)

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are ScholarGraph, an intelligent research assistant.
You queried a citation knowledge graph and received:

{context}

Answer this question clearly and concisely:
{question}

- Reference specific paper titles and years from the results
- If results are empty, say "No papers found matching that query in the current graph"
- Keep the answer under 150 words
"""
)


class RAGAgent:
    def __init__(self, database: str = None):
        self.graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            database=database or NEO4J_DATABASE,
            enhanced_schema=False,
        )

        if USE_SARVAM_LLM:
            print("[RAG] Using Sarvam LLM")
            self.llm = ChatOpenAI(
                model="sarvam-30b",
                openai_api_base="https://api.sarvam.ai/v1",
                openai_api_key=SARVAM_API_KEY,
                temperature=0,
            )
        else:
            print("[RAG] Using Groq LLM (dev mode)")
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=GROQ_API_KEY,
                temperature=0,
            )

        # Define LLM for Cypher query generation (use Groq if available for code precision, otherwise fallback)
        if GROQ_API_KEY:
            print("[RAG] Using Groq LLM for Cypher query generation")
            cypher_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=GROQ_API_KEY,
                temperature=0,
            )
        else:
            print("[RAG] Falling back to primary LLM for Cypher query generation")
            cypher_llm = self.llm

        self.chain = GraphCypherQAChain.from_llm(
            cypher_llm=cypher_llm,
            qa_llm=self.llm,
            graph=self.graph,
            cypher_prompt=CYPHER_PROMPT,
            qa_prompt=QA_PROMPT,
            verbose=True,
            allow_dangerous_requests=True,
            return_intermediate_steps=True,
        )

    def ask(self, question: str) -> dict:
        print(f"\n[RAG] Question: {question}")
        try:
            result = self.chain.invoke({"query": question})
            answer = result.get("result", "No answer generated.")
            
            # Extract generated Cypher query safely
            cypher = None
            steps = result.get("intermediate_steps")
            if steps and len(steps) > 0:
                cypher = steps[0].get("query")

            print(f"[RAG] Cypher: {cypher}")
            print(f"[RAG] Answer: {answer}")
            return {"answer": answer, "cypher": cypher}
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[RAG]  {error_msg}")
            return {"answer": error_msg, "cypher": None}


if __name__ == "__main__":
    agent = RAGAgent()

    questions = [
        "What papers does BERT cite?",
        "What is the most cited paper in the graph?",
        "What papers were published in 2017?",
    ]

    for q in questions:
        print("\n" + "="*60)
        agent.ask(q)