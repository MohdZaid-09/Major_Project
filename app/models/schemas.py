from pydantic import BaseModel
from typing import Optional


class RemedyOption(BaseModel):
    summary: str
    evidence_level: str  # "strong", "moderate", "limited", "traditional/anecdotal"
    precautions: str


class ChatResponse(BaseModel):
    conversational_reply: str
    is_emergency: bool
    allopathic: Optional[RemedyOption] = None
    ayurvedic: Optional[RemedyOption] = None
    unani: Optional[RemedyOption] = None
    homeopathic: Optional[RemedyOption] = None
    language: Optional[str] = None