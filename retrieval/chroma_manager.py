import os
import sys
import logging
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.incident import Incident

class ChromaManager:
    """
    Manages the persistent offline ChromaDB instance.
    Handles adding, updating, and querying incident embeddings.
    """
    def __init__(self, collection_name: str = "incidents"):
        if chromadb is None:
            raise ImportError("chromadb is not installed.")
        
        self.db_dir = os.path.join(PROJECT_ROOT, "storage", "vector_db") #CREATING THE DATABASE IN THE STORAGE FOLDER 
        os.makedirs(self.db_dir, exist_ok=True)
        
        logging.info(f"Initializing ChromaDB PersistentClient at {self.db_dir}...")
        self.client = chromadb.PersistentClient(path=self.db_dir)
        
        # We use cosine similarity (cosine distance is default for cosine space when normalized)
        # BGE embeddings are normalized, so inner product (ip) or cosine is fine.
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _incident_to_metadata(self, incident: Incident) -> Dict[str, Any]:
        """
        Converts an Incident object to a flat metadata dictionary for ChromaDB.
        Lists are converted to comma-separated strings because ChromaDB metadata 
        only supports str, int, float, or bool.
        """
        return {
            "incident_id": incident.incident_id,
            "date": incident.date,
            "country": incident.country,
            "state": incident.state,
            "city": incident.city,
            "attack_types": ", ".join(incident.attack_types),
            "target_types": ", ".join(incident.target_types),
            "weapon_types": ", ".join(incident.weapon_types),
            "responsible_groups": ", ".join(incident.responsible_groups),
            "killed": incident.killed,
            "injured": incident.injured,
            "has_summary": incident.has_summary,
            "source_document_id": incident.source_document_id
        }

    def _metadata_to_incident(self, metadata: Dict[str, Any], document: str) -> Incident:
        """
        Reconstructs an Incident object from ChromaDB metadata and document text.
        """
        def parse_list(val: str) -> List[str]:
            if not val: return []
            return [x.strip() for x in val.split(",") if x.strip()]

        return Incident(
            incident_id=metadata.get("incident_id", ""),
            date=metadata.get("date", ""),
            country=metadata.get("country", ""),
            state=metadata.get("state", ""),
            city=metadata.get("city", ""),
            attack_types=parse_list(metadata.get("attack_types", "")),
            target_types=parse_list(metadata.get("target_types", "")),
            weapon_types=parse_list(metadata.get("weapon_types", "")),
            responsible_groups=parse_list(metadata.get("responsible_groups", "")),
            killed=metadata.get("killed", 0),
            injured=metadata.get("injured", 0),
            has_summary=metadata.get("has_summary", False),
            source_document_id=metadata.get("source_document_id", ""),
            retrieval_text=document
        )

    def add_incidents(self, incidents: List[Incident], embeddings: List[List[float]]):
        """
        Adds a batch of Incidents and their pre-computed embeddings to ChromaDB.
        """
        if not incidents:
            return
            
        ids = [i.incident_id for i in incidents]
        documents = [i.retrieval_text for i in incidents]
        metadatas = [self._incident_to_metadata(i) for i in incidents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def query(self, query_embeddings: List[List[float]], top_k: int = 5):
        """
        Queries ChromaDB using pre-computed query embeddings.
        Returns reconstructed Incident objects and scores.
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        reconstructed_results = []
        
        # Results are batched, so we iterate through the first query's results
        if results and results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                meta = results['metadatas'][0][i]
                doc = results['documents'][0][i]
                distance = results['distances'][0][i]
                
                # Convert distance back to similarity score (1 - distance for cosine)
                similarity = 1.0 - distance
                
                incident = self._metadata_to_incident(meta, doc)
                reconstructed_results.append((incident, similarity))
                
        return reconstructed_results

    def count(self) -> int:
        """Returns the total number of items in the collection."""
        return self.collection.count()
