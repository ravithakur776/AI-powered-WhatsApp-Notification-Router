"""Multimodal processor coordinating text, image OCR, and audio voice note transcription."""

import asyncio
from typing import Dict, Tuple, Optional
from src.multimodal.ocr_engine import OCREngine
from src.multimodal.stt_engine import STTEngine
from src.schemas.input_models import RawMessage, ImageData, VoiceNoteData
from src.utils.logger import logger


class MultimodalProcessor:
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.stt_engine = STTEngine()

    async def process_message_multimodal(
        self,
        message: RawMessage,
        image_metadata: Optional[ImageData] = None,
        voice_metadata: Optional[VoiceNoteData] = None
    ) -> Tuple[Optional[str], Optional[str], str]:
        """Asynchronously processes message text, image OCR, and voice note transcription.
        
        Returns:
            Tuple[ocr_text, voice_transcription, consolidated_full_text]
        """
        ocr_text: Optional[str] = None
        voice_transcription: Optional[str] = None

        ocr_task = None
        stt_task = None

        if message.has_image or image_metadata:
            img_file = message.image_file or (image_metadata.file_path if image_metadata else "")
            pre_ocr = image_metadata.ocr_text if image_metadata else None
            ocr_task = asyncio.to_thread(self.ocr_engine.extract_text, img_file, pre_ocr)

        if message.has_voice_note or voice_metadata:
            audio_file = message.voice_note_file or (voice_metadata.file_path if voice_metadata else "")
            pre_stt = voice_metadata.transcription if voice_metadata else None
            stt_task = asyncio.to_thread(self.stt_engine.transcribe_audio, audio_file, pre_stt)

        tasks = []
        if ocr_task: tasks.append(ocr_task)
        if stt_task: tasks.append(stt_task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            res_idx = 0
            if ocr_task:
                res = results[res_idx]
                ocr_text = res if isinstance(res, str) else ""
                res_idx += 1
            if stt_task:
                res = results[res_idx]
                voice_transcription = res if isinstance(res, str) else ""

        # Build full text representation combining raw text + extracted media content
        components = []
        if message.content.strip():
            components.append(f"[Text]: {message.content.strip()}")
        if ocr_text:
            components.append(f"[Image OCR]: {ocr_text}")
        if voice_transcription:
            components.append(f"[Voice Note Audio]: {voice_transcription}")

        consolidated = " | ".join(components) if components else "[Empty Payload]"
        logger.debug(f"Message {message.message_id} consolidated text: {consolidated}")
        return ocr_text, voice_transcription, consolidated
