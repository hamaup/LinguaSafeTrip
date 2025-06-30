# backend/app/schemas/device.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    """Supported device platforms"""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"

class NetworkType(str, Enum):
    """Network connection types"""
    WIFI = "wifi"
    CELLULAR_5G = "5g"
    CELLULAR_4G = "4g"
    CELLULAR_3G = "3g"
    CELLULAR_2G = "2g"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class DeviceCapabilities(BaseModel):
    """Device capabilities and permissions"""
    has_gps: bool = Field(default=True, description="GPS capability")
    gps_enabled: bool = Field(default=False, description="GPS permission granted")
    has_sms: bool = Field(default=True, description="SMS capability")
    sms_enabled: bool = Field(default=False, description="SMS permission granted")
    has_push_notification: bool = Field(default=True, description="Push notification capability")
    push_notification_enabled: bool = Field(default=False, description="Push notification enabled")
    has_camera: bool = Field(default=True, description="Camera capability")
    camera_enabled: bool = Field(default=False, description="Camera permission granted")

class DeviceLocation(BaseModel):
    """Device GPS location information"""
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    accuracy: Optional[float] = Field(None, description="Location accuracy in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, description="Speed in m/s")
    heading: Optional[float] = Field(None, description="Heading in degrees")
    timestamp: Optional[datetime] = Field(None, description="GPS timestamp")
    # 地域情報（逆ジオコーディングで取得）
    prefecture: Optional[str] = Field(None, description="都道府県名")
    city: Optional[str] = Field(None, description="市区町村名")
    address: Optional[str] = Field(None, description="詳細住所")

class DeviceStatus(BaseModel):
    """Real-time device status information"""
    battery_level: Optional[int] = Field(None, ge=0, le=100, description="Battery level percentage")
    is_charging: Optional[bool] = Field(None, description="Whether device is charging")
    is_power_saving_mode: Optional[bool] = Field(None, description="Power saving mode active")
    network_type: Optional[NetworkType] = Field(None, description="Current network connection type")
    signal_strength: Optional[int] = Field(None, ge=0, le=5, description="Network signal strength (0-5)")
    is_airplane_mode: Optional[bool] = Field(None, description="Airplane mode active")
    location: Optional[DeviceLocation] = Field(None, description="Current GPS location")
    emergency_detected: Optional[bool] = Field(None, description="Emergency situation detected")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last status update time")

class DeviceBase(BaseModel):
    """Base device information"""
    device_id: str = Field(..., description="Unique device identifier")
    platform: PlatformType = Field(..., description="Device platform (ios/android/web)")
    fcm_token: Optional[str] = Field(None, description="Firebase Cloud Messaging token")
    app_version: Optional[str] = Field(None, description="App version number")
    os_version: Optional[str] = Field(None, description="Operating system version")
    model: Optional[str] = Field(None, description="Device model name")
    language: Optional[str] = Field("ja", description="Device language setting")
    timezone: Optional[str] = Field("Asia/Tokyo", description="Device timezone")

class DeviceCreate(DeviceBase):
    """Device creation schema"""
    capabilities: Optional[DeviceCapabilities] = None
    status: Optional[DeviceStatus] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "device_123",
                "platform": "ios",
                "fcm_token": "fcm_token_here",
                "app_version": "1.0.0",
                "os_version": "iOS 15.0",
                "model": "iPhone 12",
                "language": "ja",
                "timezone": "Asia/Tokyo",
                "capabilities": {
                    "gps_enabled": True,
                    "sms_enabled": True
                },
                "status": {
                    "battery_level": 80,
                    "is_charging": False,
                    "network_type": "wifi"
                }
            }
        }
    }

class DeviceUpdate(BaseModel):
    """Device update schema"""
    fcm_token: Optional[str] = None
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    capabilities: Optional[DeviceCapabilities] = None
    status: Optional[DeviceStatus] = None

class DeviceStatusUpdate(BaseModel):
    """Device status update schema (for frequent updates)"""
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    is_charging: Optional[bool] = None
    is_power_saving_mode: Optional[bool] = None
    network_type: Optional[NetworkType] = None
    signal_strength: Optional[int] = Field(None, ge=0, le=5)
    is_airplane_mode: Optional[bool] = None
    location: Optional[DeviceLocation] = None
    emergency_detected: Optional[bool] = None

class DeviceInDB(DeviceBase):
    """Device database schema"""
    capabilities: DeviceCapabilities = Field(default_factory=DeviceCapabilities)
    status: DeviceStatus = Field(default_factory=DeviceStatus)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        from_attributes = True

class DeviceResponse(DeviceInDB):
    """Device response schema"""
    pass

class Device(BaseModel):
    """Device schema for CRUD operations"""
    device_id: str
    fcm_token: Optional[str] = None
    user_nickname: Optional[str] = "User"
    language_code: Optional[str] = "ja"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DeviceWithProactiveContext(DeviceResponse):
    """Device with proactive suggestion context"""
    has_unread_alerts: bool = False
    last_quiz_date: Optional[datetime] = None
    emergency_contacts_count: int = 0
    guide_views_count: int = 0
    last_active: Optional[datetime] = None
    suggested_actions: list[str] = Field(default_factory=list)