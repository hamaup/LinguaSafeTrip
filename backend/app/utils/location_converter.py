"""
位置情報スキーマ変換ユーティリティ
フロントエンドからの位置情報Dictを各種スキーマに統一的に変換
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.schemas.common.location import Location
from app.schemas.device import DeviceLocation
from app.schemas.agent.suggestions import LocationModel


def dict_to_location_info(location_dict: Dict[str, Any]) -> Optional[Location]:
    """
    フロントエンドからの位置情報Dictを統一LocationInfoに変換
    
    Args:
        location_dict: {"latitude": float, "longitude": float, "accuracy": float}
    
    Returns:
        Location object or None if invalid
    """
    if not location_dict or not isinstance(location_dict, dict):
        return None
    
    latitude = location_dict.get("latitude")
    longitude = location_dict.get("longitude")
    
    if latitude is None or longitude is None:
        return None
    
    try:
        return Location(
            latitude=float(latitude),
            longitude=float(longitude),
            accuracy=location_dict.get("accuracy")
        )
    except (ValueError, TypeError):
        return None


def location_info_to_device_location(
    location_info: Location, 
    geo_info: Optional[Dict[str, Any]] = None
) -> DeviceLocation:
    """
    LocationInfoをDeviceLocationに変換（住所情報付き）
    
    Args:
        location_info: 基本位置情報
        geo_info: 住所情報 {"prefecture": str, "city": str, "address": str}
    
    Returns:
        DeviceLocation with enhanced location data
    """
    geo_info = geo_info or {}
    
    return DeviceLocation(
        latitude=location_info.latitude,
        longitude=location_info.longitude,
        accuracy=location_info.accuracy,
        timestamp=datetime.now(timezone.utc),
        prefecture=geo_info.get("prefecture"),
        city=geo_info.get("city"),
        address=geo_info.get("address")
    )


def location_info_to_location_model(location_info: Location) -> LocationModel:
    """
    LocationInfoをLocationModel（レガシー）に変換
    
    Args:
        location_info: 統一位置情報
    
    Returns:
        LocationModel for backward compatibility
    """
    return LocationModel(
        latitude=location_info.latitude,
        longitude=location_info.longitude
    )


def extract_location_from_request(request) -> Optional[Location]:
    """
    HeartbeatRequestから位置情報を統一的に抽出
    
    Args:
        request: HeartbeatRequest object
    
    Returns:
        Unified Location object or None
    """
    if not (request.device_status and request.device_status.location):
        return None
    
    return dict_to_location_info(request.device_status.location)