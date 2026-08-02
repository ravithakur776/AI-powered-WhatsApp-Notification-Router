"""Unified enriched context object combining message, relational data, multimodal text, and historical context."""

from typing import Optional, List
from pydantic import BaseModel, Field
from src.schemas.input_models import RawMessage, UserProfile, GroupInfo, BusinessAccount, UserBusinessHistory, MessageHistory


class EnrichedMessageContext(BaseModel):
    message: RawMessage
    receiver_profile: Optional[UserProfile] = None
    sender_profile: Optional[UserProfile] = None
    group_info: Optional[GroupInfo] = None
    is_sender_vip: bool = False
    is_sender_muted: bool = False
    is_group_muted: bool = False
    business_info: Optional[BusinessAccount] = None
    user_business_history: Optional[UserBusinessHistory] = None
    
    # Multimodal Extractions
    ocr_extracted_text: Optional[str] = None
    voice_note_transcription: Optional[str] = None
    full_text_content: str = ""
    
    # RAG Retrieved Historical Context
    historical_similar_messages: List[MessageHistory] = Field(default_factory=list)
    recent_interaction_history: List[MessageHistory] = Field(default_factory=list)
    
    # Temporal & Behavioral Metadata
    is_quiet_hours: bool = False
