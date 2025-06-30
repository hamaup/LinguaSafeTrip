"""
Device CRUD operations - Unified async implementation
All operations are async for consistency and performance
"""
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone
from google.cloud.firestore import SERVER_TIMESTAMP

from app.schemas.device import Device, DeviceCreate, DeviceUpdate
from app.schemas.common.location import Location
from app.utils.geo_utils import calculate_distance
from app.db.firestore_client import get_async_db

logger = logging.getLogger(__name__)

DEVICES_COLLECTION = "devices"


async def create_or_update_device(device_id: str, data: dict) -> Device:
    """
    Create or update device information in Firestore (Upsert).
    
    Args:
        device_id: Unique device ID
        data: Device data dictionary containing at least 'fcmToken'
        
    Returns:
        Device: Created or updated device object
        
    Raises:
        ValueError: If device_id is empty or data is invalid
    """
    if not device_id:
        raise ValueError("device_id is required to create or update device data")
    
    if not data or 'fcmToken' not in data:
        logger.warning(f"Data for device_id {device_id} does not contain 'fcmToken'. FCM might not work.")
    
    db = await get_async_db()
    doc_ref = db.collection(DEVICES_COLLECTION).document(device_id)
    
    update_data = data.copy()
    update_data['device_id'] = device_id  # Ensure device_id is in the data
    update_data['updatedAt'] = SERVER_TIMESTAMP
    
    # Check if document exists to set createdAt only on creation
    doc = await doc_ref.get()
    if not doc.exists:
        update_data['createdAt'] = SERVER_TIMESTAMP
        logger.info(f"Creating new device: {device_id}")
    else:
        logger.info(f"Updating existing device: {device_id}")
    
    await doc_ref.set(update_data, merge=True)
    
    # Retrieve and return the updated document
    updated_doc = await doc_ref.get()
    device_data = updated_doc.to_dict()
    device_data['device_id'] = device_id
    
    return Device(**device_data)


async def get_device_by_id(device_id: str) -> Optional[Device]:
    """
    Get device information by ID.
    
    Args:
        device_id: Device ID to retrieve
        
    Returns:
        Device object if found, None otherwise
    """
    if not device_id:
        logger.error("device_id is required to get device data")
        return None
    
    try:
        db = await get_async_db()
        doc_ref = db.collection(DEVICES_COLLECTION).document(device_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            logger.info(f"Device not found: {device_id}")
            return None
        
        device_data = doc.to_dict()
        device_data['device_id'] = device_id
        
        return Device(**device_data)
        
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return None


async def get_all_devices(active_only: bool = False) -> List[Device]:
    """
    Get all devices from Firestore.
    
    Args:
        active_only: If True, return only devices with valid FCM tokens
        
    Returns:
        List of Device objects
    """
    try:
        db = await get_async_db()
        query = db.collection(DEVICES_COLLECTION)
        
        if active_only:
            query = query.where('fcmToken', '!=', '')
        
        docs = query.stream()
        devices = []
        
        async for doc in docs:
            device_data = doc.to_dict()
            device_data['device_id'] = doc.id
            try:
                device = Device(**device_data)
                devices.append(device)
            except Exception as e:
                logger.warning(f"Invalid device data for {doc.id}: {e}")
                continue
        
        logger.info(f"Retrieved {len(devices)} devices (active_only={active_only})")
        return devices
        
    except Exception as e:
        logger.error(f"Error getting all devices: {e}")
        return []


async def delete_device(device_id: str) -> bool:
    """
    Delete a device from Firestore.
    
    Args:
        device_id: Device ID to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    if not device_id:
        logger.error("device_id is required to delete device")
        return False
    
    try:
        db = await get_async_db()
        doc_ref = db.collection(DEVICES_COLLECTION).document(device_id)
        
        # Check if document exists before deletion
        doc = await doc_ref.get()
        if not doc.exists:
            logger.warning(f"Device not found for deletion: {device_id}")
            return False
        
        await doc_ref.delete()
        logger.info(f"Device deleted: {device_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        return False


async def get_devices_in_area(
    center_location: Location,
    radius_km: float,
    active_only: bool = True
) -> List[Device]:
    """
    Get devices within a specified radius from a center location.
    
    Args:
        center_location: Center point for the search
        radius_km: Search radius in kilometers
        active_only: If True, return only devices with valid FCM tokens
        
    Returns:
        List of devices within the specified area
    """
    try:
        # Get all devices (filtering by location requires client-side processing)
        all_devices = await get_all_devices(active_only=active_only)
        
        devices_in_area = []
        for device in all_devices:
            if device.currentLocation:
                distance = calculate_distance(
                    center_location.latitude,
                    center_location.longitude,
                    device.currentLocation.latitude,
                    device.currentLocation.longitude
                )
                
                if distance <= radius_km:
                    devices_in_area.append(device)
                    logger.debug(f"Device {device.device_id} is {distance:.2f}km from center")
        
        logger.info(f"Found {len(devices_in_area)} devices within {radius_km}km radius")
        return devices_in_area
        
    except Exception as e:
        logger.error(f"Error getting devices in area: {e}")
        return []


async def get_all_active_device_tokens() -> List[str]:
    """
    Get all active FCM tokens from all devices.
    
    Returns:
        List of active FCM tokens
    """
    try:
        devices = await get_all_devices(active_only=True)
        tokens = [device.fcmToken for device in devices if device.fcmToken]
        
        # Remove duplicates while preserving order
        unique_tokens = list(dict.fromkeys(tokens))
        
        logger.info(f"Retrieved {len(unique_tokens)} unique active FCM tokens")
        return unique_tokens
        
    except Exception as e:
        logger.error(f"Error getting active device tokens: {e}")
        return []


async def get_device_tokens_for_areas(areas: List[str]) -> List[str]:
    """
    Get FCM tokens for devices in specific areas.
    
    Args:
        areas: List of area names/codes to filter by
        
    Returns:
        List of FCM tokens for devices in the specified areas
    """
    if not areas:
        logger.warning("No areas specified for token retrieval")
        return []
    
    try:
        db = await get_async_db()
        
        # Query devices where currentArea is in the specified areas
        query = db.collection(DEVICES_COLLECTION).where('currentArea', 'in', areas)
        docs = query.stream()
        
        tokens = set()
        async for doc in docs:
            device_data = doc.to_dict()
            token = device_data.get('fcmToken')
            if token:
                tokens.add(token)
        
        token_list = list(tokens)
        logger.info(f"Retrieved {len(token_list)} tokens for areas: {areas}")
        return token_list
        
    except Exception as e:
        logger.error(f"Error getting device tokens for areas {areas}: {e}")
        return []


async def update_device_location(
    device_id: str,
    location: Location,
    area: Optional[str] = None
) -> Optional[Device]:
    """
    Update device location and optionally the current area.
    
    Args:
        device_id: Device ID to update
        location: New location
        area: Optional area name/code
        
    Returns:
        Updated Device object if successful, None otherwise
    """
    if not device_id:
        logger.error("device_id is required to update location")
        return None
    
    try:
        update_data = {
            'currentLocation': {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'accuracy': location.accuracy
            },
            'locationUpdatedAt': SERVER_TIMESTAMP
        }
        
        if area:
            update_data['currentArea'] = area
        
        return await create_or_update_device(device_id, update_data)
        
    except Exception as e:
        logger.error(f"Error updating device location for {device_id}: {e}")
        return None


async def update_device_token(device_id: str, fcm_token: str) -> Optional[Device]:
    """
    Update device FCM token.
    
    Args:
        device_id: Device ID to update
        fcm_token: New FCM token
        
    Returns:
        Updated Device object if successful, None otherwise
    """
    if not device_id or not fcm_token:
        logger.error("Both device_id and fcm_token are required")
        return None
    
    try:
        update_data = {
            'fcmToken': fcm_token,
            'tokenUpdatedAt': SERVER_TIMESTAMP
        }
        
        return await create_or_update_device(device_id, update_data)
        
    except Exception as e:
        logger.error(f"Error updating FCM token for {device_id}: {e}")
        return None