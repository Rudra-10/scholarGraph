from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def verify_connection(self):
        with self.driver.session() as session:
            result = session.run("RETURN 'ScholarGraph connected!' AS msg")
            return result.single()["msg"]

    def run_query(self, query: str, params: dict = {}):
        with self.driver.session() as session:
            result = session.run(query, params)
            return [record.data() for record in result]

    def merge_paper(self, paper: dict):
        query = """
        MERGE (p:Paper {paperId: $paperId})
        SET p.title         = $title,
            p.year          = $year,
            p.abstract      = $abstract,
            p.authors       = $authors,
            p.url           = $url,
            p.citationCount = $citationCount
        RETURN p.paperId AS id
        """
        return self.run_query(query, paper)

    def merge_citation(self, from_id: str, to_id: str):
        query = """
        MATCH (a:Paper {paperId: $from_id})
        MATCH (b:Paper {paperId: $to_id})
        MERGE (a)-[:CITES]->(b)
        """
        return self.run_query(query, {"from_id": from_id, "to_id": to_id})

    def get_paper_by_arxiv_id(self, arxiv_id: str) -> dict | None:
        query = """
        MATCH (p:Paper)
        WHERE p.url CONTAINS $arxiv_id
        RETURN p LIMIT 1
        """
        records = self.run_query(query, {"arxiv_id": arxiv_id})
        if records:
            # records contains dicts, "p" is the properties dict returned by Neo4j driver
            return records[0]["p"]
        return None

    def get_local_references(self, paper_id: str) -> list[dict]:
        query = """
        MATCH (p:Paper {paperId: $paper_id})-[:CITES]->(ref:Paper)
        RETURN ref
        """
        records = self.run_query(query, {"paper_id": paper_id})
        return [r["ref"] for r in records]


if __name__ == "__main__":
    client = Neo4jClient()
    print(client.verify_connection())
    client.close()