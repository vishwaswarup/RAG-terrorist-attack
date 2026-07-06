import time
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from rag.llm_client import LLMClient

print("Loading LLM client...")
llm = LLMClient()

print("--- 3. LLM Inference Time ---")
t0 = time.perf_counter()
response = llm.generate("Summarize the impact of IED blasts in 1 sentence.", system_prompt="You are a helpful assistant.")
t1 = time.perf_counter()
elapsed = t1 - t0

print(f"Average LLM Inference Time (Qwen3:8B): {elapsed:.4f}s")
