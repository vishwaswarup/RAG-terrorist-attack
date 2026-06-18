import os 
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.retrieval_engine import RetrievalEngine
from rag.rag_engine import RAGEngine

retrieval = RetrievalEngine()
rag = RAGEngine(retrieval)
    
query = input("\nQuery: ")


answer, results = rag.query(query)

print("\n===== RETRIEVED INCIDENTS =====")
for r in results:
    print(f"{r.score:.4f} - {r.incident.date} - {r.incident.city}")

print("\n================ ANSWER ================\n")
print(answer)
print("\n========================================\n")