"""
============================================================================
FILE: services/pdf-service/app/services/queue_worker.py
PURPOSE: Background workers for PDF processing (uses shared queue package)
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
from app.services.compress_pdf import compress_pdf_ghostscript
from app.services.flatten_pdf import flatten_pdf_ghostscript
from app.services.convert_pdfa import convert_to_pdfa
from app.core.config import settings

logger = logging.getLogger(__name__)

class QueueWorker:
    """Background worker for PDF processing"""
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.is_running = False
        self.jobs_processed = 0
    
    async def process_job(self, job_data: Dict[str, Any]) -> bool:
        """Process a single PDF job"""
        
        job_id = job_data["id"]
        job_type = job_data["type"]
        start_time = time.time()
        
        try:
            logger.info(f"Worker {self.worker_id} processing {job_id} ({job_type})")
            
            task_data = job_data["data"]
            pdf_path = Path(task_data["pdf_path"])
            
            # Process based on type
            if job_type == "compress":
                compression_level = task_data["options"].get("level", "ebook")
                output_path = pdf_path.parent / f"{pdf_path.stem}_compressed.pdf"
                
                original_size, compressed_size = compress_pdf_ghostscript(
                    pdf_path, 
                    output_path, 
                    compression_level
                )
                
                result = {
                    "filename": output_path.name,
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "reduction_percent": ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0,
                    "compression_level": compression_level,
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "flatten":
                output_path = pdf_path.parent / f"{pdf_path.stem}_flattened.pdf"
                
                flatten_pdf_ghostscript(pdf_path, output_path)
                
                original_size = pdf_path.stat().st_size / 1024
                flattened_size = output_path.stat().st_size / 1024
                
                result = {
                    "filename": output_path.name,
                    "original_size": original_size,
                    "flattened_size": flattened_size,
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "pdfa":
                version = task_data["options"].get("version", "2b")
                output_path = pdf_path.parent / f"{pdf_path.stem}_pdfa{version}.pdf"
                
                convert_to_pdfa(pdf_path, output_path, version)
                
                original_size = pdf_path.stat().st_size / 1024
                converted_size = output_path.stat().st_size / 1024
                
                result = {
                    "filename": output_path.name,
                    "original_size": original_size,
                    "converted_size": converted_size,
                    "pdfa_version": version,
                    "processing_time": time.time() - start_time
                }
            
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            # Complete job
            await queue_manager.complete_job(job_id, result)
            
            self.jobs_processed += 1
            logger.info(f"Worker {self.worker_id} completed {job_id}")
            
            return True
            
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
        
        logger.info(f"Starting {num_workers} PDF workers...")
        
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