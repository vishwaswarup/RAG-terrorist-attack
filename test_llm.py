import os
from dotenv import load_dotenv
load_dotenv()
from rag.llm_client import LLMClient
print("Testing LLM:", os.environ.get("LLM_MODEL"))
client = LLMClient()
resp = client.generate("Say 'Hello, Qwen!' and nothing else.", system_prompt="You are a helpful assistant.")
print("Response:", resp)
