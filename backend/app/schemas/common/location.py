"""
Unified location schema definitions.
Consolidates all location-related data structures from across the application.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class LocationInfo(BaseModel):
    """
    Unified location information model.
    Replaces LocationModel, GeoPoint, Location from various files.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "latitude": 35.6762,
                "longitude": 139.6503,
                "accuracy": 10.5,
                "altitude": 45.2,
                "source": "gps",
                "timestamp": "2024-01-01T12:00:00Z",
                "address": "Tokyo Station, Tokyo, Japan"
            }
        }
    )
    
    latitude: float = Field(
        ..., 
        ge=-90.0, 
        le=90.0,
        description="緯度 (-90.0 to 90.0)"
    )
    longitude: float = Field(
        ..., 
        ge=-180.0, 
        le=180.0,
        description="経度 (-180.0 to 180.0)"
    )
    accuracy: Optional[float] = Field(
        None, 
        ge=0.0,
        description="位置精度（メートル単位）"
    )
    altitude: Optional[float] = Field(
        None,
        description="標高（メートル単位）"
    )
    source: Optional[str] = Field(
        None,
        description="位置情報取得方法 (gps/network/manual/cached)"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="位置情報取得時刻"
    )
    address: Optional[str] = Field(
        None,
        max_length=200,
        description="住所（読みやすい形式）"
    )

# Backward compatibility aliases
GeoPoint = LocationInfo
Location = LocationInfo

class LocationQuery(BaseModel):
    """Location-based query parameters for searches."""
    model_config = ConfigDict(extra="forbid")
    
    center: LocationInfo = Field(..., description="検索中心点")
    radius_km: float = Field(
        default=10.0,
        ge=0.1,
        le=100.0,
        description="検索半径（キロメートル）"
    )
    include_accuracy: bool = Field(
        default=False,
        description="位置精度を考慮するかどうか"
    )

class LocationBounds(BaseModel):
    """Geographic bounding box for area-based queries."""
    model_config = ConfigDict(extra="forbid")
    
    north_east: LocationInfo = Field(..., description="北東角")
    south_west: LocationInfo = Field(..., description="南西角")
    
    def contains(self, location: LocationInfo) -> bool:
        """Check if a location is within the bounds."""
        return (
            self.south_west.latitude <= location.latitude <= self.north_east.latitude and
            self.south_west.longitude <= location.longitude <= self.north_east.longitude
        )