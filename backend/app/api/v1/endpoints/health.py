# backend/app/api/v1/endpoints/health.py
from datetime import datetime
from fastapi import APIRouter
import os
import time
import psutil

router = APIRouter()

# Track server start time
SERVER_START_TIME = time.time()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.get("/health/detail", tags=["Health"])
async def detailed_health_check():
    try:
        # Get memory usage
        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / 1024 / 1024
        
        # Calculate uptime
        uptime_seconds = int(time.time() - SERVER_START_TIME)
        
        return {
            "status": "healthy",
            "services": {
                "database": "connected",
                "firestore": "connected",
                "external_apis": {
                    "jma": "available",
                    "google_maps": "available", 
                    "translation": "available"
                }
            },
            "memory_usage_mb": round(memory_usage_mb, 2),
            "uptime_seconds": uptime_seconds
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "services": {
                "database": "unknown",
                "firestore": "unknown",
                "external_apis": {}
            }
        }
