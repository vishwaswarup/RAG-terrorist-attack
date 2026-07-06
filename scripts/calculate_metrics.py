import time
from retrieval.embedding_service import EmbeddingService
from retrieval.retrieval_engine import RetrievalEngine
from rag.llm_client import LLMClient
import sys

print("Loading models...")
embedder = EmbeddingService()
retriever = RetrievalEngine()
llm = LLMClient()
print("Models loaded.\n")

# 1. Embedding generation throughput
print("--- 1. Embedding Throughput ---")
dummy_texts = ["The quick brown fox jumps over the lazy dog. " * 5 for _ in range(100)]
t0 = time.perf_counter()
embedder.embed_documents(dummy_texts)
t1 = time.perf_counter()
elapsed = t1 - t0
throughput = len(dummy_texts) / elapsed
print(f"Time taken to embed {len(dummy_texts)} documents: {elapsed:.4f}s")
print(f"Embedding Throughput: {throughput:.2f} incidents/sec\n")

# 2. Average query retrieval latency
print("--- 2. Query Retrieval Latency ---")
queries = [
    "What terrorist groups are active in Kashmir?",
    "Summarize the Pulwama attack",
    "Show me attacks involving IEDs",
    "Are there any incidents with high casualties?",
    "Tell me about Naxalite activity in Chhattisgarh"
]
latencies = []
for q in queries:
    t0 = time.perf_counter()
    retriever.search(q, top_k=5)
    t1 = time.perf_counter()
    latencies.append(t1 - t0)

avg_latency = sum(latencies) / len(latencies)
print(f"Average Retrieval Latency (across {len(queries)} queries): {avg_latency:.4f}s\n")

# 3. Average LLM inference time (Qwen3:8B)
print("--- 3. LLM Inference Time ---")
prompts = [
    "Summarize the events of the 2008 Mumbai attacks in two sentences.",
    "List three common methods used by insurgents.",
    "Explain the geopolitical impact of the Pulwama attack briefly."
]
llm_times = []
try:
    for p in prompts:
        t0 = time.perf_counter()
        llm.generate(p)
        t1 = time.perf_counter()
        llm_times.append(t1 - t0)
    
    avg_llm_time = sum(llm_times) / len(llm_times)
    print(f"Average LLM Inference Time (across {len(prompts)} prompts): {avg_llm_time:.4f}s\n")
except Exception as e:
    print(f"LLM Error: {e}")

