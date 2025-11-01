# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# sistem bağımlılıkları gerekirse ekle (örn: build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# kopyala
COPY . /app

# PORT env
ENV PORT=8080

EXPOSE 8080

# Fly, default process is the command below; burası web entrypoint
CMD ["python", "src/web.py"] 
