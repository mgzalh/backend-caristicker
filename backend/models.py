"""
models.py
---------
Skema data (Pydantic) yang dipakai sebagai kontrak response API.
Dipisah agar FastAPI otomatis menghasilkan dokumentasi OpenAPI yang rapi.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class StickerResult(BaseModel):
    image_url: str = Field(..., description="URL asli gambar/stiker")
    source_url: Optional[str] = Field(None, description="URL halaman sumber gambar")
    matched_text: str = Field(..., description="Teks hasil OCR yang berhasil dibaca dari gambar")
    score: int = Field(..., description="Skor kecocokan fuzzy (0-100)")
    width: Optional[int] = None
    height: Optional[int] = None


class SearchResponse(BaseModel):
    query: str
    total_scraped: int = Field(..., description="Jumlah kandidat gambar yang berhasil di-scrape")
    total_matched: int = Field(..., description="Jumlah gambar yang lolos threshold fuzzy match")
    results: List[StickerResult]
    errors: List[str] = Field(default_factory=list, description="Daftar error non-fatal selama proses")
