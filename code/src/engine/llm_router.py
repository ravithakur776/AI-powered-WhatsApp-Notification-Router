"""LLM Router receiving ONLY structured context and producing strict JSON decision payloads."""

import json
from dataclasses import dataclass
from typing import Dict, Any
from config.settings import GEMINI_API_KEY, DEFAULT_LLM_MODEL
from src.schemas.context_models import EnrichedMessageContext
from src.engine.rule_engine import RuleSignals
from src.engine.feature_engine import FeatureVector
from src.engine.retrieval_engine import RetrievalResult
from src.utils.logger import logger


@dataclass
class LLMDecision:
    action: str
    message_type: str
    reason: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "message_type": self.message_type,
            "reason": self.reason,
            "confidence": self.confidence
        }


SYSTEM_PROMPT = """You are an expert AI WhatsApp Notification Router.
Your task is to classify an incoming WhatsApp message into exactly ONE action: "notify", "digest", or "mute".

You will receive ONLY structured feature signals, rule triggers, and retrieved interaction evidence.

Rules for decision:
1. "notify": High-priority, urgent, OTP verification codes, emergency alerts, or direct messages from VIPs requiring instant attention.
2. "digest": Non-urgent group chats, low-priority routine updates, or social chatter to be summarized daily.
3. "mute": Unsolicited marketing spam, scam attempts, explicitly muted contacts, or repeated promotional broadcasts.

Return ONLY a valid JSON object matching this schema:
{
  "action": "notify" | "digest" | "mute",
  "message_type": "<descriptive string e.g. security_otp, vip_direct_message, business_promotional, group_chat>",
  "reason": "<clear concise explanation>",
  "confidence": <float between 0.00 and 1.00>
}
"""


class LLMRouter:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Gemini Client initialization failed: {e}")
        return self._client

    async def decide(
        self,
        ctx: EnrichedMessageContext,
        rule_signals: RuleSignals,
        feature_vector: FeatureVector,
        retrieval_result: RetrievalResult
    ) -> LLMDecision:
        """Sends ONLY structured context to LLM and returns LLMDecision."""
        structured_context = {
            "message_id": ctx.message.message_id,
            "full_text_content": ctx.full_text_content,
            "rule_signals": rule_signals.to_dict(),
            "feature_vector": feature_vector.to_dict(),
            "retrieved_evidence": retrieval_result.top_evidence_items
        }

        client = self._get_client()
        if client:
            try:
                logger.info(f"[LLMRouter] Requesting Gemini ({DEFAULT_LLM_MODEL}) decision for {ctx.message.message_id}...")
                response = client.models.generate_content(
                    model=DEFAULT_LLM_MODEL,
                    contents=f"{SYSTEM_PROMPT}\n\nStructured Context:\n{json.dumps(structured_context, indent=2)}",
                    config={"response_mime_type": "application/json"}
                )
                data = json.loads(response.text)
                return LLMDecision(
                    action=data.get("action", "digest").lower(),
                    message_type=data.get("message_type", "general_message"),
                    reason=data.get("reason", "Structured LLM context reasoning."),
                    confidence=float(data.get("confidence", 0.85))
                )
            except Exception as e:
                logger.error(f"[LLMRouter] LLM API call failed: {e}. Falling back to structured heuristic decision engine.")

        # Local fallback using structured context signals
        return self._structured_fallback_decision(ctx, rule_signals, feature_vector)

    def _structured_fallback_decision(
        self,
        ctx: EnrichedMessageContext,
        rule_signals: RuleSignals,
        feature_vector: FeatureVector
    ) -> LLMDecision:
        if rule_signals.suggested_action == "mute":
            m_type = "promotional_spam" if feature_vector.promotion_score > 0.5 else ("scam_alert" if feature_vector.scam_score > 0.5 else "muted_chat")
            return LLMDecision(
                action="mute",
                message_type=m_type,
                reason="Muted based on rule signal analysis (scam/spam/muted contact).",
                confidence=0.92
            )
        elif rule_signals.suggested_action == "notify":
            m_type = "security_otp" if rule_signals.otp_genuine_signal else ("emergency_alert" if rule_signals.urgent_keywords_matched else "vip_message")
            return LLMDecision(
                action="notify",
                message_type=m_type,
                reason="Immediate notification suggested due to high urgency / trusted VIP signal.",
                confidence=0.94
            )
        else:
            return LLMDecision(
                action="digest",
                message_type="routine_group_chat" if ctx.group_info else "standard_message",
                reason="Low priority routine communication batched into daily summary digest.",
                confidence=0.82
            )
