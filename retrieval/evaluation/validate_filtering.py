"""
Validates the similarity-window filtering by comparing
unfiltered (top_k=10) vs filtered results for benchmark queries.
"""
import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from retrieval.retrieval_engine import RetrievalEngine

QUERIES = [
    "Pulwama bombing",
    "Uri attack",
    "JeM attacks in Kashmir",
    "Maoist attacks in Chhattisgarh",
    "Bombing attacks on police",
]

def main():
    engine = RetrievalEngine()

    for query in QUERIES:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")

        # Unfiltered: disable window by passing None
        unfiltered = engine.search(query, top_k=10, similarity_window=None)
        # Filtered: use default window (0.05)
        filtered = engine.search(query, top_k=10, similarity_window=0.05)

        print(f"\n  UNFILTERED (all 10 candidates):")
        for rank, r in enumerate(unfiltered, 1):
            inc = r.incident
            label = f"{inc.city or inc.state or inc.country} | {', '.join(inc.attack_types)} | {', '.join(inc.responsible_groups)}"
            print(f"    Rank {rank:2d}  score={r.score:.4f}  {label}")

        print(f"\n  FILTERED (window=0.05):")
        for rank, r in enumerate(filtered, 1):
            inc = r.incident
            label = f"{inc.city or inc.state or inc.country} | {', '.join(inc.attack_types)} | {', '.join(inc.responsible_groups)}"
            print(f"    Rank {rank:2d}  score={r.score:.4f}  {label}")

        score_drop = unfiltered[0].score - unfiltered[-1].score if unfiltered else 0
        print(f"\n  Score spread (best-worst): {score_drop:.4f}")
        print(f"  Candidates: {len(unfiltered)} → Filtered: {len(filtered)}")

if __name__ == "__main__":
    main()
