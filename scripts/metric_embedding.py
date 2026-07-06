import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
from retrieval.embedding_service import EmbeddingService

print("Loading embedding model...")
embedder = EmbeddingService()

print("--- 1. Embedding Throughput ---")
# 100 texts of length roughly equivalent to typical incident descriptions
dummy_texts = ["The quick brown fox jumps over the lazy dog. " * 5 for _ in range(100)]
t0 = time.perf_counter()
embedder.embed_documents(dummy_texts)
t1 = time.perf_counter()
elapsed = t1 - t0
throughput = len(dummy_texts) / elapsed
print(f"Embedding Throughput: {throughput:.2f} incidents/sec")
print(f"Time taken to embed {len(dummy_texts)} documents: {elapsed:.4f}s")
