from fastapi import APIRouter
from app.config import settings
# import redis
# import psycopg2
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify API status and dependencies
    """
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "services": {}
    }
    
    # Check Redis connection (temporarily disabled for testing)
    health_status["services"]["redis"] = "disabled_for_testing"
    
    # Check Database connection (temporarily disabled for testing)
    health_status["services"]["database"] = "disabled_for_testing"
    
    # Check API Keys
    health_status["services"]["gemini_api"] = "configured" if settings.gemini_api_key else "not_configured"
    health_status["services"]["openai_api"] = "configured" if settings.openai_api_key else "not_configured"
    
    return health_status 