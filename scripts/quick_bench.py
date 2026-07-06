import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import os
import gc
import torch

from ingestion.txt_ingestor import extract_txt
from ingestion.image_ingestor import extract_image_text
from ingestion.scanned_pdf_ingestor import extract_scanned_pdf
from retrieval.embedding_service import EmbeddingService
from retrieval.retrieval_engine import RetrievalEngine
from rag.llm_client import LLMClient
from PIL import Image, ImageDraw, ImageFont

txt_path = "benchmark_test.txt"
with open(txt_path, "w") as f:
    f.write("This is a benchmark test file. " * 100)
img_path = "benchmark_test.png"
img = Image.new('RGB', (800, 600), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((50, 50), "Benchmark Test Image OCR", fill=(0, 0, 0))
img.save(img_path)
pdf_path = "benchmark_test.pdf"
img.save(pdf_path, "PDF", resolution=100.0, save_all=True)

print("Starting Quick Bench...")
results = {}

t0 = time.perf_counter()
extract_txt(txt_path)
results["TXT Ingestion"] = time.perf_counter() - t0
print("TXT Done")

try:
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    t0 = time.perf_counter()
    extract_image_text(img_path)
    results["Image OCR Ingestion"] = time.perf_counter() - t0
    print("Image OCR Done")
except Exception as e:
    print(f"Image OCR Failed: {e}")
    results["Image OCR Ingestion"] = 0.0

try:
    t0 = time.perf_counter()
    extract_scanned_pdf(pdf_path)
    results["PDF OCR Ingestion"] = time.perf_counter() - t0
    print("PDF OCR Done")
except Exception as e:
    print(f"PDF OCR Failed: {e}")
    results["PDF OCR Ingestion"] = 0.0

embedder = EmbeddingService()
test_texts = ["This is a test incident summary regarding an explosion."] * 50
t0 = time.perf_counter()
embedder.embed_queries(test_texts)
total_time = time.perf_counter() - t0
results["Embedding Throughput (incidents/sec)"] = 50 / total_time
print("Embedding Done")

retrieval = RetrievalEngine()
t0 = time.perf_counter()
retrieval.search("bombing in Mumbai", top_k=10)
results["Retrieval Latency"] = time.perf_counter() - t0
print("Retrieval Done")

llm = LLMClient()
prompt = "Summarize the following incidents: 1. Bombing in Mumbai. 2. Attack in Delhi."
t0 = time.perf_counter()
llm.generate(prompt, system_prompt="You are an analyst.")
results["LLM Inference Time"] = time.perf_counter() - t0
print("LLM Done")

print("\n" + "="*60)
print(f"{'Metric':<40} | {'Value':<15}")
print("-" * 60)
print(f"{'1. Avg TXT Ingestion Time':<40} | {results['TXT Ingestion']:.3f} s")
print(f"{'2. Avg Image OCR Ingestion Time':<40} | {results.get('Image OCR Ingestion', 0):.3f} s")
print(f"{'3. Avg Scanned PDF OCR Time (1 page)':<40} | {results.get('PDF OCR Ingestion', 0):.3f} s")
print(f"{'4. Embedding Throughput':<40} | {results.get('Embedding Throughput (incidents/sec)', 0):.2f} inc/sec")
print(f"{'5. Avg Retrieval Latency':<40} | {results.get('Retrieval Latency', 0):.3f} s")
print(f"{'6. Avg LLM Inference Time':<40} | {results.get('LLM Inference Time', 0):.3f} s")
