"""
Common enums used across the application.
Centralizes all enumeration types for consistency.
"""

from enum import Enum

class EmergencyLevel(str, Enum):
    """Emergency level classification."""
    NORMAL = "normal"
    ADVISORY = "advisory"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class DisasterType(str, Enum):
    """Types of disasters."""
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    TYPHOON = "typhoon"
    FLOOD = "flood"
    LANDSLIDE = "landslide"
    VOLCANIC_ERUPTION = "volcanic_eruption"
    HEAVY_RAIN = "heavy_rain"
    HEAVY_SNOW = "heavy_snow"
    HIGH_WIND = "high_wind"
    EXTREME_HEAT = "extreme_heat"
    FIRE = "fire"
    OTHER = "other"

class AlertStatus(str, Enum):
    """Status of alerts."""
    ACTIVE = "active"
    UPDATED = "updated"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TEST = "test"

class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"
    VOICE = "voice"

class LanguageCode(str, Enum):
    """Supported language codes."""
    JAPANESE = "ja"
    ENGLISH = "en"
    CHINESE_SIMPLIFIED = "zh_CN"
    CHINESE_TRADITIONAL = "zh_TW"
    KOREAN = "ko"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"

class IntentCategory(str, Enum):
    """User intent categories for classification."""
    DISASTER_INFORMATION = "disaster_information"
    EVACUATION_SUPPORT = "evacuation_support"
    EMERGENCY_HELP = "emergency_help"
    DISASTER_PREPARATION = "disaster_preparation"
    DISASTER_GUIDE_REQUEST = "disaster_guide_request"
    SAFETY_CONFIRMATION = "safety_confirmation"
    SHELTER_SEARCH = "shelter_search"
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    INFORMATION_REQUEST = "information_request"
    OFF_TOPIC = "off_topic"
    UNKNOWN = "unknown"

class TaskType(str, Enum):
    """Task types for agent processing."""
    INITIAL = "initial"
    OFF_TOPIC = "off_topic"
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    DISASTER_RELATED = "disaster_related"
    DISASTER_PREPARATION = "disaster_preparation"
    EVACUATION_SUPPORT = "evacuation_support"
    DISASTER_INFO = "disaster_info"
    INFORMATION_GUIDE = "information_guide"
    EMERGENCY_RESPONSE = "emergency_response"
    SAFETY_CONFIRMATION = "safety_confirmation"
    COMMUNICATION = "communication"
    ERROR = "error"
    UNKNOWN = "unknown"

class DeviceType(str, Enum):
    """Device types."""
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    SMARTWATCH = "smartwatch"
    UNKNOWN = "unknown"

class ContactType(str, Enum):
    """Emergency contact types."""
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    NEIGHBOR = "neighbor"
    MEDICAL = "medical"
    EMERGENCY_SERVICE = "emergency_service"
    OTHER = "other"