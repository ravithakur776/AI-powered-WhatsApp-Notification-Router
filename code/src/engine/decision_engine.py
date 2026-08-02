"""Unified Decision Engine orchestrating Rule, Feature, Retrieval, LLM, and Confidence layers."""

from typing import Tuple
from src.schemas.context_models import EnrichedMessageContext
from src.schemas.output_models import RouterOutput
from src.engine.rule_engine import RuleEngine, RuleSignals
from src.engine.feature_engine import FeatureEngine, FeatureVector
from src.engine.retrieval_engine import RetrievalEngine, RetrievalResult
from src.engine.llm_router import LLMRouter, LLMDecision
from src.engine.confidence_engine import ConfidenceEngine, ConfidenceMetrics
from src.utils.logger import logger


class DecisionEngine:
    """Production 5-Layer Hybrid Decision Engine orchestrator."""

    def __init__(self, retrieval_engine: RetrievalEngine):
        self.rule_engine = RuleEngine()
        self.feature_engine = FeatureEngine()
        self.retrieval_engine = retrieval_engine
        self.llm_router = LLMRouter()
        self.confidence_engine = ConfidenceEngine()

    async def evaluate_message(self, ctx: EnrichedMessageContext) -> RouterOutput:
        """Executes full 5-layer hybrid pipeline and produces final RouterOutput."""
        msg_id = ctx.message.message_id
        logger.info(f"[DecisionEngine] Processing message {msg_id} through 5-layer hybrid pipeline...")

        # 1. Layer 1: Rule Engine
        rule_signals: RuleSignals = self.rule_engine.evaluate(ctx)

        # 2. Layer 2: Feature Engine
        feature_vector: FeatureVector = self.feature_engine.extract_features(ctx, rule_signals)

        # 3. Layer 3: Retrieval Engine
        retrieval_result: RetrievalResult = self.retrieval_engine.rank_evidence(
            user_id=ctx.message.receiver_id,
            query_text=ctx.full_text_content,
            message_timestamp=ctx.message.timestamp,
            candidates=ctx.historical_similar_messages,
            top_k=3
        )

        # 4. Layer 4: LLM Router
        llm_decision: LLMDecision = await self.llm_router.decide(
            ctx=ctx,
            rule_signals=rule_signals,
            feature_vector=feature_vector,
            retrieval_result=retrieval_result
        )

        # 5. Layer 5: Confidence Engine
        confidence_metrics: ConfidenceMetrics = self.confidence_engine.calculate_confidence(
            rule_signals=rule_signals,
            feature_vector=feature_vector,
            retrieval_result=retrieval_result,
            llm_decision=llm_decision
        )

        # Construct Final Pydantic Router Output
        output = RouterOutput(
            message_id=msg_id,
            action=llm_decision.action,
            message_type=llm_decision.message_type,
            reason=llm_decision.reason,
            confidence=confidence_metrics.final_confidence,
            evidence_message_ids=retrieval_result.ranked_evidence_ids
        )

        logger.info(
            f"[DecisionEngine] Completed msg {msg_id} -> Action={output.action.upper()}, "
            f"Type={output.message_type}, Conf={output.confidence:.4f}, Evidence={output.evidence_message_ids}"
        )
        return output
