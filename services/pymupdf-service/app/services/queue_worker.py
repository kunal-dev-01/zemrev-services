"""
============================================================================
FILE: services/pymupdf-service/app/services/queue_worker.py
PURPOSE: Background workers for PyMuPDF processing (uses shared queue package)
============================================================================
"""

import asyncio
import time
import logging
from typing import Dict, Any
from pathlib import Path

# Import shared queue package
from zemrev_queue import queue_manager

# Import service-specific processors
from app.services.pdf_to_images import pdf_to_images
from app.services.images_to_pdf import images_to_pdf
from app.services.extract_text import extract_text_from_pdf
from app.services.extract_images import extract_images_from_pdf
from app.services.sign_pdf import sign_pdf
from app.services.optimize_pdf import optimize_pdf
from app.services.crop_pdf import crop_pdf
from app.services.remove_pages import remove_pages_from_pdf

from app.core.config import settings

logger = logging.getLogger(__name__)

class QueueWorker:
    """Background worker for PyMuPDF processing"""
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.is_running = False
        self.jobs_processed = 0
    
    async def process_job(self, job_data: Dict[str, Any]) -> bool:
        """Process a single PyMuPDF job"""
        
        job_id = job_data["id"]
        job_type = job_data["type"]
        start_time = time.time()
        
        try:
            logger.info(f"Worker {self.worker_id} processing {job_id} ({job_type})")
            
            task_data = job_data["data"]
            pdf_path = Path(task_data["pdf_path"])
            options = task_data.get("options", {})
            
            result = None
            
            # ================================================================
            # TOOL 1: PDF TO IMAGES
            # ================================================================
            if job_type == "pdf-to-images":
                output_paths, metadata = pdf_to_images(pdf_path, options)
                
                result = {
                    "filename": pdf_path.name,
                    "images": output_paths,
                    "metadata": metadata,
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 2: IMAGES TO PDF
            # ================================================================
            elif job_type == "images-to-pdf":
                image_paths = task_data.get("image_paths", [])
                output_path = images_to_pdf(image_paths, options)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 3: EXTRACT TEXT
            # ================================================================
            elif job_type == "extract-text":
                text_data = extract_text_from_pdf(pdf_path, options)
                
                result = {
                    "filename": pdf_path.name,
                    "text": text_data,
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 4: EXTRACT IMAGES
            # ================================================================
            elif job_type == "extract-images":
                image_paths = extract_images_from_pdf(pdf_path, options)
                
                result = {
                    "filename": pdf_path.name,
                    "images": image_paths,
                    "count": len(image_paths),
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 5: SIGN PDF (ADD WATERMARK/SIGNATURE)
            # ================================================================
            elif job_type == "sign":
                signatures = options.get("signatures", [])
                output_path = pdf_path.parent / f"{pdf_path.stem}_signed.pdf"
                
                sign_pdf(pdf_path, output_path, signatures)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "signatures_added": len(signatures),
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 6: OPTIMIZE PDF
            # ================================================================
            elif job_type == "optimize":
                output_path = pdf_path.parent / f"{pdf_path.stem}_optimized.pdf"
                
                original_size = pdf_path.stat().st_size / 1024
                optimize_pdf(pdf_path, output_path, options)
                optimized_size = output_path.stat().st_size / 1024
                reduction = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "original_size_kb": original_size,
                    "optimized_size_kb": optimized_size,
                    "reduction_percent": reduction,
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 7: CROP PDF
            # ================================================================
            elif job_type == "crop":
                output_path = pdf_path.parent / f"{pdf_path.stem}_cropped.pdf"
                
                crop_pdf(pdf_path, output_path, options)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 8: REMOVE PAGES
            # ================================================================
            elif job_type == "remove-pages":
                pages_to_remove = options.get("pages", [])
                output_path = pdf_path.parent / f"{pdf_path.stem}_removed.pdf"
                
                remaining_pages = remove_pages_from_pdf(pdf_path, output_path, pages_to_remove)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "pages_removed": len(pages_to_remove),
                    "remaining_pages": remaining_pages,
                    "processing_time": time.time() - start_time
                }
            
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            # Complete job with result
            if result:
                await queue_manager.complete_job(job_id, result)
                self.jobs_processed += 1
                logger.info(f"Worker {self.worker_id} completed {job_id}")
                return True
            else:
                raise Exception("No result generated")
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} failed {job_id}: {e}")
            await queue_manager.fail_job(job_id, str(e))
            return False
    
    async def start(self):
        """Start worker loop"""
        
        self.is_running = True
        logger.info(f"Worker {self.worker_id} started")
        
        while self.is_running:
            try:
                job_data = await queue_manager.dequeue()
                
                if job_data:
                    await self.process_job(job_data)
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def stop(self):
        """Stop worker"""
        self.is_running = False

class WorkerManager:
    """Manage multiple workers"""
    
    def __init__(self):
        self.workers = []
        self.tasks = []
    
    async def start_workers(self, num_workers: int = 4):
        """Start workers"""
        
        logger.info(f"Starting {num_workers} PyMuPDF workers...")
        
        for i in range(num_workers):
            worker = QueueWorker(worker_id=i+1)
            self.workers.append(worker)
            
            task = asyncio.create_task(worker.start())
            self.tasks.append(task)
        
        logger.info(f"✅ {num_workers} workers started")
    
    async def stop_workers(self):
        """Stop all workers"""
        
        logger.info("Stopping workers...")
        
        for worker in self.workers:
            await worker.stop()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.workers.clear()
        self.tasks.clear()
        
        logger.info("✅ Workers stopped")

worker_manager = WorkerManager()