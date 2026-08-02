"""Pydantic input schemas representing dataset records."""

from typing import Optional, List
from pydantic import BaseModel, Field


class RawMessage(BaseModel):
    message_id: str
    sender_id: str
    receiver_id: str
    group_id: Optional[str] = None
    content: str = ""
    timestamp: str
    has_image: bool = False
    has_voice_note: bool = False
    image_file: Optional[str] = None
    voice_note_file: Optional[str] = None
    is_business: bool = False
    forward_count: int = 0
    is_forwarded: bool = False
    mentions: List[str] = Field(default_factory=list)



class UserProfile(BaseModel):
    user_id: str
    name: str
    vip_contacts: List[str] = Field(default_factory=list)
    muted_contacts: List[str] = Field(default_factory=list)
    muted_groups: List[str] = Field(default_factory=list)
    notification_preference: str = "balanced"  # strict, balanced, permissive
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "07:00"


class GroupInfo(BaseModel):
    group_id: str
    group_name: str
    category: str  # work, family, social, announcement
    importance_score: float = 0.5  # 0.0 to 1.0
    is_announcement_only: bool = False


class GroupMember(BaseModel):
    group_id: str
    user_id: str
    role: str = "member"  # admin, member
    is_muted: bool = False


class BusinessAccount(BaseModel):
    business_id: str
    business_name: str
    category: str  # e-commerce, banking, healthcare, marketing
    verification_status: bool = True


class UserBusinessHistory(BaseModel):
    user_id: str
    business_id: str
    total_transactions: int = 0
    opt_in_promotions: bool = False
    last_interaction_timestamp: Optional[str] = None


class MessageHistory(BaseModel):
    history_id: str
    user_id: str
    peer_id: str
    message_content: str
    user_action_taken: str  # notify, digest, mute
    timestamp: str


class MessageEvent(BaseModel):
    event_id: str
    message_id: str
    event_type: str  # delivered, read, clicked, dismissed
    timestamp: str


class ImageData(BaseModel):
    image_id: str
    message_id: str
    file_path: str
    ocr_text: Optional[str] = None


class VoiceNoteData(BaseModel):
    voice_note_id: str
    message_id: str
    file_path: str
    duration_seconds: float = 0.0
    transcription: Optional[str] = None


class DailyNotificationSummary(BaseModel):
    user_id: str
    date: str
    total_notified: int = 0
    total_digested: int = 0
    total_muted: int = 0
