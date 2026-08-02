"""Multimodal module initializer."""
from src.multimodal.ocr_engine import OCREngine
from src.multimodal.stt_engine import STTEngine
from src.multimodal.processor import MultimodalProcessor

__all__ = ["OCREngine", "STTEngine", "MultimodalProcessor"]
