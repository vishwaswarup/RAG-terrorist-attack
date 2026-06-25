import sys
import os
sys.path.insert(0, os.path.abspath("."))
from retrieval.embedding_service import EmbeddingService
import torch
from PIL import Image

try:
    print("Initializing embedding service...")
    es = EmbeddingService()
    print("Done initializing. clip_model loaded?", es.clip_model is not None)
    
    # Create a dummy image
    img = Image.new('RGB', (224, 224), color = 'red')
    emb = es.embed_images([img])
    print("Image embedding shape:", len(emb), len(emb[0]))
    
    txt_emb = es.embed_text_for_image_search(["a red image"])
    print("Text embedding shape:", len(txt_emb), len(txt_emb[0]))
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
