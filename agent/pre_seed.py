import sys
import os
import time

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import run_pipeline


def print_seed_result(name: str, res: dict):
    if not res:
        print(f"Failed to seed {name}: No response state returned.")
        return
    status = res.get("status")
    if status == "error":
        print(f"Failed to seed {name}: {res.get('error')}")
    else:
        crawl_res = res.get("crawl_result") or {}
        print(f"{name} seeded: {status}. Crawled {crawl_res.get('papers_stored', 0)} references.")


def main():
    print("=" * 60)
    print("        ScholarGraph Database Pre-Seeding Utility")
    print("=" * 60)
    print("This script crawls and seeds Neo4j with the main demo papers")
    print("to avoid live Semantic Scholar API rate limits or latency.")
    print("-" * 60)

    # 1. Ingest Attention Is All You Need
    print("\n>>> Seeding [1/3]: Attention Is All You Need (arXiv:1706.03762)...")
    try:
        res1 = run_pipeline("1706.03762", depth=1, max_papers=30)
        print_seed_result("Attention", res1)
    except Exception as e:
        print(f"Failed to seed Attention: {e}")

    # Gentle cooldown to respect rate limits
    time.sleep(2)

    # 2. Ingest BERT (max_papers=100 to guarantee CITES link to Attention)
    print("\n>>> Seeding [2/3]: BERT (arXiv:1810.04805)...")
    try:
        res2 = run_pipeline("1810.04805", depth=2, max_papers=100)
        print_seed_result("BERT", res2)
    except Exception as e:
        print(f"Failed to seed BERT: {e}")

    # Gentle cooldown to respect rate limits
    time.sleep(2)

    # 3. Ingest RAG (Retrieval-Augmented Generation)
    print("\n>>> Seeding [3/3]: Retrieval-Augmented Generation (arXiv:2005.11401)...")
    try:
        res3 = run_pipeline("2005.11401", depth=1, max_papers=30)
        print_seed_result("RAG", res3)
    except Exception as e:
        print(f"Failed to seed RAG: {e}")

    print("\n" + "=" * 60)
    print("Pre-seeding completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
