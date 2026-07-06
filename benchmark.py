import time
import os
import gc
from PIL import Image, ImageDraw, ImageFont

# Import DRDO components
from ingestion.txt_ingestor import extract_txt
from ingestion.image_ingestor import extract_image_text
from ingestion.scanned_pdf_ingestor import extract_scanned_pdf
from retrieval.embedding_service import EmbeddingService
from retrieval.retrieval_engine import RetrievalEngine
from rag.llm_client import LLMClient

def create_test_files():
    # 1. TXT
    txt_path = "benchmark_test.txt"
    with open(txt_path, "w") as f:
        f.write("This is a benchmark test file. " * 100) # Simple 300-word file

    # 2. Image (with some text for OCR)
    img_path = "benchmark_test.png"
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("arial.ttf", 40)
    except:
        fnt = ImageFont.load_default()
    d.text((50, 50), "Benchmark Test Image OCR", font=fnt, fill=(0, 0, 0))
    d.text((50, 150), "Line two of the OCR test.", font=fnt, fill=(0, 0, 0))
    img.save(img_path)

    # 3. PDF
    pdf_path = "benchmark_test.pdf"
    img.save(pdf_path, "PDF", resolution=100.0, save_all=True)

    return txt_path, img_path, pdf_path

def cleanup(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

def run_benchmark(iterations=3):
    import torch
    print("Preparing test files...")
    txt_path, img_path, pdf_path = create_test_files()
    
    def clear_mem():
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    
    results = {}
    
    print("\n--- 1. TXT Ingestion ---")
    times = []
    for i in range(iterations):
        clear_mem()
        t0 = time.perf_counter()
        print(f"  Run {i+1}: Starting TXT...")
        extract_txt(txt_path)
        t = time.perf_counter() - t0
        times.append(t)
        print(f"  Run {i+1} completed in {t:.3f}s")
    results["TXT Ingestion"] = sum(times)/len(times)
    
    print("\n--- 2. Image OCR Ingestion ---")
    times = []
    for i in range(iterations):
        clear_mem()
        t0 = time.perf_counter()
        print(f"  Run {i+1}: Starting Image OCR...")
        extract_image_text(img_path)
        t = time.perf_counter() - t0
        times.append(t)
        print(f"  Run {i+1} completed in {t:.3f}s")
    results["Image OCR Ingestion"] = sum(times)/len(times)
    
    print("\n--- 3. Scanned PDF OCR Ingestion ---")
    times = []
    for i in range(iterations):
        clear_mem()
        t0 = time.perf_counter()
        print(f"  Run {i+1}: Starting PDF OCR...")
        extract_scanned_pdf(pdf_path)
        t = time.perf_counter() - t0
        times.append(t)
        print(f"  Run {i+1} completed in {t:.3f}s")
    results["PDF OCR Ingestion"] = sum(times)/len(times)
    
    print("\n--- 4. Embedding Generation Throughput ---")
    clear_mem()
    print("  Initializing EmbeddingService...")
    embedder = EmbeddingService()
    test_texts = ["This is a test incident summary regarding an explosion."] * 50
    t0 = time.perf_counter()
    print("  Generating embeddings for 50 incidents...")
    embedder.embed_queries(test_texts)
    total_time = time.perf_counter() - t0
    results["Embedding Throughput (incidents/sec)"] = 50 / total_time
    print(f"  Processed 50 incidents in {total_time:.3f}s")
    
    print("\n--- 5. Retrieval Latency ---")
    clear_mem()
    print("  Initializing RetrievalEngine...")
    retrieval = RetrievalEngine()
    kb_size = sum(db.count() for db in retrieval.dbs)
    times = []
    for i in range(iterations):
        clear_mem()
        t0 = time.perf_counter()
        print(f"  Run {i+1}: Searching...")
        retrieval.search("bombing in Mumbai", top_k=10)
        t = time.perf_counter() - t0
        times.append(t)
        print(f"  Run {i+1} completed in {t:.3f}s")
    results["Retrieval Latency"] = sum(times)/len(times)
    results["KB Size"] = kb_size
    
    print("\n--- 6. LLM Inference Time ---")
    clear_mem()
    print("  Initializing LLMClient...")
    llm = LLMClient()
    times = []
    prompt = "Summarize the following incidents: 1. Bombing in Mumbai. 2. Attack in Delhi."
    for i in range(iterations):
        clear_mem()
        t0 = time.perf_counter()
        print(f"  Run {i+1}: Generating LLM response...")
        llm.generate(prompt, system_prompt="You are an analyst.")
        t = time.perf_counter() - t0
        times.append(t)
        print(f"  Run {i+1} completed in {t:.3f}s")
    results["LLM Inference Time"] = sum(times)/len(times)
    
    cleanup([txt_path, img_path, pdf_path])
    
    # Print Table
    print("\n" + "="*60)
    print(f"{'DRDO PHASE 1 PIPELINE BENCHMARK':^60}")
    print("="*60)
    print(f"{'Metric':<40} | {'Value':<15}")
    print("-" * 60)
    print(f"{'1. Avg TXT Ingestion Time':<40} | {results['TXT Ingestion']:.3f} s")
    print(f"{'2. Avg Image OCR Ingestion Time':<40} | {results['Image OCR Ingestion']:.3f} s")
    print(f"{'3. Avg Scanned PDF OCR Time (1 page)':<40} | {results['PDF OCR Ingestion']:.3f} s")
    print(f"{'4. Embedding Throughput':<40} | {results['Embedding Throughput (incidents/sec)']:.2f} inc/sec")
    print(f"{'5. Avg Retrieval Latency':<40} | {results['Retrieval Latency']:.3f} s")
    print(f"{'6. Avg LLM Inference Time':<40} | {results['LLM Inference Time']:.3f} s")
    print("-" * 60)
    print("Test Conditions:")
    print(f"- Hardware: Apple Silicon Mac (Unified Memory assumed)")
    print(f"- Image/PDF size: 800x600 px (1 page)")
    print(f"- TXT file size: ~300 words")
    print(f"- Embedding Batch Size: 50")
    print(f"- Knowledge Base Size: {kb_size} incidents")
    print(f"- LLM Prompt Length: ~15 words + system prompt")
    print("="*60)

if __name__ == "__main__":
    # Ensure correct working directory
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    run_benchmark(iterations=3)
