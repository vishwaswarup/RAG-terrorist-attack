import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import os


from rag.llm_client import LLMClient

print("Loading LLM client...")
llm = LLMClient()

print("--- 3. LLM Inference Time ---")
t0 = time.perf_counter()
response = llm.generate("Summarize the impact of IED blasts in 1 sentence.", system_prompt="You are a helpful assistant.")
t1 = time.perf_counter()
elapsed = t1 - t0

print(f"Average LLM Inference Time (Qwen3:8B): {elapsed:.4f}s")
