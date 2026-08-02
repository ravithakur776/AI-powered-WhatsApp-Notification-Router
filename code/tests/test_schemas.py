"""Unit tests for Pydantic input and output data schemas."""

import pytest
from src.schemas.input_models import RawMessage, UserProfile
from src.schemas.output_models import RouterOutput


def test_raw_message_schema():
    msg = RawMessage(
        message_id="M_1001",
        sender_id="U_101",
        receiver_id="U_102",
        content="Test content",
        timestamp="2026-08-02T11:00:00Z"
    )
    assert msg.message_id == "M_1001"
    assert msg.has_image is False
    assert msg.has_voice_note is False


def test_router_output_schema():
    out = RouterOutput(
        message_id="M_1001",
        action="notify",
        message_type="security_otp",
        reason="OTP verification code received",
        confidence=0.99,
        evidence_message_ids=["M_999"]
    )
    assert out.action == "notify"
    assert out.confidence == 0.99
    assert len(out.evidence_message_ids) == 1


def test_invalid_action_schema():
    with pytest.raises(ValueError):
        RouterOutput(
            message_id="M_1001",
            action="invalid_action",  # Should fail validation
            message_type="test",
            reason="test",
            confidence=0.5
        )
