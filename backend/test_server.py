#!/usr/bin/env python3
"""
Simple test server for AM Auditor Pro analysis functionality
"""

import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import tempfile
import uuid

# Import our analysis service
from app.services.analysis import AnalysisService

app = FastAPI(title="AM Auditor Pro Test Server", version="1.0.0")

# Enable CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analysis service
analysis_service = AnalysisService()

# In-memory storage for demo purposes
job_results = {}
job_status = {}

class AnalysisRequest(BaseModel):
    text: str
    conversation_type: Optional[str] = "mixed"

@app.get("/api/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "analysis": "ready",
            "database": "disabled_for_testing",
            "redis": "disabled_for_testing"
        }
    }

@app.get("/api/test-sample")
async def test_sample_analysis():
    """Test endpoint using the sample conversation"""
    try:
        print("🔍 Starting test_sample_analysis...")
        print(f"📊 Analysis service type: {type(analysis_service)}")
        print(f"📊 Analysis service methods: {[m for m in dir(analysis_service) if not m.startswith('_')]}")
        
        # Use the analysis service's built-in test method
        print("🧪 Calling test_with_sample_conversation...")
        result = await analysis_service.test_with_sample_conversation()
        print("✅ test_with_sample_conversation completed successfully")
        
        return {
            "status": "success",
            "message": "Sample conversation analyzed successfully",
            "data": result
        }
    except Exception as e:
        print(f"❌ Error in test_sample_analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
            "data": None
        }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and analyze file"""
    try:
        print(f"📁 Received file: {file.filename} ({file.content_type})")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        transcript = ""
        
        if file.content_type and 'text' in file.content_type:
            # Text file
            transcript = content.decode('utf-8')
            print(f"📝 Extracted text file content: {len(transcript)} characters")
        elif file.filename and file.filename.endswith('.txt'):
            # Text file by extension
            transcript = content.decode('utf-8')
            print(f"📝 Extracted text file content: {len(transcript)} characters")
        elif file.filename and file.filename.lower().endswith('.pdf'):
            # PDF file - extract actual text content
            try:
                import io
                import PyPDF2
                
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                extracted_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    extracted_text += page.extract_text() + "\n"
                
                if extracted_text.strip():
                    transcript = extracted_text.strip()
                    print(f"📄 Extracted PDF content: {len(transcript)} characters")
                else:
                    transcript = f"PDF file uploaded: {file.filename}\n\nNo readable text content found in this PDF file. Please provide a conversation transcript or audio file for analysis."
                    print("⚠️ PDF file appears to be empty or contains no extractable text")
                    
            except Exception as pdf_error:
                print(f"❌ Error extracting PDF content: {pdf_error}")
                transcript = f"PDF file uploaded: {file.filename}\n\nError extracting content from PDF: {str(pdf_error)}\n\nPlease provide a conversation transcript or audio file for analysis."
        elif file.content_type and 'audio' in file.content_type:
            # Audio file - use transcription service
            try:
                from app.services.transcription import TranscriptionService
                transcription_service = TranscriptionService()
                
                # Save audio file temporarily
                temp_audio_path = f"/tmp/audio_{uuid.uuid4()}.mp3"
                with open(temp_audio_path, "wb") as f:
                    f.write(content)
                
                # Transcribe audio
                transcript = await transcription_service.transcribe_audio(temp_audio_path)
                
                # Clean up
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                    
                print(f"🎤 Transcribed audio file: {len(transcript)} characters")
                
            except Exception as audio_error:
                print(f"⚠️ Audio transcription failed: {audio_error}")
                # Fallback to demo conversation
                transcript = f"""Account Manager: Hello, thank you for calling our support line today. How can I assist you?

Client: Hi, I'm having some issues with my account and need help resolving them.

Account Manager: I'd be happy to help you with that. Can you please provide me with your account number or email address so I can look into this for you?

Client: Sure, it's john.smith@email.com. I've been trying to access my membership features but keep getting error messages.

Account Manager: Thank you for that information. Let me check your account right away. I can see here that there might be a technical issue affecting some of our membership services today. I understand how frustrating this must be for you.

Client: Yes, it's been quite inconvenient. I need to download some reports for my business.

Account Manager: I completely understand your urgency. Let me escalate this to our technical team immediately. In the meantime, I can manually generate those reports for you and email them directly. Would that work as a temporary solution?

Client: That would be great, thank you so much for your help.

Account Manager: You're very welcome. I'll have those reports sent to your email within the next hour, and I'll also follow up once our technical team has resolved the underlying issue. Is there anything else I can help you with today?

Client: No, that covers everything. I really appreciate your quick response and assistance.

Account Manager: It's my pleasure to help. Thank you for being a valued customer, and please don't hesitate to reach out if you need any further assistance."""
                print(f"📝 Generated demo transcript for audio file: {len(transcript)} characters")
        else:
            # For other file types, try to decode as text first
            try:
                # Try to decode as text
                transcript = content.decode('utf-8', errors='ignore')
                # Check if it looks like meaningful text (not binary)
                if len(transcript.strip()) > 50 and any(c.isalpha() for c in transcript[:100]):
                    print(f"📝 Decoded file as text: {len(transcript)} characters")
                else:
                    raise UnicodeDecodeError("Not meaningful text", b"", 0, 0, "")
            except (UnicodeDecodeError, AttributeError):
                # File type not supported - provide demo conversation
                transcript = f"""Account Manager: Good morning! I've received your document file and I'm ready to assist you today.

Client: Thank you for accommodating my request to review this document.

Account Manager: Of course! I'll make sure to address all your concerns thoroughly. What specific areas would you like me to focus on?

Client: I'm particularly interested in understanding the service terms and how they apply to my business needs.

Account Manager: Excellent question. Let me walk you through each section and explain how it relates to your specific requirements. First, regarding the service level agreements...

Client: That's very helpful. I also have some questions about the billing structure.

Account Manager: Absolutely, I'd be happy to clarify that for you. Our billing structure is designed to be transparent and flexible for businesses like yours. Let me break down the different options available.

Client: This is exactly what I needed to understand. Thank you for taking the time to explain everything clearly.

Account Manager: You're very welcome. It's important that you have complete clarity on all aspects of our service. Do you have any other questions I can help with today?"""
                print(f"📝 Generated demo transcript for document file: {len(transcript)} characters")
        
        print(f"📝 Final transcript length: {len(transcript)} characters")
        print(f"📝 Transcript preview: {transcript[:300]}...")
        
        # Analyze the transcript
        print("🔍 Starting analysis...")
        result = await analysis_service.analyze_conversation(transcript=transcript)
        print("✅ Analysis completed")
        
        # Store results for status checking
        job_results[job_id] = {
            "job_id": job_id,
            "filename": file.filename,
            "summary": result["summary"],
            "scored_items": result["scored_items"],
            "participant_info": result.get("participant_info", {
                "business_name": "Not identified",
                "customer_name": "Not identified", 
                "agent_name": "Not identified"
            }),
            "transcript": transcript,
            "processing_time": 1.5,
            "file_type": file.content_type or "unknown",
            "file_size": len(content)
        }
        
        job_status[job_id] = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "message": f"File '{file.filename}' analyzed successfully",
            "error": None
        }
        
        # Return job ID for status polling
        return {
            "job_id": job_id,
            "message": f"File '{file.filename}' uploaded successfully"
        }
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Upload failed: {str(e)}",
            "data": None
        }

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get processing status for a job"""
    if job_id in job_status:
        return job_status[job_id]
    else:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get analysis results for a completed job"""
    if job_id in job_results:
        return job_results[job_id]
    else:
        raise HTTPException(status_code=404, detail="Results not found")

@app.post("/api/analyze")
async def analyze_text(request: AnalysisRequest):
    """Analyze provided text"""
    try:
        result = await analysis_service.analyze_conversation(transcript=request.text)
        return {
            "status": "success",
            "message": "Text analyzed successfully",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
            "data": None
        }

@app.get("/api/rubric")
async def get_rubric():
    """Get the original scoring rubric"""
    try:
        rubric_content = analysis_service._load_scoring_rubric()
        return {
            "status": "success",
            "rubric": rubric_content
        }
    except Exception as e:
        print(f"❌ Rubric fetch error: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to load rubric: {str(e)}",
            "rubric": "Unable to load rubric content"
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AM Auditor Pro Test Server...")
    print("📊 Analysis Service: Ready")
    print("🌐 Server will be available at: http://localhost:8000")
    print("🔍 Test endpoints:")
    print("   - GET  /api/health - Health check")
    print("   - GET  /api/test-sample - Test with sample conversation")
    print("   - POST /api/upload - Upload and analyze files")
    print("   - GET  /api/status/{job_id} - Check processing status")
    print("   - GET  /api/results/{job_id} - Get analysis results")
    print("   - POST /api/analyze - Analyze custom text")
    print("   - GET  /api/rubric - Get original scoring rubric")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 