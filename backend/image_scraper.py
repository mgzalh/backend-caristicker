"""
image_scraper.py
Menggunakan Google Custom Search API (JSON API) untuk pencarian gambar.
Menggunakan Bing Image Search scraper.
"""

import asyncio
from typing import List, Dict, Any
import requests

from config import MAX_SCRAPE_RESULTS, get_logger
import os

logger = get_logger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

class ImageScraperError(Exception):
    pass

class ImageScraper:
    def __init__(self, max_results: int = MAX_SCRAPE_RESULTS):
        self.max_results = max_results

    def _scrape_serpapi(self, query: str) -> List[Dict[str, Any]]:
        if not SERPAPI_KEY:
            raise ImageScraperError(
                "Kunci SerpApi belum dikonfigurasi. Silakan tambahkan SERPAPI_KEY di file .env."
            )

        enriched_query = f"{query} meme stiker indonesia site:pinterest.com"
        
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_images",
            "q": enriched_query,
            "api_key": SERPAPI_KEY,
            "num": self.max_results,
            "safe": "active",
            "gl": "id", # Indonesia locale
            "hl": "id"
        }
        
        results = []
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            images_results = data.get("images_results", [])
            seen = set()
            
            for item in images_results:
                img_url = item.get("original")
                if not img_url or img_url in seen:
                    continue
                
                results.append({
                    "image_url": img_url,
                    "source_url": item.get("link"),
                    "title": item.get("title", ""),
                    "width": item.get("original_width"),
                    "height": item.get("original_height"),
                })
                seen.add(img_url)
                if len(results) >= self.max_results:
                    break
                    
            logger.info(f"SerpApi: {len(results)} hasil ditemukan.")
            
        except Exception as e:
            logger.error(f"SerpApi gagal: {e}")
            raise ImageScraperError(f"Gagal mengambil gambar dari SerpApi: {e}")
            
        return results

    def _sync_search(self, query: str) -> List[Dict[str, Any]]:
        return self._scrape_serpapi(query)

    async def search_images(self, query: str) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            raise ImageScraperError("Query tidak boleh kosong.")
        
        loop = asyncio.get_running_loop()
        try:
            results = await loop.run_in_executor(None, self._sync_search, query)
        except ImageScraperError:
            raise
        except Exception as e:
            logger.error(f"Error tidak terduga saat pencarian gambar: {e}")
            raise ImageScraperError(f"Error pencarian gambar: {e}") from e
            
        if not results:
            logger.warning(f"Tidak ada hasil gambar untuk: '{query}'")
            
        return results
