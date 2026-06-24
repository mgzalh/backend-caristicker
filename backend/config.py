"""
config.py
---------
Konfigurasi global aplikasi. Dipisah dari logic agar mudah di-tune
tanpa menyentuh kode inti (OOP - Single Responsibility).
"""

import logging
import os
from dotenv import load_dotenv

# Muat variabel dari file .env (jika ada)
load_dotenv()

# ----- Google Custom Search API settings -----
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# ----- Scraper settings -----
MAX_SCRAPE_RESULTS = 15          # jumlah maksimal URL gambar yang diambil dari sumber
SCRAPE_REGION = "wt-wt"          # region pencarian (jika relevan)
SCRAPE_SAFESEARCH = "moderate"

# ----- Downloader settings -----
DOWNLOAD_TIMEOUT_SECONDS = 20      # timeout per gambar saat diunduh
MAX_IMAGE_BYTES = 6 * 1024 * 1024  # 6 MB, guard agar RAM tidak jebol oleh gambar raksasa
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# ----- OCR & Matching settings -----
OCR_LANGUAGES = "ind+eng"         # Bahasa Indonesia + Inggris (Tesseract lang pack)
FUZZY_MATCH_THRESHOLD = 0        # ambang batas akurasi minimal (%)
MAX_CONCURRENT_TASKS = 8          # batasi concurrency agar CPU/RAM tidak overload

# ----- Logging -----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
