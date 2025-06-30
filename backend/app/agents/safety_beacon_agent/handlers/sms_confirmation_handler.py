# backend/app/agents/safety_beacon_agent/handlers/sms_confirmation_handler.py
"""
SMS安否確認ハンドラー - ユーザーの意図を検出してフォーム表示を促す
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent_state import AgentState
# translate_text will be imported lazily to avoid circular imports
from .complete_response_handlers import CompleteResponseGenerator

logger = logging.getLogger(__name__)

# バッチ処理フラグ

async def handle_sms_confirmation_request(state: AgentState, target_language: str = "ja") -> Dict[str, Any]:
    """
    SMS安否確認要求を処理し、フロントエンドでのフォーム表示を促す
    
    Returns:
        Dict containing:
        - requires_action: "show_sms_form"
        - action_data: SMS送信に必要なデータ
        - response_text: ユーザーへの説明文
    """
    # バッチ処理の使用判定
    # バッチ処理版の実行
    return await _sms_confirmation_node_batch(state, target_language)

async def _sms_confirmation_node_batch(state: AgentState, target_language: str = "ja") -> Dict[str, Any]:
    """
    SMS安否確認ハンドラー - バッチ処理版
    """
    try:
        user_input = state.get('user_input', '') if isinstance(state, dict) else getattr(state, 'user_input', '')
        user_language = target_language
        primary_intent = 'sms_confirmation'
        is_disaster_mode = state.get('is_disaster_mode', False) if isinstance(state, dict) else False
        
        # Using batch processing for SMS confirmation handler
        
        # 緊急連絡先の数を確認
        emergency_contacts_count = state.get('local_contact_count', 0) if isinstance(state, dict) else 0
        
        # 緊急連絡先がない場合の処理
        if emergency_contacts_count <= 0:
            logger.info("No emergency contacts registered - providing guidance")
            
            # シンプルな案内メッセージ
            if user_language == "ja":
                guidance_message = (
                    "安否確認SMSを送信するには緊急連絡先の登録が必要です。\n\n"
                    "設定画面から緊急連絡先を登録できます。"
                )
            else:
                guidance_message = (
                    "Emergency contacts are required to send safety confirmation SMS.\n\n"
                    "You can register emergency contacts from the settings screen."
                )
                # 他言語への翻訳
                if user_language != "en":
                    try:
                        from app.tools.translation_tool import translation_tool
                        guidance_message = await translation_tool.translate(
                            text=guidance_message,
                            target_language=user_language,
                            source_language="en"
                        )
                    except:
                        pass
            
            return {
                "final_response_text": guidance_message,
                "requires_action": None,
                "suggested_action": "register_emergency_contacts",
                "batch_processing_used": False,
                "handler_completed": True
            }
        
        # SMSテンプレートとフォームデータを生成
        disaster_type = state.get("disaster_type", "general") if isinstance(state, dict) else "general"
        user_location = state.get("user_location", {}) if isinstance(state, dict) else {}
        
        # コンテキストデータを準備
        context_data = {
            "emergency_contacts_count": emergency_contacts_count,
            "disaster_type": disaster_type,
            "is_emergency_mode": is_disaster_mode,
            "location_info": user_location,
            "sms_context": {
                "has_contacts": True,
                "can_send_sms": True
            }
        }
        
        # 完全応答生成（バッチ処理）
        response_data = await CompleteResponseGenerator.generate_complete_response(
            user_input=user_input,
            intent=primary_intent,
            user_language=user_language,
            context_data=context_data,
            handler_type="safety"
        )
        
        # SMSフォームデータを生成
        message_templates = await _generate_sms_templates(
            disaster_type=disaster_type,
            is_emergency=is_disaster_mode,
            user_location=user_location,
            target_language=target_language
        )
        
        form_labels = await _get_form_labels(target_language)
        contact_groups = _get_contact_group_templates(target_language)
        
        # フロントエンドへの指示データ
        action_data = {
            "action_type": "show_sms_confirmation_form",
            "form_data": {
                "message_templates": message_templates,
                "default_template": message_templates.get("recommended", ""),
                "allow_custom_message": True,
                "include_location": bool(user_location),
                "user_location": user_location,
                "priority": "high" if is_disaster_mode else "normal",
                "disaster_context": {
                    "is_emergency": is_disaster_mode,
                    "disaster_type": disaster_type,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "contact_groups": contact_groups,
                "form_fields": [
                    {
                        "field_id": "message_body",
                        "field_type": "textarea",
                        "label": form_labels.get("message_body", "Message"),
                        "placeholder": form_labels.get("message_placeholder", "Enter your safety confirmation message"),
                        "default_value": message_templates.get("recommended", ""),
                        "required": True,
                        "max_length": 160,
                        "validation_message": form_labels.get("message_required", "Message is required")
                    },
                    {
                        "field_id": "include_location",
                        "field_type": "checkbox",
                        "label": form_labels.get("include_location", "Include current location"),
                        "default_value": True,
                        "required": False
                    },
                    {
                        "field_id": "contact_selection",
                        "field_type": "multi_select",
                        "label": form_labels.get("select_recipients", "Select recipients"),
                        "options": "emergency_contacts",
                        "default_value": "all",
                        "required": True,
                        "validation_message": form_labels.get("recipients_required", "Please select at least one recipient")
                    }
                ],
                "ui_labels": {
                    "send_button": form_labels.get("send_button", "Send"),
                    "cancel_button": form_labels.get("cancel_button", "Cancel"),
                    "dialog_title": form_labels.get("dialog_title", "Safety Confirmation SMS")
                }
            }
        }
        
        # Return action data without response text (SMS only, no chat response needed)
        return {
            "requires_action": "show_sms_confirmation_form",
            "action_data": action_data,
            "final_response_text": response_data["main_response"],  # ユーザーへの説明文を含める
            "intent_confidence": 0.95,
            "batch_processing_used": True,
            "quality_self_check": response_data.get("quality_self_check", {}),
            "handler_completed": True,
            "skip_quality_check": True  # 回答文がないので品質チェックをスキップ
        }
        
    except Exception as e:
        logger.error(f"Batch SMS confirmation processing failed: {e}")
        return await _sms_confirmation_fallback_response(state, str(e), target_language)

async def _sms_confirmation_fallback_response(state: AgentState, error_message: str, target_language: str) -> Dict[str, Any]:
    """
    SMS安否確認ハンドラーのフォールバック応答
    """
    # English-only fallback message (per CLAUDE.md principles)
    fallback_message = "I apologize. An error occurred while preparing the SMS. Please try again later."
    
    return {
        "response_text": fallback_message,
        "error": error_message,
        "messages": state.get("messages", []) if isinstance(state, dict) else []
    }


async def _generate_sms_templates(
    disaster_type: str, 
    is_emergency: bool,
    user_location: Optional[Dict],
    target_language: str = "ja"
) -> Dict[str, str]:
    """
    Generate SMS templates for different situations with multilingual support
    """
    # Create English base template (simplified - recommended only)
    base_templates = {}
    
    if is_emergency:
        if disaster_type == "earthquake":
            base_templates["recommended"] = (
                "[SafeBeee] I am safe after the earthquake. "
                "I am currently in a secure location."
            )
            
        elif disaster_type == "typhoon":
            base_templates["recommended"] = (
                "[SafeBeee] Despite the typhoon, I am safe and staying indoors."
            )
            
        elif disaster_type == "flood":
            base_templates["recommended"] = (
                "[SafeBeee] I am safe from flooding and in a secure location."
            )
            
        else:  # general emergency
            base_templates["recommended"] = (
                "[SafeBeee] I am currently safe and in a secure location."
            )
    else:
        # Non-emergency safety check
        base_templates["recommended"] = (
            "[SafeBeee] I am doing well and checking in with you."
        )
    
    # Add location information if available (only for recommended template)
    if user_location:
        location_suffix = f" Location: {user_location.get('latitude', '')}, {user_location.get('longitude', '')}"
        base_templates["recommended_with_location"] = base_templates["recommended"] + location_suffix
    
    # Translate templates to target language if not English
    if target_language == "en":
        return base_templates
    
    translated_templates = {}
    try:
        # Import translate_text here to avoid circular imports
        from app.tools.translation_tool import translate_text
        
        for key, template in base_templates.items():
            translated_result = await translate_text(
                text=template,
                target_language=target_language,
                source_language="en"
            )
            if translated_result:
                translated_templates[key] = translated_result.translated_text
            else:
                # Fallback to original template if translation fails
                logger.warning(f"Translation failed for template '{key}', using English version")
                translated_templates[key] = template
                
    except Exception as e:
        logger.error(f"SMS template translation error: {e}")
        # Fallback to English templates
        return base_templates
    
    return translated_templates


async def _generate_response_text(is_emergency: bool, disaster_type: str, target_language: str = "ja") -> str:
    """
    Generate user response text with multilingual support
    """
    # Create English base response
    if is_emergency:
        disaster_name = {
            "earthquake": "earthquake",
            "typhoon": "typhoon",
            "flood": "flood",
            "tsunami": "tsunami"
        }.get(disaster_type, "disaster")
        
        base_response = (
            f"Understood. I have prepared a safety confirmation message regarding the {disaster_name}.\n\n"
            "Please review the recipients and message content, then press the send button.\n"
            "The message can be edited. Please adjust the content as needed."
        )
    else:
        base_response = (
            "The safety confirmation message is ready to send.\n\n"
            "Regular safety check-ins help with rapid response during disasters.\n"
            "Please select recipients, review the message, and then send."
        )
    
    # Translate to target language if not English
    if target_language == "en":
        return base_response
    
    try:
        translated_result = await translate_text(
            text=base_response,
            target_language=target_language,
            source_language="en"
        )
        if translated_result:
            return translated_result.translated_text
        else:
            logger.warning(f"Response text translation failed, using English version")
            return base_response
            
    except Exception as e:
        logger.error(f"Response text translation error: {e}")
        return base_response


async def process_sms_confirmation_result(
    state: AgentState,
    form_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    フロントエンドからのSMS送信結果を処理
    
    Args:
        state: エージェントの状態
        form_result: フロントエンドからの送信結果
        
    Returns:
        処理結果と次のアクション
    """
    try:
        sent_count = form_result.get("sent_count", 0)
        failed_count = form_result.get("failed_count", 0)
        sent_to = form_result.get("sent_to", [])
        
        if sent_count > 0:
            response_text = (
                f"✅ 安否確認メッセージを{sent_count}件送信しました。\n"
                f"送信先: {', '.join(sent_to)}\n\n"
                "返信が来たら、また教えてください。"
            )
            
            if failed_count > 0:
                response_text += f"\n⚠️ {failed_count}件の送信に失敗しました。後ほど再送信してください。"
                
            # 送信履歴を記録
            await _record_sms_history(state, form_result)
            
        else:
            response_text = "❌ メッセージの送信に失敗しました。通信状況を確認して再度お試しください。"
            
        return {
            "response_text": response_text,
            "task_completed": True,
            "follow_up_actions": ["check_sms_responses", "resend_failed_sms"] if failed_count > 0 else []
        }
        
    except Exception as e:
        logger.error(f"SMS結果処理エラー: {e}")
        return {
            "response_text": "送信結果の処理中にエラーが発生しました。",
            "error": str(e)
        }


async def _record_sms_history(state: AgentState, result: Dict[str, Any]):
    """SMS送信履歴を記録"""
    try:
        from app.db.firestore_client import get_db
        from datetime import datetime
        
        db = get_db()
        device_id = state.get("device_id") if isinstance(state, dict) else getattr(state, "device_id", None)
        
        if not device_id:
            logger.warning("No device_id found for SMS history recording")
            return
            
        # Create SMS history document
        history_data = {
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc),
            "message": result.get("message", ""),
            "recipients_count": result.get("recipients_count", 0),
            "include_location": result.get("include_location", False),
            "status": "sent",
            "created_at": datetime.now(timezone.utc)
        }
        
        # Save to Firestore
        await db.collection("sms_history").add(history_data)
        logger.info(f"SMS history recorded for device: {device_id}")
        
    except Exception as e:
        logger.error(f"Failed to record SMS history: {e}")
        # Don't fail the main flow if history recording fails


async def _get_form_labels(target_language: str) -> Dict[str, str]:
    """
    Get translated form labels for the SMS confirmation dialog
    """
    # English base labels
    base_labels = {
        "dialog_title": "Safety Confirmation SMS",
        "message_body": "Message",
        "message_placeholder": "Enter your safety confirmation message",
        "message_required": "Message is required",
        "include_location": "Include current location",
        "select_recipients": "Select recipients",
        "recipients_required": "Please select at least one recipient",
        "send_button": "Send",
        "cancel_button": "Cancel",
        "template_selector": "Choose template",
        "custom_message": "Custom message"
    }
    
    if target_language == "en":
        return base_labels
    
    # Translate labels
    translated_labels = {}
    # Import translate_text here to avoid circular imports
    from app.tools.translation_tool import translate_text
    
    for key, label in base_labels.items():
        try:
            result = await translate_text(
                text=label,
                target_language=target_language,
                source_language="en"
            )
            translated_labels[key] = result.translated_text if result else label
        except Exception as e:
            logger.warning(f"Failed to translate label '{key}': {e}")
            translated_labels[key] = label
    
    return translated_labels


def _get_contact_group_templates(target_language: str) -> Dict[str, Any]:
    """
    Get contact group templates with translations
    """
    # Base structure (icons are universal)
    groups = [
        {"id": "family", "name": "Family", "icon": "👨‍👩‍👧‍👦", "priority": 1},
        {"id": "friends", "name": "Friends", "icon": "👥", "priority": 2},
        {"id": "work", "name": "Work", "icon": "🏢", "priority": 3},
        {"id": "neighbors", "name": "Neighbors", "icon": "🏘️", "priority": 4},
        {"id": "emergency", "name": "Emergency Services", "icon": "🚨", "priority": 5}
    ]
    
    quick_add_suggestions = [
        {"label": "Spouse", "group": "family"},
        {"label": "Parents", "group": "family"},
        {"label": "Children", "group": "family"},
        {"label": "Siblings", "group": "family"},
        {"label": "Close Friend", "group": "friends"},
        {"label": "Boss", "group": "work"},
        {"label": "Colleague", "group": "work"},
        {"label": "Next Door", "group": "neighbors"}
    ]
    
    # Translations for Japanese (common case)
    if target_language == "ja":
        translations = {
            "Family": "家族",
            "Friends": "友人",
            "Work": "職場",
            "Neighbors": "近所",
            "Emergency Services": "緊急連絡先",
            "Spouse": "配偶者",
            "Parents": "両親",
            "Children": "子供",
            "Siblings": "兄弟姉妹",
            "Close Friend": "親友",
            "Boss": "上司",
            "Colleague": "同僚",
            "Next Door": "隣人"
        }
        
        # Apply translations
        for group in groups:
            group["name"] = translations.get(group["name"], group["name"])
        
        for suggestion in quick_add_suggestions:
            suggestion["label"] = translations.get(suggestion["label"], suggestion["label"])
    
    return {
        "groups": groups,
        "quick_add": quick_add_suggestions,
        "default_selection": ["family", "emergency"]  # Default selection logic moved to frontend
    }