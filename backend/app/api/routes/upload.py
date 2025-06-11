from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
import magic
from pathlib import Path
import aiofiles
from pydantic import BaseModel

from app.config import settings
from app.services.file_processor import FileProcessor
from app.services.analysis import AnalysisService
from app.models.schemas import UploadResponse, ProcessingStatus

router = APIRouter()

class APIKeyRequest(BaseModel):
    api_key: str

def validate_file_type(file: UploadFile) -> bool:
    """Validate file type based on MIME type and extension"""
    if not file.filename:
        return False
    
    file_extension = file.filename.split('.')[-1].lower()
    return file_extension in settings.allowed_extensions_list

def validate_file_size(file: UploadFile) -> bool:
    """Validate file size"""
    if not file.size:
        return True  # If size is not available, allow upload and check later
    
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    return file.size <= max_size_bytes

async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return the file path"""
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1].lower()
    filename = f"{file_id}.{file_extension}"
    file_path = os.path.join(settings.upload_dir, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return file_path

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> UploadResponse:
    """
    Upload a conversation file for processing
    
    Supports: audio (.mp3, .wav), video (.mp4, .avi, .mov), 
    documents (.pdf, .docx, .txt), images (.png, .jpg, .jpeg)
    """
    
    # Validate file type
    if not validate_file_type(file):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(settings.allowed_extensions_list)}"
        )
    
    # Validate file size
    if not validate_file_size(file):
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    try:
        # Save the uploaded file
        file_path = await save_uploaded_file(file)
        
        # Generate processing job ID
        job_id = str(uuid.uuid4())
        
        # Initialize file processor
        processor = FileProcessor()
        
        # Add background task for processing
        background_tasks.add_task(
            processor.process_file,
            file_path=file_path,
            job_id=job_id,
            original_filename=file.filename
        )
        
        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            status="uploaded",
            message="File uploaded successfully. Processing started."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/test-sample")
async def test_sample_conversation():
    """
    Test the analysis system with the uploaded sample conversation
    """
    try:
        analysis_service = AnalysisService()
        results = await analysis_service.test_with_sample_conversation()
        
        return {
            "message": "Sample conversation analysis completed",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing sample conversation: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=ProcessingStatus)
async def get_processing_status(job_id: str) -> ProcessingStatus:
    """
    Get the processing status of an uploaded file
    """
    processor = FileProcessor()
    
    try:
        status = await processor.get_processing_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {str(e)}"
        )

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Get the audit results for a processed file
    """
    processor = FileProcessor()
    
    try:
        results = await processor.get_results(job_id)
        if not results:
            raise HTTPException(
                status_code=404,
                detail="Results not found or processing not complete"
            )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving results: {str(e)}"
        )

@router.post("/configure-api-key")
async def configure_api_key(request: APIKeyRequest):
    """
    Configure Gemini API key to enable real LLM analysis
    """
    try:
        # Get the global analysis service instance
        analysis_service = AnalysisService()
        
        # Try to set the API key
        success = analysis_service.set_api_key(request.api_key)
        
        if success:
            return {
                "message": "Gemini API key configured successfully",
                "status": "success",
                "llm_enabled": True
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to configure API key. Please check if the key is valid."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring API key: {str(e)}"
        ) 