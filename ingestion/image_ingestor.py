"""
Image Ingestor
==============

Extracts text from images using EasyOCR.
"""

import os
import easyocr
from PIL import Image

def extract_image_text(file_path: str) -> dict:
    """
    Run OCR on an image and generate an OpenCLIP image embedding and BLIP caption.

    Returns
    -------
    dict with keys:
        text            – combined extracted text
        detections      – number of text detections
        extractor       – name of the extractor used
        image_embedding – the OpenCLIP embedding vector
        caption         – the BLIP generated caption
    """
    import time
    t0 = time.perf_counter()
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- 1. Initialise PaddleOCR reader ---
    try:
        from paddleocr import PaddleOCR
        # use_angle_cls=True helps with rotated text
        reader = PaddleOCR(use_angle_cls=True, lang='en')
    except Exception as e:
        raise RuntimeError(f"Could not initialise PaddleOCR: {e}")

    # --- 2. Run OCR ---
    try:
        results = reader.ocr(file_path)
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")

    combined_text = ""
    detections = 0
    
    if results and len(results) > 0:
        # PaddleOCR v6 / PaddleX can return a list of dictionaries
        if isinstance(results[0], dict) and 'rec_texts' in results[0]:
            texts = results[0]['rec_texts']
            combined_text = " ".join(texts)
            detections = len(texts)
        # Fallback for standard older PaddleOCR format
        elif isinstance(results[0], list):
            lines = results[0]
            # result format: [[[[x,y], [x,y], [x,y], [x,y]], ('text', confidence)], ...]
            texts = [line[1][0] for line in lines if isinstance(line, (list, tuple)) and len(line) >= 2 and isinstance(line[1], (list, tuple)) and len(line[1]) >= 1]
            combined_text = " ".join(texts)
            detections = len(texts)

    # Convert to PIL Image once for visual models
    try:
        pil_image = Image.open(file_path).convert("RGB")
    except Exception as e:
        raise RuntimeError(f"Failed to load image for visual models: {e}")

    # --- 3. Generate Image Embedding via OpenCLIP ---
    image_embedding = None
    try:
        from retrieval.embedding_service import EmbeddingService
        es = EmbeddingService()
        if es.clip_model is not None:
            emb_list = es.embed_images([pil_image])
            if emb_list and len(emb_list) > 0:
                image_embedding = emb_list[0]
    except Exception as e:
        import logging
        logging.error(f"Failed to generate image embedding for {file_path}: {e}")

    # --- 4. Generate Image Caption via BLIP ---
    caption = ""
    try:
        from retrieval.caption_service import CaptionService
        cs = CaptionService()
        caption = cs.generate_caption(pil_image)
    except Exception as e:
        import logging
        logging.error(f"Failed to generate image caption for {file_path}: {e}")

    elapsed = time.perf_counter() - t0
    print(f"[Timing] Image OCR & Multimodal Ingestion completed in {elapsed:.4f}s")

    return {
        "text": combined_text,
        "detections": detections,
        "extractor": "PaddleOCR + OpenCLIP + BLIP",
        "image_embedding": image_embedding,
        "caption": caption
    }
