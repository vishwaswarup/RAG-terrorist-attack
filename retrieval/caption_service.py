import os
import logging
from PIL import Image

class CaptionService:
    """
    A Singleton service for generating offline image captions using BLIP.
    """
    _instance = None 

    def __new__(cls, model_name: str = "Salesforce/blip-image-captioning-base"):
        if cls._instance is None:
            cls._instance = super(CaptionService, cls).__new__(cls)
            cls._instance._initialize(model_name)
        return cls._instance

    def _initialize(self, model_name: str):
        self.model_name = model_name
        logging.info(f"Loading captioning model: {self.model_name}...")
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import torch
        except ImportError:
            logging.error("transformers is not installed.")
            self.model = None
            self.processor = None
            return

        # Try offline first
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        self.device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

        try:
            self.processor = BlipProcessor.from_pretrained(self.model_name, local_files_only=True)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_name, local_files_only=True).to(self.device)
            logging.info("Captioning model loaded successfully from local cache.")
        except Exception as e:
            logging.warning(f"Failed to load model locally: {e}. Attempting download...")
            os.environ["HF_HUB_OFFLINE"] = "0"
            os.environ["TRANSFORMERS_OFFLINE"] = "0"
            try:
                self.processor = BlipProcessor.from_pretrained(self.model_name)
                self.model = BlipForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
                logging.info("Successfully downloaded and cached captioning model.")
            except Exception as e2:
                logging.error(f"Failed to download captioning model: {e2}")
                self.model = None
                self.processor = None
            finally:
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"

    def generate_caption(self, image: Image.Image) -> str:
        """
        Generates a text description for a given PIL Image.
        """
        if self.model is None or self.processor is None:
            logging.warning("Captioning model is not initialized. Skipping caption.")
            return ""
            
        try:
            import torch
            # unconditionally generate text
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                out = self.model.generate(**inputs, max_new_tokens=50)
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            return caption.strip()
        except Exception as e:
            logging.error(f"Caption generation failed: {e}")
            return ""
