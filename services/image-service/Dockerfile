# ============================================================================
# FILE: services/image-service/Dockerfile
# PURPOSE: Production with shared package support
# ============================================================================

# ============================================================================
# STAGE 1: BUILD LIBHEIF WITH ENCODERS
# ============================================================================

FROM python:3.11-slim AS libheif-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config cmake wget \
    libaom-dev libx265-dev libde265-dev libjpeg62-turbo-dev libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN wget https://github.com/strukturag/libheif/releases/download/v1.17.6/libheif-1.17.6.tar.gz && \
    tar xf libheif-1.17.6.tar.gz && cd libheif-1.17.6 && mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DWITH_EXAMPLES=OFF -DWITH_AOM_ENCODER=ON -DWITH_AOM_DECODER=ON \
        -DWITH_X265=ON -DWITH_LIBDE265=ON && \
    make -j$(nproc) && make install && ldconfig && \
    rm -rf /tmp/libheif-*

# ============================================================================
# STAGE 2: BUILD LIBVIPS WITH HEIF SUPPORT
# ============================================================================

FROM python:3.11-slim AS libvips-builder

COPY --from=libheif-builder /usr/local /usr/local

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config meson ninja-build wget \
    libaom-dev libx265-dev libde265-dev \
    libjpeg62-turbo-dev libpng-dev libwebp-dev libtiff-dev libgif-dev \
    librsvg2-dev libfreetype6-dev libfribidi-dev libharfbuzz-dev \
    liblcms2-dev libopenjp2-7-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN ldconfig

WORKDIR /tmp
RUN wget https://github.com/libvips/libvips/releases/download/v8.15.1/vips-8.15.1.tar.xz && \
    tar xf vips-8.15.1.tar.xz && cd vips-8.15.1 && \
    meson setup build --buildtype=release --prefix=/usr/local \
        -Dheif=enabled -Dheif-module=enabled && \
    cd build && ninja && ninja install && ldconfig && \
    rm -rf /tmp/vips-*

# ============================================================================
# STAGE 3: PYTHON BUILDER (Install shared package + dependencies)
# ============================================================================

FROM python:3.11-slim AS python-builder

COPY --from=libvips-builder /usr/local /usr/local

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config gcc \
    libaom3 libde265-0 \
    libjpeg62-turbo libpng16-16 libwebp7 libtiff6 libgif7 \
    librsvg2-2 libfreetype6 libfribidi0 libharfbuzz0b \
    liblcms2-2 libopenjp2-7 zlib1g \
    && rm -rf /var/lib/apt/lists/*

RUN ldconfig

# Copy shared package (relative to ROOT context)
WORKDIR /build
COPY packages/zemrev-queue ./packages/zemrev-queue
RUN pip install ./packages/zemrev-queue

# Copy service requirements (relative to ROOT context)
COPY services/image-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# STAGE 4: RUNTIME (Minimal)
# ============================================================================

FROM python:3.11-slim

# Copy libraries from builder
COPY --from=libvips-builder /usr/local /usr/local

# Copy Python packages
COPY --from=python-builder /usr/local /usr/local

# Runtime dependencies only (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libx265-215 \
    libaom3 libde265-0 \
    libjpeg62-turbo libpng16-16 libwebp7 libwebpmux3 libwebpdemux2 \
    libtiff6 libgif7 librsvg2-2 \
    libfreetype6 libfribidi0 libharfbuzz0b liblcms2-2 libopenjp2-7 zlib1g \
    && rm -rf /var/lib/apt/lists/*


RUN ldconfig

# Important: Set library path for libvips
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PATH=/root/.local/bin:$PATH

# Non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy application code (relative to ROOT context)
COPY --chown=appuser:appuser services/image-service/ .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info"]