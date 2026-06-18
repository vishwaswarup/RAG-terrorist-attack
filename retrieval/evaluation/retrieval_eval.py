import os
import sys
import logging
from typing import Callable, List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.retrieval_engine import RetrievalEngine
from models.incident import Incident

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def contains_any(expected_keywords: List[str], actual_list: List[str]) -> bool:
    if not actual_list:
        return False
    actual_lower = [a.lower() for a in actual_list]
    for k in expected_keywords:
        for a in actual_lower:
            if k.lower() in a:
                return True
    return False

# Benchmark Dataset: Query -> Expectation Function
# The expectation function returns True if the given Incident is considered a "relevant hit".
BENCHMARK_QUERIES = [
    {
        "query": "Pulwama bombing",
        "is_relevant": lambda i: "pulwama" in i.city.lower() and contains_any(["bombing", "explosion"], i.attack_types)
    },
    {
        "query": "Maoist attacks in Chhattisgarh",
        "is_relevant": lambda i: "chhattisgarh" in i.state.lower() and contains_any(["maoist"], i.responsible_groups)
    },
    {
        "query": "Grenade attacks on police",
        "is_relevant": lambda i: contains_any(["grenade"], i.summary.lower().split() + i.weapon_types) and contains_any(["police", "government"], i.target_types + i.summary.lower().split())
    },
    {
        "query": "JeM attacks in Kashmir",
        "is_relevant": lambda i: ("kashmir" in i.state.lower() or "jammu" in i.state.lower()) and contains_any(["jaish-e-mohammad", "jem"], i.responsible_groups + i.summary.lower().split())
    },
    {
        "query": "Attacks using explosives",
        "is_relevant": lambda i: contains_any(["explosives", "bombing"], i.weapon_types + i.attack_types)
    }
]

def evaluate_retrieval(collection_name: str = "incidents"):
    logging.info("Initializing RetrievalEngine for Evaluation...")
    engine = RetrievalEngine(collection_name=collection_name)
    
    metrics = {
        "mrr": 0.0,
        "recall_at_1": 0.0,
        "recall_at_5": 0.0,
        "recall_at_10": 0.0
    }
    
    total_queries = len(BENCHMARK_QUERIES)
    
    print("\n=== Retrieval Evaluation ===")
    
    for item in BENCHMARK_QUERIES:
        query = item["query"]
        is_relevant_fn = item["is_relevant"]
        
        # We query top 10 to measure Recall@1, 5, 10
        results = engine.search(query, top_k=10)
        
        # Evaluate ranks
        relevant_ranks = []
        for rank, result in enumerate(results, start=1):
            if is_relevant_fn(result.incident):
                relevant_ranks.append(rank)
                
        first_relevant_rank = relevant_ranks[0] if relevant_ranks else None
        
        print(f"\nQuery: '{query}'")
        if first_relevant_rank:
            print(f"  First relevant result found at Rank: {first_relevant_rank}")
            print(f"  Total relevant in Top 10: {len(relevant_ranks)}")
        else:
            print(f"  No relevant results found in Top 10.")
            
        # Update metrics
        if first_relevant_rank:
            metrics["mrr"] += 1.0 / first_relevant_rank
            if first_relevant_rank == 1:
                metrics["recall_at_1"] += 1
            if first_relevant_rank <= 5:
                metrics["recall_at_5"] += 1
            if first_relevant_rank <= 10:
                metrics["recall_at_10"] += 1
                
    # Averages
    mrr = metrics["mrr"] / total_queries
    r_at_1 = metrics["recall_at_1"] / total_queries
    r_at_5 = metrics["recall_at_5"] / total_queries
    r_at_10 = metrics["recall_at_10"] / total_queries
    
    print("\n=== Summary Metrics ===")
    print(f"Total Queries : {total_queries}")
    print(f"MRR           : {mrr:.3f}")
    print(f"Recall@1      : {r_at_1:.3f}")
    print(f"Recall@5      : {r_at_5:.3f}")
    print(f"Recall@10     : {r_at_10:.3f}")

if __name__ == "__main__":
    evaluate_retrieval()
