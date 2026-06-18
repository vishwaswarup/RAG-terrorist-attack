import logging
import re
from retrieval.retrieval_engine import RetrievalEngine
from .llm_client import LLMClient
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

BROAD_ANALYTICAL_INDICATORS = [
    "compare", "comparison", "versus", "vs", "difference between",
    "most common", "top", "trend", "trends", "across india", 
    "nationwide", "statistics", "statistical", "frequency", "distribution"
]

def is_broad_analytical_query(query: str) -> bool:
    q_lower = query.lower()
    for indicator in BROAD_ANALYTICAL_INDICATORS:
        if re.search(r'\b' + re.escape(indicator) + r'\b', q_lower):
            return True
    return False

class RAGEngine:
    """
    Orchestrates Retrieval and LLM Generation.
    """
    def __init__(self, retrieval_engine: RetrievalEngine, model_name: str = "phi3:mini", max_context_tokens: int = 3000):
        self.retrieval_engine = retrieval_engine
        self.llm_client = LLMClient(model_name=model_name)
        self.prompt_builder = PromptBuilder(max_context_tokens=max_context_tokens)

    def query(self, user_query: str, top_k: int = 10, similarity_window: float = 0.05) -> str:
        """
        Executes an end-to-end RAG workflow.
        """
        logger.info(f"Executing RAG query: '{user_query}'")
        
        if is_broad_analytical_query(user_query):
            logger.info("Query classified as BROAD_ANALYTICAL_QUERY. Short-circuiting.")
            return "Broad statistical analysis is not currently supported by the retrieval engine. Please ask about a specific group, region, attack type, or incident."
        
        # 1. Retrieve
        results = self.retrieval_engine.search(user_query, top_k=top_k, similarity_window=similarity_window)
        if not results:
            return "No relevant incidents found for the query."
            
        logger.info(f"Retrieved {len(results)} relevant incidents after filtering.")

        print("\n===== RETRIEVED INCIDENTS =====")
        for r in results:
            print(r.score)
            print(r.incident.retrieval_text[:300])

        # 2. Build Prompt
        system_prompt, user_prompt = self.prompt_builder.build_prompt(user_query, results)

        # 3. Generate
        synthesis = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        
        return synthesis
