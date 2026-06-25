from dataclasses import dataclass
from typing import Any, Union
from models.incident import Incident
from models.image_asset import ImageAsset

@dataclass
class RetrievalResult:
    """
    Represents a single result returned by the RetrievalEngine.
    
    Fields:
    - payload: The Incident or ImageAsset object.
    - score: The similarity score (distance) computed by Chroma.
    """
    payload: Union[Incident, ImageAsset]
    score: float

    @property
    def incident(self):
        """Backward compatibility property for existing code."""
        return self.payload
