import sys
import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from .embedding_service import EmbeddingService
from .chroma_manager import ChromaManager
from .models.retrieval_result import RetrievalResult
from models.incident import Incident
from models.image_asset import ImageAsset

# --- Configuration ---
DEFAULT_TOP_K = 20          # Candidates fetched from ChromaDB before filtering
SIMILARITY_WINDOW = 0.05    # Max allowed drop from the best score

logger = logging.getLogger(__name__)

# ============================================================================
# Known Group Aliases (for query parsing)
# ============================================================================
GROUP_ALIASES = {
    "maoist": ["cpi-maoist", "maoist", "naxal", "maoists", "communist party of india - maoist (cpi-maoist)"],
    "jem": ["jaish-e-mohammad", "jem", "jaish-e-mohammed", "jaish-e-mohammad (jem)"],
    "let": ["lashkar-e-taiba", "let", "lashkar-e-toiba", "lashkar-e-tayyaba", "lashkar-e-taiba (let)"],
    "hm": ["hizbul mujahideen", "hizb-ul-mujahideen", "hizbul mujahideen (hm)"],
    "ulfa": ["united liberation front of assam", "ulfa", "united liberation front of assam (ulfa)"],
    "ndfb": ["national democratic front of bodoland", "ndfb", "national democratic front of bodoland (ndfb)"],
    "im": ["indian mujahideen", "im"],
    "simi": ["students islamic movement of india", "simi"],
    "bki": ["babbar khalsa international", "bki", "babbar khalsa international (bki)"],
    "ltte": ["liberation tigers of tamil eelam", "ltte"],
    "pwg": ["people's war group", "pwg", "people's war group (pwg)"],
}

# ============================================================================
# Attack type keyword mappings (user terms → DB values)
# ============================================================================
ATTACK_TYPE_MAP = {
    "bombing": "Bombing/Explosion",
    "bomb": "Bombing/Explosion",
    "explosion": "Bombing/Explosion",
    "ied": "Bombing/Explosion",
    "blast": "Bombing/Explosion",
    "armed assault": "Armed Assault",
    "shooting": "Armed Assault",
    "gunfire": "Armed Assault",
    "ambush": "Armed Assault",
    "assassination": "Assassination",
    "kidnapping": "Hostage Taking (Kidnapping)",
    "kidnap": "Hostage Taking (Kidnapping)",
    "abduction": "Hostage Taking (Kidnapping)",
    "hostage": "Hostage Taking (Barricade Incident)",
    "hijacking": "Hijacking",
    "hijack": "Hijacking",
    "arson": "Facility/Infrastructure Attack",
    "sabotage": "Facility/Infrastructure Attack",
}

# ============================================================================
# Target type keyword mappings
# ============================================================================
TARGET_TYPE_MAP = {
    "police": "Police",
    "military": "Military",
    "army": "Military",
    "soldier": "Military",
    "soldiers": "Military",
    "civilian": "Private Citizens & Property",
    "civilians": "Private Citizens & Property",
    "government": "Government (General)",
    "school": "Educational Institution",
    "college": "Educational Institution",
    "university": "Educational Institution",
    "mosque": "Religious Figures/Institutions",
    "temple": "Religious Figures/Institutions",
    "church": "Religious Figures/Institutions",
    "religious": "Religious Figures/Institutions",
    "bus": "Transportation",
    "train": "Transportation",
    "railway": "Transportation",
    "airport": "Airports & Aircraft",
    "journalist": "Journalists & Media",
    "media": "Journalists & Media",
    "tourist": "Tourists",
    "tourists": "Tourists",
}

# ============================================================================
# Weapon type keyword mappings
# ============================================================================
WEAPON_TYPE_MAP = {
    "explosive": "Explosives",
    "explosives": "Explosives",
    "bomb": "Explosives",
    "firearm": "Firearms",
    "firearms": "Firearms",
    "gun": "Firearms",
    "guns": "Firearms",
    "rifle": "Firearms",
    "grenade": "Explosives",
    "knife": "Melee",
    "machete": "Melee",
    "melee": "Melee",
    "incendiary": "Incendiary",
    "chemical": "Chemical",
}

# ============================================================================
# Known Indian states (for query parsing)
# ============================================================================
KNOWN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chandigarh",
    "chhattisgarh", "delhi", "goa", "gujarat", "haryana", "himachal pradesh",
    "jammu and kashmir", "jharkhand", "karnataka", "kerala", "madhya pradesh",
    "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland", "odisha",
    "orissa", "puducherry", "punjab", "rajasthan", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttaranchal", "west bengal", "kashmir",
}

# Known major cities (subset — most common in GTD India)
KNOWN_CITIES = {
    "mumbai", "new delhi", "delhi", "srinagar", "jammu", "imphal",
    "kolkata", "chennai", "hyderabad", "bangalore", "bengaluru", "pune",
    "ahmedabad", "jaipur", "lucknow", "patna", "guwahati", "agartala",
    "bhopal", "chandigarh", "thiruvananthapuram", "kochi", "coimbatore",
    "varanasi", "raipur", "ranchi", "shimla", "dehradun", "gangtok",
    "aizawl", "kohima", "itanagar", "panaji", "shillong", "dispur",
    "sopore", "baramulla", "anantnag", "pulwama", "kupwara", "uri",
    "pathankot", "gurdaspur", "amritsar", "ludhiana", "rajouri",
    "poonch", "doda", "kishtwar", "kathua", "udhampur", "handwara",
    "tral", "shopian", "kulgam", "bijbehara", "bandipora",
}

# ============================================================================
# Named entity keywords for document-level text search
# ============================================================================
DOCUMENT_SEARCH_KEYWORDS = [
    "parliament", "embassy", "consulate", "airport", "hospital",
    "hotel", "market", "temple", "mosque", "church", "station",
    "crpf", "bsf", "itbp", "cisf", "rpf", "suicide", "grenade",
]


class RetrievalEngine:
    """
    Core Retrieval Engine for Offline Multimodal Intelligence Analysis System.
    Provides hybrid search: metadata-filtered + semantic search over indexed incidents.
    """
    def __init__(self, collection_names=None):
        if collection_names is None:
            collection_names = ["incidents"]
        elif isinstance(collection_names, str):
            collection_names = [collection_names]
            
        self.embedder = EmbeddingService()
        self.dbs = [ChromaManager(collection_name=c) for c in collection_names]

    # ========================================================================
    # Query Metadata Extraction (lightweight, rule-based)
    # ========================================================================
    def _extract_query_filters(self, query: str) -> Dict[str, Any]:
        """
        Parses a user query to extract structured metadata filters.
        Returns a dict with optional keys: year, city, state, group, 
        attack_type, target_type, weapon_type, doc_keywords.
        """
        q_lower = query.lower()
        filters = {}

        # 1. Extract year
        year_match = re.findall(r'\b(19\d{2}|20\d{2})\b', q_lower)
        if year_match:
            filters["years"] = list(set(year_match))

        # 2. Extract state
        for state in sorted(KNOWN_STATES, key=len, reverse=True):
            if state in q_lower:
                # Special case: "kashmir" should map to "Jammu and Kashmir"
                if state == "kashmir":
                    filters["state"] = "Jammu and Kashmir"
                else:
                    filters["state"] = state.title()
                break

        # 3. Extract city
        for city in sorted(KNOWN_CITIES, key=len, reverse=True):
            if city in q_lower:
                # Normalize city names
                city_map = {
                    "delhi": "New Delhi",
                    "bengaluru": "Bangalore",
                }
                filters["city"] = city_map.get(city, city.title())
                break

        # 4. Extract group
        for alias_key, alias_list in GROUP_ALIASES.items():
            # Check if any alias key or full name appears in query
            if re.search(r'\b' + re.escape(alias_key) + r'\b', q_lower):
                filters["group_aliases"] = alias_list
                break
            for alias in alias_list:
                if alias in q_lower:
                    filters["group_aliases"] = alias_list
                    break
            if "group_aliases" in filters:
                break

        # 5. Extract attack type
        for keyword, attack_type in ATTACK_TYPE_MAP.items():
            if re.search(r'\b' + re.escape(keyword) + r's?\b', q_lower):
                filters["attack_type"] = attack_type
                break

        # 6. Extract target type
        for keyword, target_type in TARGET_TYPE_MAP.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', q_lower):
                filters["target_type"] = target_type
                break

        # 7. Extract weapon type
        for keyword, weapon_type in WEAPON_TYPE_MAP.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', q_lower):
                filters["weapon_type"] = weapon_type
                break

        # 8. Extract document-level keyword for text search
        for keyword in DOCUMENT_SEARCH_KEYWORDS:
            if keyword in q_lower:
                filters.setdefault("doc_keywords", []).append(keyword)

        logger.info(f"Extracted query filters: {filters}")
        return filters

    # ========================================================================
    # Build ChromaDB where clause from extracted filters
    # ========================================================================
    def _build_where_clause(self, filters: Dict[str, Any]) -> Optional[Dict]:
        """
        Converts extracted filters into a ChromaDB where clause.
        Only uses fields that ChromaDB can filter on (exact match on metadata).
        """
        conditions = []

        if "city" in filters:
            conditions.append({"city": filters["city"]})
        
        if "state" in filters:
            conditions.append({"state": filters["state"]})

        if "attack_type" in filters:
            conditions.append({"attack_types": {"$contains": filters["attack_type"]}})

        if "target_type" in filters:
            conditions.append({"target_types": {"$contains": filters["target_type"]}})

        if "weapon_type" in filters:
            conditions.append({"weapon_types": {"$contains": filters["weapon_type"]}})

        if "group_aliases" in filters:
            # Use $contains on the responsible_groups string field
            # Try the most specific alias first
            group_conditions = []
            for alias in filters["group_aliases"]:
                group_conditions.append({"responsible_groups": {"$contains": alias}})
            if len(group_conditions) == 1:
                conditions.append(group_conditions[0])
            elif len(group_conditions) >= 2:
                conditions.append({"$or": group_conditions})

        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    # ========================================================================
    # Metadata bonus scoring (enhanced)
    # ========================================================================
    def _calculate_metadata_bonus(self, query: str, obj, filters: Dict[str, Any]) -> float:
        """
        Calculates a metadata-based relevance bonus.
        Enhanced: uses extracted filters for more precise matching.
        """
        if isinstance(obj, ImageAsset):
            query_lower = query.lower()
            bonus = 0.0
            if obj.filename and query_lower in obj.filename.lower():
                bonus += 0.10
            return bonus

        incident = obj
        query_lower = query.lower()
        bonus = 0.0
        
        # 1. Year Match (+0.10)
        if incident.date and "years" in filters:
            year = incident.date[:4]
            if year in filters["years"]:
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
                if re.search(r'\b' + re.escape(alias_key) + r'\b', query_lower):
                    if any(a in g_lower for a in alias_list):
                        group_matched = True
                        break
            if group_matched:
                break
                
        if group_matched:
            bonus += 0.15
            
        return min(bonus, 0.35)

    # ========================================================================
    # Main Search Method (Hybrid: metadata filter + semantic search)
    # ========================================================================
    def search(self, query: str, top_k: int = DEFAULT_TOP_K,
               similarity_window: float = SIMILARITY_WINDOW) -> List[RetrievalResult]:
        """
        Hybrid search: extracts metadata filters from query, uses them to narrow
        ChromaDB candidates, then ranks by semantic similarity + metadata bonus.
        Falls back to pure semantic search if no filters match or filtered results are sparse.
        """
        if not query.strip():
            return []
        
        # 0. Extract structured filters from query
        filters = self._extract_query_filters(query)
        where_clause = self._build_where_clause(filters)
        
        # 1. Embed query
        query_embeddings = self.embedder.embed_queries([query])
        
        # Also embed for image search
        image_query_embeddings = None
        if self.embedder.clip_model is not None:
            try:
                image_query_embeddings = self.embedder.embed_text_for_image_search([query])
            except Exception as e:
                logger.error(f"Failed to embed query for image search: {e}")
        
        # Fetch a wider pool to allow metadata bonuses to elevate items
        fetch_k = max(top_k * 5, 50)
        
        # 2. Search ChromaDB with hybrid strategy
        all_raw_results = []
        doc_keyword_matched_ids = set()  # Track IDs found via document text search
        
        for db in self.dbs:
            # --- Strategy A: Filtered semantic search ---
            if where_clause is not None:
                try:
                    filtered_results = db.collection.query(
                        query_embeddings=query_embeddings,
                        n_results=fetch_k,
                        where=where_clause,
                        include=["documents", "metadatas", "distances"]
                    )
                    if filtered_results and filtered_results['ids'] and filtered_results['ids'][0]:
                        for i in range(len(filtered_results['ids'][0])):
                            meta = filtered_results['metadatas'][0][i]
                            doc = filtered_results['documents'][0][i]
                            distance = filtered_results['distances'][0][i]
                            similarity = 1.0 - distance
                            obj = db._metadata_to_object(meta, doc)
                            all_raw_results.append((obj, similarity))
                        logger.info(f"Filtered search returned {len(filtered_results['ids'][0])} results")
                except Exception as e:
                    logger.warning(f"Filtered search failed (falling back to unfiltered): {e}")

            # --- Strategy B: Document text search (for named entities) ---
            if "doc_keywords" in filters:
                for keyword in filters["doc_keywords"]:
                    # ChromaDB $contains is case-sensitive, so we try multiple casings
                    casings = [keyword, keyword.title(), keyword.upper()]
                    for case_variant in casings:
                        try:
                            doc_results = db.collection.query(
                                query_embeddings=query_embeddings,
                                n_results=min(fetch_k, 20),
                                where_document={"$contains": case_variant},
                                include=["documents", "metadatas", "distances"]
                            )
                            if doc_results and doc_results['ids'] and doc_results['ids'][0]:
                                for i in range(len(doc_results['ids'][0])):
                                    meta = doc_results['metadatas'][0][i]
                                    doc_text = doc_results['documents'][0][i]
                                    distance = doc_results['distances'][0][i]
                                    similarity = 1.0 - distance
                                    obj = db._metadata_to_object(meta, doc_text)
                                    all_raw_results.append((obj, similarity))
                                    # Track this ID as a document keyword match
                                    obj_id = getattr(obj, 'incident_id', None) or getattr(obj, 'asset_id', None)
                                    if obj_id:
                                        doc_keyword_matched_ids.add(obj_id)
                                logger.info(f"Document text search for '{case_variant}' returned {len(doc_results['ids'][0])} results")
                        except Exception as e:
                            logger.warning(f"Document text search failed for '{case_variant}': {e}")

            # --- Strategy C: Pure semantic search (always run as fallback/complement) ---
            raw_results = db.query(query_embeddings, top_k=fetch_k)
            all_raw_results.extend(raw_results)
            
            # --- Image search ---
            if image_query_embeddings is not None:
                image_results = db.query_images(image_query_embeddings, top_k=fetch_k)
                all_raw_results.extend(image_results)
        
        # 3. Deduplicate by incident_id (keep highest score)
        seen_ids = {}
        for obj, score in all_raw_results:
            obj_id = getattr(obj, 'incident_id', None) or getattr(obj, 'asset_id', None) or id(obj)
            if obj_id not in seen_ids or score > seen_ids[obj_id][1]:
                seen_ids[obj_id] = (obj, score)
        
        deduped_results = list(seen_ids.values())
        
        # 4. Apply metadata bonus scoring + document keyword bonus
        candidates = []
        for obj, score in deduped_results:
            metadata_bonus = self._calculate_metadata_bonus(query, obj, filters)
            
            # Document keyword match bonus: if this incident was found via
            # where_document search, it contains the exact keyword the user asked about
            # (e.g., "Parliament", "CRPF"). This is a strong relevance signal.
            obj_id = getattr(obj, 'incident_id', None) or getattr(obj, 'asset_id', None)
            doc_keyword_bonus = 0.15 if obj_id in doc_keyword_matched_ids else 0.0
            
            # Attack Type strict enforcement
            attack_type_bonus = 0.0
            if "attack_type" in filters:
                # Fallback logic: boost exact metadata matches so they crush pure semantic non-matches
                if getattr(obj, 'attack_types', None) and filters["attack_type"] in obj.attack_types:
                    attack_type_bonus = 1.0 
                else:
                    attack_type_bonus = -0.5
            
            final_score = score + metadata_bonus + doc_keyword_bonus + attack_type_bonus
            candidates.append(RetrievalResult(payload=obj, score=final_score))

        if not candidates:
            return []
            
        # Sort candidates by final score descending
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Take top_k AFTER applying bonuses
        candidates = candidates[:top_k]

        # 5. Similarity-window filtering
        if similarity_window is not None:
            best_score = candidates[0].score
            threshold = best_score - similarity_window
            filtered = [r for r in candidates if r.score >= threshold]

            logger.debug(
                "Retrieved %d candidates | Best score: %.3f | Threshold: %.3f | Returned: %d results",
                len(candidates), best_score, threshold, len(filtered)
            )
            return filtered

        logger.debug("Retrieved %d candidates (no filtering)", len(candidates))
        return candidates
