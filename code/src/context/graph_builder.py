"""Context Graph Builder constructing EnrichedMessageContext for every incoming message."""

from datetime import datetime
from data.loader import DatasetLoader
from src.context.feature_store import FeatureStore
from src.context.history_rag import HistoryRAG
from src.multimodal.processor import MultimodalProcessor
from src.schemas.input_models import RawMessage
from src.schemas.context_models import EnrichedMessageContext
from src.utils.logger import logger


class ContextGraphBuilder:
    def __init__(self, dataset_loader: DatasetLoader):
        self.loader = dataset_loader
        self.feature_store = FeatureStore(dataset_loader)
        self.rag = HistoryRAG(dataset_loader.message_histories)
        self.multimodal_processor = MultimodalProcessor()

    async def build_context(self, message: RawMessage) -> EnrichedMessageContext:
        """Asynchronously builds unified enriched message context."""
        logger.debug(f"Building context for message {message.message_id}")

        # 1. Fetch relational entities microsecond O(1)
        receiver = self.feature_store.get_user_profile(message.receiver_id)
        sender = self.feature_store.get_user_profile(message.sender_id)
        group = self.feature_store.get_group_info(message.group_id) if message.group_id else None
        
        is_vip = self.feature_store.is_user_vip_for_receiver(message.sender_id, message.receiver_id)
        is_sender_muted = self.feature_store.is_sender_muted_by_receiver(message.sender_id, message.receiver_id)
        is_group_muted = self.feature_store.is_group_muted_by_user(message.group_id, message.receiver_id) if message.group_id else False
        
        business = self.feature_store.get_business_account(message.sender_id) if message.is_business else None
        user_business = self.feature_store.get_user_business_history(message.receiver_id, message.sender_id) if message.is_business else None

        # 2. Extract Multimodal Data (OCR / STT)
        image_meta = self.loader.images.get(message.message_id)
        voice_meta = self.loader.voice_notes.get(message.message_id)
        
        ocr_text, voice_transcription, full_text = await self.multimodal_processor.process_message_multimodal(
            message, image_meta, voice_meta
        )

        # 3. Vector RAG Retrieval over Historical Interactions
        similar_history = self.rag.retrieve_similar_history(
            user_id=message.receiver_id,
            query_text=full_text,
            top_k=3
        )

        recent_history = [
            h for h in self.loader.message_histories
            if h.user_id == message.receiver_id and h.peer_id == message.sender_id
        ][-3:]

        # 4. Check Quiet Hours
        is_quiet_hours = False
        if receiver and receiver.quiet_hours_start and receiver.quiet_hours_end:
            try:
                # Parse timestamp if available e.g. "2026-08-02T11:00:00Z"
                msg_time = datetime.fromisoformat(message.timestamp.replace("Z", "+00:00"))
                curr_hour = msg_time.hour
                q_start = int(receiver.quiet_hours_start.split(":")[0])
                q_end = int(receiver.quiet_hours_end.split(":")[0])
                if q_start > q_end:
                    is_quiet_hours = curr_hour >= q_start or curr_hour < q_end
                else:
                    is_quiet_hours = q_start <= curr_hour < q_end
            except Exception:
                is_quiet_hours = False

        enriched = EnrichedMessageContext(
            message=message,
            receiver_profile=receiver,
            sender_profile=sender,
            group_info=group,
            is_sender_vip=is_vip,
            is_sender_muted=is_sender_muted,
            is_group_muted=is_group_muted,
            business_info=business,
            user_business_history=user_business,
            ocr_extracted_text=ocr_text,
            voice_note_transcription=voice_transcription,
            full_text_content=full_text,
            historical_similar_messages=similar_history,
            recent_interaction_history=recent_history,
            is_quiet_hours=is_quiet_hours
        )

        return enriched
