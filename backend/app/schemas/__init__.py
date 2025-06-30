"""
LinguaSafeTrip Backend Schemas

Unified schema definitions for the LinguaSafeTrip backend application.
This module provides a centralized access point for all schema definitions.
"""

# Common schemas (base types)
from .common import (
    LocationInfo,
    GeoPoint,
    EmergencyLevel,
    DisasterType,
    AlertStatus,
    NotificationChannel,
    LanguageCode,
    IntentCategory,
    TaskType,
    DeviceType,
    ContactType,
    TimestampMixin
)

# Agent schemas
from .agent import (
    AgentState,
    AgentStateModel,
    SuggestionItem,
    SuggestionCard,
    ProactiveSuggestion,
    AgentResponse,
    ErrorResponse,
    RoutingDecision,
    DisasterIntentSchema
)

# Legacy compatibility - Re-export commonly used schemas
from .chat_schemas import ChatRequest, ChatResponse
from .disaster import JMAEvent, RelevantDisasterEvent
from .alert import AlertLevel, LatestAlertSummary, AlertHistoryCreate, FcmAlertInfo

# Version info
__version__ = "2.0.0"
__schema_version__ = "2024.01"

# Public API
__all__ = [
    # Common types
    "LocationInfo",
    "GeoPoint", 
    "EmergencyLevel",
    "DisasterType",
    "AlertStatus",
    "NotificationChannel",
    "LanguageCode",
    "IntentCategory",
    "TaskType", 
    "DeviceType",
    "ContactType",
    "TimestampMixin",
    
    # Agent types
    "AgentState",
    "AgentStateModel",
    "SuggestionItem",
    "SuggestionCard",
    "ProactiveSuggestion", 
    "AgentResponse",
    "ErrorResponse",
    "RoutingDecision",
    "DisasterIntentSchema",
    
    # Legacy compatibility
    "ChatRequest",
    "ChatResponse",
    "JMAEvent",
    "RelevantDisasterEvent",
    "AlertLevel",
    "LatestAlertSummary",
    "AlertHistoryCreate",
    "FcmAlertInfo",
    
    # Version info
    "__version__",
    "__schema_version__"
]

