"""Rule Engine producing structured signals from deterministic heuristics."""

import re
from dataclasses import dataclass, field
from typing import List, Set
from src.schemas.context_models import EnrichedMessageContext
from config.constants import OTP_KEYWORDS, EMERGENCY_KEYWORDS, PROMOTIONAL_KEYWORDS
from src.utils.logger import logger


# Pattern regexes for suspicious URLs & domain analysis
SUSPICIOUS_DOMAIN_REGEX = re.compile(
    r'https?://(?:www\.)?(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|cutt\.ly|is\.gd|rb\.gy|v\.ht|ow\.ly|'
    r'[a-zA-Z0-9-]+\.(?:top|xyz|club|work|loan|click|gq|cf|tk|ml|ga|zip|mov)|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[^\s]*',
    re.IGNORECASE
)

SCAM_KEYWORDS: Set[str] = {
    "lottery", "winner", "claim prize", "jackpot", "transfer money", "wire transfer",
    "crypto giveaway", "double your bitcoin", "suspended", "credentials",
    "verify bank", "send pin", "cash prize", "unauthorized access", "click link"
}

SPAM_KEYWORDS: Set[str] = {
    "buy now", "click here", "limited offer", "exclusive deal", "discount code",
    "free gift", "subscribe today", "cheap loans", "fast credit", "earn $", "make money fast"
}



@dataclass
class RuleSignals:
    scam_signal: float = 0.0
    spam_signal: float = 0.0
    excessive_forwarding: bool = False
    suspicious_domain_detected: bool = False
    suspicious_domains_found: List[str] = field(default_factory=list)
    otp_banking_fraud_risk: bool = False
    otp_genuine_signal: bool = False
    repeated_promotions_signal: bool = False
    is_verified_business: bool = False
    is_trusted_contact: bool = False
    is_direct_mention: bool = False
    urgent_keywords_matched: List[str] = field(default_factory=list)
    triggered_rule_names: List[str] = field(default_factory=list)
    suggested_action: str = "digest"
    rule_score_notify: float = 0.0
    rule_score_mute: float = 0.0

    def to_dict(self) -> dict:
        return {
            "scam_signal": self.scam_signal,
            "spam_signal": self.spam_signal,
            "excessive_forwarding": self.excessive_forwarding,
            "suspicious_domain_detected": self.suspicious_domain_detected,
            "suspicious_domains_found": self.suspicious_domains_found,
            "otp_banking_fraud_risk": self.otp_banking_fraud_risk,
            "otp_genuine_signal": self.otp_genuine_signal,
            "repeated_promotions_signal": self.repeated_promotions_signal,
            "is_verified_business": self.is_verified_business,
            "is_trusted_contact": self.is_trusted_contact,
            "is_direct_mention": self.is_direct_mention,
            "urgent_keywords_matched": self.urgent_keywords_matched,
            "triggered_rules": self.triggered_rule_names,
            "suggested_action": self.suggested_action,
            "rule_score_notify": self.rule_score_notify,
            "rule_score_mute": self.rule_score_mute
        }


class RuleEngine:
    """Evaluates message context against deterministic business rules and generates structured signals."""

    def evaluate(self, ctx: EnrichedMessageContext) -> RuleSignals:
        signals = RuleSignals()
        text = ctx.full_text_content
        text_lower = text.lower()
        msg = ctx.message

        # 1. Suspicious Domain Detection
        domains_found = SUSPICIOUS_DOMAIN_REGEX.findall(text)
        if domains_found:
            signals.suspicious_domain_detected = True
            signals.suspicious_domains_found = domains_found
            signals.triggered_rule_names.append("RULE_SUSPICIOUS_DOMAIN")
            signals.scam_signal += 0.5
            signals.rule_score_mute += 0.6


        # 2. Scam Detection
        scam_matches = [kw for kw in SCAM_KEYWORDS if kw in text_lower]
        if scam_matches:
            signals.scam_signal += min(1.0, 0.3 * len(scam_matches))
            signals.triggered_rule_names.append("RULE_SCAM_KEYWORDS_DETECTED")
            signals.rule_score_mute += 0.5

        # 3. Spam Detection & Repeated Promotions
        spam_matches = [kw for kw in SPAM_KEYWORDS if kw in text_lower]
        if spam_matches:
            signals.spam_signal += min(1.0, 0.25 * len(spam_matches))
            signals.triggered_rule_names.append("RULE_SPAM_KEYWORDS_DETECTED")
            signals.rule_score_mute += 0.3

        if ctx.user_business_history and not ctx.user_business_history.opt_in_promotions and any(kw in text_lower for kw in PROMOTIONAL_KEYWORDS):
            signals.repeated_promotions_signal = True
            signals.triggered_rule_names.append("RULE_UNSOLICITED_BUSINESS_PROMOTION")
            signals.rule_score_mute += 0.4

        # 4. Excessive Forwarding Rule
        if msg.forward_count >= 3 or (msg.is_forwarded and "forwarded many times" in text_lower):
            signals.excessive_forwarding = True
            signals.triggered_rule_names.append("RULE_EXCESSIVE_FORWARDING")
            signals.spam_signal += 0.3
            signals.rule_score_mute += 0.3

        # 5. OTP & Banking Fraud Rule
        has_otp_kw = any(kw in text_lower for kw in OTP_KEYWORDS)
        if has_otp_kw:
            if ctx.business_info and ctx.business_info.verification_status and ctx.business_info.category in {"banking", "finance", "auth"}:
                signals.otp_genuine_signal = True
                signals.triggered_rule_names.append("RULE_GENUINE_BANKING_OTP")
                signals.rule_score_notify += 0.9
            elif signals.scam_signal > 0.3 or not ctx.is_sender_vip:
                if any(bad in text_lower for bad in ["share pin", "send otp back", "urgent action required"]):
                    signals.otp_banking_fraud_risk = True
                    signals.triggered_rule_names.append("RULE_OTP_BANKING_FRAUD_RISK")
                    signals.rule_score_mute += 0.8
            else:
                signals.otp_genuine_signal = True
                signals.triggered_rule_names.append("RULE_STANDARD_OTP")
                signals.rule_score_notify += 0.8

        # 6. Verified Business Check
        if ctx.business_info and ctx.business_info.verification_status:
            signals.is_verified_business = True
            signals.triggered_rule_names.append("RULE_VERIFIED_BUSINESS")

        # 7. Trusted Contacts (VIPs / Muted check)
        if ctx.is_sender_vip:
            signals.is_trusted_contact = True
            signals.triggered_rule_names.append("RULE_VIP_TRUSTED_CONTACT")
            signals.rule_score_notify += 0.7
        elif ctx.is_sender_muted or ctx.is_group_muted:
            signals.triggered_rule_names.append("RULE_EXPLICITLY_MUTED_SENDER_OR_GROUP")
            signals.rule_score_mute += 0.9

        # 8. Direct Mentions
        receiver_name = ctx.receiver_profile.name if ctx.receiver_profile else ""
        if receiver_name and f"@{receiver_name.split()[0].lower()}" in text_lower or msg.receiver_id in msg.mentions:
            signals.is_direct_mention = True
            signals.triggered_rule_names.append("RULE_DIRECT_MENTION")
            signals.rule_score_notify += 0.6

        # 9. Urgent Keywords Check
        urgent_matches = [kw for kw in EMERGENCY_KEYWORDS if kw in text_lower]
        if urgent_matches:
            signals.urgent_keywords_matched = urgent_matches
            signals.triggered_rule_names.append("RULE_URGENT_KEYWORDS_FOUND")
            signals.rule_score_notify += 0.8

        # Determine Suggested Action based on net score comparison
        if signals.rule_score_mute > signals.rule_score_notify and signals.rule_score_mute >= 0.5:
            signals.suggested_action = "mute"
        elif signals.rule_score_notify > signals.rule_score_mute and signals.rule_score_notify >= 0.5:
            signals.suggested_action = "notify"
        else:
            signals.suggested_action = "digest"

        logger.debug(f"[RuleEngine] Evaluated message {msg.message_id}. Triggered {len(signals.triggered_rule_names)} rules. Action={signals.suggested_action}")
        return signals
