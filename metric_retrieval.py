import time
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from retrieval.retrieval_engine import RetrievalEngine

print("Loading retrieval engine...")
retriever = RetrievalEngine()

print("--- 2. Query Retrieval Latency ---")
queries = [
    "Lashkar-e-Taiba bombing in Kashmir 2018",
    "IED blast targeting CRPF convoy",
    "Maoist ambush in Chhattisgarh",
    "Assassination of political leader in Punjab",
    "Grenade attack in Srinagar market"
]
total_latency = 0
for q in queries:
    t0 = time.perf_counter()
    retriever.search(q, top_k=5)
    t1 = time.perf_counter()
    total_latency += (t1 - t0)

avg_latency = total_latency / len(queries)
print(f"Average Query Retrieval Latency: {avg_latency:.4f}s")
