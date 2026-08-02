"""OCR Engine extracting text from image attachments with fallback cascade."""

from pathlib import Path
from typing import Optional
from src.utils.logger import logger


class OCREngine:
    def __init__(self):
        self._easyocr_reader = None

    def extract_text(self, file_path: str, preloaded_ocr: Optional[str] = None) -> str:
        """Extracts OCR text from image file path or pre-computed metadata."""
        if preloaded_ocr and preloaded_ocr.strip():
            logger.debug(f"Using pre-extracted OCR text for {file_path}")
            return preloaded_ocr.strip()

        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Image file does not exist at {file_path}")
            return ""

        try:
            import easyocr
            if self._easyocr_reader is None:
                logger.info("Initializing EasyOCR reader...")
                self._easyocr_reader = easyocr.Reader(['en'], gpu=False)
            results = self._easyocr_reader.readtext(str(path), detail=0)
            extracted = " ".join(results).strip()
            logger.info(f"EasyOCR extracted text: '{extracted}' from {path.name}")
            return extracted
        except Exception as e:
            logger.warning(f"EasyOCR extraction failed for {file_path}: {e}")
            return ""
