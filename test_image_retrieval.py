import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.retrieval_engine import RetrievalEngine

def test_retrieval():
    print("Initializing RetrievalEngine...")
    engine = RetrievalEngine(collection_names=["incidents", "incidents_images"])
    print("Testing query...")
    results = engine.search("Find images of rifles", top_k=5, similarity_window=None)
    print(f"Got {len(results)} results:")
    for res in results:
        payload = res.payload
        score = res.score
        if hasattr(payload, 'filename'):
            print(f"IMAGE: {payload.filename} (Score: {score:.3f}) - Caption: {payload.caption}")
        else:
            print(f"INCIDENT: {payload.date} in {payload.city} (Score: {score:.3f})")

if __name__ == "__main__":
    test_retrieval()
