"""
============================================================================
FILE: services/pymupdf-service/app/main.py
PURPOSE: PyMuPDF Service FastAPI app (uses shared queue package)
============================================================================
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.routes import pymupdf_routes
from app.services.queue_worker import worker_manager

# Import shared queue package
from zemrev_queue import redis_client

# ============================================================================
# LOGGING
# ============================================================================

setup_logging()
logger = get_logger(__name__)

# ============================================================================
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    
    logger.info("🚀 Starting ZEMREV PyMuPDF Service...")
    logger.info(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"⏱️  Queue timeout: {settings.QUEUE_MAX_WORKERS}s")
    logger.info(f"👷 Max workers: {settings.QUEUE_MAX_WORKERS}")
    logger.info(f"📊 All Tools - Max: {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB, {settings.MAX_PAGES} pages, {settings.TOOL_TIMEOUT}s timeout")
    
    # Connect to shared Redis queue
    try:
        await redis_client.connect()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis failed: {e}")
        raise
    
    # Start workers
    try:
        await worker_manager.start_workers(settings.QUEUE_MAX_WORKERS)
        logger.info(f"✅ {settings.QUEUE_MAX_WORKERS} workers started")
    except Exception as e:
        logger.error(f"❌ Workers failed: {e}")
        raise
    
    logger.info("✅ PyMuPDF Service ready")
    
    yield
    
    # Shutdown
    logger.info("🔴 Shutting down...")
    
    try:
        await worker_manager.stop_workers()
    except Exception as e:
        logger.error(f"❌ Worker shutdown error: {e}")
    
    await redis_client.disconnect()
    
    logger.info("🔴 Shutdown complete")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="ZEMREV PyMuPDF API",
    description="Ultra-fast PDF processing with PyMuPDF + Queue",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# ROUTES
# ============================================================================

app.include_router(pymupdf_routes.router)

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API info"""
    return {
        "service": "ZEMREV PyMuPDF API",
        "version": "1.0.0",
        "status": "operational",
        "engine": "PyMuPDF",
        "tools": [
            "pdf-to-images",
            "images-to-pdf",
            "extract-text",
            "extract-images",
            "add-watermark",
            "optimize",
            "crop"
        ]
    }

@app.get("/health")
async def health():
    """Health check"""
    
    try:
        redis_status = await redis_client.ping()
    except:
        redis_status = False
    
    from zemrev_queue import queue_manager
    queue_size = await queue_manager.get_queue_size()
    
    return {
        "status": "healthy" if redis_status else "degraded",
        "redis": "connected" if redis_status else "disconnected",
        "queue_size": queue_size,
        "workers": len(worker_manager.workers)
    }