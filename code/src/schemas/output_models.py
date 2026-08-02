"""Pydantic output schema strictly matching hackathon evaluation requirements."""

from typing import List, Literal
from pydantic import BaseModel, Field


class RouterOutput(BaseModel):
    message_id: str = Field(..., description="Unique message identifier matching input")
    action: Literal["notify", "digest", "mute"] = Field(
        ..., description="Routing decision: notify immediately, add to digest, or mute"
    )
    message_type: str = Field(
        ..., description="Category of message e.g. security_otp, direct_message, business_promotional, group_chat"
    )
    reason: str = Field(
        ..., description="Clear human-readable justification for the routing decision"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of the routing decision between 0.0 and 1.0"
    )
    evidence_message_ids: List[str] = Field(
        default_factory=list, description="List of historical message_ids supporting this decision"
    )
