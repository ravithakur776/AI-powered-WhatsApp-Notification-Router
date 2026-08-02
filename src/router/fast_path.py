"""Sub-5ms Fast-Path rule engine for deterministic message routing."""

from typing import Optional
from config.constants import ActionEnum, MessageTypeEnum, OTP_KEYWORDS, EMERGENCY_KEYWORDS, PROMOTIONAL_KEYWORDS
from src.schemas.context_models import EnrichedMessageContext
from src.schemas.output_models import RouterOutput
from src.utils.logger import logger


class FastPathRouter:
    """High-speed heuristic engine evaluating deterministic cases in <5ms."""

    def evaluate(self, ctx: EnrichedMessageContext) -> Optional[RouterOutput]:
        msg_id = ctx.message.message_id
        text_lower = ctx.full_text_content.lower()

        # 1. Direct Mute Rules (Explicit user preference)
        if ctx.is_sender_muted:
            logger.info(f"[FastPath] Message {msg_id} muted: Sender is in muted contacts.")
            return RouterOutput(
                message_id=msg_id,
                action="mute",
                message_type="muted_sender",
                reason="Sender is explicitly listed in receiver's muted contacts list.",
                confidence=0.99,
                evidence_message_ids=[]
            )

        if ctx.is_group_muted:
            logger.info(f"[FastPath] Message {msg_id} muted: Group is muted by user.")
            return RouterOutput(
                message_id=msg_id,
                action="mute",
                message_type="muted_group",
                reason="Group is explicitly muted by the user.",
                confidence=0.99,
                evidence_message_ids=[]
            )

        # 2. Security & Verification OTP (Instant Notification)
        if any(keyword in text_lower for keyword in OTP_KEYWORDS):
            logger.info(f"[FastPath] Message {msg_id} notify: OTP / Verification code detected.")
            return RouterOutput(
                message_id=msg_id,
                action="notify",
                message_type="security_otp",
                reason="Time-sensitive authentication OTP detected. Requires immediate user notification.",
                confidence=0.99,
                evidence_message_ids=[]
            )

        # 3. Emergency & Safety Alerts (Instant Notification)
        if any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS):
            logger.info(f"[FastPath] Message {msg_id} notify: Emergency keyword detected.")
            return RouterOutput(
                message_id=msg_id,
                action="notify",
                message_type="emergency_alert",
                reason="Emergency alert keyword identified. High priority immediate delivery.",
                confidence=0.98,
                evidence_message_ids=[]
            )

        # 4. VIP Sender Direct Message (Instant Notification unless quiet hours)
        if ctx.is_sender_vip and not ctx.message.group_id:
            if not ctx.is_quiet_hours:
                logger.info(f"[FastPath] Message {msg_id} notify: Sender is VIP.")
                return RouterOutput(
                    message_id=msg_id,
                    action="notify",
                    message_type="vip_direct_message",
                    reason="Message received from a designated VIP contact.",
                    confidence=0.95,
                    evidence_message_ids=[]
                )
            else:
                logger.info(f"[FastPath] Message {msg_id} digest: Sender is VIP but quiet hours active.")
                return RouterOutput(
                    message_id=msg_id,
                    action="digest",
                    message_type="vip_quiet_hours",
                    reason="VIP message received during user's quiet hours. Added to digest.",
                    confidence=0.90,
                    evidence_message_ids=[]
                )

        # 5. Business Promotional Messages without opt-in
        if ctx.message.is_business and ctx.user_business_history:
            if not ctx.user_business_history.opt_in_promotions and any(kw in text_lower for kw in PROMOTIONAL_KEYWORDS):
                logger.info(f"[FastPath] Message {msg_id} mute: Promotional broadcast without opt-in.")
                return RouterOutput(
                    message_id=msg_id,
                    action="mute",
                    message_type="business_promotional",
                    reason="Promotional marketing message from business without user opt-in.",
                    confidence=0.94,
                    evidence_message_ids=[]
                )

        # No fast-path match -> Escalate to Deep-Path LLM
        return None
