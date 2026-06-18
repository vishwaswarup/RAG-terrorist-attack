import logging

logger = logging.getLogger(__name__)

# Very rough approximation: 1 token ~= 4 chars for English text
CHARS_PER_TOKEN = 4

class PromptBuilder:
    def __init__(self, max_context_tokens: int = 3000):
        self.max_context_chars = max_context_tokens * CHARS_PER_TOKEN

    def build_prompt(self, query: str, incidents: list) -> tuple[str, str]:
        """
        Takes a query and a list of RetrievalResult objects.
        Returns (system_prompt, user_prompt)
        """
        system_prompt = (
            "You are a Senior Intelligence Analyst. You will be provided with several incident reports.\n"
            "Your task is to answer the user's analytical query based strictly on the provided incidents.\n"
            "Do not speculate beyond the provided context. If information is not present in the retrieved "
            "incidents, state that it is not available in the provided data.\n"
            "\n"
            "Requirements:\n"
            "- Default answer length: 75-120 words unless the user explicitly requests a detailed report, "
            "comprehensive analysis, or a specific word count.\n"
            "- Use factual intelligence-report style.\n"
            "- No speculation, assumptions, or unsupported conclusions.\n"
            "- Use only retrieved context.\n"
            "- Prefer bullet points when multiple attack patterns or trends are identified."
        )

        context_text = ""
        added_incidents = 0
        
        for r in incidents:
            inc_text = f"--- Incident (Score: {r.score:.3f}) ---\n" + r.incident.retrieval_text + "\n\n"
            
            if len(context_text) + len(inc_text) > self.max_context_chars:
                logger.warning(f"Context length limit reached. Truncated after {added_incidents} incidents.")
                break
                
            context_text += inc_text
            added_incidents += 1

        user_prompt = (
            f"ANALYTICAL QUERY: {query}\n\n"
            f"RELEVANT INCIDENTS:\n"
            f"{context_text}\n"
            f"Please provide your synthesis based only on the incidents above.\n\n"
            f"CRITICAL REMINDER: Your response MUST be concise (between 75 to 120 words) "
            f"unless the query explicitly asked for a detailed or comprehensive analysis."
        )

        return system_prompt, user_prompt
