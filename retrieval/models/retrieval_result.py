from dataclasses import dataclass
from models.incident import Incident

@dataclass
class RetrievalResult:
    """
    Represents a single result returned by the RetrievalEngine.
    
    Fields:
    - incident: The Incident object reconstructed from metadata.
    - score: The similarity score (distance) computed by Chroma.
    """
    incident: Incident
    score: float
