"""Retrieval Engine providing multi-factor ranking over historical interaction evidence."""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from src.schemas.input_models import MessageHistory, MessageEvent
from src.context.history_rag import HistoryRAG
from src.utils.logger import logger


@dataclass
class RetrievalResult:
    ranked_evidence_ids: List[str] = field(default_factory=list)
    top_evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    retrieval_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ranked_evidence_ids": self.ranked_evidence_ids,
            "top_evidence_items": self.top_evidence_items,
            "retrieval_confidence": self.retrieval_confidence
        }


class RetrievalEngine:
    """Multi-factor retrieval engine scoring past message logs by similarity, recency, reply, open, and dismiss history."""

    def __init__(self, rag: HistoryRAG, events: List[MessageEvent] = None):
        self.rag = rag
        self.events = events or []

    def rank_evidence(
        self,
        user_id: str,
        query_text: str,
        message_timestamp: str,
        candidates: List[MessageHistory],
        top_k: int = 3
    ) -> RetrievalResult:
        if not candidates:
            return RetrievalResult()

        # Parse message timestamp
        try:
            current_dt = datetime.fromisoformat(message_timestamp.replace("Z", "+00:00"))
        except Exception:
            current_dt = datetime.now()

        # Vector RAG initial similarity scores
        similar_items = self.rag.retrieve_similar_history(user_id=user_id, query_text=query_text, top_k=len(candidates))
        similar_map = {item.history_id: idx for idx, item in enumerate(similar_items)}

        # Pre-build lookup for message events (read, clicked, dismissed)
        event_type_map = {ev.message_id: ev.event_type for ev in self.events}

        scored_candidates = []

        for candidate in candidates:
            # 1. Semantic Similarity Score (0.0 to 1.0)
            rank_idx = similar_map.get(candidate.history_id, len(candidates))
            sim_score = max(0.0, 1.0 - (rank_idx / float(len(candidates))))

            # 2. Recency Score (Exponential Decay)
            try:
                cand_dt = datetime.fromisoformat(candidate.timestamp.replace("Z", "+00:00"))
                days_diff = abs((current_dt - cand_dt).days)
                recency_score = math.exp(-days_diff / 30.0)
            except Exception:
                recency_score = 0.5

            # 3. Reply History Bonus
            reply_bonus = 1.0 if candidate.user_action_taken == "notify" else 0.0

            # 4. Open History Bonus
            ev_type = event_type_map.get(candidate.history_id, "")
            open_bonus = 0.8 if ev_type in {"read", "clicked"} or candidate.user_action_taken == "read" else 0.0

            # 5. Dismiss History Penalty
            dismiss_penalty = 1.0 if ev_type == "dismissed" or candidate.user_action_taken == "mute" else 0.0

            # Composite Weighted Multi-Factor Score
            composite_score = (
                (0.40 * sim_score) +
                (0.25 * recency_score) +
                (0.20 * reply_bonus) +
                (0.15 * open_bonus) -
                (0.20 * dismiss_penalty)
            )
            composite_score = max(0.0, min(1.0, round(composite_score, 4)))

            scored_candidates.append((composite_score, candidate))

        # Sort descending by composite score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        # Filter top evidence candidates above relevance threshold score >= 0.20
        relevant_candidates = [c for c in scored_candidates if c[0] >= 0.20][:top_k]

        evidence_ids = [c[1].history_id for c in relevant_candidates]
        top_items = [
            {
                "history_id": c[1].history_id,
                "content": c[1].message_content,
                "user_action": c[1].user_action_taken,
                "score": c[0]
            }
            for c in relevant_candidates
        ]

        retrieval_conf = relevant_candidates[0][0] if relevant_candidates else 0.0


        logger.debug(f"[RetrievalEngine] Ranked {len(candidates)} items. Top evidence IDs: {evidence_ids} (conf={retrieval_conf})")
        return RetrievalResult(
            ranked_evidence_ids=evidence_ids,
            top_evidence_items=top_items,
            retrieval_confidence=retrieval_conf
        )
