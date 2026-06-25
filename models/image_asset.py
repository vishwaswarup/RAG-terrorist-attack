from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ImageAsset:
    """
    A unified internal representation of an ingested image.
    Treated as a first-class knowledge object during retrieval.
    """
    asset_id: str
    filename: str
    ocr_text: str
    caption: str
    source_document_id: str
    image_embedding: List[float] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    # Required field for retrieval engine compatibility
    retrieval_text: str = ""

    def __post_init__(self):
        # The retrieval text combines caption and OCR for text-based queries
        parts = []
        if self.caption:
            parts.append(f"Caption: {self.caption}")
        if self.ocr_text:
            parts.append(f"OCR: {self.ocr_text}")
            
        if not parts:
            self.retrieval_text = "Image with no caption or extracted text."
        else:
            self.retrieval_text = "\n".join(parts)
