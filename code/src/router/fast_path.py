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

        # Helper to extract relevant evidence IDs from context
        evidence_ids = [h.history_id for h in (ctx.recent_interaction_history or ctx.historical_similar_messages)[:3]]

        # 1. Direct Mute Rules (Explicit user preference)
        if ctx.is_sender_muted:
            logger.info(f"[FastPath] Message {msg_id} muted: Sender is in muted contacts.")
            return RouterOutput(
                message_id=msg_id,
                action="mute",
                message_type="muted_sender",
                reason="Sender is explicitly listed in receiver's muted contacts list.",
                confidence=0.96,
                evidence_message_ids=evidence_ids
            )

        if ctx.is_group_muted:
            logger.info(f"[FastPath] Message {msg_id} muted: Group is muted by user.")
            return RouterOutput(
                message_id=msg_id,
                action="mute",
                message_type="muted_group",
                reason="Group is explicitly muted by the user.",
                confidence=0.96,
                evidence_message_ids=evidence_ids
            )

        # 2. Security & Verification OTP (Instant Notification if trusted sender and no scam indicators)
        if any(keyword in text_lower for keyword in OTP_KEYWORDS):
            # Check for scam indicators before fast-path routing
            if not ("http" in text_lower or "bit.ly" in text_lower or "share pin" in text_lower):
                is_verified_bank = ctx.business_info and ctx.business_info.verification_status if ctx.business_info else False
                conf = 0.98 if is_verified_bank else 0.92
                logger.info(f"[FastPath] Message {msg_id} notify: Genuine OTP / Verification code detected.")
                return RouterOutput(
                    message_id=msg_id,
                    action="notify",
                    message_type="security_otp",
                    reason="Time-sensitive authentication OTP detected from valid sender. Requires immediate user notification.",
                    confidence=conf,
                    evidence_message_ids=evidence_ids
                )

        # 3. Emergency & Safety Alerts (Instant Notification regardless of quiet hours)
        if any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS):
            logger.info(f"[FastPath] Message {msg_id} notify: Emergency keyword detected.")
            return RouterOutput(
                message_id=msg_id,
                action="notify",
                message_type="emergency_alert",
                reason="Emergency alert keyword identified. High priority immediate delivery.",
                confidence=0.96,
                evidence_message_ids=evidence_ids
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
                    confidence=0.94,
                    evidence_message_ids=evidence_ids
                )
            else:
                logger.info(f"[FastPath] Message {msg_id} digest: Sender is VIP but quiet hours active.")
                return RouterOutput(
                    message_id=msg_id,
                    action="digest",
                    message_type="vip_quiet_hours",
                    reason="VIP message received during user's quiet hours. Added to digest.",
                    confidence=0.88,
                    evidence_message_ids=evidence_ids
                )

        # 5. Direct Mention in Group Chat (Instant Notification if not quiet hours)
        receiver_name = ctx.receiver_profile.name if ctx.receiver_profile else ""
        is_mentioned = (receiver_name and f"@{receiver_name.split()[0].lower()}" in text_lower) or (ctx.message.receiver_id in ctx.message.mentions)
        if is_mentioned and ctx.message.group_id and not ctx.is_quiet_hours and not ctx.is_group_muted:
            logger.info(f"[FastPath] Message {msg_id} notify: Direct user mention in group.")
            return RouterOutput(
                message_id=msg_id,
                action="notify",
                message_type="group_mention",
                reason="Direct @mention received in group conversation.",
                confidence=0.90,
                evidence_message_ids=evidence_ids
            )

        # 6. Business Promotional Messages without opt-in
        if ctx.message.is_business and ctx.user_business_history:
            if not ctx.user_business_history.opt_in_promotions and any(kw in text_lower for kw in PROMOTIONAL_KEYWORDS):
                logger.info(f"[FastPath] Message {msg_id} mute: Promotional broadcast without opt-in.")
                return RouterOutput(
                    message_id=msg_id,
                    action="mute",
                    message_type="business_promotional",
                    reason="Promotional marketing message from business without user opt-in.",
                    confidence=0.93,
                    evidence_message_ids=evidence_ids
                )

        # No fast-path match -> Escalate to Deep-Path LLM
        return None



        # No fast-path match -> Escalate to Deep-Path LLM
        return None
