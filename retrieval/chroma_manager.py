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
from models.image_asset import ImageAsset

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
        
        # Multimodal Image Collection
        self.image_collection = self.client.get_or_create_collection(
            name=collection_name + "_images",
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
            "source_document_id": incident.source_document_id,
            "asset_type": "incident"
        }

    def _metadata_to_object(self, metadata: Dict[str, Any], document: str) -> Any:
        """
        Reconstructs an Incident or ImageAsset object from ChromaDB metadata and document text.
        """
        asset_type = metadata.get("asset_type", "incident")
        
        if asset_type == "image" or metadata.get("modality") == "image":
            return ImageAsset(
                asset_id=metadata.get("incident_id", metadata.get("asset_id", "")),
                filename=metadata.get("filename", ""),
                ocr_text=metadata.get("ocr_text", ""),
                caption=metadata.get("caption", ""),
                source_document_id=metadata.get("source_document_id", ""),
                retrieval_text=document
            )

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
        
        # Inject modality
        for m in metadatas:
            m["modality"] = "text"
            m["embedding_type"] = "bge-small"
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def add_image_asset(self, asset: ImageAsset, text_embedding: List[float], image_embedding: List[float]):
        """
        Adds an ImageAsset to BOTH the text collection (using text_embedding) 
        and the image collection (using image_embedding).
        """
        metadata = {
            "asset_id": asset.asset_id,
            "filename": asset.filename,
            "ocr_text": asset.ocr_text,
            "caption": asset.caption,
            "source_document_id": asset.source_document_id,
            "asset_type": "image",
            "modality": "image"
        }
        
        # Add to Text Collection (for keyword/semantic text queries)
        if text_embedding:
            text_metadata = metadata.copy()
            text_metadata["embedding_type"] = "bge-small"
            self.collection.add(
                ids=[asset.asset_id],
                embeddings=[text_embedding],
                documents=[asset.retrieval_text],
                metadatas=[text_metadata]
            )
            
        # Add to Image Collection (for visual/cross-modal queries)
        if image_embedding:
            img_metadata = metadata.copy()
            img_metadata["embedding_type"] = "openclip"
            self.image_collection.add(
                ids=[asset.asset_id],
                embeddings=[image_embedding],
                documents=[asset.retrieval_text],
                metadatas=[img_metadata]
            )

    def add_multimodal_record(self, record_id: str, document: str, embedding: List[float], metadata: Dict[str, Any]):
        """
        Adds a single raw multimodal record to ChromaDB.
        Used to store OpenCLIP image embeddings alongside their OCR text.
        """
        # Ensure primitive types
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            else:
                clean_metadata[k] = str(v)
                
        self.image_collection.add(
            ids=[record_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[clean_metadata]
        )

    def query(self, query_embeddings: List[List[float]], top_k: int = 5):
        """
        Queries ChromaDB using pre-computed query embeddings.
        Returns reconstructed objects and scores.
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
                
                obj = self._metadata_to_object(meta, doc)
                reconstructed_results.append((obj, similarity))
                
        return reconstructed_results

    def query_images(self, query_embeddings: List[List[float]], top_k: int = 5):
        """
        Queries the multimodal image collection in ChromaDB.
        """
        results = self.image_collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        reconstructed_results = []
        
        if results and results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                meta = results['metadatas'][0][i]
                doc = results['documents'][0][i]
                distance = results['distances'][0][i]
                
                similarity = 1.0 - distance
                obj = self._metadata_to_object(meta, doc)
                reconstructed_results.append((obj, similarity))
                
        return reconstructed_results

    def count(self) -> int:
        """Returns the total number of items in the collection."""
        return self.collection.count()
