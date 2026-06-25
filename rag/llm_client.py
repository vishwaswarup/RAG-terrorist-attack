import ollama
import logging
import os

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Offline interface to local Ollama.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.environ.get("LLM_MODEL", "qwen3:8b")

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Calls the local Ollama model to generate a response.
        """
        logger.info(f"Calling Ollama model: {self.model_name}")
        logger.debug(f"System prompt length: {len(system_prompt)} chars")
        logger.debug(f"User prompt length: {len(prompt)} chars")

        logger.debug("\n===== SYSTEM PROMPT =====\n%s", system_prompt)
        logger.debug("\n===== USER PROMPT =====\n%s", prompt)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        options = {
            "temperature": 0.1,
            "top_p": 0.8,
            "num_predict": 300,
            "num_ctx": 4096
        }
        
        try:
            response = ollama.chat(
                model=self.model_name, 
                messages=messages,
                options=options
            )
            content = response['message']['content'].strip()
            
            # Post-processing safeguard to ensure grammatically complete ending
            valid_enders = ('.', '!', '?', ':')
            if content and not content.endswith(valid_enders):
                last_idx = max(content.rfind(e) for e in valid_enders)
                if last_idx != -1:
                    content = content[:last_idx+1].strip()
            
            logger.debug(f"Generated response length: {len(content)} chars")
            return content
        except Exception as e:
            logger.error(f"Failed to generate response from Ollama: {e}")
            raise
