import logging
import sys
import os

# Ensure the root directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from retrieval.chroma_manager import ChromaManager
from retrieval.embedding_service import EmbeddingService
from retrieval.retrieval_engine import RetrievalEngine
from rag.rag_engine import RAGEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    print("Loading Offline Services...")
    retrieval_engine = RetrievalEngine()
    
    # 3000 tokens * 4 chars = 12000 chars limit
    rag_engine = RAGEngine(retrieval_engine, model_name="phi3:mini", max_context_tokens=3000)

    queries = [
        "Summarize the attack patterns used by JeM in Kashmir based on the retrieved incidents.",
        "What are the most common targets for Maoist attacks in Chhattisgarh?"
    ]

    for q in queries:
        print("\n" + "="*80)
        print(f"QUERY: {q}")
        print("="*80)
        
        try:
            # We use a tighter window for RAG to avoid context contamination
            response = rag_engine.query(q, top_k=10, similarity_window=0.05)
            print("\nSYNTHESIS:\n")
            print(response)
        except Exception as e:
            print(f"RAG Engine failed: {e}")

if __name__ == "__main__":
    main()
