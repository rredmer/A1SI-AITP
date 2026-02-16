FROM python:3.10-slim

WORKDIR /app

# Install system deps for ccxt and aiosqlite
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend package and install
COPY backend/pyproject.toml backend/
COPY backend/src/ backend/src/
RUN pip install --no-cache-dir "./backend[analysis]" scipy

# Copy platform modules (common.*, research.*, etc.)
COPY common/ common/
COPY configs/ configs/
COPY freqtrade/ freqtrade/
COPY run.py ./

# Ensure common modules are importable
ENV PYTHONPATH=/app

# Create data directory
RUN mkdir -p backend/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend/src"]
