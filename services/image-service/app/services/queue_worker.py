"""
============================================================================
FILE: services/image-service/app/services/queue_worker.py
PURPOSE: Background workers (uses shared queue package)
============================================================================
"""

import asyncio
import time
import logging
from typing import Dict, Any

# Import shared queue package
from zemrev_queue import queue_manager

# Import service-specific processors
from app.services.converter import converter
from app.services.compressor import compressor
from app.services.resizer import resizer
from app.services.optimizer import optimizer
from app.services.cropper import cropper
from app.services.watermark import watermarker
from app.services.metadata import metadata_extractor
from app.services.palette import color_palette_generator
from app.models.schemas import *

logger = logging.getLogger(__name__)

class QueueWorker:
    """Background worker"""
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.is_running = False
        self.jobs_processed = 0
    
    async def process_job(self, job_data: Dict[str, Any]) -> bool:
        """Process a single job"""
        
        job_id = job_data["id"]
        job_type = job_data["type"]
        start_time = time.time()
        
        try:
            logger.info(f"Worker {self.worker_id} processing {job_id}")
            
            task_data = job_data["data"]
            content = task_data["content"]
            filename = task_data["filename"]
            
            # Process based on type
            if job_type == "convert":
                options = ConvertRequest(**task_data["options"])
                output, new_name = converter.convert(content, filename, options)
                
                result = {
                    "filename": new_name,
                    "original_size": len(content),
                    "output_size": len(output),
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "compress":
                options = CompressRequest(**task_data["options"])
                output, new_name = compressor.compress(content, filename, options)
                
                result = {
                    "filename": new_name,
                    "original_size": len(content),
                    "output_size": len(output),
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "resize":
                options = ResizeRequest(**task_data["options"])
                output, new_name, dims = resizer.resize(content, filename, options)
                
                result = {
                    "filename": new_name,
                    "dimensions": f"{dims[0]}x{dims[1]}",
                    "original_size": len(content),
                    "output_size": len(output),
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "optimize":
                options = OptimizeRequest(**task_data["options"])
                output, new_name = optimizer.optimize(content, filename, options)
                
                result = {
                    "filename": new_name,
                    "original_size": len(content),
                    "output_size": len(output),
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "crop":
                options = CropRequest(**task_data["options"])
                output, new_name = cropper.crop(content, filename, options)
                
                result = {
                    "filename": new_name,
                    "original_size": len(content),
                    "output_size": len(output),
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "watermark_text":
                options = TextWatermarkRequest(**task_data["options"])
                output, new_name = watermarker.add_text_watermark(content, filename, options)
                
                result = {
                    "filename": new_name,
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "watermark_image":
                options = ImageWatermarkRequest(**task_data["options"])
                watermark_content = task_data["watermark_content"]
                output, new_name = watermarker.add_image_watermark(
                    content, watermark_content, filename, options
                )
                
                result = {
                    "filename": new_name,
                    "processing_time": time.time() - start_time
                }

            elif job_type == "metadata":
                options = MetadataRequest(**task_data["options"])
                metadata = metadata_extractor.extract_metadata(content, filename)
                
                result = {
                    "filename": filename,
                    "metadata": metadata,
                    "processing_time": time.time() - start_time
                }
            
            elif job_type == "palette":
                options = PaletteRequest(**task_data["options"])
                palette_data, preview_bytes, preview_name = color_palette_generator.extract_palette(
                    content, filename, options.num_colors
                )
                
                import base64
                preview_base64 = base64.b64encode(preview_bytes).decode('utf-8')
                
                result = {
                    "filename": filename,
                    "palette": palette_data["palette"],
                    "total_colors": palette_data["total_colors"],
                    "preview_image": {
                        "filename": preview_name,
                        "data": f"data:image/png;base64,{preview_base64}",
                        "size": len(preview_bytes)
                    },
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
        
        logger.info(f"Starting {num_workers} workers...")
        
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