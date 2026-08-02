"""Unit tests for the Fast-Path heuristic engine."""

import pytest
from src.schemas.input_models import RawMessage, UserProfile
from src.schemas.context_models import EnrichedMessageContext
from src.router.fast_path import FastPathRouter


def test_fast_path_otp_trigger():
    msg = RawMessage(
        message_id="M_99",
        sender_id="B_01",
        receiver_id="U_01",
        content="Your OTP login code is 554321",
        timestamp="2026-08-02T11:00:00Z"
    )
    ctx = EnrichedMessageContext(
        message=msg,
        full_text_content="[Text]: Your OTP login code is 554321"
    )
    router = FastPathRouter()
    res = router.evaluate(ctx)
    assert res is not None
    assert res.action == "notify"
    assert res.message_type == "security_otp"


def test_fast_path_muted_sender():
    msg = RawMessage(
        message_id="M_100",
        sender_id="U_SPAM",
        receiver_id="U_01",
        content="Hey look at this",
        timestamp="2026-08-02T11:00:00Z"
    )
    ctx = EnrichedMessageContext(
        message=msg,
        is_sender_muted=True,
        full_text_content="[Text]: Hey look at this"
    )
    router = FastPathRouter()
    res = router.evaluate(ctx)
    assert res is not None
    assert res.action == "mute"
