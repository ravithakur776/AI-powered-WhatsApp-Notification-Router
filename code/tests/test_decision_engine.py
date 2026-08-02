"""Unit tests for the 5-Layer Hybrid Decision Engine."""

import asyncio
import pytest
from src.schemas.input_models import RawMessage, UserProfile, MessageHistory
from src.schemas.context_models import EnrichedMessageContext
from src.engine.rule_engine import RuleEngine, RuleSignals
from src.engine.feature_engine import FeatureEngine, FeatureVector
from src.engine.retrieval_engine import RetrievalEngine, RetrievalResult
from src.engine.llm_router import LLMRouter, LLMDecision
from src.engine.confidence_engine import ConfidenceEngine, ConfidenceMetrics
from src.engine.decision_engine import DecisionEngine
from src.context.history_rag import HistoryRAG


def test_rule_engine_signals():
    rule_engine = RuleEngine()
    msg = RawMessage(
        message_id="M_TEST_01",
        sender_id="U_99",
        receiver_id="U_01",
        content="URGENT: Your bank account is suspended! Click http://bit.ly/fake-link to verify pin",
        timestamp="2026-08-02T12:00:00Z"
    )
    ctx = EnrichedMessageContext(
        message=msg,
        full_text_content=msg.content
    )
    signals = rule_engine.evaluate(ctx)

    assert signals.suspicious_domain_detected is True
    assert signals.scam_signal > 0.0
    assert "RULE_SUSPICIOUS_DOMAIN" in signals.triggered_rule_names
    assert signals.suggested_action == "mute"


def test_feature_engine_vector():
    feature_engine = FeatureEngine()
    msg = RawMessage(
        message_id="M_TEST_02",
        sender_id="U_VIP",
        receiver_id="U_01",
        content="Production server emergency! Memory leak detected.",
        timestamp="2026-08-02T12:00:00Z"
    )
    ctx = EnrichedMessageContext(
        message=msg,
        is_sender_vip=True,
        full_text_content=msg.content
    )
    signals = RuleSignals(urgent_keywords_matched=["emergency"])
    fv = feature_engine.extract_features(ctx, signals)

    assert fv.sender_trust == 1.0
    assert fv.urgency_score >= 0.8
    assert fv.quiet_hours == 0.0


def test_retrieval_engine_ranking():
    histories = [
        MessageHistory(history_id="H_1", user_id="U_01", peer_id="U_VIP", message_content="Fix server bug", user_action_taken="notify", timestamp="2026-08-01T10:00:00Z"),
        MessageHistory(history_id="H_2", user_id="U_01", peer_id="U_SPAM", message_content="Buy crypto token", user_action_taken="mute", timestamp="2026-07-20T10:00:00Z")
    ]
    rag = HistoryRAG(histories)
    retrieval_engine = RetrievalEngine(rag)

    res = retrieval_engine.rank_evidence(
        user_id="U_01",
        query_text="Fix production bug urgent",
        message_timestamp="2026-08-02T12:00:00Z",
        candidates=histories
    )

    assert len(res.ranked_evidence_ids) > 0
    assert res.ranked_evidence_ids[0] == "H_1"
    assert 0.0 <= res.retrieval_confidence <= 1.0


def test_confidence_engine_clamping():
    conf_engine = ConfidenceEngine()
    signals = RuleSignals(suggested_action="notify")
    fv = FeatureVector(urgency_score=0.9, sender_trust=1.0)
    ret_res = RetrievalResult(ranked_evidence_ids=["H_1"], retrieval_confidence=0.95)
    llm_dec = LLMDecision(action="notify", message_type="security_otp", reason="OTP test", confidence=0.98)

    metrics = conf_engine.calculate_confidence(signals, fv, ret_res, llm_dec)

    assert 0.0 <= metrics.final_confidence <= 1.0
    assert metrics.rule_agreement_score == 1.0


def test_decision_engine_orchestration():
    async def _test():
        histories = [
            MessageHistory(history_id="H_1", user_id="U_01", peer_id="B_501", message_content="Your OTP code is 123456", user_action_taken="notify", timestamp="2026-08-01T10:00:00Z")
        ]
        rag = HistoryRAG(histories)
        retrieval_engine = RetrievalEngine(rag)
        decision_engine = DecisionEngine(retrieval_engine)

        msg = RawMessage(
            message_id="M_999",
            sender_id="B_501",
            receiver_id="U_01",
            content="Your login verification OTP is 789102",
            timestamp="2026-08-02T12:00:00Z",
            is_business=True
        )
        ctx = EnrichedMessageContext(
            message=msg,
            full_text_content=msg.content,
            historical_similar_messages=histories
        )

        out = await decision_engine.evaluate_message(ctx)

        assert out.message_id == "M_999"
        assert out.action in {"notify", "digest", "mute"}
        assert 0.0 <= out.confidence <= 1.0
        assert isinstance(out.reason, str)

    asyncio.run(_test())
