import os
import sys
import json
import time
import logging
from typing import List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.incident import Incident
from retrieval.embedding_service import EmbeddingService
from retrieval.chroma_manager import ChromaManager

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_incidents_from_json(filepath: str) -> List[Incident]:
    logging.info(f"Loading incidents from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    incidents = []
    for item in data:
        incident = Incident(
            incident_id=item.get("incident_id", ""),
            date=item.get("date", ""),
            country=item.get("country", ""),
            state=item.get("state", ""),
            city=item.get("city", ""),
            attack_types=item.get("attack_types", []),
            target_types=item.get("target_types", []),
            weapon_types=item.get("weapon_types", []),
            responsible_groups=item.get("responsible_groups", []),
            killed=item.get("killed", 0),
            injured=item.get("injured", 0),
            summary=item.get("summary", ""),
            has_summary=item.get("has_summary", False),
            retrieval_text=item.get("retrieval_text", ""),
            source_document_id=item.get("source_document_id", "")
        )
        incidents.append(incident)
    return incidents

def build_index(dataset_name: str = "gtd_india_summary.json", collection_name: str = "incidents", batch_size: int = 1000):
    start_time = time.time()
    filepath = os.path.join(PROJECT_ROOT, "storage", dataset_name)
    
    incidents = load_incidents_from_json(filepath)
    total_incidents = len(incidents)
    logging.info(f"Loaded {total_incidents} incidents.")

    logging.info("Initializing Embedding Service and Chroma Manager...")
    embedder = EmbeddingService()
    db = ChromaManager(collection_name=collection_name)
    
    logging.info(f"Building index in batches of {batch_size}...")
    for i in range(0, total_incidents, batch_size):
        batch = incidents[i : i + batch_size]
        logging.info(f"Processing batch {i} to {min(i + batch_size, total_incidents)}...")
        
        # 1. Extract documents
        documents = [inc.retrieval_text for inc in batch]
        
        # 2. Generate embeddings
        embeddings = embedder.embed_documents(documents)
        
        # 3. Add to ChromaDB
        db.add_incidents(batch, embeddings)

    elapsed = time.time() - start_time
    logging.info("--- Index Build Complete ---")
    logging.info(f"Total incidents indexed : {db.count()}")
    logging.info(f"Embedding dimension     : {len(embeddings[0]) if total_incidents > 0 else 'N/A'}")
    logging.info(f"Index build time        : {elapsed:.2f} seconds")

if __name__ == "__main__":
    # We index gtd_india_summary.json as requested for the initial target.
    build_index(dataset_name="gtd_india_summary.json", collection_name="incidents", batch_size=1000)
