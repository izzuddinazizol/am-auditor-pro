#!/usr/bin/env python3
"""
Debug script to test AnalysisService directly
"""

import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

from app.services.analysis import AnalysisService

async def test_analysis():
    print("🔍 Testing AnalysisService...")
    
    try:
        analysis_service = AnalysisService()
        print("✅ AnalysisService initialized successfully")
        
        # Test with simple transcript
        test_transcript = "Sarah: Hello Mr. Tan, how are you today? Mr. Tan: I'm doing well, thank you."
        
        print(f"📝 Testing with simple transcript: {test_transcript[:50]}...")
        result = await analysis_service.analyze_conversation(transcript=test_transcript)
        
        print("✅ Simple analysis completed successfully")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Test sample conversation
        print("\n🧪 Testing sample conversation method...")
        sample_result = await analysis_service.test_with_sample_conversation()
        
        print("✅ Sample conversation analysis completed successfully")
        print(f"📊 Sample result type: {type(sample_result)}")
        print(f"📊 Sample result keys: {sample_result.keys() if isinstance(sample_result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analysis()) 