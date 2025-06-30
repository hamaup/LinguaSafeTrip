# backend/app/schemas/sms_intents.py
"""
SMS関連のIntent定義とフォームスキーマ
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class SMSIntentType(str, Enum):
    """SMS関連の詳細なIntent分類"""
    SEND_SAFETY_CONFIRMATION = "send_safety_confirmation"  # 安否確認SMS送信
    CHECK_SMS_RESPONSES = "check_sms_responses"           # SMS返信確認
    RESEND_TO_NO_RESPONSE = "resend_to_no_response"      # 未返信者へ再送信
    SEND_LOCATION_UPDATE = "send_location_update"        # 位置情報更新送信
    SEND_HELP_REQUEST = "send_help_request"              # 救助要請SMS
    SEND_ALL_CLEAR = "send_all_clear"                    # 安全確認完了通知

class SMSFormField(BaseModel):
    """フォームフィールド定義"""
    field_id: str
    field_type: str = Field(..., description="text, textarea, checkbox, select, multi_select")
    label: str
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = True
    validation: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, str]]] = None

class SMSFormConfig(BaseModel):
    """SMS送信フォーム設定"""
    form_id: str = "sms_confirmation_form"
    title: str = "安否確認メッセージ送信"
    description: Optional[str] = None
    fields: List[SMSFormField]
    submit_button_text: str = "送信"
    cancel_button_text: str = "キャンセル"
    show_preview: bool = True
    auto_save_draft: bool = True

class SMSActionData(BaseModel):
    """フロントエンドへのアクションデータ"""
    action_type: str = "show_sms_confirmation_form"
    intent_type: SMSIntentType
    form_config: SMSFormConfig
    message_templates: Dict[str, str]
    context_data: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"  # normal, high, urgent
    
class SMSSendResult(BaseModel):
    """SMS送信結果"""
    success: bool
    sent_count: int = 0
    failed_count: int = 0
    sent_to: List[str] = Field(default_factory=list)
    failed_to: List[str] = Field(default_factory=list)
    message_ids: List[str] = Field(default_factory=list)
    error_details: Optional[Dict[str, str]] = None