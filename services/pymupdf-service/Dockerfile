# ============================================================================
# FILE: services/pymupdf-service/Dockerfile
# PURPOSE: Production with shared package support
# ============================================================================

# ============================================================================
# STAGE 1: PYTHON BUILDER (Install dependencies)
# ============================================================================

FROM python:3.11-slim AS python-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared queue package (relative to ROOT context)
WORKDIR /build
COPY packages/zemrev-queue ./packages/zemrev-queue
RUN pip install ./packages/zemrev-queue

# Copy service requirements (relative to ROOT context)
COPY services/pymupdf-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# STAGE 2: RUNTIME (Minimal)
# ============================================================================

FROM python:3.11-slim

# Copy Python packages from builder
COPY --from=python-builder /usr/local /usr/local

ENV PATH=/root/.local/bin:$PATH

# Non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app && \
    mkdir -p /tmp/zemrev_pymupdf_uploads && \
    chown -R appuser:appuser /tmp/zemrev_pymupdf_uploads

WORKDIR /app

# Copy application code (relative to ROOT context)
COPY --chown=appuser:appuser services/pymupdf-service/ .

USER appuser

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8002", \
     "--workers", "4", \
     "--log-level", "info"]