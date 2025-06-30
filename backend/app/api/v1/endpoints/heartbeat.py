# backend/app/api/v1/endpoints/heartbeat.py
"""
統合ハートビートAPI
デバイス状態更新、災害情報取得を処理
プロアクティブ提案はSSEエンドポイントに移行
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List, Dict, Any
from google.cloud.firestore_v1 import FieldFilter
from google.cloud import firestore
import logging
from datetime import datetime, timedelta, timezone
import uuid
import os

from app.schemas.heartbeat import (
    HeartbeatRequest,
    HeartbeatResponse,
    DisasterStatus,
    DisasterAlert,
    NearestShelter,
    ProactiveSuggestion,
    SyncConfig,
    DeviceMode,
    HeartbeatError,
    UserActionRequest
)
from app.schemas.device import DeviceStatusUpdate, DeviceLocation
from app.schemas.common.location import Location
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from app.utils.location_converter import (
    extract_location_from_request,
    location_info_to_device_location,
    location_info_to_location_model
)
from app.services.device_service import update_device_status, get_device_by_id
from app.tools.disaster_info_tools import disaster_info_tool
from app.agents.safety_beacon_agent.proactive_suggester import invoke_proactive_agent

logger = logging.getLogger(__name__)
router = APIRouter()

# ハートビート統合アーキテクチャ - SSE組み込み版
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import Dict, List

# デバイス別SSE接続管理
heartbeat_sse_connections: Dict[str, List] = {}


# ハートビート同期間隔はフロントエンドで管理するため削除

async def _get_available_suggestion_types_at_heartbeat(request: HeartbeatRequest) -> tuple[List[str], bool]:
    """
    ハートビート受信時点でクールダウン解除済みの提案タイプを特定
    
    Returns:
        tuple: (available_types, has_pending_types)
        - available_types: 現在送信可能な提案タイプ
        - has_pending_types: 将来送信可能になる提案タイプがあるか
    """
    try:
        from app.db.firestore_client import get_db
        db = get_db()
        doc_ref = db.collection("device_suggestion_history").document(request.device_id)
        
        # 最近の履歴確認
        recent_suggestions = doc_ref.collection("suggestions").order_by("sync_timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
        
        current_time = datetime.now(timezone.utc)
        
        # 現在のモードを判定
        is_emergency_mode = request.client_context.current_mode.value == "emergency"
        mode = "emergency" if is_emergency_mode else "normal"
        
        # 統一設定から提案タイプ別のクールダウン設定を取得（モード別）
        from app.config import app_settings
        
        cooldown_settings = {
            # 平常時重視の提案
            "welcome_message": app_settings.get_cooldown_hours("welcome_message", mode),
            "seasonal_warning": app_settings.get_cooldown_hours("seasonal", mode),
            "disaster_preparedness": app_settings.get_cooldown_hours("disaster_preparedness", mode),
            
            # 基本提案
            "emergency_contact_setup": app_settings.get_cooldown_hours("emergency_contact", mode),
            "low_battery_warning": app_settings.get_cooldown_hours("low_battery", mode),
            "location_permission_reminder": app_settings.get_cooldown_hours("location", mode),
            "notification_permission_reminder": app_settings.get_cooldown_hours("notification", mode),
            "quiz_reminder": app_settings.get_cooldown_hours("quiz_reminder", mode),  # quiz_reminder追加
            
            # 緊急時提案
            "disaster_news": app_settings.get_cooldown_hours("disaster_news", mode),
            "shelter_status_update": app_settings.get_cooldown_hours("shelter", mode),
            "hazard_map_url": app_settings.get_cooldown_hours("hazard_map", mode),
            "safety_confirmation_sms_proposal": app_settings.get_cooldown_hours("sms_proposal", mode),  # 安否確認SMS提案
        }
        
        # 各提案タイプのクールダウン状況をチェック
        excluded_types = []
        pending_types = []  # 将来利用可能になるタイプ
        
        for doc in recent_suggestions:
            doc_data = doc.to_dict()
            if 'suggestions' in doc_data:
                for suggestion in doc_data['suggestions']:
                    suggestion_type = suggestion.get('type')
                    sent_at = suggestion.get('sent_at')
                    
                    if suggestion_type and sent_at and suggestion_type in cooldown_settings:
                        # Check if this suggestion had its cooldown reset
                        cooldown_was_reset = suggestion.get('cooldown_reset', False)
                        
                        # Skip cooldown check if it was reset due to emergency mode transition
                        if cooldown_was_reset and suggestion.get('reset_reason') == 'emergency_mode_transition':
                            # Skipping cooldown check - was reset due to emergency mode transition
                            continue
                        
                        # sent_atがdatetimeオブジェクトでない場合の処理
                        if hasattr(sent_at, 'replace'):
                            if sent_at.tzinfo is None:
                                sent_at = sent_at.replace(tzinfo=timezone.utc)
                        
                        # クールダウン時間を確認
                        cooldown_hours = cooldown_settings[suggestion_type]
                        time_since_sent = (current_time - sent_at).total_seconds() / 3600
                        
                        if time_since_sent < cooldown_hours:
                            if suggestion_type not in excluded_types:
                                excluded_types.append(suggestion_type)
                                remaining_hours = cooldown_hours - time_since_sent
                                # 6時間以内に解除される提案は「保留中」として記録
                                if remaining_hours <= 6.0:
                                    pending_types.append(suggestion_type)
        
        # 現在利用可能な提案タイプを算出
        available_types = [t for t in cooldown_settings.keys() if t not in excluded_types]
        has_pending_types = len(pending_types) > 0
        
        return available_types, has_pending_types
        
    except Exception as e:
        logger.error(f"提案タイプ分析エラー: {e}")
        return [], False


async def _check_and_handle_mode_transition(device_id: str, new_mode: str) -> bool:
    """
    Check if there's a mode transition and handle cooldown reset if transitioning to emergency mode
    
    Args:
        device_id: Device ID
        new_mode: New mode (emergency/normal)
        
    Returns:
        bool: True if transitioned to emergency mode and cooldowns were reset
    """
    try:
        from app.db.firestore_client import get_db
        db = get_db()
        
        # Get device's previous mode state
        device_ref = db.collection("device_states").document(device_id)
        device_state = device_ref.get()
        
        previous_mode = "normal"  # Default if no previous state
        if device_state.exists:
            state_data = device_state.to_dict()
            previous_mode = state_data.get("current_mode", "normal")
        
        # Update current mode
        device_ref.set({
            "current_mode": new_mode,
            "last_updated": datetime.now(timezone.utc)
        }, merge=True)
        
        # Check if transitioning from normal to emergency
        if previous_mode == "normal" and new_mode == "emergency":
            logger.warning(f"Mode transition detected for device {device_id}: normal → emergency")
            
            # Reset cooldowns for critical emergency suggestions
            await _reset_emergency_suggestion_cooldowns(device_id)
            
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking mode transition for device {device_id}: {e}")
        return False


async def _reset_emergency_suggestion_cooldowns(device_id: str):
    """
    Reset cooldowns for critical emergency suggestions when transitioning to emergency mode
    
    This allows immediate delivery of critical safety information regardless of previous cooldowns
    """
    try:
        from app.db.firestore_client import get_db
        db = get_db()
        
        # Critical emergency-only suggestion types to reset
        emergency_types_to_reset = [
            "disaster_news",
            "shelter_status_update", 
            "emergency_contact_setup",  # Critical if user has no emergency contacts
            "safety_confirmation_sms_proposal"  # Safety confirmation SMS for emergency situations
        ]
        
        # Get suggestion history
        history_ref = db.collection("device_suggestion_history").document(device_id)
        suggestions_ref = history_ref.collection("suggestions")
        
        # Query recent suggestions
        recent_suggestions = suggestions_ref.order_by("sync_timestamp", direction=firestore.Query.DESCENDING).limit(50).get()
        
        # Track which suggestions were reset
        reset_count = 0
        
        for doc in recent_suggestions:
            doc_data = doc.to_dict()
            if 'suggestions' in doc_data:
                modified = False
                for suggestion in doc_data['suggestions']:
                    if suggestion.get('type') in emergency_types_to_reset:
                        # Reset the sent_at timestamp to allow immediate resend
                        # We set it to 48 hours ago to ensure it passes all cooldown checks
                        suggestion['sent_at'] = datetime.now(timezone.utc) - timedelta(hours=48)
                        suggestion['cooldown_reset'] = True
                        suggestion['reset_reason'] = 'emergency_mode_transition'
                        suggestion['reset_at'] = datetime.now(timezone.utc)
                        modified = True
                        reset_count += 1
                
                if modified:
                    # Update the document
                    doc.reference.update({
                        'suggestions': doc_data['suggestions'],
                        'last_modified': datetime.now(timezone.utc)
                    })
        
        # Reset emergency suggestion cooldowns for device
        
        # Also log this event for tracking
        history_ref.collection("events").add({
            "event_type": "cooldown_reset",
            "reason": "emergency_mode_transition",
            "reset_types": emergency_types_to_reset,
            "reset_count": reset_count,
            "timestamp": datetime.now(timezone.utc)
        })
        
    except Exception as e:
        logger.error(f"Error resetting emergency suggestion cooldowns for device {device_id}: {e}")


async def _generate_single_suggestion_type(request: HeartbeatRequest, suggestion_type: str) -> List[ProactiveSuggestion]:
    """
    単一タイプの提案のみを効率的に生成
    
    Args:
        suggestion_type: 生成対象の提案タイプ（1つのみ）
    """
    try:
        # 提案タイプ別の専用生成関数
        from app.agents.safety_beacon_agent.suggestion_generators.unified_generator import generate_single_suggestion_by_type
        from app.schemas.agent.suggestions import ProactiveSuggestionContext, LocationModel, UserAppUsageSummary
        
        # 簡易コンテキスト構築
        location_info = extract_location_from_request(request)
        location_model = location_info_to_location_model(location_info) if location_info else None
        
        # 新規ユーザー判定
        is_new_user = False
        try:
            device_data = await get_device_by_id(request.device_id)
            if device_data:
                created_at = getattr(device_data, 'created_at', None)
                if created_at:
                    # datetime比較の修正: タイムゾーン対応
                    now = datetime.now(timezone.utc)
                    if hasattr(created_at, 'tzinfo') and created_at.tzinfo is None:
                        # created_atがnaiveの場合、UTCとして扱う
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    time_since_creation = (now - created_at).total_seconds()
                    is_new_user = time_since_creation < 86400
            else:
                is_new_user = True
        except Exception as e:
            logger.warning(f"Failed to check device data: {e}")
            is_new_user = True
        
        
        user_usage_summary = UserAppUsageSummary(
            is_new_user=is_new_user,
            last_app_open_days_ago=0 if is_new_user else 1,
            local_contact_count=request.client_context.emergency_contacts_count
        )
        
        # 緊急モード状態を正しく設定（DeviceModeのEnumを考慮）
        is_emergency_mode = request.client_context.current_mode.value == "emergency"
        current_situation = "alert_active" if is_emergency_mode else "normal"
        
        # デバッグ用：モード情報をログ出力
        # Emergency mode check for suggestion context
        
        # 災害アラート情報を取得してコンテキストに追加
        active_disaster_alerts = []
        if is_emergency_mode and suggestion_type == "disaster_news":
            # 緊急モードで災害ニュース生成時のみ災害情報を取得
            try:
                location = extract_location_from_request(request)
                if location:
                    # 高速災害情報取得（キャッシュから）
                    cached_info = await disaster_info_tool.get_fast_disaster_info(
                        location=location,
                        radius_km=50.0,  # 広範囲の災害情報を取得
                        device_id=request.device_id
                    )
                    
                    if cached_info and cached_info.disaster_alerts:
                        for alert_data in cached_info.disaster_alerts:
                            alert_type = None
                            if isinstance(alert_data, dict):
                                alert_type = alert_data.get('alert_type', 'unknown')
                            else:
                                alert_type = getattr(alert_data, 'alert_type', 'unknown')
                            
                            if alert_type and alert_type != 'unknown':
                                active_disaster_alerts.append({"type": alert_type})
            except Exception as e:
                logger.warning(f"Failed to get disaster alerts for suggestion context: {e}")
        
        suggestion_context = ProactiveSuggestionContext(
            device_id=request.device_id,
            language_code=request.client_context.language_code,
            current_situation=current_situation,
            is_emergency_mode=is_emergency_mode,
            current_location=location_model,
            device_status={
                "battery_level": request.device_status.battery_level if request.device_status else 80,
                "is_charging": request.device_status.is_charging if request.device_status else False,
                "network_type": request.device_status.network_type if request.device_status else "wifi",
                "signal_strength": request.device_status.signal_strength if request.device_status else 4,
                "active_disaster_alerts": active_disaster_alerts  # 災害アラート情報を追加
            },
            suggestion_history_summary=[],
            last_suggestion_timestamp=None,
            user_app_usage_summary=user_usage_summary,
            permissions=request.client_context.permissions
        )
        
        # 単一タイプ専用生成
        suggestion_data = await generate_single_suggestion_by_type(suggestion_type, suggestion_context, request.client_context.language_code)
        
        if suggestion_data:
            content = suggestion_data.get("content", "")
            action_query = suggestion_data.get("action_query", "")
            action_display_text = suggestion_data.get("action_display_text", "")
            action_data = suggestion_data.get("action_data", {})
            
            # 翻訳が必要かチェック（バッチ処理で最適化）
            # Translation check for single suggestion
            if action_data.get("requires_translation", False) and request.client_context.language_code != "en":
                try:
                    from app.tools.translation_tool import translation_tool
                    
                    # Starting translation from EN to target language
                    # Original content for translation
                    
                    # バッチ翻訳で3つのフィールドを同時処理（LLM呼び出し削減）
                    content, action_query, action_display_text = await translation_tool.translate_suggestion_fields(
                        content=content,
                        action_query=action_query or "",
                        action_display_text=action_display_text or "",
                        target_language=request.client_context.language_code
                    )
                    
                    # Translation completed
                    # Action display text translated
                    
                    
                except Exception as e:
                    logger.error(f"Batch translation failed for single suggestion {suggestion_type}: {e}")
                    # 翻訳に失敗しても元の値を使用
            
            proactive_suggestion = ProactiveSuggestion(
                type=suggestion_type,
                content=content,
                priority="normal",
                action_query=action_query,
                action_display_text=action_display_text,
                action_data=action_data,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            return [proactive_suggestion]
        
        return []
        
    except Exception as e:
        logger.error(f"単一タイプ生成エラー ({suggestion_type}): {e}")
        return []


async def _check_and_generate_suggestions_from_queue(request: HeartbeatRequest, target_types: List[str]) -> List[ProactiveSuggestion]:
    """
    提案生成の統合エントリーポイント
    
    Args:
        target_types: 生成対象の提案タイプリスト（空の場合は全タイプ生成）
    """
    try:
        if not target_types or len(target_types) == 0:
            # 全タイプ生成（従来のフル生成）
            return await _generate_all_suggestions_bulk(request)
        elif len(target_types) == 1:
            # 単一タイプ生成（効率的）
            return await _generate_single_suggestion_type(request, target_types[0])
        else:
            # 複数タイプ指定（バッチ処理）
            return await _generate_multiple_suggestions_batch(request, target_types)
        
    except Exception as e:
        logger.error(f"提案生成エラー: {e}")
        return []


async def _generate_all_suggestions_bulk(request: HeartbeatRequest) -> List[ProactiveSuggestion]:
    """全タイプの提案を一括生成（バッチ生成器使用で最適化）"""
    from app.schemas.agent.suggestions import ProactiveSuggestionContext, LocationModel, UserAppUsageSummary
    from app.agents.safety_beacon_agent.suggestion_generators.batch_generator import BatchSuggestionGenerator
    from app.tools.translation_tool import translation_tool
    from datetime import datetime, timedelta
    
    # バッチ生成器を初期化
    batch_generator = BatchSuggestionGenerator()
    
    # コンテキスト構築
    is_emergency_mode = request.client_context.current_mode.value == "emergency"
    current_situation = "alert_active" if is_emergency_mode else "normal"
    
    # デバッグ用：モード情報をログ出力（バッチ生成器用）
    # Batch generation emergency mode check
    
    # ユーザー使用状況を取得
    user_usage_summary = UserAppUsageSummary(is_new_user=True)
    try:
        if request.client_context.user_app_usage_summary:
            user_usage_summary = UserAppUsageSummary(
                unread_guide_topics=request.client_context.user_app_usage_summary.get("unread_guide_topics"),
                incomplete_settings=request.client_context.user_app_usage_summary.get("incomplete_settings"),
                last_app_open_days_ago=request.client_context.user_app_usage_summary.get("last_app_open_days_ago", 0),
                is_new_user=request.client_context.user_app_usage_summary.get("is_new_user", True),
                local_contact_count=request.client_context.user_app_usage_summary.get("local_contact_count", 0)
            )
    except Exception as e:
        logger.warning(f"Failed to parse user app usage summary: {e}")
    
    # 位置情報
    location_model = None
    if request.client_context.location:
        location_model = LocationModel(
            latitude=request.client_context.location.latitude,
            longitude=request.client_context.location.longitude,
            accuracy=getattr(request.client_context.location, 'accuracy', None),
            timestamp=getattr(request.client_context.location, 'timestamp', None)
        )
    
    # 提案コンテキストを構築
    suggestion_context = ProactiveSuggestionContext(
        device_id=request.device_id,
        language_code=request.client_context.language_code,
        current_situation=current_situation,
        is_emergency_mode=is_emergency_mode,
        current_location=location_model,
        device_status={
            "battery_level": request.device_status.battery_level if request.device_status else 80,
            "is_charging": request.device_status.is_charging if request.device_status else False,
            "network_type": request.device_status.network_type if request.device_status else "wifi",
            "signal_strength": request.device_status.signal_strength if request.device_status else 4
        },
        suggestion_history_summary=[],
        last_suggestion_timestamp=None,
        user_app_usage_summary=user_usage_summary,
        permissions=request.client_context.permissions
    )
    
    # 生成する提案タイプを決定（フィルタリング）
    all_types = [
        "welcome_message",
        "seasonal_warning", 
        "disaster_preparedness",
        "emergency_contact_setup",
        "low_battery_warning",
        "location_permission_reminder",
        "notification_permission_reminder",
        "quiz_reminder",
        "disaster_news",
        "shelter_status_update",
        "hazard_map_url"
    ]
    
    # SMS提案は削除済み
    
    # カスタムフィルタリングを適用（統一された関数を使用）
    types_to_generate = _apply_custom_filtering(all_types, request)
    
    if not types_to_generate:
        logger.info("No suggestions to generate after filtering")
        return []
    
    try:
        # バッチ生成（1回のLLM呼び出しで全て生成）
        # Generating suggestions in batch
        batch_results = await batch_generator.generate_batch_suggestions(
            suggestion_types=types_to_generate,
            context=suggestion_context,
            language_code="en"  # 内部処理は英語で統一
        )
        
        # 結果を収集
        suggestions_to_translate = []
        for suggestion_type, suggestion_item in batch_results.items():
            if suggestion_item:
                suggestions_to_translate.append({
                    "type": suggestion_type,
                    "content": suggestion_item.content,
                    "action_query": suggestion_item.action_query,
                    "action_display_text": suggestion_item.action_display_text,
                    "action_data": suggestion_item.action_data
                })
        
        if not suggestions_to_translate:
            return []
        
        # 一括翻訳（言語が英語でない場合）
        if request.client_context.language_code != "en":
            # Batch translating suggestions to target language
            
            # 翻訳対象のテキストを集める
            texts_to_translate = []
            for s in suggestions_to_translate:
                texts_to_translate.extend([s["content"], s["action_query"], s["action_display_text"]])
            
            # 一括翻訳実行
            translated_texts = await translation_tool.translate_multiple(
                texts=texts_to_translate,
                target_language=request.client_context.language_code,
                source_language="en"
            )
            
            # 翻訳結果を適用
            text_index = 0
            for s in suggestions_to_translate:
                s["content"] = translated_texts[text_index]
                s["action_query"] = translated_texts[text_index + 1]
                s["action_display_text"] = translated_texts[text_index + 2]
                # action_data内のaction_queryも更新（存在する場合）
                if s.get("action_data") and "action_query" in s["action_data"]:
                    s["action_data"]["action_query"] = translated_texts[text_index + 1]
                text_index += 3
        
        # ProactiveSuggestionオブジェクトに変換
        proactive_suggestions = []
        for s in suggestions_to_translate:
            proactive_suggestions.append(ProactiveSuggestion(
                type=s["type"],
                content=s["content"],
                priority="normal",
                action_query=s["action_query"],
                action_display_text=s["action_display_text"],
                action_data=s["action_data"],
                expires_at=datetime.utcnow() + timedelta(hours=1)
            ))
        
        # Successfully generated suggestions using batch processing
        return proactive_suggestions
        
    except Exception as e:
        logger.error(f"Batch suggestion generation failed: {e}")
        return []


def _apply_custom_filtering(available_types: List[str], request: HeartbeatRequest) -> List[str]:
    """カスタムフィルタリングロジック - 許可リスト方式"""
    is_emergency_mode = request.client_context.current_mode.value == "emergency"
    emergency_contacts_count = request.client_context.emergency_contacts_count
    battery_level = request.device_status.battery_level if request.device_status else 100
    has_emergency_contacts = emergency_contacts_count > 0
    
    # 許可リストを定義（proactive_suggester.pyと同じロジック）
    if is_emergency_mode:
        # 緊急時の許可リスト
        if has_emergency_contacts:
            allowed_types = [
                "disaster_news",
                "shelter_status_update", 
                "safety_confirmation_sms_proposal"
            ]
        else:
            allowed_types = [
                "emergency_contact_setup",
                "disaster_news",
                "shelter_status_update"
            ]
    else:
        # 平常時の許可リスト
        if has_emergency_contacts:
            allowed_types = [
                "seasonal_warning",
                "welcome_message",
                "disaster_preparedness",
                "shelter_status_update",
                "hazard_map_url"
            ]
        else:
            allowed_types = [
                "welcome_message",
                "seasonal_warning",
                "disaster_preparedness",
                "emergency_contact_setup",
                "shelter_status_update",
                "hazard_map_url"
            ]
    
    # 条件付き提案を追加
    # バッテリー警告（45%以下）
    if battery_level <= 45:
        allowed_types.append("low_battery_warning")
        # Including low_battery_warning due to low battery
    
    # 権限リマインダー
    if request.client_context.permissions:
        location_granted = request.client_context.permissions.get("location_permission_granted", False)
        if not location_granted:
            allowed_types.append("location_permission_reminder")
            # Including location_permission_reminder: permission not granted
        
        notification_granted = request.client_context.permissions.get("notification_permission_granted", False)
        if not notification_granted:
            allowed_types.append("notification_permission_reminder")
            # Including notification_permission_reminder: permission not granted
    
    # 許可リストと利用可能タイプの交差を取る
    filtered_types = [t for t in available_types if t in allowed_types]
    
    if filtered_types:
        # Heartbeat suggestions after filtering
        pass
    
    return filtered_types


async def _generate_multiple_suggestions_batch(request: HeartbeatRequest, target_types: List[str]) -> List[ProactiveSuggestion]:
    """複数タイプの提案をバッチ生成"""
    all_suggestions = []
    
    # 各タイプを並列生成
    import asyncio
    tasks = [_generate_single_suggestion_type(request, stype) for stype in target_types]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, list):
            all_suggestions.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"バッチ生成エラー: {result}")
    
    return all_suggestions




async def convert_to_proactive_suggestions(suggestions: List, target_language: str = "ja") -> List[ProactiveSuggestion]:
    """プロアクティブ提案の形式を変換（SuggestionItemと辞書の両方に対応）"""
    converted = []
    for suggestion in suggestions[:5]:  # 最大5件まで
        try:
            # SuggestionItemオブジェクトか辞書かを判定
            if hasattr(suggestion, 'type'):
                # SuggestionItemオブジェクトの場合
                suggestion_type = suggestion.type
                content = suggestion.content
                action_query = getattr(suggestion, 'action_query', None)
                action_data = getattr(suggestion, 'action_data', None)
            elif isinstance(suggestion, dict):
                # 辞書の場合
                suggestion_type = suggestion.get('type', 'general')
                content = suggestion.get('content', '')
                action_query = suggestion.get('action_query', None)
                action_data = suggestion.get('action_data', None)
            else:
                logger.warning(f"Unknown suggestion format: {type(suggestion)}")
                continue
            
            # 翻訳が必要かチェック
            requires_translation = False
            if action_data and action_data.get("requires_translation", False):
                requires_translation = True
            
            # 翻訳処理（内部処理は英語、最終出力はアプリ指定言語）
            # Bulk translation check
            if requires_translation and target_language != "en":
                try:
                    from app.tools.translation_tool import translation_tool
                    
                    # Starting bulk translation
                    # Original content for translation
                    
                    # action_display_textを取得
                    action_display_text = ""
                    if hasattr(suggestion, 'action_display_text') and suggestion.action_display_text:
                        action_display_text = suggestion.action_display_text
                    
                    # バッチ翻訳で3つのフィールドを同時処理（LLM呼び出し大幅削減）
                    content, action_query, translated_action_display_text = await translation_tool.translate_suggestion_fields(
                        content=content,
                        action_query=action_query or "",
                        action_display_text=action_display_text,
                        target_language=target_language
                    )
                    
                    # Bulk translation completed
                    
                    # action_display_textが翻訳された場合はaction_dataに格納
                    if translated_action_display_text and action_display_text:
                        if action_data is None:
                            action_data = {}
                        action_data["action_display_text"] = translated_action_display_text
                    
                except Exception as e:
                    logger.error(f"Batch translation failed for suggestion {suggestion_type}: {e}")
                    # 翻訳に失敗しても元のcontentを使用
            
            # 優先度の判定
            priority = "normal"
            if suggestion_type in ["emergency_action", "evacuation_info"]:
                priority = "critical"
            elif suggestion_type in ["hazard_map_url", "disaster_news", "alert_info"]:
                priority = "high"
            
            converted.append(ProactiveSuggestion(
                type=suggestion_type,
                content=content,
                priority=priority,
                action_query=action_query,
                action_data=action_data,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            ))
        except Exception as e:
            logger.error(f"Failed to convert suggestion: {e}")
            continue
    
    return converted


@router.post("/sync/heartbeat-sse")
async def device_heartbeat_with_sse(request: HeartbeatRequest, http_request: Request):
    """
    ハートビート + SSE統合エンドポイント
    
    注意: このエンドポイントは通常のハートビート(/sync/heartbeat)の後に呼ばれるため、
    デバイス状態更新は行わず、提案のSSE配信のみを行います。
    
    1. 提案のクールダウンチェック
    2. SSEで条件に合った提案をプッシュ配信
    3. 接続維持：ハートビート間隔でのキープアライブ
    """
    device_id = request.device_id
    
    async def heartbeat_sse_stream():
        try:
            # 初回ハートビート処理は行わない（すでに/sync/heartbeatで処理済み）
            
            # SSE接続確立の通知
            connection_data = {
                'type': 'connection_established',
                'message': 'SSE接続が確立されました',
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(connection_data, ensure_ascii=False)}\n\n"
            
            # 2. ハートビート受信時点で送信対象の提案タイプを特定
            available_types, has_pending = await _get_available_suggestion_types_at_heartbeat(request)
            
            
            if not available_types:
                # 送信対象なし = 即座にSSE終了
                complete_data = {
                    'type': 'stream_complete',
                    'reason': 'no_suggestions_available',
                    'message': '現在送信可能な提案がありません',
                    'has_pending_suggestions': has_pending,
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                return  # SSE終了
            
            # 3. 送信対象提案があればSSE接続を管理リストに追加
            queue = asyncio.Queue()
            if device_id not in heartbeat_sse_connections:
                heartbeat_sse_connections[device_id] = []
            heartbeat_sse_connections[device_id].append(queue)
            
            
            # 緊急モード判定（フロントエンドから送信された値を使用、DeviceModeのEnumを考慮）
            is_emergency_mode = request.client_context.current_mode.value == "emergency"
            
            # 4. 提案タイプを優先順位で並べ替え（緊急災害時優先）
            if is_emergency_mode:
                # 緊急災害時の優先順位（緊急性の高い提案のみ）
                priority_order = [
                    "disaster_news",                     # 災害情報
                    "shelter_status_update",             # 避難所情報
                    "hazard_map_url",                    # ハザードマップ
                    "emergency_contact_setup",           # 緊急連絡先設定
                    "notification_permission_reminder",  # 通知権限（緊急時重要）
                    "location_permission_reminder",      # 位置情報権限
                    "low_battery_warning"                # バッテリー警告
                ]
            else:
                # 平常時の優先順位
                priority_order = [
                    "welcome_message",  # ウェルカムメッセージ（新規ユーザー向け）
                    "seasonal_warning",  # 季節性災害警告
                    "disaster_news",  # 最新の災害情報を優先
                    "emergency_contact_setup",
                    "disaster_preparedness",  # 防災準備情報
                    "shelter_status_update", 
                    "hazard_map_url",
                    "low_battery_warning",
                    "location_permission_reminder", 
                    "notification_permission_reminder",
                ]
            
            # 優先順位に従って並べ替え
            sorted_types = []
            for ptype in priority_order:
                if ptype in available_types:
                    sorted_types.append(ptype)
            
            # 優先リストにないタイプも追加
            for atype in available_types:
                if atype not in sorted_types:
                    sorted_types.append(atype)
            
            # 処理対象タイプの詳細リストは削除
            
            # 5. 真の並列提案生成：条件付き生成とSSEストリーミング
            sent_types = []
            processing_start = datetime.utcnow()
            
            # 統一されたフィルタリング関数を使用
            filtered_types = _apply_custom_filtering(sorted_types, request)
                
            
            # 各提案タイプの生成タスクを作成
            async def generate_single_type(suggestion_type: str):
                """単一タイプを生成して返す"""
                try:
                    suggestions = await _check_and_generate_suggestions_from_queue(request, [suggestion_type])
                    if suggestions:
                        return (suggestion_type, suggestions)
                    else:
                        return None
                except Exception as e:
                    logger.error(f"{suggestion_type} generation error: {e}")
                    return None
            
            # 全タスクを作成（まだ実行しない）
            tasks = {
                asyncio.create_task(generate_single_type(stype)): stype 
                for stype in filtered_types
            }
            
            # as_completedで完了順に処理
            try:
                completed_count = 0
                
                # 完了したタスクから順に処理
                for completed_task in asyncio.as_completed(tasks.keys()):
                    try:
                        result = await completed_task
                        
                        if result is not None:
                            suggestion_type, suggestions = result
                            completed_count += 1
                            
                            # 即座にSSE送信
                            push_data = {
                                'type': 'suggestions_push',
                                'data': [s.model_dump() for s in suggestions],
                                'timestamp': datetime.utcnow().isoformat(),
                                'trigger': f'parallel_{suggestion_type}',
                                'sent_type': suggestion_type,
                                'progress': f'{completed_count}/{len(filtered_types)}'
                            }
                            
                            yield f"data: {json.dumps(push_data, ensure_ascii=False, default=str)}\n\n"
                            
                            sent_types.append(suggestion_type)
                            
                            # 送信後の履歴記録（非同期で実行）
                            async def record_history(stype):
                                try:
                                    from app.db.firestore_client import get_db
                                    db = get_db()
                                    doc_ref = db.collection("device_suggestion_history").document(request.device_id)
                                    doc_ref.collection("suggestions").add({
                                        "sync_timestamp": datetime.now(timezone.utc),
                                        "suggestions": [{
                                            "type": stype,
                                            "sent_at": datetime.now(timezone.utc),
                                            "source": "heartbeat_sse_parallel"
                                        }],
                                        "source": "heartbeat_sse_parallel"
                                    })
                                except Exception as e:
                                    pass
                            
                            asyncio.create_task(record_history(suggestion_type))
                        
                    except Exception as e:
                        logger.error(f"タスク処理エラー: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Parallel generation error: {e}")
            
            
            # 6. すべての送信対象を処理完了 = SSE終了
            complete_data = {
                'type': 'stream_complete',
                'reason': 'all_suggestions_sent',
                'message': f'個別生成・送信完了 ({len(sent_types)}タイプ)',
                'sent_types': sent_types,
                'has_pending_suggestions': has_pending,
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                        
        except Exception as e:
            logger.error(f"ハートビートSSEエラー: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 接続終了時のクリーンアップ
            try:
                heartbeat_sse_connections[device_id].remove(queue)
                if not heartbeat_sse_connections[device_id]:
                    del heartbeat_sse_connections[device_id]
            except (ValueError, KeyError):
                pass
    
    return StreamingResponse(
        heartbeat_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/sync/heartbeat", response_model=HeartbeatResponse)
async def device_heartbeat(request: HeartbeatRequest, http_request: Request):
    """
    従来のハートビートエンドポイント（互換性維持）
    
    1. デバイス状態を更新
    2. 災害情報を取得
    3. モードを判定
    4. プロアクティブ提案を生成
    5. 次回同期設定を決定
    """
    return await _process_initial_heartbeat(request, http_request)


async def _process_initial_heartbeat(request: HeartbeatRequest, http_request: Request) -> HeartbeatResponse:
    """
    初回ハートビート処理（SSE版と従来版で共通）
    """
    start_time = datetime.utcnow()
    sync_id = f"sync_{start_time.strftime('%Y%m%d_%H%M%S')}_{request.device_id[-4:]}"
    
    
    try:
        # 緊急連絡先数のログ追加
        emergency_contacts_count = request.client_context.emergency_contacts_count
        
        # 位置情報のログ強化
        if request.device_status and request.device_status.location:
            location_data = request.device_status.location
            lat = location_data.get('latitude')
            lon = location_data.get('longitude')
            accuracy = location_data.get('accuracy')
            # 位置情報の妥当性チェック
            if lat is None or lon is None:
                logger.warning(f"Invalid location data: latitude or longitude is None")
            elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.warning(f"Invalid location coordinates: lat={lat}, lon={lon} (out of valid range)")
            elif accuracy and accuracy > 1000:
                logger.warning(f"Low accuracy location: {accuracy}m (threshold: 1000m)")
        
        # 1. デバイス状態を更新
        if request.device_status:
            # 統一的な位置情報変換
            location_info = extract_location_from_request(request)
            device_location = None
            geo_info = {}
            
            if location_info:
                # GPS座標から逆ジオコーディング
                from app.services.geocoding_service import reverse_geocode
                geo_info = await reverse_geocode(location_info.latitude, location_info.longitude)
                device_location = location_info_to_device_location(location_info, geo_info)
                
                if not geo_info.get("prefecture"):
                    logger.warning(f"Geocoding failed for {request.device_id}, coordinates: {location_info.latitude}, {location_info.longitude}")
            
            status_update = DeviceStatusUpdate(
                battery_level=request.device_status.battery_level,
                is_charging=request.device_status.is_charging,
                network_type=request.device_status.network_type,
                signal_strength=request.device_status.signal_strength,
                location=device_location
            )
            
            await update_device_status(request.device_id, status_update)
        
        # 2. 災害情報を取得
        active_alerts = []
        nearest_shelter = None
        mode = DeviceMode.NORMAL
        mode_reason = "平常時"
        location = None  # location変数を初期化
        
        # デバッグ用: 緊急モード強制解除チェック
        try:
            from app.db.firestore_client import get_db
            db = get_db()
            emergency_override_ref = db.collection("device_emergency_overrides").document(request.device_id)
            emergency_override = emergency_override_ref.get()
            
            if emergency_override.exists:
                override_data = emergency_override.to_dict()
                if (override_data.get("force_normal_mode") and 
                    override_data.get("override_until") and 
                    override_data["override_until"] > datetime.now(timezone.utc)):
                    
                    mode = DeviceMode.NORMAL
                    mode_reason = "デバッグ用強制解除中"
                    # active_alertsは空のままにして強制的にnormalモードにする
                    
                    # 統合災害情報は取得せずにスキップ
                    # 強制解除モードでは災害情報を取得しない
                    nearest_shelter = None
                    # 通常の災害情報取得をスキップして、モード判定に進む
                    skip_disaster_check = True
                else:
                    # 期限切れのオーバーライドを削除
                    emergency_override_ref.delete()
                    skip_disaster_check = False
            else:
                skip_disaster_check = False
        except Exception as e:
            logger.warning(f"Failed to check emergency override for device {request.device_id}: {e}")
            skip_disaster_check = False
        
        if not locals().get('skip_disaster_check', False):
            location = extract_location_from_request(request)
            
        if location:
            
            # 高速災害情報取得（キャッシュファースト + バックグラウンド更新）
            disaster_start_time = datetime.utcnow()
            
            try:
                # テストモードでは直接取得、本番ではキャッシュから高速取得
                from app.config import app_settings
                cached_info = None  # Initialize cached_info
                
                if app_settings.is_test_mode():
                    # テストモードでも統合災害情報を使用してdevice_idを考慮
                    from app.tools.disaster_info_tools import UnifiedDisasterInfoTool
                    disaster_tool = UnifiedDisasterInfoTool()
                    
                    # get_unified_disaster_infoを使用してdevice_idを渡す
                    unified_info = await disaster_tool.get_unified_disaster_info(
                        location=location,
                        radius_km=10.0,
                        device_id=request.device_id
                    )
                    
                    # 統合情報からアラートを取得
                    if unified_info and unified_info.disaster_alerts:
                        for alert_data in unified_info.disaster_alerts:
                            if isinstance(alert_data, dict):
                                active_alerts.append(DisasterAlert(
                                    alert_id=alert_data.get('alert_id', 'unknown'),
                                    type=alert_data.get('alert_type', 'unknown'),
                                    severity=alert_data.get('severity', 'unknown'),
                                    title=alert_data.get('title', 'Unknown Alert'),
                                    issued_at=alert_data.get('timestamp', datetime.utcnow())
                                ))
                            else:
                                # オブジェクトの場合
                                issued_at = getattr(alert_data, 'timestamp', datetime.utcnow())
                                # datetimeでない場合の変換
                                if isinstance(issued_at, str):
                                    try:
                                        issued_at = datetime.fromisoformat(issued_at.replace('Z', '+00:00'))
                                    except:
                                        issued_at = datetime.utcnow()
                                elif not isinstance(issued_at, datetime):
                                    issued_at = datetime.utcnow()
                                
                                active_alerts.append(DisasterAlert(
                                    alert_id=getattr(alert_data, 'alert_id', 'unknown'),
                                    type=getattr(alert_data, 'alert_type', 'unknown'),
                                    severity=getattr(alert_data, 'severity', 'unknown'),
                                    title=getattr(alert_data, 'title', 'Unknown Alert'),
                                    issued_at=issued_at
                                ))
                    
                    # 最寄りの避難所も取得
                    if unified_info and unified_info.shelter_info:
                        shelter_data = unified_info.shelter_info[0]  # 最も近い避難所
                        if isinstance(shelter_data, dict):
                            nearest_shelter = NearestShelter(
                                shelter_id=shelter_data.get('shelter_id', 'unknown'),
                                name=shelter_data.get('name', 'Unknown Shelter'),
                                distance_km=shelter_data.get('distance_km', 0.0),
                                status=shelter_data.get('status', 'unknown')
                            )
                        else:
                            nearest_shelter = NearestShelter(
                                shelter_id=getattr(shelter_data, 'shelter_id', 'unknown'),
                                name=getattr(shelter_data, 'name', 'Unknown Shelter'),
                                distance_km=getattr(shelter_data, 'distance_km', 0.0),
                                status=getattr(shelter_data, 'status', 'unknown')
                            )
                else:
                    # 本番モード: キャッシュから高速取得
                    cached_info = await disaster_info_tool.get_fast_disaster_info(
                        location=location,
                        radius_km=10.0,
                        device_id=request.device_id
                    )
                
                
                # キャッシュされた災害アラートを変換（本番モードのみ）
                if cached_info and cached_info.disaster_alerts:
                    for alert_data in cached_info.disaster_alerts:
                        if isinstance(alert_data, dict):
                            active_alerts.append(DisasterAlert(
                                alert_id=alert_data.get('alert_id', 'unknown'),
                                type=alert_data.get('alert_type', 'unknown'),
                                severity=alert_data.get('severity', 'unknown'),
                                title=alert_data.get('title', 'Unknown Alert'),
                                issued_at=alert_data.get('timestamp', datetime.utcnow())
                            ))
                        else:
                            # オブジェクトの場合（DisasterAlertオブジェクト）
                            issued_at = getattr(alert_data, 'timestamp', datetime.utcnow())
                            # datetimeでない場合の変換
                            if isinstance(issued_at, str):
                                try:
                                    issued_at = datetime.fromisoformat(issued_at.replace('Z', '+00:00'))
                                except:
                                    issued_at = datetime.utcnow()
                            elif not isinstance(issued_at, datetime):
                                issued_at = datetime.utcnow()
                            
                            active_alerts.append(DisasterAlert(
                                alert_id=getattr(alert_data, 'alert_id', 'unknown'),
                                type=getattr(alert_data, 'alert_type', 'unknown'),
                                severity=getattr(alert_data, 'severity', 'unknown'),
                                title=getattr(alert_data, 'title', 'Unknown Alert'),
                                issued_at=issued_at
                            ))
                
                # 最寄りの避難所を取得（本番モードのみ）
                if cached_info and cached_info.shelter_info:
                    shelter_data = cached_info.shelter_info[0]  # 最も近い避難所
                    if isinstance(shelter_data, dict):
                        nearest_shelter = NearestShelter(
                            shelter_id=shelter_data.get('shelter_id', 'unknown'),
                            name=shelter_data.get('name', 'Unknown Shelter'),
                            distance_km=shelter_data.get('distance_km', 0.0),
                            status=shelter_data.get('status', 'unknown')
                        )
                    else:
                        nearest_shelter = NearestShelter(
                            shelter_id=getattr(shelter_data, 'shelter_id', 'unknown'),
                            name=getattr(shelter_data, 'name', 'Unknown Shelter'),
                            distance_km=getattr(shelter_data, 'distance_km', 0.0),
                            status=getattr(shelter_data, 'status', 'unknown')
                        )
                
            except Exception as e:
                logger.error(f"Error getting disaster info from cache: {e}")
                # キャッシュエラーの場合は空の結果で続行
                logger.warning("Continuing with empty disaster info due to cache error")
        
        # 3. モード判定
        from app.config import app_settings
        
        # フロントエンドの緊急モード設定を尊重（テストモード関係なく）
        if request.client_context.current_mode == "emergency":
            mode = DeviceMode.EMERGENCY
            mode_reason = "フロントエンド緊急モード"
        # サーバー側災害アラートがある場合
        elif active_alerts:
            mode = DeviceMode.EMERGENCY
            # 最も深刻なアラートのタイトルを理由として使用
            severities = ["critical", "emergency", "warning", "advisory"]
            most_severe = min(active_alerts, key=lambda a: severities.index(a.severity) if a.severity in severities else 999)
            mode_reason = most_severe.title
            
            # 災害アラート送信は enhanced_disaster_monitor.py に統合されたため、ここでは行わない
            # enhanced_disaster_monitor が自動的に影響範囲内の全デバイスにアラートを送信します
        else:
            # 災害アラートがない場合は平常時
            mode = DeviceMode.NORMAL
            mode_reason = "平常時"
        
        # 3.1 モード遷移チェックとクールダウンリセット
        mode_string = "emergency" if mode == DeviceMode.EMERGENCY else "normal"
        mode_transition_detected = await _check_and_handle_mode_transition(request.device_id, mode_string)
        
        if mode_transition_detected:
            # Mode transition handled: Cooldowns reset for emergency suggestions
            pass
        
        # 4. プロアクティブ提案を生成
        # Starting proactive suggestion generation
        proactive_suggestions = []
        
        try:
            # 利用可能な提案タイプを取得
            available_types, has_pending = await _get_available_suggestion_types_at_heartbeat(request)
            # Available suggestion types after cooldown check
            
            # カスタムフィルタリングを適用
            filtered_types = _apply_custom_filtering(available_types, request)
            # Suggestion types after custom filtering
            
            if filtered_types:
                # バッチ生成で提案を作成
                proactive_suggestions = await _generate_multiple_suggestions_batch(request, filtered_types)
                # Generated proactive suggestions
            else:
                logger.info("No available suggestion types after cooldown filtering")
                
        except Exception as e:
            logger.error(f"Proactive suggestion generation failed: {e}", exc_info=True)
            proactive_suggestions = []
        
        # 5. 同期設定（フロントエンドで管理するため固定値）
        
        # レスポンスを構築
        response = HeartbeatResponse(
            sync_id=sync_id,
            server_timestamp=datetime.utcnow(),
            disaster_status=DisasterStatus(
                mode=mode,
                mode_reason=mode_reason,
                active_alerts=active_alerts,
                nearest_shelter=nearest_shelter
            ),
            proactive_suggestions=proactive_suggestions,
            sync_config=SyncConfig(
                min_sync_interval=30,  # フロントエンドで管理するため固定
                force_refresh=False
            )
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Heartbeat processing failed for device {request.device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": HeartbeatError(
                    code="HEARTBEAT_FAILED",
                    message="ハートビート処理に失敗しました",
                    retry_after=60
                ).dict()
            }
        )


# ユーザーアクション記録エンドポイントは削除済み
# フロントエンドはローカルで管理

# ステータスエンドポイントは削除済み
# ヘルスチェックは /api/v1/health を使用