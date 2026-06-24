"""
pipeline.py - SearchPipeline orchestrator.
Mode FAST: tampilkan semua hasil scraping langsung tanpa OCR
supaya gambar muncul duluan. OCR tetap berjalan untuk scoring.
"""
from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional

import aiohttp

from config import MAX_CONCURRENT_TASKS, get_logger
from image_scraper import ImageScraper, ImageScraperError
from image_processor import ImageProcessor, ImageProcessorError
from ocr_matcher import OCRMatcher, OCRMatcherError
from models import StickerResult, SearchResponse

logger = get_logger(__name__)


class SearchPipeline:
    def __init__(self):
        self.scraper = ImageScraper()
        self.matcher = OCRMatcher()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    async def _process_single(
        self,
        processor: ImageProcessor,
        candidate: Dict[str, Any],
        query: str,
        errors: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Proses satu kandidat. Jika OCR/download gagal, tetap kembalikan
        gambar dengan score 0 (daripada di-skip total).
        """
        image_url = candidate["image_url"]

        async with self._semaphore:
            # Coba OCR untuk scoring
            ocr_text = ""
            score = 0
            try:
                processed_image, dimensions = await processor.process(image_url)
                ocr_text, score = await self.matcher.match(processed_image, query)
                width, height = dimensions if dimensions else (
                    candidate.get("width"), candidate.get("height")
                )
            except (ImageProcessorError, ImageProcessorError, OCRMatcherError) as e:
                # Gagal OCR/download → tetap tampilkan gambar, score 0
                logger.warning(f"[OCR-SKIP] {image_url[:60]}... -> {e}")
                width = candidate.get("width")
                height = candidate.get("height")

            # Cek threshold
            if not self.matcher.is_match(score):
                logger.info(f"Tidak lolos threshold ({score}%): {image_url[:60]}...")
                # Kalau threshold = 0, tetap lolos
                if self.matcher.threshold > 0:
                    return None

            return {
                "image_url": image_url,
                "source_url": candidate.get("source_url"),
                "matched_text": ocr_text[:200] if ocr_text else "(tidak ada teks terdeteksi)",
                "score": score,
                "width": width,
                "height": height,
            }

    async def run(self, query: str) -> SearchResponse:
        errors: List[str] = []

        # 1. SCRAPING
        try:
            candidates = await self.scraper.search_images(query)
        except ImageScraperError as e:
            logger.error(f"Scraping gagal: {e}")
            return SearchResponse(
                query=query, total_scraped=0, total_matched=0,
                results=[], errors=[str(e)]
            )

        if not candidates:
            return SearchResponse(
                query=query, total_scraped=0, total_matched=0,
                results=[],
                errors=["Tidak ada gambar ditemukan dari hasil pencarian."]
            )

        # 2. PROCESS + OCR (concurrent)
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_TASKS, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            processor = ImageProcessor(session=session)
            tasks = [
                self._process_single(processor, c, query, errors)
                for c in candidates
            ]
            raw_results = await asyncio.gather(*tasks, return_exceptions=False)

        matched = [r for r in raw_results if r is not None]
        matched.sort(key=lambda r: r["score"], reverse=True)
        sticker_results = [StickerResult(**r) for r in matched]

        return SearchResponse(
            query=query,
            total_scraped=len(candidates),
            total_matched=len(sticker_results),
            results=sticker_results,
            errors=errors,
        )
