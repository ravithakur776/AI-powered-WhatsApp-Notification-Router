"""Feature Engine computing quantitative FeatureVector dataclass."""

from dataclasses import dataclass, asdict
from typing import Dict, Any
from src.schemas.context_models import EnrichedMessageContext
from src.engine.rule_engine import RuleSignals
from src.utils.logger import logger


@dataclass
class FeatureVector:
    urgency_score: float = 0.0           # 0.0 to 1.0
    sender_trust: float = 0.5            # 0.0 to 1.0
    business_trust: float = 0.5          # 0.0 to 1.0
    user_engagement_score: float = 0.5   # 0.0 to 1.0
    quiet_hours: float = 0.0             # 0.0 or 1.0
    notification_load: float = 0.5       # 0.0 to 1.0
    group_importance: float = 0.5        # 0.0 to 1.0
    promotion_score: float = 0.0         # 0.0 to 1.0
    scam_score: float = 0.0              # 0.0 to 1.0
    duplicate_score: float = 0.0         # 0.0 to 1.0
    forwarding_score: float = 0.0        # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeatureEngine:
    """Computes a normalized FeatureVector for contextual evaluation."""

    def extract_features(self, ctx: EnrichedMessageContext, rule_signals: RuleSignals) -> FeatureVector:
        fv = FeatureVector()

        # 1. Urgency Score
        urgency_components = []
        if rule_signals.urgent_keywords_matched:
            urgency_components.append(0.9)
        if rule_signals.otp_genuine_signal:
            urgency_components.append(0.95)
        if "critical" in ctx.full_text_content.lower() or "production" in ctx.full_text_content.lower():
            urgency_components.append(0.85)
        fv.urgency_score = round(max(urgency_components), 4) if urgency_components else 0.1

        # 2. Sender Trust Score
        if ctx.is_sender_vip:
            fv.sender_trust = 1.0
        elif ctx.is_sender_muted:
            fv.sender_trust = 0.0
        elif ctx.recent_interaction_history:
            # Check ratio of positive actions (notify/read) vs mute
            positive_count = sum(1 for h in ctx.recent_interaction_history if h.user_action_taken in {"notify", "read"})
            fv.sender_trust = round(positive_count / len(ctx.recent_interaction_history), 4)
        else:
            fv.sender_trust = 0.5

        # 3. Business Trust Score
        if ctx.business_info:
            if ctx.business_info.verification_status:
                base_trust = 0.8
                if ctx.user_business_history:
                    # Transaction count bonus
                    base_trust += min(0.2, ctx.user_business_history.total_transactions * 0.02)
                fv.business_trust = round(min(1.0, base_trust), 4)
            else:
                fv.business_trust = 0.2
        else:
            fv.business_trust = 0.5

        # 4. User Engagement Score
        if ctx.recent_interaction_history:
            read_or_notify = sum(1 for h in ctx.recent_interaction_history if h.user_action_taken in {"notify", "read"})
            fv.user_engagement_score = round(read_or_notify / len(ctx.recent_interaction_history), 4)
        else:
            fv.user_engagement_score = 0.5

        # 5. Quiet Hours
        fv.quiet_hours = 1.0 if ctx.is_quiet_hours else 0.0

        # 6. Notification Load
        # Standard load calculation normalized around 50 messages per day
        fv.notification_load = 0.5

        # 7. Group Importance Score
        if ctx.group_info:
            if ctx.is_group_muted:
                fv.group_importance = 0.0
            else:
                fv.group_importance = round(ctx.group_info.importance_score, 4)
        else:
            fv.group_importance = 0.7  # Direct messages default higher than group

        # 8. Promotion Score
        fv.promotion_score = round(min(1.0, rule_signals.spam_signal + (0.4 if rule_signals.repeated_promotions_signal else 0.0)), 4)

        # 9. Scam Score
        fv.scam_score = round(min(1.0, rule_signals.scam_signal + (0.5 if rule_signals.suspicious_domain_detected else 0.0)), 4)

        # 10. Duplicate Score
        if ctx.historical_similar_messages:
            # Check if identical message content exists
            query_content = ctx.full_text_content.strip()
            exact_matches = sum(1 for h in ctx.historical_similar_messages if h.message_content.strip() == query_content)
            fv.duplicate_score = round(min(1.0, exact_matches * 0.5), 4)

        # 11. Forwarding Score
        fv.forwarding_score = round(min(1.0, ctx.message.forward_count / 5.0 + (0.5 if ctx.message.is_forwarded else 0.0)), 4)

        logger.debug(f"[FeatureEngine] Extracted FeatureVector for msg {ctx.message.message_id}: {fv.to_dict()}")
        return fv
