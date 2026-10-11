# =========================================================
# Sorim.ai ITSM — Backend Dockerfile
# Python 3.11 base (pre-built chroma-hnswlib wheel available)
# =========================================================
FROM python:3.11-slim

# ---- System deps ----
# build-essential + gcc: in case any wheel needs compiling
# curl: for healthchecks
# libgomp1: OpenMP runtime needed by torch / onnxruntime / scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ---- Working dir ----
WORKDIR /app

# ---- Python deps (cached layer) ----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ---- App code ----
COPY src/ ./src/

# ---- Data dir (PDF will be mounted at runtime) ----
RUN mkdir -p /app/src/data

# ---- ChromaDB persistence dir ----
RUN mkdir -p /app/src/chroma_db

# ---- Env ----
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    CHROMA_DIR=/app/src/chroma_db \
    ANONYMIZED_TELEMETRY=False

EXPOSE 8000

# ---- Healthcheck ----
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ---- Start ----
CMD ["python", "-m", "src.main"]