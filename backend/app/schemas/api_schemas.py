"""
API Integration Schemas
政府・自治体API連携用のスキーマ定義

This module defines Pydantic schemas for government API integration,
data validation, and normalization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, model_validator

from .shelter import ShelterBase as ShelterData


class DataSourceType(str, Enum):
    """Available data sources"""
    GSI_HAZARD = "gsi_hazard"
    GSI_ELEVATION = "gsi_elevation"
    GSI_SHELTER_GEOJSON = "gsi_shelter_geojson"
    CABINET_OFFICE = "cabinet_office"
    FDMA = "fdma"
    MOCK = "mock"


class APIStatus(str, Enum):
    """API health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HazardType(str, Enum):
    """Types of hazards"""
    FLOOD = "flood"
    TSUNAMI = "tsunami"
    EARTHQUAKE = "earthquake"
    LANDSLIDE = "landslide"
    TYPHOON = "typhoon"
    STORM_SURGE = "storm_surge"


class RiskLevel(str, Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ElevationData(BaseModel):
    """Elevation data from GSI API"""
    elevation: Optional[float] = Field(None, description="Elevation in meters")
    data_source: str = Field(..., description="Source of elevation data")
    accuracy: str = Field("unknown", description="Data accuracy level")
    coordinates: Dict[str, float] = Field(..., description="Longitude and latitude")
    fetched_at: datetime = Field(default_factory=datetime.now)
    
    @validator('elevation')
    def validate_elevation(cls, v):
        if v is not None and (v < -500 or v > 10000):
            raise ValueError("Elevation must be between -500m and 10000m")
        return v
    
    @model_validator(mode='after')
    def validate_coordinates(self):
        coords = self.coordinates
        if not coords.get('longitude') or not coords.get('latitude'):
            raise ValueError("Both longitude and latitude are required")
        
        lon = coords['longitude']
        lat = coords['latitude']
        
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        
        return self


class HazardArea(BaseModel):
    """Hazard affected area definition"""
    area_id: str = Field(..., description="Unique area identifier")
    area_name: str = Field(..., description="Human-readable area name")
    coordinates: List[List[float]] = Field(..., description="Polygon coordinates")
    risk_level: RiskLevel = Field(..., description="Risk level for this area")
    expected_impact: Optional[str] = Field(None, description="Expected impact description")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Polygon must have at least 3 coordinate pairs")
        
        for coord in v:
            if len(coord) != 2:
                raise ValueError("Each coordinate must have longitude and latitude")
            if not (-180 <= coord[0] <= 180) or not (-90 <= coord[1] <= 90):
                raise ValueError("Invalid coordinate values")
        
        return v


class HazardData(BaseModel):
    """Hazard map data"""
    hazard_type: HazardType = Field(..., description="Type of hazard")
    region: str = Field(..., description="Geographic region")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    affected_areas: List[HazardArea] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: DataSourceType = Field(..., description="Data source")
    last_updated: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = Field(None, description="Data validity period")
    
    @validator('affected_areas')
    def validate_affected_areas(cls, v):
        if len(v) > 1000:  # Reasonable limit
            raise ValueError("Too many affected areas")
        return v


class HazardTileInfo(BaseModel):
    """Hazard map tile information for XYZ tile access"""
    hazard_type: str = Field(..., description="Type of hazard")
    region: str = Field(..., description="Geographic region")
    tile_id: str = Field(..., description="GSI tile identifier")
    tile_base_url: str = Field(..., description="Base URL for XYZ tiles")
    wmts_url: Optional[str] = Field(None, description="WMTS metadata URL")
    bounds: Dict[str, float] = Field(..., description="Bounding box coordinates")
    zoom_levels: Dict[str, int] = Field(..., description="Min/max zoom levels")
    attribution: str = Field(..., description="Required attribution text")
    data_format: str = Field(..., description="Tile data format")
    
    @validator('bounds')
    def validate_bounds(cls, v):
        required_keys = ['west', 'south', 'east', 'north']
        if not all(k in v for k in required_keys):
            raise ValueError("Bounds must contain west, south, east, north")
        
        west, south, east, north = v['west'], v['south'], v['east'], v['north']
        if not (-180 <= west <= 180) or not (-180 <= east <= 180):
            raise ValueError("Invalid longitude bounds")
        if not (-90 <= south <= 90) or not (-90 <= north <= 90):
            raise ValueError("Invalid latitude bounds")
        if west >= east or south >= north:
            raise ValueError("Invalid bounds: west must be < east, south must be < north")
        
        return v


class ShelterDataRequest(BaseModel):
    """Request schema for shelter data"""
    region: str = Field(..., description="Target region")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Center coordinates")
    radius_km: float = Field(5.0, ge=0.1, le=50.0, description="Search radius in kilometers")
    shelter_types: Optional[List[str]] = Field(None, description="Filter by shelter types")
    include_elevation: bool = Field(True, description="Include elevation data")
    include_hazard_info: bool = Field(True, description="Include hazard information")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if v is not None:
            lon = v.get('longitude')
            lat = v.get('latitude')
            
            if lon is None or lat is None:
                raise ValueError("Both longitude and latitude are required")
            
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                raise ValueError("Invalid coordinates")
        
        return v


class APIHealthCheck(BaseModel):
    """API health check response"""
    source: DataSourceType = Field(..., description="Data source")
    status: APIStatus = Field(..., description="Health status")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    last_check: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = Field(None, description="Error details if unhealthy")
    endpoints_tested: List[str] = Field(default_factory=list)


class APIUsageStats(BaseModel):
    """API usage statistics"""
    source: DataSourceType = Field(..., description="Data source")
    requests_today: int = Field(0, ge=0)
    requests_this_hour: int = Field(0, ge=0)
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    average_response_time: float = Field(0.0, ge=0.0)
    rate_limit_remaining: Optional[int] = Field(None, ge=0)
    last_reset: datetime = Field(default_factory=datetime.now)


class DataCollectionJob(BaseModel):
    """Data collection job configuration"""
    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Type of data collection")
    sources: List[DataSourceType] = Field(..., description="Target data sources")
    schedule: str = Field(..., description="Cron-like schedule expression")
    enabled: bool = Field(True, description="Whether job is enabled")
    last_run: Optional[datetime] = Field(None)
    next_run: Optional[datetime] = Field(None)
    success_count: int = Field(0, ge=0)
    failure_count: int = Field(0, ge=0)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('schedule')
    def validate_schedule(cls, v):
        # Basic validation for cron-like expressions
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Schedule must be in cron format (5 parts)")
        return v


class DataCollectionResult(BaseModel):
    """Result of a data collection operation"""
    job_id: str = Field(..., description="Associated job ID")
    source: DataSourceType = Field(..., description="Data source")
    status: str = Field(..., description="Collection status")
    records_collected: int = Field(0, ge=0)
    records_updated: int = Field(0, ge=0)
    records_failed: int = Field(0, ge=0)
    start_time: datetime = Field(..., description="Collection start time")
    end_time: datetime = Field(..., description="Collection end time")
    duration_seconds: float = Field(0.0, ge=0.0)
    error_details: Optional[List[str]] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_times(self):
        start = self.start_time
        end = self.end_time
        
        if start and end and end < start:
            raise ValueError("End time must be after start time")
        
        return self


class EnhancedShelterData(ShelterData):
    """Enhanced shelter data with additional API-sourced information"""
    elevation_data: Optional[ElevationData] = Field(None)
    hazard_info: Optional[List[HazardData]] = Field(default_factory=list)
    data_sources: List[DataSourceType] = Field(default_factory=list)
    last_verified: Optional[datetime] = Field(None)
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Data confidence score")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class BatchShelterResponse(BaseModel):
    """Response for batch shelter data requests"""
    shelters: List[EnhancedShelterData] = Field(..., description="Enhanced shelter data")
    total_count: int = Field(..., ge=0, description="Total number of shelters found")
    data_sources_used: List[DataSourceType] = Field(..., description="Sources used for data")
    collection_time: datetime = Field(default_factory=datetime.now)
    cache_status: Dict[DataSourceType, bool] = Field(default_factory=dict)
    health_status: Dict[DataSourceType, APIStatus] = Field(default_factory=dict)
    
    @validator('total_count')
    def validate_total_count(cls, v, values):
        shelters = values.get('shelters', [])
        if v != len(shelters):
            raise ValueError("Total count must match number of shelters")
        return v


class APIConfiguration(BaseModel):
    """API configuration settings"""
    source: DataSourceType = Field(..., description="Data source identifier")
    base_url: str = Field(..., description="Base API URL")
    api_key: Optional[str] = Field(None, description="API key if required")
    rate_limit: int = Field(60, ge=1, description="Requests per minute")
    timeout: int = Field(10, ge=1, le=300, description="Request timeout in seconds")
    retry_attempts: int = Field(3, ge=0, le=10, description="Number of retry attempts")
    cache_ttl: int = Field(3600, ge=0, description="Cache TTL in seconds")
    enabled: bool = Field(True, description="Whether API is enabled")
    health_check_interval: int = Field(300, ge=60, description="Health check interval in seconds")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')


class DataQualityMetrics(BaseModel):
    """Data quality metrics"""
    source: DataSourceType = Field(..., description="Data source")
    completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="Data completeness")
    accuracy_score: float = Field(0.0, ge=0.0, le=1.0, description="Data accuracy")
    timeliness_score: float = Field(0.0, ge=0.0, le=1.0, description="Data timeliness")
    consistency_score: float = Field(0.0, ge=0.0, le=1.0, description="Data consistency")
    overall_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall quality score")
    missing_fields: List[str] = Field(default_factory=list)
    invalid_records: int = Field(0, ge=0)
    total_records: int = Field(0, ge=0)
    last_assessment: datetime = Field(default_factory=datetime.now)
    
    @model_validator(mode='after')
    def calculate_overall_score(self):
        scores = [
            self.completeness_score,
            self.accuracy_score,
            self.timeliness_score,
            self.consistency_score
        ]
        self.overall_score = sum(scores) / len(scores)
        return self