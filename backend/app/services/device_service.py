# backend/app/services/device_service.py
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceStatusUpdate,
    DeviceInDB,
    DeviceResponse,
    DeviceWithProactiveContext,
    DeviceCapabilities,
    DeviceStatus
)
from app.db.firestore_client import get_db
# Removed user_crud import - using device-based context only

logger = logging.getLogger(__name__)

async def create_device(device: DeviceCreate) -> DeviceResponse:
    """Create a new device in Firestore"""
    try:
        db = get_db()
        
        # Prepare device data, excluding None values to allow default_factory
        device_dict = device.dict(exclude_none=True)
        device_data = DeviceInDB(
            **device_dict,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        # Convert to dict and ensure all fields are present
        device_dict = device_data.dict()
        
        # Save to Firestore
        doc_ref = db.collection("devices").document(device.device_id)
        doc_ref.set(device_dict)
        
        logger.info(f"Created device: {device.device_id}")
        return DeviceResponse(**device_dict)
        
    except Exception as e:
        logger.error(f"Failed to create device: {e}", exc_info=True)
        raise

async def get_device_by_id(device_id: str) -> Optional[DeviceResponse]:
    """Get device by ID from Firestore"""
    try:
        db = get_db()
        doc = db.collection("devices").document(device_id).get()
        
        if not doc.exists:
            return None
            
        device_data = doc.to_dict()
        
        # Ensure all required fields are present
        if not device_data.get("capabilities"):
            device_data["capabilities"] = DeviceCapabilities().dict()
        if not device_data.get("status"):
            device_data["status"] = DeviceStatus().dict()
            
        return DeviceResponse(**device_data)
        
    except Exception as e:
        logger.error(f"Failed to get device: {e}", exc_info=True)
        return None

async def update_device(device_id: str, device_update: DeviceUpdate) -> Optional[DeviceResponse]:
    """Update device information"""
    try:
        db = get_db()
        doc_ref = db.collection("devices").document(device_id)
        
        # Get existing device
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        # Prepare update data
        update_data = {
            k: v for k, v in device_update.dict(exclude_unset=True).items()
            if v is not None
        }
        
        # Handle nested updates for capabilities and status
        if device_update.capabilities:
            update_data["capabilities"] = device_update.capabilities.dict()
        if device_update.status:
            update_data["status"] = device_update.status.dict()
            
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in Firestore
        doc_ref.update(update_data)
        
        # Get updated device
        updated_doc = doc_ref.get()
        return DeviceResponse(**updated_doc.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to update device: {e}", exc_info=True)
        return None

async def update_device_status(device_id: str, status_update: DeviceStatusUpdate) -> Optional[DeviceResponse]:
    """Update device status (optimized for frequent updates)"""
    try:
        db = get_db()
        doc_ref = db.collection("devices").document(device_id)
        
        # Get existing device
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        # Build status update
        device_data = doc.to_dict()
        current_status = device_data.get("status", {})
        
        # Update only provided fields
        status_dict = status_update.dict(exclude_unset=True)
        for key, value in status_dict.items():
            if value is not None:
                current_status[key] = value
        
        current_status["last_updated"] = datetime.utcnow()
        
        # Update in Firestore
        doc_ref.update({
            "status": current_status,
            "updated_at": datetime.utcnow()
        })
        
        # Get updated device
        updated_doc = doc_ref.get()
        return DeviceResponse(**updated_doc.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to update device status: {e}", exc_info=True)
        return None

async def get_device_with_context(device_id: str, user_id: Optional[str] = None) -> Optional[DeviceWithProactiveContext]:
    """Get device with proactive suggestion context"""
    try:
        # Get device
        device = await get_device_by_id(device_id)
        if not device:
            return None
        
        # Build proactive context
        context_data = {
            "has_unread_alerts": False,  # TODO: Check unread alerts
            "last_quiz_date": None,
            "emergency_contacts_count": 0,
            "guide_views_count": 0,
            "last_active": device.updated_at,
            "suggested_actions": []
        }
        
        # Get device-based context from device metadata
        # Since user data is not stored on backend, we use device metadata
        device_metadata = device.metadata or {}
        
        context_data.update({
            "last_quiz_date": device_metadata.get("last_quiz_date"),
            "emergency_contacts_count": device_metadata.get("emergency_contacts_count", 0),
            "guide_views_count": device_metadata.get("guide_views_count", 0),
            "last_active": device.updated_at
        })
        
        # Suggest actions based on device context
        if device_metadata.get("emergency_contacts_count", 0) == 0:
            context_data["suggested_actions"].append("register_contacts")
        if not device_metadata.get("last_quiz_date"):
            context_data["suggested_actions"].append("take_quiz")
        if device.status.battery_level and device.status.battery_level < 30:
            context_data["suggested_actions"].append("charge_battery")
        
        # Create response
        device_with_context = DeviceWithProactiveContext(
            **device.dict(),
            **context_data
        )
        
        return device_with_context
        
    except Exception as e:
        logger.error(f"Failed to get device with context: {e}", exc_info=True)
        return None

async def get_devices_by_user(user_id: str) -> list[DeviceResponse]:
    """Get all devices for a user"""
    try:
        db = get_db()
        devices = []
        
        # Query devices by user_id
        query = db.collection("devices").where("user_id", "==", user_id)
        docs = query.stream()
        
        for doc in docs:
            device_data = doc.to_dict()
            
            # Ensure all required fields are present
            if not device_data.get("capabilities"):
                device_data["capabilities"] = DeviceCapabilities().dict()
            if not device_data.get("status"):
                device_data["status"] = DeviceStatus().dict()
                
            devices.append(DeviceResponse(**device_data))
        
        return devices
        
    except Exception as e:
        logger.error(f"Failed to get user devices: {e}", exc_info=True)
        return []

async def deactivate_device(device_id: str) -> bool:
    """Deactivate a device"""
    try:
        db = get_db()
        doc_ref = db.collection("devices").document(device_id)
        
        # Update device status
        doc_ref.update({
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"Deactivated device: {device_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to deactivate device: {e}", exc_info=True)
        return False