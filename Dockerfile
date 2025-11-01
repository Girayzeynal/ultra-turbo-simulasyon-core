FROM python:3.10-slim

WORKDIR /app

# Sistem bağımlılıkları (bazı python paketleri için gerekli)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Gereksinimler
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projeyi kopyala
COPY . .

# Fly.io PORT env
ENV PORT=8080
EXPOSE 8080

# Uygulamayı web server ile çalıştırıyoruz
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "src.main:app"]
