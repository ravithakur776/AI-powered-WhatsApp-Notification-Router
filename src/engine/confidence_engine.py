"""Confidence Engine calculating calibrated confidence scores across rule, retrieval, feature, and LLM signals."""

from dataclasses import dataclass
from typing import Dict, Any
from src.engine.rule_engine import RuleSignals
from src.engine.feature_engine import FeatureVector
from src.engine.retrieval_engine import RetrievalResult
from src.engine.llm_router import LLMDecision
from src.utils.logger import logger


@dataclass
class ConfidenceMetrics:
    final_confidence: float
    rule_agreement_score: float
    retrieval_confidence_score: float
    feature_consistency_score: float
    llm_confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_confidence": round(self.final_confidence, 4),
            "rule_agreement_score": round(self.rule_agreement_score, 4),
            "retrieval_confidence_score": round(self.retrieval_confidence_score, 4),
            "feature_consistency_score": round(self.feature_consistency_score, 4),
            "llm_confidence_score": round(self.llm_confidence_score, 4)
        }


class ConfidenceEngine:
    """Calculates composite calibrated confidence score clamped between 0.0 and 1.0."""

    def calculate_confidence(
        self,
        rule_signals: RuleSignals,
        feature_vector: FeatureVector,
        retrieval_result: RetrievalResult,
        llm_decision: LLMDecision
    ) -> ConfidenceMetrics:
        action = llm_decision.action.lower()

        # 1. Rule Agreement Score
        if rule_signals.suggested_action == action:
            rule_agreement = 1.0
        elif rule_signals.suggested_action == "digest" or action == "digest":
            rule_agreement = 0.65
        else: # Direct conflict (notify vs mute)
            rule_agreement = 0.20

        # 2. Retrieval Confidence Score
        if retrieval_result.ranked_evidence_ids:
            retrieval_conf = retrieval_result.retrieval_confidence
        else:
            # Neutral confidence baseline when user has no prior history with sender
            retrieval_conf = 0.50 if feature_vector.sender_trust == 0.5 else feature_vector.sender_trust

        # 3. Feature Consistency Score
        if action == "notify":
            # High urgency or high sender trust aligns with notify
            consistency = max(feature_vector.urgency_score, feature_vector.sender_trust)
            if feature_vector.scam_score > 0.4:
                consistency *= 0.2  # Heavy penalty if scam score is high
            if feature_vector.quiet_hours == 1.0 and feature_vector.urgency_score < 0.8:
                consistency *= 0.6  # Penalty for non-urgent notifications during quiet hours
        elif action == "mute":
            # High scam, promotion, or low sender trust aligns with mute
            consistency = max(feature_vector.scam_score, feature_vector.promotion_score, 1.0 - feature_vector.sender_trust)
        else: # action == "digest"
            # Low urgency and moderate group importance aligns with digest
            consistency = 1.0 - abs(feature_vector.urgency_score - 0.2)
            if feature_vector.quiet_hours == 1.0:
                consistency = min(1.0, consistency + 0.2)  # Digest preferred during quiet hours


        feature_consistency = max(0.0, min(1.0, round(consistency, 4)))

        # 4. LLM Confidence Score
        llm_conf = max(0.0, min(1.0, llm_decision.confidence))

        # Composite Weighted Calculation
        weighted_conf = (
            (0.30 * rule_agreement) +
            (0.20 * retrieval_conf) +
            (0.25 * feature_consistency) +
            (0.25 * llm_conf)
        )

        final_clamped = max(0.0, min(1.0, round(weighted_conf, 4)))

        metrics = ConfidenceMetrics(
            final_confidence=final_clamped,
            rule_agreement_score=rule_agreement,
            retrieval_confidence_score=retrieval_conf,
            feature_consistency_score=feature_consistency,
            llm_confidence_score=llm_conf
        )

        logger.debug(f"[ConfidenceEngine] Calculated confidence breakdown for action '{action}': {metrics.to_dict()}")
        return metrics
