"""
============================================================================
FILE: services/image-service/app/main.py
PURPOSE: Image Service FastAPI app (uses shared queue package)
============================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.api.routes.image_routes import router
from app.services.queue_worker import worker_manager

# Import shared queue package
from zemrev_queue import redis_client

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    
    logger.info("🚀 Starting ZEMREV Image Service...")
    
    # Connect to shared Redis queue
    try:
        await redis_client.connect()
    except Exception as e:
        logger.error(f"❌ Redis failed: {e}")
    
    # Start workers
    try:
        await worker_manager.start_workers(settings.QUEUE_MAX_WORKERS)
    except Exception as e:
        logger.error(f"❌ Workers failed: {e}")
    
    logger.info("✅ Image Service ready")
    
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
    title="ZEMREV Image API",
    description="Ultra-fast PyVIPS image processing with HEIC support",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600
)

# ============================================================================
# ROUTES
# ============================================================================

app.include_router(router)

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

# ============================================================================
# UPDATE: services/image-service/app/main.py
# Replace the existing @app.get("/") endpoint with this updated version:
# ============================================================================

@app.get("/")
async def root():
    """API info"""
    return {
        "service": "ZEMREV Image API",
        "version": "1.0.0",
        "status": "operational",
        "engine": "PyVIPS",
        "formats": ["JPEG", "PNG", "WebP", "AVIF", "HEIC", "HEIF", "TIFF"],
        "tools": [
            "convert",
            "compress",
            "resize",
            "optimize",
            "crop",
            "watermark",
            "metadata",
            "palette"
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