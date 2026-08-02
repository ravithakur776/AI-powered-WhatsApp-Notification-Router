"""Speech-to-Text engine for audio voice notes with Faster-Whisper / preloaded fallback."""

from pathlib import Path
from typing import Optional
from src.utils.logger import logger


class STTEngine:
    def __init__(self):
        self._whisper_model = None

    def transcribe_audio(self, file_path: str, preloaded_transcription: Optional[str] = None) -> str:
        """Transcribes voice note audio into text."""
        if preloaded_transcription and preloaded_transcription.strip():
            logger.debug(f"Using pre-extracted transcription for {file_path}")
            return preloaded_transcription.strip()

        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Voice note audio file does not exist at {file_path}")
            return ""

        try:
            from faster_whisper import WhisperModel
            if self._whisper_model is None:
                logger.info("Loading Faster-Whisper model (small)...")
                self._whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
            segments, _ = self._whisper_model.transcribe(str(path), beam_size=5)
            transcription = " ".join([segment.text for segment in segments]).strip()
            logger.info(f"STT transcribed text: '{transcription}' from {path.name}")
            return transcription
        except Exception as e:
            logger.warning(f"Whisper STT failed for {file_path}: {e}")
            return ""
