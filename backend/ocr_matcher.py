"""
ocr_matcher.py
--------------
Class OCRMatcher bertugas:
1. Mengekstrak teks dari gambar hasil preprocessing (array numpy di memori)
   menggunakan pytesseract.
2. Mencocokkan teks hasil OCR dengan query pengguna menggunakan Fuzzy
   String Matching (thefuzz / Levenshtein Distance based).
"""

import asyncio
from typing import Tuple

import numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from thefuzz import fuzz

from config import OCR_LANGUAGES, FUZZY_MATCH_THRESHOLD, get_logger

logger = get_logger(__name__)


class OCRMatcherError(Exception):
    """Exception khusus untuk kegagalan proses OCR."""
    pass


class OCRMatcher:
    def __init__(self, threshold: int = FUZZY_MATCH_THRESHOLD, lang: str = OCR_LANGUAGES):
        self.threshold = threshold
        self.lang = lang

    def _sync_extract_text(self, image: np.ndarray) -> str:
        """Operasi blocking (Tesseract C++ binding), dijalankan di thread pool."""
        try:
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text.strip()
        except pytesseract.TesseractNotFoundError as e:
            raise OCRMatcherError(
                "Tesseract OCR engine tidak ditemukan di sistem. "
                "Pastikan sudah di-install (lihat README)."
            ) from e
        except Exception as e:
            raise OCRMatcherError(f"Gagal melakukan OCR: {e}") from e

    async def extract_text(self, image: np.ndarray) -> str:
        """Wrapper async dari ekstraksi teks agar tidak blok event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_extract_text, image)

    def calculate_score(self, ocr_text: str, query: str) -> int:
        """
        Menghitung skor kecocokan menggunakan kombinasi dua algoritma thefuzz:
        - token_set_ratio: tahan terhadap urutan kata & kata duplikat/berlebih
          (cocok untuk teks meme yang berantakan / banyak noise OCR).
        - partial_ratio: tahan jika query hanya merupakan SEBAGIAN dari teks
          panjang yang terbaca di gambar.
        Skor akhir = nilai maksimum dari keduanya (paling optimis namun tetap valid).
        """
        if not ocr_text:
            return 0

        ocr_clean = ocr_text.lower().strip()
        query_clean = query.lower().strip()

        score_token_set = fuzz.token_set_ratio(query_clean, ocr_clean)
        score_partial = fuzz.partial_ratio(query_clean, ocr_clean)

        return max(score_token_set, score_partial)

    async def match(self, image: np.ndarray, query: str) -> Tuple[str, int]:
        """
        Method gabungan: extract text -> hitung skor.
        Mengembalikan tuple (teks_ocr, skor).
        """
        text = await self.extract_text(image)
        score = self.calculate_score(text, query)
        return text, score

    def is_match(self, score: int) -> bool:
        return score >= self.threshold
