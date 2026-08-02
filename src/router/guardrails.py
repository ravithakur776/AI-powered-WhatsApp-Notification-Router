"""Guardrails & Output Validation layer ensuring strict schema compliance."""

from src.schemas.output_models import RouterOutput
from src.utils.logger import logger


class OutputGuardrails:
    @staticmethod
    def validate_and_sanitize(output: RouterOutput) -> RouterOutput:
        """Sanitizes confidence bounds, ensures non-empty reasons, and cleans evidence IDs."""
        # 1. Clamp confidence score between 0.0 and 1.0
        clamped_confidence = max(0.0, min(1.0, round(output.confidence, 4)))
        
        # 2. Ensure non-empty reason
        reason_text = output.reason.strip() if output.reason and output.reason.strip() else "Message classified according to personalized router policies."

        # 3. Deduplicate evidence message IDs
        clean_evidence = list(dict.fromkeys(output.evidence_message_ids)) if output.evidence_message_ids else []

        # 4. Valid actions check
        valid_actions = {"notify", "digest", "mute"}
        sanitized_action = output.action if output.action in valid_actions else "digest"

        sanitized = RouterOutput(
            message_id=output.message_id,
            action=sanitized_action,
            message_type=output.message_type or "unclassified",
            reason=reason_text,
            confidence=clamped_confidence,
            evidence_message_ids=clean_evidence
        )

        logger.debug(f"[Guardrails] Verified message {output.message_id} payload.")
        return sanitized
