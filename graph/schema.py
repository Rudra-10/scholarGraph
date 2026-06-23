from graph.neo4j_client import Neo4jClient


def create_schema():
    client = Neo4jClient()

    statements = [
        "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.paperId IS UNIQUE",
        "CREATE INDEX paper_title IF NOT EXISTS FOR (p:Paper) ON (p.title)",
        "CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year)",
    ]

    for stmt in statements:
        client.run_query(stmt)
        print(f"✓ Done: {stmt[:60]}...")

    client.close()
    print("\nSchema ready.")


if __name__ == "__main__":
    create_schema()