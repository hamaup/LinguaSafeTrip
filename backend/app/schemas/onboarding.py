# backend/app/schemas/onboarding.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class OnboardingStepType(str, Enum):
    """Types of onboarding steps"""
    WELCOME = "welcome"
    FEATURE_INTRO = "feature_intro"
    SETUP_GUIDE = "setup_guide"
    PERMISSIONS = "permissions"
    EMERGENCY_CONTACTS = "emergency_contacts"
    LOCATION_SETTINGS = "location_settings"
    NOTIFICATION_SETTINGS = "notification_settings"
    QUIZ_INTRO = "quiz_intro"
    GUIDE_INTRO = "guide_intro"
    COMPLETION = "completion"

class OnboardingStep(BaseModel):
    """Individual onboarding step"""
    id: str = Field(..., description="Step ID")
    type: OnboardingStepType = Field(..., description="Step type")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    icon: Optional[str] = Field(None, description="Step icon")
    action_label: Optional[str] = Field(None, description="Action button label")
    action_type: Optional[str] = Field(None, description="Action type")
    action_data: Optional[Dict[str, Any]] = Field(None, description="Action data")
    is_required: bool = Field(default=False, description="Whether this step is required")
    estimated_time_minutes: int = Field(default=1, description="Estimated completion time")
    order: int = Field(..., description="Step order")

class WelcomeMessage(BaseModel):
    """Welcome message for first-time users"""
    title: str = Field(..., description="Welcome title")
    message: str = Field(..., description="Welcome message")
    app_introduction: str = Field(..., description="App introduction")
    key_features: List[str] = Field(..., description="Key features list")
    getting_started_tip: str = Field(..., description="Getting started tip")
    language: str = Field(default="ja", description="Message language")

class FeatureGuide(BaseModel):
    """Feature guide item"""
    feature_id: str = Field(..., description="Feature ID")
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    icon: str = Field(..., description="Feature icon")
    demo_action: Optional[str] = Field(None, description="Demo action")
    importance_level: str = Field(default="medium", description="Importance level (high/medium/low)")
    category: str = Field(..., description="Feature category")

class OnboardingProgress(BaseModel):
    """User's onboarding progress"""
    user_id: str = Field(..., description="User ID")
    device_id: str = Field(..., description="Device ID")
    is_first_time: bool = Field(default=True, description="Is first time user")
    completed_steps: List[str] = Field(default_factory=list, description="Completed step IDs")
    current_step_id: Optional[str] = Field(None, description="Current step ID")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Onboarding start time")
    completed_at: Optional[datetime] = Field(None, description="Onboarding completion time")
    skipped_steps: List[str] = Field(default_factory=list, description="Skipped step IDs")
    language: str = Field(default="ja", description="User language")

class OnboardingResponse(BaseModel):
    """Onboarding flow response"""
    is_first_time: bool = Field(..., description="Is first time user")
    welcome_message: Optional[WelcomeMessage] = Field(None, description="Welcome message")
    current_step: Optional[OnboardingStep] = Field(None, description="Current onboarding step")
    remaining_steps: List[OnboardingStep] = Field(default_factory=list, description="Remaining steps")
    progress_percentage: float = Field(default=0.0, description="Completion percentage")
    estimated_remaining_time: int = Field(default=0, description="Estimated remaining time in minutes")
    feature_guides: List[FeatureGuide] = Field(default_factory=list, description="Available feature guides")

class OnboardingStepComplete(BaseModel):
    """Mark onboarding step as complete"""
    step_id: str = Field(..., description="Completed step ID")
    user_data: Optional[Dict[str, Any]] = Field(None, description="Data collected in this step")
    skip_remaining: bool = Field(default=False, description="Skip remaining steps")

class QuickSetupRequest(BaseModel):
    """Quick setup request for essential features"""
    enable_location: bool = Field(default=False, description="Enable location services")
    enable_notifications: bool = Field(default=True, description="Enable push notifications")
    add_emergency_contact: bool = Field(default=False, description="Add emergency contact now")
    language: str = Field(default="ja", description="Preferred language")
    skip_tutorial: bool = Field(default=False, description="Skip tutorial")

class OnboardingAnalytics(BaseModel):
    """Onboarding analytics data"""
    user_id: str = Field(..., description="User ID")
    total_time_spent: int = Field(..., description="Total time spent in seconds")
    steps_completed: int = Field(..., description="Number of steps completed")
    steps_skipped: int = Field(..., description="Number of steps skipped")
    completion_rate: float = Field(..., description="Completion rate (0.0-1.0)")
    drop_off_step: Optional[str] = Field(None, description="Step where user dropped off")
    most_time_spent_step: Optional[str] = Field(None, description="Step with most time spent")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="Analytics timestamp")

# API Request/Response models
class OnboardingStatusRequest(BaseModel):
    """Request for getting onboarding status"""
    user_id: Optional[str] = Field(None, description="User ID")
    device_id: str = Field(..., description="Device ID")
    language: str = Field(default="ja", description="Preferred language")

class OnboardingStatusResponse(OnboardingResponse):
    """Response for onboarding status"""
    pass

class OnboardingCompleteRequest(BaseModel):
    """Request for completing an onboarding step"""
    user_id: Optional[str] = Field(None, description="User ID")
    device_id: str = Field(..., description="Device ID")
    step_id: str = Field(..., description="Step ID to complete")
    step_data: Optional[Dict[str, Any]] = Field(None, description="Data from the step")

class OnboardingCompleteResponse(BaseModel):
    """Response for completing an onboarding step"""
    success: bool = Field(..., description="Whether the step was completed successfully")
    progress_percentage: float = Field(..., description="Updated progress percentage")
    next_step: Optional[OnboardingStep] = Field(None, description="Next step if any")
    is_complete: bool = Field(default=False, description="Whether onboarding is complete")