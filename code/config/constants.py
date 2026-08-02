"""Constants and Enums for the WhatsApp Notification Router."""

from enum import Enum


class ActionEnum(str, Enum):
    NOTIFY = "notify"
    DIGEST = "digest"
    MUTE = "mute"


class MessageTypeEnum(str, Enum):
    DIRECT_MESSAGE = "direct_message"
    GROUP_MENTION = "group_mention"
    GROUP_CHAT = "group_chat"
    BUSINESS_PROMOTIONAL = "business_promotional"
    BUSINESS_TRANSACTIONAL = "business_transactional"
    SECURITY_OTP = "security_otp"
    EMERGENCY_ALERT = "emergency_alert"
    MEDIA_IMAGE = "media_image"
    VOICE_NOTE = "voice_note"
    SYSTEM_NOTIFICATION = "system_notification"


# Keywords for sub-5ms Fast-Path heuristic engine
OTP_KEYWORDS = {"otp", "verification code", "verify your account", "auth code", "login code", "passcode", "2fa"}
EMERGENCY_KEYWORDS = {"emergency", "urgent help", "hospital", "sos", "accident", "blood required", "ambulance", "critical alert"}
PROMOTIONAL_KEYWORDS = {"off", "discount", "buy 1 get 1", "sale", "limited offer", "cashback", "coupon", "promo", "deal of the day"}

# Default Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.60
