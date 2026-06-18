import sys
import os
import logging
from typing import List
from .embedding_service import EmbeddingService
from .chroma_manager import ChromaManager
from .models.retrieval_result import RetrievalResult
from models.incident import Incident

# --- Configuration ---
DEFAULT_TOP_K = 20          # Candidates fetched from ChromaDB before filtering
SIMILARITY_WINDOW = 0.05    # Max allowed drop from the best score (tightened for BGE embeddings)

logger = logging.getLogger(__name__)

GROUP_ALIASES = {
    "maoist": ["cpi-maoist", "maoist", "naxal"],
    "jem": ["jaish-e-mohammad", "jem", "jaish-e-mohammed"],
    "let": ["lashkar-e-taiba", "let", "lashkar-e-toiba", "lashkar-e-tayyaba"],
    "hm": ["hizbul mujahideen", "hizb-ul-mujahideen"],
    "ulfa": ["united liberation front of assam", "ulfa"]
}

class RetrievalEngine:
    """
    Core Retrieval Engine for Offline Multimodal Intelligence Analysis System.
    Provides semantic search over indexed incidents using BGE/MiniLM embeddings and ChromaDB.

    Post-retrieval filtering:
        After fetching DEFAULT_TOP_K candidates, only results whose similarity
        score is within SIMILARITY_WINDOW of the best score are returned.
        This reduces context contamination for incident-specific queries
        while preserving breadth for analytical queries.
    """
    def __init__(self, collection_name: str = "incidents"):
        self.embedder = EmbeddingService()
        self.db = ChromaManager(collection_name=collection_name)

    def _calculate_metadata_bonus(self, query: str, incident: Incident) -> float:
        query_lower = query.lower()
        bonus = 0.0
        
        # 1. Year Match (+0.10)
        if incident.date:
            year = incident.date[:4]
            if year in query_lower:
                bonus += 0.10
                
        # 2. Location Match (+0.10)
        loc_matched = False
        for loc in [incident.city, incident.state, incident.country]:
            if loc and loc.lower() != "unknown" and loc.lower() in query_lower:
                loc_matched = True
                break
        if loc_matched:
            bonus += 0.10
            
        # 3. Group Match (+0.15)
        group_matched = False
        for group in incident.responsible_groups:
            if not group or group.lower() == "unknown":
                continue
            g_lower = group.lower()
            
            # Direct match
            if g_lower in query_lower:
                group_matched = True
                break
                
            # Alias match
            for alias_key, alias_list in GROUP_ALIASES.items():
                if f" {alias_key} " in f" {query_lower} " or alias_key == query_lower:
                    if any(a in g_lower for a in alias_list):
                        group_matched = True
                        break
            if group_matched:
                break
                
        if group_matched:
            bonus += 0.15
            
        return min(bonus, 0.35)

    def search(self, query: str, top_k: int = DEFAULT_TOP_K,
               similarity_window: float = SIMILARITY_WINDOW) -> List[RetrievalResult]:
        """
        Embeds the query, searches the Chroma vector database, and applies
        similarity-window filtering to return only the most relevant subset.

        Args:
            query:              The natural-language search query.
            top_k:              Number of candidates to fetch from ChromaDB.
            similarity_window:  Maximum allowed score drop from the best result.
                                Set to None to disable filtering and return all top_k.
        """
        if not query.strip():
            return []
            
        # 1. Embed query
        query_embeddings = self.embedder.embed_queries([query])
        
        # 2. Search ChromaDB for candidates
        raw_results = self.db.query(query_embeddings, top_k=top_k)
        
        # 3. Construct RetrievalResult objects and apply metadata scoring
        candidates = []
        for incident, score in raw_results:
            metadata_bonus = self._calculate_metadata_bonus(query, incident)
            final_score = score + metadata_bonus
            candidates.append(RetrievalResult(incident=incident, score=final_score))

        if not candidates:
            return []
            
        # Sort candidates by final score descending
        candidates.sort(key=lambda x: x.score, reverse=True)

        # 4. Similarity-window filtering
        if similarity_window is not None:
            best_score = candidates[0].score
            threshold = best_score - similarity_window
            filtered = [r for r in candidates if r.score >= threshold]

            logger.debug(
                "Retrieved %d candidates | Best score: %.3f | Threshold: %.3f | Returned: %d incidents",
                len(candidates), best_score, threshold, len(filtered)
            )
            return filtered

        logger.debug("Retrieved %d candidates (no filtering)", len(candidates))
        return candidates
