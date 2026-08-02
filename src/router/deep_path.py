"""Deep-Path LLM Reasoning Engine enforcing Pydantic structured JSON outputs."""

import json
from typing import List, Optional
from config.settings import GEMINI_API_KEY, DEFAULT_LLM_MODEL
from src.schemas.context_models import EnrichedMessageContext
from src.schemas.output_models import RouterOutput
from src.utils.logger import logger


SYSTEM_PROMPT = """You are an expert AI Notification Router for WhatsApp.
Your task is to classify an incoming WhatsApp message into exactly one of three routing actions:
1. "notify": High-priority, urgent, direct messages from VIPs, or time-critical alerts requiring immediate attention.
2. "digest": Low to medium priority messages, non-urgent group chats, or updates to be batched into a daily summary.
3. "mute": Promotional spam, muted group chatter, unsolicited marketing, or irrelevant broadcasts.

Input context includes message text, multimodal image/voice note extractions, user profile preferences, group info, and historical interactions.

Return ONLY a JSON object matching this exact schema:
{
  "message_id": "<string>",
  "action": "notify" | "digest" | "mute",
  "message_type": "<string>",
  "reason": "<string explanation>",
  "confidence": <float between 0.0 and 1.0>,
  "evidence_message_ids": ["<string history_ids>"]
}
"""


class DeepPathRouter:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}")
        return self._client

    async def route_message(self, ctx: EnrichedMessageContext) -> RouterOutput:
        """Invokes LLM reasoning engine to classify message action."""
        msg = ctx.message
        evidence_ids = [h.history_id for h in ctx.historical_similar_messages]

        # Prepare context payload for LLM prompt
        prompt_payload = {
            "message_id": msg.message_id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "is_group": bool(msg.group_id),
            "group_name": ctx.group_info.group_name if ctx.group_info else None,
            "content": ctx.full_text_content,
            "is_sender_vip": ctx.is_sender_vip,
            "is_quiet_hours": ctx.is_quiet_hours,
            "receiver_preference": ctx.receiver_profile.notification_preference if ctx.receiver_profile else "balanced",
            "historical_similar": [
                {"history_id": h.history_id, "content": h.message_content, "user_action": h.user_action_taken}
                for h in ctx.historical_similar_messages
            ]
        }

        client = self._get_client()
        if client:
            try:
                logger.info(f"[DeepPath] Invoking Gemini ({DEFAULT_LLM_MODEL}) for message {msg.message_id}...")
                response = client.models.generate_content(
                    model=DEFAULT_LLM_MODEL,
                    contents=f"{SYSTEM_PROMPT}\n\nMessage Context:\n{json.dumps(prompt_payload, indent=2)}",
                    config={"response_mime_type": "application/json"}
                )
                raw_json = response.text
                data = json.loads(raw_json)
                return RouterOutput(
                    message_id=msg.message_id,
                    action=data.get("action", "digest"),
                    message_type=data.get("message_type", "general_message"),
                    reason=data.get("reason", "LLM classified based on context."),
                    confidence=float(data.get("confidence", 0.85)),
                    evidence_message_ids=data.get("evidence_message_ids", evidence_ids)
                )
            except Exception as e:
                logger.error(f"[DeepPath] LLM invocation failed: {e}. Falling back to rule-assisted heuristic reasoning.")

        # Robust Local Deep-Path Fallback (when API key is offline or unavailable)
        return self._local_fallback_reasoning(ctx, evidence_ids)

    def _local_fallback_reasoning(self, ctx: EnrichedMessageContext, evidence_ids: List[str]) -> RouterOutput:
        msg = ctx.message
        text = ctx.full_text_content.lower()

        if "memory leak" in text or "production" in text or "alert" in text or "urgent" in text:
            return RouterOutput(
                message_id=msg.message_id,
                action="notify",
                message_type="work_incident",
                reason="High severity work incident report detected in content.",
                confidence=0.92,
                evidence_message_ids=evidence_ids
            )
        elif "sale" in text or "discount" in text or "crypto" in text or "offer" in text:
            return RouterOutput(
                message_id=msg.message_id,
                action="mute",
                message_type="promotional_spam",
                reason="Commercial marketing promotion or unsolicited broadcast.",
                confidence=0.90,
                evidence_message_ids=evidence_ids
            )
        elif ctx.group_info and ctx.group_info.importance_score < 0.3:
            return RouterOutput(
                message_id=msg.message_id,
                action="digest",
                message_type="low_priority_group",
                reason="Low priority social group update batched for summary digest.",
                confidence=0.85,
                evidence_message_ids=evidence_ids
            )
        else:
            return RouterOutput(
                message_id=msg.message_id,
                action="digest",
                message_type="standard_message",
                reason="Non-critical standard communication routed to digest.",
                confidence=0.80,
                evidence_message_ids=evidence_ids
            )
