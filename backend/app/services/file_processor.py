import os
import asyncio
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
import redis
import magic
from pathlib import Path

from app.config import settings
from app.models.schemas import ProcessingStatus, ProcessingStatusEnum, AuditResults
from app.services.transcription import TranscriptionService
from app.services.analysis import AnalysisService

class FileProcessor:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.transcription_service = TranscriptionService()
        self.analysis_service = AnalysisService()
    
    async def process_file(self, file_path: str, job_id: str, original_filename: str):
        """
        Main file processing pipeline
        """
        start_time = time.time()
        
        try:
            # Update status to processing
            await self._update_status(job_id, ProcessingStatusEnum.PROCESSING, 10, "Starting file processing...")
            
            # Detect file type
            file_type = self._detect_file_type(file_path)
            
            # Extract transcript based on file type
            await self._update_status(job_id, ProcessingStatusEnum.TRANSCRIBING, 30, "Extracting transcript...")
            transcript = await self._extract_transcript(file_path, file_type)
            
            if not transcript:
                raise Exception("Failed to extract transcript from file")
            
            # Analyze transcript
            await self._update_status(job_id, ProcessingStatusEnum.ANALYZING, 70, "Analyzing conversation...")
            analysis_results = await self.analysis_service.analyze_conversation(transcript)
            
            # Compile final results
            processing_time = time.time() - start_time
            results = AuditResults(
                job_id=job_id,
                filename=original_filename,
                summary=analysis_results["summary"],
                scored_items=analysis_results["scored_items"],
                transcript=transcript,
                processing_time=processing_time
            )
            
            # Store results
            await self._store_results(job_id, results)
            
            # Update status to completed
            await self._update_status(job_id, ProcessingStatusEnum.COMPLETED, 100, "Analysis complete!")
            
        except Exception as e:
            await self._update_status(job_id, ProcessingStatusEnum.FAILED, 0, f"Processing failed: {str(e)}", str(e))
            raise
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type using python-magic"""
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(file_path)
        
        if file_mime.startswith('audio/'):
            return 'audio'
        elif file_mime.startswith('video/'):
            return 'video'
        elif file_mime.startswith('image/'):
            return 'image'
        elif 'pdf' in file_mime:
            return 'pdf'
        elif 'document' in file_mime or 'text' in file_mime:
            return 'document'
        else:
            # Fallback to extension
            extension = Path(file_path).suffix.lower()
            if extension in ['.mp3', '.wav', '.m4a']:
                return 'audio'
            elif extension in ['.mp4', '.avi', '.mov']:
                return 'video'
            elif extension in ['.png', '.jpg', '.jpeg']:
                return 'image'
            elif extension == '.pdf':
                return 'pdf'
            elif extension in ['.docx', '.txt']:
                return 'document'
            else:
                return 'unknown'
    
    async def _extract_transcript(self, file_path: str, file_type: str) -> str:
        """Extract transcript based on file type"""
        if file_type in ['audio', 'video']:
            return await self.transcription_service.transcribe_audio(file_path)
        elif file_type == 'image':
            return await self.transcription_service.extract_text_from_image(file_path)
        elif file_type == 'pdf':
            return await self.transcription_service.extract_text_from_pdf(file_path)
        elif file_type == 'document':
            return await self.transcription_service.extract_text_from_document(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_type}")
    
    async def _update_status(self, job_id: str, status: ProcessingStatusEnum, progress: int, message: str, error: str = None):
        """Update processing status in Redis"""
        status_data = {
            "job_id": job_id,
            "status": status.value,
            "progress": progress,
            "message": message,
            "error": error,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.redis_client.setex(f"status_{job_id}", 3600, json.dumps(status_data))  # 1 hour TTL
    
    async def _store_results(self, job_id: str, results: AuditResults):
        """Store analysis results in Redis"""
        results_json = results.model_dump_json()
        self.redis_client.setex(f"results_{job_id}", 86400, results_json)  # 24 hours TTL
    
    async def get_processing_status(self, job_id: str) -> ProcessingStatus:
        """Get current processing status"""
        status_data = self.redis_client.get(f"status_{job_id}")
        
        if not status_data:
            raise Exception("Job not found")
        
        status_dict = json.loads(status_data)
        return ProcessingStatus(**status_dict)
    
    async def get_results(self, job_id: str) -> Optional[AuditResults]:
        """Get analysis results"""
        results_data = self.redis_client.get(f"results_{job_id}")
        
        if not results_data:
            return None
        
        results_dict = json.loads(results_data)
        return AuditResults(**results_dict) 