"""Synthetic dataset generator to ensure dataset directory has valid CSV files and media."""

import os
from pathlib import Path
import pandas as pd
from config.settings import DATA_DIR, MEDIA_DIR


def generate_synthetic_dataset():
    """Generates complete mock CSV dataset matching all hackathon schema requirements if files do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. users.csv
    users_data = [
        {"user_id": "U_101", "name": "Alice Johnson", "vip_contacts": "U_102,U_103", "muted_contacts": "U_105", "muted_groups": "G_99", "notification_preference": "balanced", "quiet_hours_start": "22:00", "quiet_hours_end": "07:00"},
        {"user_id": "U_102", "name": "Bob Smith (VIP)", "vip_contacts": "U_101", "muted_contacts": "", "muted_groups": "", "notification_preference": "strict", "quiet_hours_start": "23:00", "quiet_hours_end": "06:00"},
        {"user_id": "U_103", "name": "Charlie Brown", "vip_contacts": "", "muted_contacts": "", "muted_groups": "G_50", "notification_preference": "permissive", "quiet_hours_start": "00:00", "quiet_hours_end": "06:00"},
        {"user_id": "U_105", "name": "Spammer Dave", "vip_contacts": "", "muted_contacts": "", "muted_groups": "", "notification_preference": "balanced", "quiet_hours_start": "22:00", "quiet_hours_end": "07:00"}
    ]
    pd.DataFrame(users_data).to_csv(DATA_DIR / "users.csv", index=False)

    # 2. groups.csv
    groups_data = [
        {"group_id": "G_10", "group_name": "DevOps Incident Response", "category": "work", "importance_score": 0.95, "is_announcement_only": False},
        {"group_id": "G_50", "group_name": "Weekend Football Banter", "category": "social", "importance_score": 0.20, "is_announcement_only": False},
        {"group_id": "G_99", "group_name": "Meme Central Spammers", "category": "social", "importance_score": 0.05, "is_announcement_only": False}
    ]
    pd.DataFrame(groups_data).to_csv(DATA_DIR / "groups.csv", index=False)

    # 3. group_members.csv
    group_members_data = [
        {"group_id": "G_10", "user_id": "U_101", "role": "admin", "is_muted": False},
        {"group_id": "G_10", "user_id": "U_102", "role": "member", "is_muted": False},
        {"group_id": "G_50", "user_id": "U_101", "role": "member", "is_muted": True},
        {"group_id": "G_99", "user_id": "U_101", "role": "member", "is_muted": True}
    ]
    pd.DataFrame(group_members_data).to_csv(DATA_DIR / "group_members.csv", index=False)

    # 4. business_accounts.csv
    business_data = [
        {"business_id": "B_501", "business_name": "SecureBank Auth Service", "category": "banking", "verification_status": True},
        {"business_id": "B_502", "business_name": "MegaDeals E-Commerce", "category": "marketing", "verification_status": True}
    ]
    pd.DataFrame(business_data).to_csv(DATA_DIR / "business_accounts.csv", index=False)

    # 5. user_business_history.csv
    user_business_data = [
        {"user_id": "U_101", "business_id": "B_501", "total_transactions": 14, "opt_in_promotions": False, "last_interaction_timestamp": "2026-08-01T14:30:00Z"},
        {"user_id": "U_101", "business_id": "B_502", "total_transactions": 1, "opt_in_promotions": True, "last_interaction_timestamp": "2026-07-20T10:15:00Z"}
    ]
    pd.DataFrame(user_business_data).to_csv(DATA_DIR / "user_business_history.csv", index=False)

    # 6. messages.csv
    messages_data = [
        {"message_id": "M_1001", "sender_id": "B_501", "receiver_id": "U_101", "group_id": "", "content": "Your 6-digit verification OTP is 894-120. Valid for 5 mins.", "timestamp": "2026-08-02T11:00:00Z", "has_image": False, "has_voice_note": False, "image_file": "", "voice_note_file": "", "is_business": True},
        {"message_id": "M_1002", "sender_id": "U_102", "receiver_id": "U_101", "group_id": "", "content": "Hey Alice, critical server memory leak in production. Please check!", "timestamp": "2026-08-02T11:05:00Z", "has_image": False, "has_voice_note": False, "image_file": "", "voice_note_file": "", "is_business": False},
        {"message_id": "M_1003", "sender_id": "B_502", "receiver_id": "U_101", "group_id": "", "content": "FLASH SALE! Get 70% OFF on shoes today only! Click link to claim discount.", "timestamp": "2026-08-02T11:10:00Z", "has_image": False, "has_voice_note": False, "image_file": "", "voice_note_file": "", "is_business": True},
        {"message_id": "M_1004", "sender_id": "U_105", "receiver_id": "U_101", "group_id": "", "content": "Buy cheap crypto tokens now before 100x surge!!", "timestamp": "2026-08-02T11:15:00Z", "has_image": False, "has_voice_note": False, "image_file": "", "voice_note_file": "", "is_business": False},
        {"message_id": "M_1005", "sender_id": "U_103", "receiver_id": "U_101", "group_id": "G_99", "content": "Check out this funny dog meme guys haha", "timestamp": "2026-08-02T11:20:00Z", "has_image": True, "has_voice_note": False, "image_file": "meme.jpg", "voice_note_file": "", "is_business": False},
        {"message_id": "M_1006", "sender_id": "U_102", "receiver_id": "U_101", "group_id": "", "content": "", "timestamp": "2026-08-02T11:25:00Z", "has_image": False, "has_voice_note": True, "image_file": "", "voice_note_file": "audio_urgent.mp3", "is_business": False}
    ]
    pd.DataFrame(messages_data).to_csv(DATA_DIR / "messages.csv", index=False)

    # 7. message_history.csv
    message_history_data = [
        {"history_id": "H_01", "user_id": "U_101", "peer_id": "B_501", "message_content": "Your login OTP code is 123456", "user_action_taken": "notify", "timestamp": "2026-08-01T10:00:00Z"},
        {"history_id": "H_02", "user_id": "U_101", "peer_id": "B_502", "message_content": "Weekend mega clearance sale starts now", "user_action_taken": "mute", "timestamp": "2026-07-28T09:00:00Z"},
        {"history_id": "H_03", "user_id": "U_101", "peer_id": "U_105", "message_content": "Free gift card inside click here", "user_action_taken": "mute", "timestamp": "2026-07-25T11:00:00Z"}
    ]
    pd.DataFrame(message_history_data).to_csv(DATA_DIR / "message_history.csv", index=False)

    # 8. message_events.csv
    message_events_data = [
        {"event_id": "E_01", "message_id": "M_1001", "event_type": "read", "timestamp": "2026-08-02T11:01:00Z"},
        {"event_id": "E_02", "message_id": "M_1003", "event_type": "dismissed", "timestamp": "2026-08-02T11:11:00Z"}
    ]
    pd.DataFrame(message_events_data).to_csv(DATA_DIR / "message_events.csv", index=False)

    # 9. images.csv
    images_data = [
        {"image_id": "IMG_01", "message_id": "M_1005", "file_path": "dataset/media/meme.jpg", "ocr_text": "WHEN THE CODE PASSES CI/CD ON THE FIRST TRY! CELEBRATE TIME."}
    ]
    pd.DataFrame(images_data).to_csv(DATA_DIR / "images.csv", index=False)

    # 10. voice_notes.csv
    voice_notes_data = [
        {"voice_note_id": "VN_01", "message_id": "M_1006", "file_path": "dataset/media/audio_urgent.mp3", "duration_seconds": 8.5, "transcription": "Hey Alice, the database cluster CPU is at ninety nine percent. Please call me back immediately!"}
    ]
    pd.DataFrame(voice_notes_data).to_csv(DATA_DIR / "voice_notes.csv", index=False)

    # 11. daily_notification_summary.csv
    daily_summary_data = [
        {"user_id": "U_101", "date": "2026-08-01", "total_notified": 12, "total_digested": 25, "total_muted": 50}
    ]
    pd.DataFrame(daily_summary_data).to_csv(DATA_DIR / "daily_notification_summary.csv", index=False)


if __name__ == "__main__":
    generate_synthetic_dataset()
    print(f"Synthetic dataset generated at {DATA_DIR}")
