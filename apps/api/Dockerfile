# AI Career Copilot API
#
# Build args:
#   INSTALL_ML=true  -> installs sentence-transformers + spaCy (large image,
#                       real semantic embeddings). Default is a slim image
#                       using the deterministic fallback embedder, so
#                       `docker compose up --build` works quickly everywhere.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY requirements.txt requirements-ml.txt ./
ARG INSTALL_ML=false
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_ML" = "true" ]; then pip install -r requirements-ml.txt; fi

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN mkdir -p uploads && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Apply migrations, then start the API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
