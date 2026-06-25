import os
import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class EmbeddingService:
    """
    A Singleton service for generating embeddings using local models.
    Supports both BGE (SentenceTransformer) for text and OpenCLIP for multimodal.
    """
    _instance = None 

    def __new__(cls, text_model_name: str = "BAAI/bge-small-en-v1.5", clip_model_name: str = "ViT-B-32", clip_pretrained: str = "laion2b_s34b_b79k"):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize(text_model_name, clip_model_name, clip_pretrained)
        return cls._instance

    def _initialize(self, text_model_name: str, clip_model_name: str, clip_pretrained: str):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is not installed. Please install it to use EmbeddingService.")
        
        # Enforce strict offline mode for HuggingFace and Transformers
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        
        # Initialize BGE Text Model
        self.text_model_name = text_model_name
        logging.info(f"Loading text embedding model: {self.text_model_name}...")
        try:
            self.text_model = SentenceTransformer(self.text_model_name, local_files_only=True)
            logging.info("Text embedding model loaded successfully from local cache.")
        except Exception as e:
            logging.error(f"Failed to load text model locally: {e}")
            # Try to load it online if offline fails (useful for first run)
            try:
                logging.info(f"Attempting to download {self.text_model_name}...")
                os.environ["HF_HUB_OFFLINE"] = "0"
                os.environ["TRANSFORMERS_OFFLINE"] = "0"
                self.text_model = SentenceTransformer(self.text_model_name)
                logging.info(f"Successfully downloaded and cached {self.text_model_name}.")
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
            except Exception as e2:
                raise RuntimeError(f"Could not load or download text model '{self.text_model_name}': {e2}")

        # Initialize OpenCLIP Multimodal Model
        self.clip_model_name = clip_model_name
        self.clip_pretrained = clip_pretrained
        logging.info(f"Loading OpenCLIP model: {self.clip_model_name} ({self.clip_pretrained})...")
        try:
            import open_clip
            import torch
            
            # Using cache_dir from open_clip default or checking if it exists
            # We don't enforce strict offline here as open_clip handles its own cache, 
            # but we will try to load it and if it fails, download it.
            self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
                self.clip_model_name, 
                pretrained=self.clip_pretrained
            )
            self.clip_tokenizer = open_clip.get_tokenizer(self.clip_model_name)
            self.device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
            self.clip_model = self.clip_model.to(self.device)
            logging.info("OpenCLIP model loaded successfully.")
        except ImportError:
            logging.error("open_clip_torch is not installed. Please install it to use multimodal features.")
            self.clip_model = None
        except Exception as e:
            logging.error(f"Failed to load OpenCLIP model: {e}")
            self.clip_model = None

    def embed_queries(self, queries: list[str]) -> list[list[float]]:
        """
        Embeds a batch of queries using the BGE text model.
        """
        if "bge" in self.text_model_name.lower():
            prefix = "Represent this sentence for searching relevant passages: "
            queries = [prefix + q for q in queries]
        
        embeddings = self.text_model.encode(queries, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """
        Embeds a batch of documents using the BGE text model.
        """
        embeddings = self.text_model.encode(documents, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()
        
    def embed_images(self, images: list) -> list[list[float]]:
        """
        Embeds a batch of PIL Images using OpenCLIP.
        """
        if self.clip_model is None:
            raise RuntimeError("OpenCLIP model is not initialized.")
            
        import torch
        with torch.no_grad(), torch.cuda.amp.autocast() if torch.cuda.is_available() else torch.cpu.amp.autocast():
            # Preprocess images
            image_tensors = torch.stack([self.clip_preprocess(img) for img in images]).to(self.device)
            image_features = self.clip_model.encode_image(image_tensors)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().tolist()
            
    def embed_text_for_image_search(self, queries: list[str]) -> list[list[float]]:
        """
        Embeds a batch of queries using OpenCLIP's text encoder.
        This is required to search against image embeddings because BGE and CLIP 
        operate in completely different vector spaces.
        """
        if self.clip_model is None:
            raise RuntimeError("OpenCLIP model is not initialized.")
            
        import torch
        with torch.no_grad(), torch.cuda.amp.autocast() if torch.cuda.is_available() else torch.cpu.amp.autocast():
            text_tokens = self.clip_tokenizer(queries).to(self.device)
            text_features = self.clip_model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            return text_features.cpu().tolist()
