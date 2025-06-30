"""
Agent suggestion schemas.
Consolidates all suggestion-related data structures.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from ..common.location import LocationInfo
from ..common.enums import IntentCategory, EmergencyLevel, LanguageCode
from ..common.datetime_utils import TimestampMixin
from ..alert import LatestAlertSummary
from ..unified_event import UnifiedEventData


class ProactiveTriggerType(str, Enum):
    """Types of proactive triggers"""
    # オンボーディングトリガー
    WELCOME_NEW_USER = "welcome_new_user"
    ONBOARDING_REMINDER = "onboarding_reminder"
    ONBOARDING_COMPLETED = "onboarding_completed"
    
    # 平常時トリガー
    QUIZ_REMINDER = "quiz_reminder"
    LOW_BATTERY_WARNING = "low_battery_warning"
    GUIDE_INTRODUCTION = "guide_introduction"
    EMERGENCY_CONTACT_SETUP = "emergency_contact_setup"
    NEW_DISASTER_NEWS = "new_disaster_news"
    SEASONAL_WARNING = "seasonal_warning"
    
    # 災害時トリガー
    SAFETY_CHECK_ASSISTANCE = "safety_check_assistance"
    NEW_DISASTER_ALERT = "new_disaster_alert_jma"
    LONG_TIME_INACTIVE = "long_time_no_see_user"
    GUIDE_VIEWED = "user_viewed_specific_guide"
    DISASTER_ANNIVERSARY = "approaching_disaster_anniversary"


class SuggestionPriority(str, Enum):
    """Suggestion priority levels"""
    CRITICAL = "critical"  # 緊急・生命に関わる
    HIGH = "high"  # 重要・早急な対応推奨
    MEDIUM = "medium"  # 通常・適切なタイミングで
    LOW = "low"  # 情報提供・余裕がある時に


class ActionType(str, Enum):
    """Types of actions suggested"""
    # Navigation actions
    OPEN_QUIZ = "open_quiz"
    VIEW_GUIDE = "view_guide"
    VIEW_ALERT_DETAILS = "view_alert_details"
    VIEW_NEWS = "view_news"
    OPEN_SETTINGS = "open_settings"
    EXPLORE_APP = "explore_app"
    VIEW_RECOMMENDATIONS = "view_recommendations"
    
    # Device actions
    CHARGE_BATTERY = "charge_battery"
    ENABLE_POWER_SAVING = "enable_power_saving"
    
    # Communication actions
    REGISTER_CONTACTS = "register_contacts"
    SEND_SAFETY_MESSAGE = "send_safety_message"
    
    # Emergency actions
    NAVIGATE_TO_SHELTER = "navigate_to_shelter"
    CHECK_UPDATES = "check_updates"
    
    # Learning actions
    LEARN_DISASTER_PREP = "learn_disaster_prep"


class SuggestionItem(BaseModel):
    """
    Individual suggestion item - Unified version.
    This consolidates all SuggestionItem variations.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "guide_recommendation",
                "content": "地震に備えて家具の固定方法を学びましょう",
                "action_query": "地震対策について教えて",
                "action_data": {"guide_topic": "earthquake_prep"}
            }
        }
    )
    
    # Core fields
    suggestion_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="提案の一意なID"
    )
    type: str = Field(
        ..., 
        description="提案種別 (e.g., 'info', 'sms_proposal', 'guide_recommendation', 'low_battery_warning')"
    )
    content: str = Field(
        ..., 
        description="タイムラインに表示するテキスト"
    )
    
    # Optional descriptive fields
    title: Optional[str] = Field(None, max_length=100, description="提案タイトル")
    description: Optional[str] = Field(None, max_length=500, description="提案の詳細説明")
    
    # Action-related fields
    action_query: Optional[str] = Field(
        None, 
        description="提案をタップした際にエージェントに送信する質問文"
    )
    action_display_text: Optional[str] = Field(
        None, 
        description="ユーザーのメッセージとして表示するテキスト"
    )
    action_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="ボタンなどのアクションに必要なデータ"
    )
    action_type: Optional[str] = Field(None, description="アクションタイプ")
    
    # Metadata
    priority: Optional[str] = Field(
        default="medium", 
        description="優先度 (low/medium/high/critical)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, 
        description="提案作成日時"
    )
    
    # UI hints
    icon: Optional[str] = Field(None, description="アイコン名")
    url: Optional[str] = Field(None, description="関連URL")


class SuggestionCardActionButton(BaseModel):
    """Action button for suggestion cards."""
    button_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="ボタンの一意なID"
    )
    label: str = Field(..., description="ボタンのラベル (ユーザー言語)")
    action_type: Literal[
        "url",                  # 指定されたURLをブラウザで開く
        "call_tool",            # バックエンドの特定のツールを呼び出す
        "show_guide",           # アプリ内の特定のガイドコンテンツを表示する
        "show_map",             # 地図を表示する
        "ask_clarification",    # ユーザーに追加情報を尋ねる
        "send_sms_intent",      # SMSアプリケーションを起動
        "trigger_notification", # システム内部で通知をトリガー
        "custom_event",         # カスタムイベントを発生
        "dismiss_card"          # カードを非表示にする
    ] = Field(..., description="ボタンが実行するアクションの種類")
    action_value: Optional[Any] = Field(
        None, 
        description="アクションに関する値 (URLやツール名など)"
    )
    tool_name: Optional[str] = Field(
        None, 
        description="call_toolアクションの場合、呼び出すツール名"
    )
    tool_args: Optional[Dict[str, Any]] = Field(
        None, 
        description="call_toolアクションの場合、ツールに渡す引数"
    )
    custom_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="カスタムアクション用の追加データ"
    )


class SuggestionCard(BaseModel):
    """
    Suggestion card for frontend display.
    Enhanced from agent_schemas.py
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "card_id": "550e8400-e29b-41d4-a716-446655440000",
                "card_type": "guide_recommendation",
                "title": "地震への備え",
                "content": "地震に備えて、家具の固定や非常用品の準備をしましょう。",
                "priority": "high",
                "action_buttons": [{
                    "label": "ガイドを見る",
                    "action_type": "show_guide",
                    "action_value": "earthquake_preparation"
                }]
            }
        }
    )
    
    card_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="カードの一意なID"
    )
    card_type: str = Field(
        ..., 
        description="カードのタイプ (info/action/alert/guide等)"
    )
    title: str = Field(..., description="カードのタイトル (ユーザー言語)")
    content: str = Field(..., description="カードの本文 (ユーザー言語)")
    
    # Visual elements
    image_url: Optional[str] = Field(None, description="カード画像のURL")
    icon_name: Optional[str] = Field(None, description="アイコン名")
    
    # Priority and timing
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        default="medium", 
        description="カードの優先度"
    )
    display_duration_seconds: Optional[int] = Field(
        None, 
        description="カード表示時間(秒)"
    )
    expires_at: Optional[datetime] = Field(
        None, 
        description="カードの有効期限"
    )
    
    # Actions
    action_buttons: List[SuggestionCardActionButton] = Field(
        default_factory=list, 
        description="カードに表示するボタンのリスト"
    )
    
    # Metadata
    source_tool: Optional[str] = Field(
        None, 
        description="カードを生成したツール名"
    )
    related_event_id: Optional[str] = Field(
        None, 
        description="関連する災害イベントID"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="追加のメタデータ"
    )
    
    # Suggestion item compatibility
    suggestion_item: Optional[SuggestionItem] = Field(
        None,
        description="関連する提案アイテム"
    )


class ProactiveSuggestion(BaseModel):
    """
    Proactive suggestion with full context.
    Enhanced from proactive_suggestions.py
    """
    model_config = ConfigDict(extra="forbid")
    
    id: str = Field(..., description="Unique suggestion ID")
    trigger_type: ProactiveTriggerType
    priority: SuggestionPriority
    
    # Content
    title: str = Field(..., max_length=100)
    message: str = Field(..., max_length=500)
    action_type: ActionType
    action_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Display properties
    icon: Optional[str] = Field(None, description="Icon identifier")
    color_scheme: Optional[str] = Field(None, description="Color theme")
    display_duration_seconds: Optional[int] = Field(None, ge=1, le=300)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Context
    is_dismissible: bool = Field(default=True)
    requires_acknowledgment: bool = Field(default=False)
    target_languages: List[LanguageCode] = Field(default_factory=list)
    
    # Analytics
    analytics_tags: List[str] = Field(default_factory=list)
    
    def to_suggestion_item(self) -> SuggestionItem:
        """Convert to SuggestionItem for compatibility"""
        return SuggestionItem(
            type=self.trigger_type.value,
            content=self.message,
            title=self.title,
            action_type=self.action_type.value,
            action_data=self.action_data,
            priority=self.priority.value,
            icon=self.icon
        )


class ProactiveSuggestionResponse(BaseModel):
    """Response containing proactive suggestions"""
    suggestions: List[Union[SuggestionItem, ProactiveSuggestion]]
    has_more_items: bool = Field(
        False, 
        description="さらに過去の提案が存在するかどうか"
    )
    is_disaster_related: Optional[bool] = Field(
        False, 
        description="災害関連の提案かどうか"
    )
    disaster_severity: Optional[str] = Field(
        None, 
        description="災害の深刻度"
    )
    disaster_event_ids: Optional[List[str]] = Field(
        None, 
        description="関連する災害イベントID"
    )
    next_check_after: Optional[datetime] = Field(
        None, 
        description="次回チェック時刻"
    )


class LocationModel(BaseModel):
    """Simple location model for suggestions"""
    latitude: float
    longitude: float


class UserAppUsageSummary(BaseModel):
    """User app usage summary for context"""
    unread_guide_topics: Optional[List[str]] = Field(
        None, 
        description="未読ガイドトピック"
    )
    incomplete_settings: Optional[List[str]] = Field(
        None, 
        description="未完了設定項目"
    )
    last_app_open_days_ago: Optional[int] = Field(
        None, 
        description="最終アプリ起動からの経過日数"
    )
    is_new_user: Optional[bool] = Field(
        None, 
        description="新規ユーザーフラグ"
    )
    local_contact_count: Optional[int] = Field(
        None, 
        description="登録済み緊急連絡先数"
    )


class ProactiveSuggestionContext(BaseModel):
    """Context for generating proactive suggestions"""
    model_config = ConfigDict(extra="forbid")
    
    # Required fields
    device_id: str = Field(..., description="デバイスID")
    language_code: str = Field(..., description="言語コード")
    
    # Optional context
    limit: Optional[int] = Field(None, description="取得する提案の最大数", ge=1, le=50)
    current_location: Optional[LocationModel] = Field(
        None, 
        description="現在地情報"
    )
    latest_alert_summary: Optional[LatestAlertSummary] = Field(
        None, 
        description="最新アラート概要"
    )
    
    # Situation and mode
    current_situation: str = Field(
        default="normal", 
        description="Current situation: 'alert_active' or 'normal'"
    )
    is_emergency_mode: Optional[bool] = Field(
        False, 
        description="緊急モードフラグ"
    )
    
    # History and usage
    last_suggestion_timestamp: Optional[datetime] = Field(
        None, 
        description="最後の提案日時"
    )
    suggestion_history_summary: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="提案履歴サマリー"
    )
    user_app_usage_summary: Optional[UserAppUsageSummary] = Field(
        None, 
        description="アプリ利用状況"
    )
    
    # Event and location data
    recent_normalized_events: Optional[List[UnifiedEventData]] = Field(
        None, 
        description="最近のイベントデータ"
    )
    current_area_codes: Optional[List[str]] = Field(
        None, 
        description="現在地の市区町村コード"
    )
    
    # Device state
    permissions: Optional[Dict[str, bool]] = Field(
        None, 
        description="権限状態"
    )
    device_status: Optional[Dict[str, Any]] = Field(
        None, 
        description="デバイスステータス"
    )
    location: Optional[Dict[str, Any]] = Field(
        None, 
        description="位置情報詳細"
    )


class TriggerEvaluation(BaseModel):
    """Trigger evaluation result for proactive suggestions"""
    trigger_type: ProactiveTriggerType = Field(..., description="Trigger type")
    is_triggered: bool = Field(..., description="Whether the trigger is activated")
    priority: SuggestionPriority = Field(default=SuggestionPriority.MEDIUM, description="Suggestion priority")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    suggestion_data: Optional[Dict[str, Any]] = Field(None, description="Additional data for suggestion generation")
    expires_at: Optional[datetime] = Field(None, description="When this trigger evaluation expires")
    created_at: datetime = Field(default_factory=datetime.now, description="When this evaluation was created")


# Ensure forward references are resolved
ProactiveSuggestionContext.model_rebuild()
UserAppUsageSummary.model_rebuild()