"""
Common schema definitions used across the application.
This module contains base types and common data structures.
"""

from .location import LocationInfo, GeoPoint
from .enums import (
    EmergencyLevel,
    DisasterType,
    AlertStatus,
    NotificationChannel,
    LanguageCode,
    IntentCategory,
    TaskType,
    DeviceType,
    ContactType
)
from .datetime_utils import TimestampMixin

__all__ = [
    # Location types
    "LocationInfo",
    "GeoPoint", 
    
    # Enums
    "EmergencyLevel",
    "DisasterType", 
    "AlertStatus",
    "NotificationChannel",
    "LanguageCode",
    "IntentCategory",
    "TaskType",
    "DeviceType",
    "ContactType",
    
    # Mixins
    "TimestampMixin"
]