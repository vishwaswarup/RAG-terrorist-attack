# test_retrieval.py
import sys 
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from retrieval.retrieval_engine import RetrievalEngine

engine = RetrievalEngine()

queries = [
    "2008 mumbai terror attacks",
    "JeM attacks in Kashmir",
    "Maoist attacks in Chhattisgarh"
]

for q in queries:
    print(f"\n================ QUERY: {q} ================")
    results = engine.search(q, top_k=20)
    for i, result in enumerate(results, start=1):
        print(f"[{i}] Score: {result.score:.3f} | Date: {result.incident.date} | Loc: {result.incident.city}, {result.incident.state} | Group: {', '.join(result.incident.responsible_groups)}")
    print("========================================================================\n")