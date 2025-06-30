from fastapi import APIRouter, HTTPException, status, Body, Path, Request
from fastapi.exceptions import RequestValidationError
from typing import Optional
import logging
from datetime import datetime
from pydantic import ValidationError

from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceStatusUpdate,
    DeviceWithProactiveContext,
    DeviceCapabilities,
    DeviceStatus
)
from app.services.device_service import (
    create_device,
    get_device_by_id,
    update_device,
    update_device_status,
    get_device_with_context
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/devices",
    response_model=DeviceResponse,
    summary="Register a new device",
    description="Register a new device with capabilities and initial status",
    status_code=status.HTTP_201_CREATED,
    tags=["Devices"]
)
async def register_device(
    request: Request
) -> DeviceResponse:
    """Register a new device"""
    try:
        # Get raw request body for debugging
        body = await request.body()
        # Parse JSON manually to provide better error messages
        import json
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Try to create DeviceCreate object with detailed validation
        try:
            device = DeviceCreate(**data)
            logger.info(f"Registering new device: {device.device_id}")
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            # Check for specific validation errors
            for error in e.errors():
                if error.get('loc') == ('device_id',) and error.get('type') == 'missing':
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "validation_error",
                            "message": "device_id is required",
                            "code": "MISSING_DEVICE_ID"
                        }
                    )
                elif error.get('loc') == ('platform',) and error.get('type') == 'enum':
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "validation_error",
                            "message": "Invalid platform. Must be one of: ios, android, web",
                            "code": "INVALID_PLATFORM"
                        }
                    )
            # Return detailed validation error for other cases
            raise HTTPException(
                status_code=422, 
                detail={
                    "message": "Validation failed",
                    "errors": e.errors(),
                    "received_data": data
                }
            )
        
        # Check if device already exists
        existing = await get_device_by_id(device.device_id)
        if existing:
            # Update existing device instead
            logger.info(f"Device {device.device_id} already exists, updating")
            return await update_device(device.device_id, DeviceUpdate(
                fcm_token=device.fcm_token,
                app_version=device.app_version,
                os_version=device.os_version,
                language=device.language,
                timezone=device.timezone,
                capabilities=device.capabilities,
                status=device.status
            ))
        
        # Create new device
        created_device = await create_device(device)
        return created_device
    
    except HTTPException:
        # Re-raise HTTPException as is
        raise
    except Exception as e:
        logger.error(f"Device registration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device registration failed: {str(e)}"
        )

# GET /devices/{device_id} は削除済み
# 統合ハートビートAPIでデバイス情報を取得可能

# PUT /devices/{device_id} は削除済み
# 統合ハートビートAPIでデバイス設定更新可能

# PATCH /devices/{device_id}/status は削除済み
# 統合ハートビートAPIでデバイス状態更新 + 緊急検出を統合処理

# GET /devices/{device_id}/context は削除済み
# 統合ハートビートAPIでデバイスコンテキスト情報を取得可能