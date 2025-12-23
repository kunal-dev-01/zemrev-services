"""
============================================================================
FILE: services/pypdf-service/app/services/queue_worker.py
PURPOSE: Background workers for PyPDF processing (uses shared queue package)
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
from app.services.encrypt_service import encrypt_pdf
from app.services.decrypt_service import decrypt_pdf
from app.services.merge_service import merge_pdfs
from app.services.split_service import split_pdf
from app.services.rotate_service import rotate_pdf_pages

from app.core.config import settings

logger = logging.getLogger(__name__)

class QueueWorker:
    """Background worker for PyPDF processing"""
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.is_running = False
        self.jobs_processed = 0
    
    async def process_job(self, job_data: Dict[str, Any]) -> bool:
        """Process a single PyPDF job"""
        
        job_id = job_data["id"]
        job_type = job_data["type"]
        start_time = time.time()
        
        try:
            logger.info(f"Worker {self.worker_id} processing {job_id} ({job_type})")
            
            task_data = job_data["data"]
            options = task_data.get("options", {})
            
            result = None
            
            # ================================================================
            # TOOL 1: ENCRYPT PDF
            # ================================================================
            if job_type == "encrypt":
                pdf_path = Path(task_data["pdf_path"])
                password = options.get("password", "")
                output_path = pdf_path.parent / f"{pdf_path.stem}_encrypted.pdf"
                
                encrypt_pdf(pdf_path, output_path, password, options)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "encrypted": True,
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 2: DECRYPT PDF
            # ================================================================
            elif job_type == "decrypt":
                pdf_path = Path(task_data["pdf_path"])
                password = options.get("password", "")
                output_path = pdf_path.parent / f"{pdf_path.stem}_decrypted.pdf"
                
                decrypt_pdf(pdf_path, output_path, password)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "decrypted": True,
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 3: MERGE PDFS
            # ================================================================
            elif job_type == "merge":
                pdf_paths = [Path(p) for p in task_data.get("pdf_paths", [])]
                output_path = Path(task_data.get("output_name", "merged.pdf"))
                
                if not output_path.is_absolute():
                    output_path = pdf_paths[0].parent / output_path if pdf_paths else Path("/tmp/merged.pdf")
                
                merge_pdfs(pdf_paths, output_path, options)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "pdfs_merged": len(pdf_paths),
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 4: SPLIT PDF
            # ================================================================
            elif job_type == "split":
                pdf_path = Path(task_data["pdf_path"])
                pages = options.get("pages", [])
                output_dir = pdf_path.parent
                
                output_paths = split_pdf(pdf_path, pages, output_dir, options)
                
                result = {
                    "filename": pdf_path.name,
                    "output_paths": output_paths,
                    "splits_created": len(output_paths),
                    "processing_time": time.time() - start_time
                }
            
            # ================================================================
            # TOOL 5: ROTATE PDF PAGES
            # ================================================================
            elif job_type == "rotate":
                pdf_path = Path(task_data["pdf_path"])
                rotation = options.get("rotation", 0)  # 0, 90, 180, 270
                pages = options.get("pages", [])  # Empty = all pages
                output_path = pdf_path.parent / f"{pdf_path.stem}_rotated.pdf"
                
                rotated_count = rotate_pdf_pages(pdf_path, output_path, rotation, pages)
                
                result = {
                    "filename": output_path.name,
                    "output_path": str(output_path),
                    "rotation_degrees": rotation,
                    "pages_rotated": rotated_count,
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
        
        logger.info(f"Starting {num_workers} PyPDF workers...")
        
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