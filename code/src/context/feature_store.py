"""In-memory microsecond feature store indexing relational entities."""

from typing import Optional
from data.loader import DatasetLoader
from src.schemas.input_models import (
    UserProfile, GroupInfo, BusinessAccount, UserBusinessHistory
)
from src.utils.logger import logger


class FeatureStore:
    def __init__(self, dataset_loader: DatasetLoader):
        self.loader = dataset_loader
        logger.info("FeatureStore initialized with in-memory indexes.")

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        return self.loader.users.get(user_id)

    def get_group_info(self, group_id: str) -> Optional[GroupInfo]:
        return self.loader.groups.get(group_id)

    def get_business_account(self, business_id: str) -> Optional[BusinessAccount]:
        return self.loader.businesses.get(business_id)

    def get_user_business_history(self, user_id: str, business_id: str) -> Optional[UserBusinessHistory]:
        key = f"{user_id}_{business_id}"
        return self.loader.user_business_histories.get(key)

    def is_user_vip_for_receiver(self, sender_id: str, receiver_id: str) -> bool:
        receiver = self.get_user_profile(receiver_id)
        if receiver and sender_id in receiver.vip_contacts:
            return True
        return False

    def is_sender_muted_by_receiver(self, sender_id: str, receiver_id: str) -> bool:
        receiver = self.get_user_profile(receiver_id)
        if receiver and sender_id in receiver.muted_contacts:
            return True
        return False

    def is_group_muted_by_user(self, group_id: str, user_id: str) -> bool:
        user = self.get_user_profile(user_id)
        if user and group_id in user.muted_groups:
            return True
        # Check group member level mute settings
        for member in self.loader.group_members:
            if member.group_id == group_id and member.user_id == user_id:
                if member.is_muted:
                    return True
        return False
