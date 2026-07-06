"""Diagnostic: Run benchmark queries and show raw retrieval results."""
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


import os, sys
from dotenv import load_dotenv
load_dotenv()



from retrieval.retrieval_engine import RetrievalEngine
from models.image_asset import ImageAsset

engine = RetrievalEngine()

BENCHMARK_QUERIES = [
    "Who was responsible behind the 2001 Indian Parliament Attack?",
    "Tell me about the 2008 Mumbai Attack",
    "JeM attacks in Kashmir",
    "Maoist attacks in Chhattisgarh",
    "Show terrorist attacks near Srinagar",
    "List suicide bombings",
    "Compare Pulwama and Uri attacks",
    "Show attacks involving explosives",
    "Find attacks targeting police",
    "Summarize terrorist activity in Jammu and Kashmir",
]

for q in BENCHMARK_QUERIES:
    print(f"\n{'='*80}")
    print(f"QUERY: {q}")
    print(f"{'='*80}")
    results = engine.search(q, top_k=10, similarity_window=0.05)
    print(f"  Retrieved: {len(results)} results")
    for i, r in enumerate(results):
        if isinstance(r.payload, ImageAsset):
            print(f"  [{i+1}] score={r.score:.4f} IMAGE: {r.payload.filename}")
        else:
            inc = r.payload
            print(f"  [{i+1}] score={r.score:.4f} | {inc.date} | {inc.city}, {inc.state} | groups={inc.responsible_groups} | attack={inc.attack_types} | killed={inc.killed}")
    print()
