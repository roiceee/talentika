FROM python:3.13-slim

# System deps: tesseract-ocr (OCR engine), poppler-utils (pdf2image),
# libpq-dev (psycopg2), netcat-openbsd (DB readiness check),
# libreoffice (DOCX → PDF conversion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libpq-dev \
    netcat-openbsd \
    libreoffice \
  && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install Python deps (cached layer — only re-runs when lock/toml change)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Production: gunicorn. Override with the desired command for workers.
CMD ["uv", "run", "gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]