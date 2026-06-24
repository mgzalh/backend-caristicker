"""
main.py
-------
Entrypoint FastAPI. Aplikasi sepenuhnya STATELESS — tidak ada database,
tidak ada penyimpanan ke disk. Setiap request /search memicu alur penuh:
live scraping -> download in-memory -> OCR -> fuzzy match -> response JSON.
"""

from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import aiohttp

from config import get_logger
from models import SearchResponse
from pipeline import SearchPipeline

logger = get_logger(__name__)

app = FastAPI(
    title="WA Sticker/Meme Search Engine (Stateless)",
    description=(
        "Mesin pencari stiker/meme WhatsApp. Live scraping + in-memory OCR "
        "+ fuzzy matching, tanpa database."
    ),
    version="1.0.0",
)

# CORS dibuka lebar karena frontend adalah static HTML terpisah (file:// atau port lain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline diinstansiasi sekali (stateless secara data, tapi objeknya reusable)
pipeline = SearchPipeline()


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "WA Sticker Search Engine API is running."}


@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search_stickers(
    q: str = Query(
        ...,
        min_length=1,
        max_length=100,
        description="Kata kunci pencarian stiker/meme, contoh: 'kucing ngantuk'",
    )
):
    """
    Alur:
    1. ImageScraper -> cari ~15 kandidat gambar live dari internet.
    2. ImageProcessor -> unduh tiap gambar ke RAM, preprocessing OpenCV.
    3. OCRMatcher -> ekstrak teks, hitung fuzzy score vs query.
    4. Kembalikan hanya gambar dengan score >= threshold (default 75%).

    Seluruh proses no.2 & no.3 dijalankan KONKUREN (asyncio.gather) untuk
    menekan latency.
    """
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Parameter 'q' tidak boleh kosong.")

    logger.info(f"Menerima request pencarian: '{query}'")

    try:
        result = await pipeline.run(query)
    except Exception as e:
        logger.exception("Unhandled error pada pipeline pencarian.")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan internal saat memproses pencarian: {e}",
        )

    return result


@app.get("/download", tags=["Download"])
async def download_image(url: str = Query(..., description="URL gambar yang akan diunduh")):
    """
    Endpoint untuk mengunduh gambar secara proxy untuk menghindari masalah CORS
    di frontend saat mencoba menyimpan gambar langsung.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                resp.raise_for_status()
                content = await resp.read()
                content_type = resp.headers.get("Content-Type", "image/jpeg")
                headers = {
                    "Content-Disposition": 'attachment; filename="stiker.jpg"'
                }
                return Response(content=content, media_type=content_type, headers=headers)
    except Exception as e:
        logger.error(f"Gagal mengunduh gambar dari {url}: {e}")
        raise HTTPException(status_code=400, detail="Gagal mengunduh gambar")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
