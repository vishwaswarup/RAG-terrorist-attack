from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SentenceEvent:
    sentence_id: int
    text: str
    date: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    attack_types: list[str] = field(default_factory=list)
    weapon_types: list[str] = field(default_factory=list)
    target_organizations: list[str] = field(default_factory=list)
    responsible_groups: list[str] = field(default_factory=list)
    killed: int = 0
    injured: int = 0
    is_anchor: bool = False
    cluster_id: Optional[int] = None

@dataclass
class EventCluster:
    cluster_id: int
    anchor_sentence: SentenceEvent
    supporting_sentences: list[SentenceEvent] = field(default_factory=list)
    
    @property
    def all_sentences(self) -> list[SentenceEvent]:
        return [self.anchor_sentence] + self.supporting_sentences
