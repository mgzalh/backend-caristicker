# Gunakan image Python ringan sebagai base
FROM python:3.10-slim

# Set working directory di dalam container
WORKDIR /app

# Install dependency sistem yang dibutuhkan oleh OpenCV dan Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt terlebih dahulu
COPY requirements.txt .

# Install dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode backend ke dalam container
COPY . .

# Ekspos port yang akan digunakan oleh FastAPI
EXPOSE 8000

# Perintah untuk menjalankan aplikasi saat container menyala
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
