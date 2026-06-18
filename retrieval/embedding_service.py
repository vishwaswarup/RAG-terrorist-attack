import os
import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class EmbeddingService:
    """
    A Singleton service for generating embeddings using local SentenceTransformer models.
    Operates entirely offline once the model is cached.
    """
    _instance = None

    def __new__(cls, model_name: str = "BAAI/bge-small-en-v1.5"):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize(model_name)
        return cls._instance

    def _initialize(self, model_name: str):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is not installed. Please install it to use EmbeddingService.")
        
        self.model_name = model_name
        logging.info(f"Loading embedding model: {self.model_name}...")
        
        # Enforce strict offline mode for HuggingFace and Transformers
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        
        try:
            self.model = SentenceTransformer(self.model_name, local_files_only=True)
            logging.info("Embedding model loaded successfully from local cache (offline mode).")
        except Exception as e:
            logging.error(f"Failed to load model locally: {e}")
            raise RuntimeError(f"Model must be downloaded before running offline. Run once with WiFi on to cache '{self.model_name}'.")

    def embed_queries(self, queries: list[str]) -> list[list[float]]:
        """
        Embeds a batch of queries. For BGE models, we usually prepend a query instruction, 
        but we'll keep it simple or follow the model's recommendation.
        BGE recommends "Represent this sentence for searching relevant passages: " for queries.
        """
        if "bge" in self.model_name.lower():
            prefix = "Represent this sentence for searching relevant passages: "
            queries = [prefix + q for q in queries]
        
        embeddings = self.model.encode(queries, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """
        Embeds a batch of documents (e.g. Incident retrieval_text).
        Normalizes embeddings to use cosine similarity efficiently via inner product.
        """
        embeddings = self.model.encode(documents, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        return embeddings.tolist()
