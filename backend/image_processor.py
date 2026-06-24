"""
image_processor.py
-------------------
Class ImageProcessor bertugas:
1. Mengunduh gambar dari URL secara asinkron ke dalam BytesIO (RAM), TANPA
   menulis ke disk sama sekali (stateless requirement).
2. Melakukan preprocessing dengan OpenCV: Grayscale -> Noise Removal ->
   Adaptive Thresholding, supaya teks di dalam stiker/meme lebih mudah
   dibaca oleh OCR engine.
"""

import asyncio
import io
from typing import Optional, Tuple

import aiohttp
import cv2
import numpy as np

from config import DOWNLOAD_TIMEOUT_SECONDS, MAX_IMAGE_BYTES, USER_AGENT, get_logger

logger = get_logger(__name__)


class ImageProcessorError(Exception):
    """Exception khusus untuk kegagalan download/preprocessing gambar."""
    pass


class ImageProcessor:
    """
    Semua method di sini sengaja stateless terhadap disk: input URL,
    output berupa array numpy di memori. Cocok untuk arsitektur tanpa database.
    """

    def __init__(self, session: aiohttp.ClientSession):
        # Session aiohttp di-inject dari luar (connection pooling) bukan dibuat
        # baru setiap request, supaya efisien.
        self._session = session

    async def download_to_memory(self, image_url: str) -> bytes:
        """Mengunduh gambar dan mengembalikan raw bytes-nya dari BytesIO buffer."""
        timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
        headers = {"User-Agent": USER_AGENT}

        try:
            async with self._session.get(
                image_url, timeout=timeout, headers=headers, ssl=False
            ) as response:
                if response.status != 200:
                    raise ImageProcessorError(
                        f"HTTP {response.status} saat mengunduh gambar."
                    )

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_IMAGE_BYTES:
                    raise ImageProcessorError("Ukuran gambar melebihi batas maksimum.")

                buffer = io.BytesIO()
                downloaded = 0
                async for chunk in response.content.iter_chunked(64 * 1024):
                    downloaded += len(chunk)
                    if downloaded > MAX_IMAGE_BYTES:
                        raise ImageProcessorError(
                            "Ukuran gambar melebihi batas maksimum saat streaming."
                        )
                    buffer.write(chunk)

                return buffer.getvalue()

        except aiohttp.ClientConnectorError as e:
            raise ImageProcessorError(f"Gagal konek ke host gambar: {e}") from e
        except aiohttp.ClientError as e:
            raise ImageProcessorError(f"Client error saat mengunduh gambar: {e}") from e
        except asyncio.TimeoutError as e:
            raise ImageProcessorError("Timeout saat mengunduh gambar.") from e

    def decode_image(self, raw_bytes: bytes) -> np.ndarray:
        """Decode raw bytes (dari memori) menjadi array OpenCV (BGR)."""
        np_array = np.frombuffer(raw_bytes, dtype=np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ImageProcessorError("Gagal decode gambar (format tidak didukung/korup).")
        return image

    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Pipeline preprocessing untuk meningkatkan akurasi OCR pada stiker/meme:
        1. Resize (upscale) jika gambar terlalu kecil, supaya teks lebih jelas.
        2. Grayscale.
        3. Noise removal (Median Blur / Denoising).
        4. Adaptive Thresholding -> menghasilkan citra biner hitam-putih
           yang kontras tinggi, ideal untuk Tesseract.
        """
        try:
            # 1. Upscale jika gambar kecil (stiker WA biasanya berukuran kecil ~512px)
            h, w = image.shape[:2]
            if max(h, w) < 600:
                scale = 600 / max(h, w)
                image = cv2.resize(
                    image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
                )

            # 2. Grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 3. Noise Removal menggunakan Median Blur (jauh lebih cepat dibanding fastNlMeansDenoising)
            denoised = cv2.medianBlur(gray, 3)

            # 4. Adaptive Thresholding (Gaussian) untuk binarisasi adaptif
            #    terhadap variasi pencahayaan/background pada meme.
            thresholded = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=31,
                C=15,
            )

            return thresholded

        except cv2.error as e:
            raise ImageProcessorError(f"OpenCV error saat preprocessing: {e}") from e

    def _sync_process_image(self, raw_bytes: bytes) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Menjalankan decode dan preprocess secara sinkron (blocking)."""
        decoded = self.decode_image(raw_bytes)
        h, w = decoded.shape[:2]
        processed = self.preprocess_for_ocr(decoded)
        return processed, (w, h)

    async def process(self, image_url: str) -> Tuple[np.ndarray, Optional[Tuple[int, int]]]:
        """
        Method gabungan: download -> decode -> preprocess.
        Mengembalikan tuple (gambar_siap_ocr, (width, height) asli).
        """
        raw_bytes = await self.download_to_memory(image_url)
        loop = asyncio.get_running_loop()
        processed, dimensions = await loop.run_in_executor(None, self._sync_process_image, raw_bytes)
        return processed, dimensions
