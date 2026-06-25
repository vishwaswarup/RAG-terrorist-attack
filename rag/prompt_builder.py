import re
import logging

logger = logging.getLogger(__name__)

# Very rough approximation: 1 token ~= 4 chars for English text
CHARS_PER_TOKEN = 4

# ============================================================================
# Query Classification (lightweight, rule-based)
# ============================================================================
QUERY_TYPES = {
    "enumeration": [
        r"\blist\b", r"\bshow all\b", r"\benumerate\b", r"\bfind all\b",
    ],
    "comparison": [
        r"\bcompare\b", r"\bcomparison\b", r"\bversus\b", r"\bvs\b",
        r"\bdifference between\b", r"\bsimilarities between\b",
    ],
    "factual": [
        r"\bhow many\b", r"\bcount\b",
        r"\bwho was\b", r"\bwho is\b", r"\bwho are\b",
        r"\bwhat was\b", r"\bwhat is\b", r"\bwhat are\b",
        r"\bwhen did\b", r"\bwhen was\b",
        r"\bwhere did\b", r"\bwhere was\b",
        r"\bhow did\b", r"\bhow was\b",
        r"\bwho carried\b", r"\bwho attacked\b",
        r"\bresponsible\b",
    ],
    "summary": [
        r"\bsummarize\b", r"\bsummary\b", r"\boverview\b",
        r"\btell me about\b", r"\bdescribe\b", r"\bexplain\b",
        r"\bwhat happened\b", r"\bdetails\b",
    ],
}


def classify_query(query: str) -> str:
    """
    Classifies a query into one of: enumeration, comparison, factual, summary.
    Returns the query type string. Defaults to 'summary' if no pattern matches.
    """
    q_lower = query.lower()
    for query_type, patterns in QUERY_TYPES.items():
        for pattern in patterns:
            if re.search(pattern, q_lower):
                return query_type
    return "summary"


# ============================================================================
# Query-specific system prompt suffixes
# ============================================================================
QUERY_TYPE_INSTRUCTIONS = {
    "enumeration": (
        "\n\nFORMATTING INSTRUCTIONS:\n"
        "The user is asking for a list. Present each matching incident as a numbered item.\n"
        "For each incident include: Date, Location, Responsible Group, Attack Type, Killed, Injured.\n"
        "Use this exact format for each item:\n"
        "1. **[Date]** — [Location]\n"
        "   - Attack: [type] | Group: [group] | Killed: [N] | Injured: [N]\n"
        "   - [One-line summary]\n"
    ),
    "comparison": (
        "\n\nFORMATTING INSTRUCTIONS:\n"
        "The user is asking for a comparison. Present each incident side-by-side.\n"
        "For each incident, list: Date, Location, Attack Type, Responsible Group, Killed, Injured.\n"
        "Then provide a brief comparison of key differences and similarities.\n"
    ),
    "factual": (
        "\n\nFORMATTING INSTRUCTIONS:\n"
        "The user is asking a specific factual question. Answer directly in 1-3 sentences.\n"
        "State the fact first, then provide supporting detail if available.\n"
        "If the answer is not in the provided incidents, state that clearly.\n"
    ),
    "summary": (
        "\n\nFORMATTING INSTRUCTIONS:\n"
        "Provide a concise analytical summary (75-150 words).\n"
        "Include key facts: dates, locations, responsible groups, casualty figures.\n"
        "Use factual intelligence-report style.\n"
    ),
}


class PromptBuilder:
    def __init__(self, max_context_tokens: int = 3000):
        self.max_context_chars = max_context_tokens * CHARS_PER_TOKEN

    def _build_structured_incident_block(self, result, index: int) -> str:
        """
        Builds a clean structured block for a single incident.
        """
        from models.image_asset import ImageAsset
        
        if isinstance(result.payload, ImageAsset):
            return (
                f"--- Retrieved Image Asset #{index} (Relevance: {result.score:.3f}) ---\n"
                f"Filename: {result.payload.filename}\n"
                f"Caption: {result.payload.caption}\n"
                f"OCR Text: {result.payload.ocr_text}\n\n"
            )
        
        inc = result.payload
        
        # Build structured block from metadata fields
        lines = [f"--- Incident Report #{index} (Relevance: {result.score:.3f}) ---"]
        lines.append(f"Date: {inc.date or 'Unknown'}")
        
        loc_parts = []
        if inc.city and inc.city != "Unknown": loc_parts.append(inc.city)
        if inc.state and inc.state != "Unknown": loc_parts.append(inc.state)
        if inc.country and inc.country != "Unknown": loc_parts.append(inc.country)
        lines.append(f"Location: {', '.join(loc_parts) if loc_parts else 'Unknown'}")
        
        if inc.attack_types:
            lines.append(f"Attack Type: {', '.join(inc.attack_types)}")
        if inc.target_types:
            lines.append(f"Target Type: {', '.join(inc.target_types)}")
        if inc.weapon_types:
            lines.append(f"Weapon Type: {', '.join(inc.weapon_types)}")
        if inc.responsible_groups:
            groups = [g for g in inc.responsible_groups if g and g.lower() != "unknown"]
            if groups:
                lines.append(f"Responsible Group: {', '.join(groups)}")
            else:
                lines.append("Responsible Group: Unknown")
        else:
            lines.append("Responsible Group: Unknown")
            
        lines.append(f"Killed: {inc.killed} | Injured: {inc.injured}")
        
        # Add summary if available (from retrieval_text)
        if inc.has_summary and inc.summary and inc.summary.strip():
            lines.append(f"Summary: {inc.summary.strip()}")
        elif inc.retrieval_text:
            # Extract summary section from retrieval_text if present
            rt = inc.retrieval_text
            summary_idx = rt.find("Summary:")
            if summary_idx != -1:
                summary_text = rt[summary_idx + len("Summary:"):].strip()
                if summary_text:
                    lines.append(f"Summary: {summary_text}")
        
        lines.append("")  # blank line separator
        return "\n".join(lines)

    def build_prompt(self, query: str, incidents: list) -> tuple[str, str]:
        """
        Takes a query and a list of RetrievalResult objects.
        Returns (system_prompt, user_prompt)
        
        Enhanced with:
        - Query classification for type-specific instructions
        - Structured incident context blocks
        """
        # Classify the query
        query_type = classify_query(query)
        logger.info(f"Query classified as: {query_type}")
        
        # Build system prompt with query-type-specific instructions
        system_prompt = (
            "You are a Senior Intelligence Analyst. You will be provided with several incident reports.\n"
            "Your task is to answer the user's analytical query based strictly on the provided incidents.\n"
            "Do not speculate beyond the provided context. If information is not present in the retrieved "
            "incidents, state that it is not available in the provided data.\n"
            "\n"
            "Requirements:\n"
            "- Answer ONLY the specific question asked. Do NOT generate additional questions or answers.\n"
            "- Use factual intelligence-report style.\n"
            "- No speculation, assumptions, or unsupported conclusions.\n"
            "- Use only retrieved context."
        )
        
        # Append query-type-specific formatting instructions
        system_prompt += QUERY_TYPE_INSTRUCTIONS.get(query_type, QUERY_TYPE_INSTRUCTIONS["summary"])

        # Build structured context
        context_text = ""
        added_incidents = 0
        
        for idx, r in enumerate(incidents, 1):
            inc_text = self._build_structured_incident_block(r, idx)
            
            if len(context_text) + len(inc_text) > self.max_context_chars:
                remaining_chars = self.max_context_chars - len(context_text)
                if remaining_chars > 200:
                    context_text += inc_text[:remaining_chars] + "... [TRUNCATED]\n\n"
                    added_incidents += 1
                logger.warning(f"Context length limit reached. Truncated after {added_incidents} items.")
                break
                
            context_text += inc_text
            added_incidents += 1

        user_prompt = (
            f"ANALYTICAL QUERY: {query}\n\n"
            f"RELEVANT INCIDENTS ({added_incidents} retrieved):\n"
            f"{context_text}\n"
            f"Please provide your answer based only on the incidents above.\n\n"
            f"CRITICAL REMINDER: Provide the final answer directly. Do not output 'Question:' or 'Answer:' headers. Do not ask follow-up questions."
        )

        return system_prompt, user_prompt
