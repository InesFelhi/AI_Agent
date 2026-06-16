# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

# Installer torch CPU + le reste dans /install
RUN pip install --no-cache-dir \
    --target=/install \
    torch==2.10.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
    --target=/install \
    --default-timeout=1000 --retries 10 \
    -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/install

# Copier les dépendances depuis builder
COPY --from=builder /install /install

# Copier le code
COPY . .

# Créer l'utilisateur non-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "src.main", "--app", "chat"]