"""
Disaster Update Request Service
Service for enqueuing and managing background disaster update requests
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.db.firestore_client import get_db
from app.schemas.common.location import Location

logger = logging.getLogger(__name__)


async def enqueue_disaster_update_request(
    device_id: str,
    location: Location,
    radius_km: float = 10.0,
    priority: str = "normal"
) -> str:
    """
    Enqueue a disaster update request for background processing
    
    Args:
        device_id: Device requesting the update
        location: Location to fetch disaster info for
        radius_km: Search radius in kilometers
        priority: Request priority (high, normal, low)
        
    Returns:
        str: Request ID
    """
    try:
        db = get_db()
        request_id = str(uuid.uuid4())
        
        request_data = {
            "request_id": request_id,
            "device_id": device_id,
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "radius_km": radius_km,
            "priority": priority,
            "status": "pending",
            "retry_count": 0,
            "requested_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc)
        }
        
        # Add to disaster_update_requests collection
        doc_ref = db.collection("disaster_update_requests").document(request_id)
        doc_ref.set(request_data)
        
        logger.info(f"Enqueued disaster update request: {request_id} for device: {device_id}")
        return request_id
        
    except Exception as e:
        logger.error(f"Failed to enqueue disaster update request: {e}")
        raise


async def get_request_status(request_id: str) -> Optional[dict]:
    """
    Get the status of a disaster update request
    
    Args:
        request_id: Request ID to check
        
    Returns:
        dict: Request data or None if not found
    """
    try:
        db = get_db()
        doc_ref = db.collection("disaster_update_requests").document(request_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
        
    except Exception as e:
        logger.error(f"Failed to get request status: {e}")
        return None


async def cancel_request(request_id: str) -> bool:
    """
    Cancel a pending disaster update request
    
    Args:
        request_id: Request ID to cancel
        
    Returns:
        bool: True if successfully cancelled
    """
    try:
        db = get_db()
        doc_ref = db.collection("disaster_update_requests").document(request_id)
        
        # Update status to cancelled
        doc_ref.update({
            "status": "cancelled",
            "updated_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Cancelled disaster update request: {request_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to cancel request: {e}")
        return False