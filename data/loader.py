"""Dataset loader parsing CSV files into strongly-typed Pydantic models."""

import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from config.settings import DATA_DIR
from data.generator import generate_synthetic_dataset
from src.schemas.input_models import (
    RawMessage, UserProfile, GroupInfo, GroupMember, BusinessAccount,
    UserBusinessHistory, MessageHistory, MessageEvent, ImageData,
    VoiceNoteData, DailyNotificationSummary
)
from src.utils.logger import logger


class DatasetLoader:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.ensure_dataset_exists()
        
        self.users: Dict[str, UserProfile] = {}
        self.groups: Dict[str, GroupInfo] = {}
        self.group_members: List[GroupMember] = []
        self.businesses: Dict[str, BusinessAccount] = {}
        self.user_business_histories: Dict[str, UserBusinessHistory] = {}
        self.messages: List[RawMessage] = []
        self.message_histories: List[MessageHistory] = []
        self.message_events: List[MessageEvent] = []
        self.images: Dict[str, ImageData] = {}
        self.voice_notes: Dict[str, VoiceNoteData] = {}
        self.daily_summaries: List[DailyNotificationSummary] = []
        
        self.load_all()

    def ensure_dataset_exists(self):
        if not (self.data_dir / "messages.csv").exists():
            logger.warning(f"Dataset missing at {self.data_dir}. Generating synthetic dataset...")
            generate_synthetic_dataset()

    def load_all(self):
        """Loads all CSV files into structured dictionaries and lists."""
        logger.info(f"Loading dataset from {self.data_dir}")
        self._load_users()
        self._load_groups()
        self._load_group_members()
        self._load_businesses()
        self._load_user_business_history()
        self._load_messages()
        self._load_message_history()
        self._load_message_events()
        self._load_images()
        self._load_voice_notes()
        self._load_daily_summaries()
        logger.info(f"Dataset loaded: {len(self.messages)} messages, {len(self.users)} users, {len(self.groups)} groups.")

    def _load_users(self):
        path = self.data_dir / "users.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            vip = [x.strip() for x in str(row["vip_contacts"]).split(",") if x.strip()]
            muted_c = [x.strip() for x in str(row["muted_contacts"]).split(",") if x.strip()]
            muted_g = [x.strip() for x in str(row["muted_groups"]).split(",") if x.strip()]
            user = UserProfile(
                user_id=str(row["user_id"]),
                name=str(row["name"]),
                vip_contacts=vip,
                muted_contacts=muted_c,
                muted_groups=muted_g,
                notification_preference=str(row.get("notification_preference", "balanced")),
                quiet_hours_start=str(row.get("quiet_hours_start", "22:00")),
                quiet_hours_end=str(row.get("quiet_hours_end", "07:00")),
            )
            self.users[user.user_id] = user

    def _load_groups(self):
        path = self.data_dir / "groups.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            group = GroupInfo(
                group_id=str(row["group_id"]),
                group_name=str(row["group_name"]),
                category=str(row["category"]),
                importance_score=float(row.get("importance_score", 0.5)),
                is_announcement_only=bool(row.get("is_announcement_only", False))
            )
            self.groups[group.group_id] = group

    def _load_group_members(self):
        path = self.data_dir / "group_members.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            member = GroupMember(
                group_id=str(row["group_id"]),
                user_id=str(row["user_id"]),
                role=str(row.get("role", "member")),
                is_muted=bool(row.get("is_muted", False))
            )
            self.group_members.append(member)

    def _load_businesses(self):
        path = self.data_dir / "business_accounts.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            biz = BusinessAccount(
                business_id=str(row["business_id"]),
                business_name=str(row["business_name"]),
                category=str(row["category"]),
                verification_status=bool(row.get("verification_status", True))
            )
            self.businesses[biz.business_id] = biz

    def _load_user_business_history(self):
        path = self.data_dir / "user_business_history.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            ubh = UserBusinessHistory(
                user_id=str(row["user_id"]),
                business_id=str(row["business_id"]),
                total_transactions=int(row.get("total_transactions", 0)),
                opt_in_promotions=bool(row.get("opt_in_promotions", False)),
                last_interaction_timestamp=str(row.get("last_interaction_timestamp", ""))
            )
            key = f"{ubh.user_id}_{ubh.business_id}"
            self.user_business_histories[key] = ubh

    def _load_messages(self):
        path = self.data_dir / "messages.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            msg = RawMessage(
                message_id=str(row["message_id"]),
                sender_id=str(row["sender_id"]),
                receiver_id=str(row["receiver_id"]),
                group_id=str(row["group_id"]) if str(row["group_id"]).strip() else None,
                content=str(row["content"]),
                timestamp=str(row["timestamp"]),
                has_image=bool(row.get("has_image", False)),
                has_voice_note=bool(row.get("has_voice_note", False)),
                image_file=str(row.get("image_file", "")) if str(row.get("image_file", "")).strip() else None,
                voice_note_file=str(row.get("voice_note_file", "")) if str(row.get("voice_note_file", "")).strip() else None,
                is_business=bool(row.get("is_business", False))
            )
            self.messages.append(msg)

    def _load_message_history(self):
        path = self.data_dir / "message_history.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            mh = MessageHistory(
                history_id=str(row["history_id"]),
                user_id=str(row["user_id"]),
                peer_id=str(row["peer_id"]),
                message_content=str(row["message_content"]),
                user_action_taken=str(row["user_action_taken"]),
                timestamp=str(row["timestamp"])
            )
            self.message_histories.append(mh)

    def _load_message_events(self):
        path = self.data_dir / "message_events.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            me = MessageEvent(
                event_id=str(row["event_id"]),
                message_id=str(row["message_id"]),
                event_type=str(row["event_type"]),
                timestamp=str(row["timestamp"])
            )
            self.message_events.append(me)

    def _load_images(self):
        path = self.data_dir / "images.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            img = ImageData(
                image_id=str(row["image_id"]),
                message_id=str(row["message_id"]),
                file_path=str(row["file_path"]),
                ocr_text=str(row.get("ocr_text", ""))
            )
            self.images[img.message_id] = img

    def _load_voice_notes(self):
        path = self.data_dir / "voice_notes.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            vn = VoiceNoteData(
                voice_note_id=str(row["voice_note_id"]),
                message_id=str(row["message_id"]),
                file_path=str(row["file_path"]),
                duration_seconds=float(row.get("duration_seconds", 0.0)),
                transcription=str(row.get("transcription", ""))
            )
            self.voice_notes[vn.message_id] = vn

    def _load_daily_summaries(self):
        path = self.data_dir / "daily_notification_summary.csv"
        if not path.exists(): return
        df = pd.read_csv(path).fillna("")
        for _, row in df.iterrows():
            ds = DailyNotificationSummary(
                user_id=str(row["user_id"]),
                date=str(row["date"]),
                total_notified=int(row.get("total_notified", 0)),
                total_digested=int(row.get("total_digested", 0)),
                total_muted=int(row.get("total_muted", 0))
            )
            self.daily_summaries.append(ds)
