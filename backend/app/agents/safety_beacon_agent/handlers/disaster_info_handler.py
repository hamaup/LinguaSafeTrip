"""災害情報エージェントノードハンドラー - 災害情報の収集・処理・応答生成を担当"""
import logging
from typing import Dict, Any, List, Optional, Union
import asyncio
import os
from datetime import datetime, timezone

from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage

from app.schemas.agent import AgentState

# 簡易キャッシュ（メモリベース）
_disaster_info_cache: Dict[str, Any] = {}
_analysis_cache: Dict[str, Any] = {}  # ユーザー要求分析結果のキャッシュ
_cache_ttl_seconds = 300  # 5分間キャッシュ

async def _get_current_disaster_context(state: AgentState) -> Dict[str, Any]:
    """現在のアクティブな災害情報から災害タイプを取得"""
    try:
        # 位置情報を取得
        user_location = _get_state_value(state, 'user_location')
        if not user_location:
            return {"disaster_type": "general", "active_disasters": []}
        
        # デバイスIDを取得
        device_id = _get_state_value(state, 'device_id')
        
        # 統合災害情報ツールを使用してアクティブな災害を取得
        from app.tools.disaster_info_tools import UnifiedDisasterInfoTool
        disaster_tool = UnifiedDisasterInfoTool()
        
        # 現在の災害情報を取得
        location_dict = {
            "latitude": user_location.get("latitude"),
            "longitude": user_location.get("longitude")
        }
        
        # アクティブな災害アラートを確認（device_idを渡す）
        # 常に統合災害情報を使用してdevice_idを考慮
        from app.schemas.common.location import Location
        location = Location(latitude=user_location.get("latitude"), longitude=user_location.get("longitude"))
        unified_info = await disaster_tool.get_unified_disaster_info(location, radius_km=50.0, device_id=device_id)
        disaster_info = unified_info.disaster_alerts
        
        if disaster_info:
            # 最も重要度の高い災害タイプを特定
            disaster_types = [info.type for info in disaster_info if hasattr(info, 'type')]
            if disaster_types:
                # 重要度順（津波 > 地震 > 台風 > 豪雨 > 火事）
                priority_order = ["tsunami", "earthquake", "typhoon", "heavy_rain", "fire"]
                for disaster_type in priority_order:
                    if disaster_type in disaster_types:
                        return {
                            "disaster_type": disaster_type,
                            "active_disasters": disaster_types,
                            "context_source": "active_alert"
                        }
                
                # 優先順位にない場合は最初のタイプを使用
                return {
                    "disaster_type": disaster_types[0],
                    "active_disasters": disaster_types,
                    "context_source": "active_alert"
                }
        
        return {"disaster_type": "general", "active_disasters": [], "context_source": "no_active_alerts"}
        
    except Exception as e:
        logger.error(f"Failed to get disaster context: {e}")
        return {"disaster_type": "general", "active_disasters": [], "context_source": "error"}

from app.schemas.disaster_info import RelevantDisasterEvent
from app.schemas.agent_state import AgentState
from ..core.llm_singleton import get_llm_client, get_shared_llm
from app.tools.alert_tools import evaluate_alert_level_from_jma_event
from app.tools.disaster_info_tools import UnifiedDisasterInfoTool
# Import will be done lazily to avoid circular imports
from app.prompts.disaster_prompts import (
    ANALYZE_USER_REQUEST_PROMPT,
    GENERATE_DISASTER_INFO_RESPONSE_PROMPT,
    NO_INFORMATION_FOUND_RESPONSE_PROMPT,
    ERROR_RESPONSE_PROMPT,
    CONTEXT_ANALYSIS_PROMPT,
    PERSONALIZED_DISASTER_PREPARATION_PROMPT,
    TSUNAMI_NO_INFO_PROMPT,
    TYPHOON_NO_INFO_PROMPT,
    LANDSLIDE_NO_INFO_PROMPT
)
from .complete_response_handlers import CompleteResponseGenerator

logger = logging.getLogger(__name__)

# バッチ処理フラグ

def _get_state_value(state, key, default=None):
    """統一された状態値取得メソッド"""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)

def _update_state(state, key, value):
    """統一された状態更新メソッド"""
    if isinstance(state, dict):
        state[key] = value
    else:
        setattr(state, key, value)
    return state

async def handle_disaster_information_request(state: AgentState) -> Dict[str, Any]:
    """災害情報リクエストを処理するLangGraphノード関数

    Args:
        state: 現在のAgentState

    Returns:
        更新されたAgentStateの辞書表現 (messagesフィールドを含む)
    """
    logger.info(f"🔵 NODE ENTRY: disaster_processor")
    logger.info(f"🔵 NODE INPUT: user_input='{_get_state_value(state, 'user_input', '')[:50]}...'")
    logger.info(f"🔵 NODE INPUT: session_id={_get_state_value(state, 'session_id', 'unknown')}")
    
    # enhance_qualityからのフィードバック取得・活用
    improvement_feedback = _get_state_value(state, 'improvement_feedback', '')
    if improvement_feedback:
        logger.info(f"🔄 Processing with improvement feedback: {improvement_feedback}")
    else:
        logger.info("🆕 Initial processing (no improvement feedback)")
    
    # バッチ処理版の実行
    device_id = _get_state_value(state, 'device_id')
    logger.info(f"🔍 disaster_info_handler - device_id from state: {device_id}")
    return await _disaster_info_node_batch(state)
    
async def _disaster_info_node_batch(state: AgentState) -> Dict[str, Any]:
    """災害情報ハンドラー - バッチ処理版"""
    try:
        user_input = _get_state_value(state, 'user_input', '')
        user_language = _get_state_value(state, 'user_language', 'ja')
        primary_intent = _get_state_value(state, 'primary_intent', 'disaster_information')
        is_disaster_mode = _get_state_value(state, 'is_disaster_mode', False)
        
        logger.info(f"🔥 Using batch processing for disaster info handler")
        
        # コンテキストデータを準備
        context_data = {
            "emotional_context": _get_state_value(state, 'emotional_context', {}),
            "location_info": _get_state_value(state, 'location_info', {}),
            "is_emergency_mode": is_disaster_mode,
            "disaster_context": {}
        }
        
        # feedback活用チェック
        improvement_feedback = _get_state_value(state, 'improvement_feedback', '')
        
        # 災害データ収集（必要に応じて）
        analysis_result = await _analyze_user_request(state)
        disaster_events = await _collect_disaster_info(analysis_result, state)
        processed_info = await _process_disaster_info(disaster_events, state)
        
        # 検索結果を追加
        search_results = _get_state_value(state, 'web_search_results', [])
        
        # Convert disaster events to dict format for guide_content
        guide_content_dicts = []
        for event in disaster_events:
            guide_content_dicts.append({
                "title": event.title,
                "content": event.description,
                "event_type": event.event_type,
                "severity": event.severity,
                "location": event.location,
                "time": event.event_time.isoformat() if event.event_time else ""
            })
        
        # 完全応答生成（バッチ処理）
        response_data = await CompleteResponseGenerator.generate_complete_response(
            user_input=user_input,
            intent=primary_intent,
            user_language=user_language,
            context_data=context_data,
            handler_type="disaster",
            improvement_feedback=improvement_feedback,  # feedbackを渡す
            search_results=search_results,
            guide_content=guide_content_dicts,
            state=state  # state追加で自動バックアップ
        )
        
        # メッセージ構築
        from langchain_core.messages import AIMessage
        message = AIMessage(
            content=response_data["main_response"],
            additional_kwargs={
                "cards": response_data["suggestion_cards"],
                "follow_up_questions": response_data["follow_up_questions"],
                "priority": response_data["priority_level"],
                "handler_type": "disaster",
                "alert_level": processed_info.get("highest_alert_level", "none")
            }
        )
        
        # 緊急応答フラグの判定
        is_emergency_response = (
            is_disaster_mode or 
            processed_info.get("highest_alert_level") in ["emergency", "critical", "warning"] or
            response_data["priority_level"] == "critical"
        )
        
        # バッチ処理使用フラグを設定
        intermediate_results = _get_state_value(state, 'intermediate_results', {})
        intermediate_results.update({
            "batch_processing_used": True,
            "disaster_info": processed_info,
            "current_alert_level": processed_info.get("highest_alert_level")
        })
        
        return {
            "messages": [message],
            "final_response_text": response_data["main_response"],
            "last_response": response_data["main_response"],
            "current_task_type": ["task_complete_disaster_info"],
            "secondary_intents": [],
            "is_emergency_response": is_emergency_response,
            "intermediate_results": intermediate_results,
            "cards_to_display_queue": response_data["suggestion_cards"],
            "quality_self_check": response_data.get("quality_self_check", {}),
            "handler_completed": True
        }
        
    except Exception as e:
        logger.error(f"Batch disaster info processing failed: {e}")
        return await _disaster_info_fallback_response(state, str(e))

async def _disaster_info_fallback_response(state: AgentState, error_message: str) -> Dict[str, Any]:
    user_language = _get_state_value(state, 'user_language', 'ja')
    is_disaster_mode = _get_state_value(state, 'is_disaster_mode', False)
    
    # English-only fallback message (per CLAUDE.md principles)
    fallback_message = "Sorry, an error occurred while retrieving disaster information. Please check official disaster information websites for the latest updates."
    
    return {
        "messages": [],
        "final_response_text": fallback_message,
        "last_response": fallback_message,
        "current_task_type": ["error"],
        "intermediate_results": {"error": error_message},
        "cards_to_display_queue": [],
        "is_emergency_response": is_disaster_mode
    }

async def _analyze_user_request(state: AgentState) -> Dict[str, Any]:
    """ユーザーの要求内容を分析

    Args:
        state: 現在のAgentState

    Returns:
        {
            "disaster_type": str,  # 災害タイプ (earthquake/tsunami/floodなど)
            "location_specific": bool,  # 特定地域への関心があるか
            "detail_level": str,  # "summary" or "detailed"
            "time_range": str,  # "current", "recent", or "future"
        }
    """
    # 最適化: すでに分析済みの結果があるかチェック
    intermediate_results = _get_state_value(state, 'intermediate_results', {})
    if intermediate_results and 'analysis_result' in intermediate_results:
        analysis = intermediate_results['analysis_result']
        if isinstance(analysis, dict) and 'intent_category' in analysis:
            # まず、アクティブな災害アラートから災害タイプを取得
            disaster_context = await _get_current_disaster_context(state)
            disaster_type = disaster_context.get("disaster_type", "disaster")
            
            # アクティブアラートがない場合は intent_category をチェック
            if disaster_type in ["disaster", "general"]:
                if 'earthquake' in analysis.get('intent_category', ''):
                    disaster_type = "earthquake"
                elif 'tsunami' in analysis.get('intent_category', ''):
                    disaster_type = "tsunami"
                elif 'typhoon' in analysis.get('intent_category', ''):
                    disaster_type = "typhoon"
                elif 'flood' in analysis.get('intent_category', ''):
                    disaster_type = "flood"
                elif 'preparation' in analysis.get('intent_category', '') or 'prepare' in analysis.get('intent_category', ''):
                    disaster_type = "preparation"
                elif 'seasonal' in analysis.get('intent_category', ''):
                    disaster_type = "seasonal"
            
            return {
                "disaster_type": disaster_type,
                "location_specific": analysis.get('needs_location', False),
                "detail_level": "detailed" if analysis.get('urgency_level', 0) > 3 else "summary",
                "time_range": "current",
                "search_keywords": analysis.get('search_keywords', []),
                "user_situation": analysis.get('user_situation', ''),
                "response_type": analysis.get('response_type', 'direct_answer')
            }
    
    # フォールバック: 従来の分析（既存のコードのまま）
    user_input = _get_state_value(state, 'user_input', '')
    
    # キャッシュキーを生成
    import hashlib
    cache_key = f"analysis:{hashlib.md5(user_input.encode()).hexdigest()[:16]}"
    
    # キャッシュから確認
    current_time = datetime.now(timezone.utc)
    if cache_key in _analysis_cache:
        cached_data = _analysis_cache[cache_key]
        cache_time = cached_data.get('timestamp', datetime.min.replace(tzinfo=timezone.utc))
        if (current_time - cache_time).total_seconds() < _cache_ttl_seconds:
            return cached_data.get('result', {})

    llm = get_shared_llm()
    
    # 簡略化されたプロンプト（高速化）
    disaster_mode = 'Active' if _get_state_value(state, 'is_disaster_mode') else 'Normal'
    
    # シンプルなプロンプトでLLM呼び出しを高速化
    prompt = ANALYZE_USER_REQUEST_PROMPT.format(
        user_input=user_input,
        disaster_mode=disaster_mode
    )

    try:
        from langchain_core.messages import HumanMessage
        
        # 統一的なLLM呼び出しを使用
        from ..core.llm_singleton import ainvoke_llm
        
        response_text = await ainvoke_llm(
            prompt=prompt,
            task_type="analysis",
            temperature=0.3,  # 低い温度で高速化
            max_tokens=300   # Increased for proper JSON response
        )
        
        # JSON文字列を安全にパース
        import json
        response_text = response_text.strip()
        
        # 空の応答チェック
        if not response_text:
            logger.warning("Empty response from LLM during request analysis")
            raise ValueError("Empty response from LLM")
        
        # LLMベースのアプローチに従った柔軟なJSON解析
        try:
            # Enhanced JSON extraction with multiple patterns
            import re
            
            # Try multiple JSON extraction patterns
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',  # ```json { } ```
                r'```\s*(\{.*?\})\s*```',     # ``` { } ```
                r'(\{[^{}]*\})',              # Simple { }
                r'(\{.*\})'                   # Any { } content
            ]
            
            json_str = response_text.strip()
            for pattern in json_patterns:
                match = re.search(pattern, response_text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    break
            
            analysis = json.loads(json_str)
            
            # 分析結果をキャッシュに保存
            _analysis_cache[cache_key] = {
                'result': analysis,
                'timestamp': datetime.now(timezone.utc)
            }
            
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON decode error: {json_error}, response: {response_text[:200]}...")
            # LLMベースの分析に失敗した場合のフォールバック
            # 自然言語処理に依存し、キーワードマッチングは使用しない
            logger.warning("Using safe fallback due to JSON parsing error")
            
            # LLMベースの自然言語分析（フォールバック時の簡易版）
            is_news_query = await _is_news_query_semantic(user_input)
            
            analysis = {
                "disaster_type": "disaster",  # 一般的な災害情報として扱う
                "location_specific": bool(_get_state_value(state, 'user_location')),
                "detail_level": "summary",
                "time_range": "normal_time" if is_news_query else "recent"
            }

        # 必須フィールドの検証とdisaster_typeの改善
        required_fields = ["disaster_type", "location_specific", "detail_level", "time_range"]
        for field in required_fields:
            if field not in analysis:
                analysis[field] = "disaster" if field == "disaster_type" else "general"
        
        # disaster_typeが汎用的すぎる場合、アクティブな災害アラートから検出
        if analysis.get("disaster_type") in ["disaster", "general", ""]:
            disaster_context = await _get_current_disaster_context(state)
            detected_type = disaster_context.get("disaster_type", "disaster")
            if detected_type not in ["disaster", "general"]:
                analysis["disaster_type"] = detected_type
                analysis["active_disasters"] = disaster_context.get("active_disasters", [])
                logger.info(f"🎯 Using active disaster context: {detected_type}, source: {disaster_context.get('context_source')}")

        # Check for rejection reasons (e.g., evacuation requests)
        if analysis.get("reject_reason") == "evacuation_request":
            analysis["disaster_type"] = "rejected"
            analysis["semantic_intent"] = "User is asking about evacuation centers, not disaster information"
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze user request: {e}")
        # LLMベースの分析が完全に失敗した場合のフォールバック
        # キーワードマッチングは使用せず、安全なデフォルト値を返す
        logger.warning("Using safe fallback due to LLM analysis failure")
        
        return {
            "disaster_type": "disaster",  # 一般的な災害情報として扱う
            "location_specific": bool(_get_state_value(state, 'user_location')),
            "detail_level": "summary",  # デフォルトは概要レベル
            "time_range": "current"  # デフォルトは現在の情報
        }

async def _collect_disaster_info(
    analysis: Dict[str, Any],
    state: AgentState
) -> List[RelevantDisasterEvent]:
    """適切なツールを選択して災害情報を収集（キャッシュ対応）

    Args:
        analysis: _analyze_user_requestの結果
        state: 現在のAgentState

    Returns:
        収集した災害情報のリスト
    """
    disaster_type = analysis.get('disaster_type', 'disaster')
    user_input = _get_state_value(state, 'user_input', '')
    
    # キャッシュキーを生成（災害タイプ + ユーザー入力のハッシュ）
    import hashlib
    cache_key = f"{disaster_type}:{hashlib.md5(user_input.encode()).hexdigest()[:8]}"
    current_time = datetime.now(timezone.utc)
    
    # キャッシュから確認
    if cache_key in _disaster_info_cache:
        cached_data = _disaster_info_cache[cache_key]
        cache_time = cached_data.get('timestamp', datetime.min.replace(tzinfo=timezone.utc))
        if (current_time - cache_time).total_seconds() < _cache_ttl_seconds:
            return cached_data.get('data', [])
    

    # Store analysis result in state for tool execution
    state['analysis_result'] = analysis
    
    # Simplified approach - directly use web search tool
    disaster_type = analysis.get('disaster_type', 'disaster')
    user_input = _get_state_value(state, 'user_input', '')
    is_emergency = _get_state_value(state, 'is_disaster_mode', False) or _get_state_value(state, 'is_emergency_level', False)
    device_id = _get_state_value(state, 'device_id')  # デバイスIDを取得
    
    # アクティブな災害アラートから災害タイプを取得
    disaster_context = await _get_current_disaster_context(state)
    active_disaster_type = disaster_context.get("disaster_type", "general")
    
    # 災害タイプが一般的な場合、アクティブな災害タイプを使用
    if disaster_type in ['disaster', 'general'] and active_disaster_type not in ['disaster', 'general']:
        logger.info(f"🎯 Using active disaster type: {active_disaster_type} instead of {disaster_type}")
        disaster_type = active_disaster_type
        analysis['active_disasters'] = disaster_context.get("active_disasters", [])
    
    # 緊急時は災害タイプを強制的に災害関連に変更
    if is_emergency and disaster_type == 'general':
        disaster_type = 'disaster'
    
    # Handle preparation and seasonal queries with temporal context
    time_range = analysis.get('time_range', 'current')
    
    # If user asked for "normal time" disaster news, search for preparation content
    if time_range == 'normal_time':
        search_type = 'preparation'
        # Query modification will be handled after translation to Japanese
    elif disaster_type == 'preparation' or analysis.get('preparation_focus', False):
        # For preparation queries, search for preparation guides
        search_type = 'preparation'
        season = analysis.get('season_specific', 'none')
        if season != 'none':
            # Add season to search query
            user_input = f"{user_input} {season}"
    elif disaster_type == 'seasonal':
        search_type = 'seasonal'
    else:
        search_type = disaster_type
    
    # Use UnifiedDisasterInfoTool to get disaster data
    disaster_info_tool = UnifiedDisasterInfoTool(is_emergency=is_emergency)
    
    try:
        # 位置情報を取得
        user_location = _get_state_value(state, 'user_location')
        if not user_location:
            # 位置情報がない場合は空のリストを返す
            logger.warning("No user location available for disaster info collection")
            return []
        
        # Location オブジェクトを作成
        from app.schemas.common.location import Location
        location = Location(
            latitude=user_location.get("latitude", 35.6762),  # デフォルトは東京
            longitude=user_location.get("longitude", 139.6503)
        )
        
        # 統合災害情報を使用してdevice_idを考慮
        unified_info = await disaster_info_tool.get_unified_disaster_info(
            location, 
            radius_km=50.0, 
            device_id=device_id
        )
        
        # 災害アラートを取得
        mock_disasters = unified_info.disaster_alerts
        
        # 準備・季節情報の場合はフォールバックを使用
        if disaster_type in ['preparation', 'seasonal'] and not mock_disasters:
            mock_disasters = disaster_info_tool._get_fallback_news(max_items=5)
        
        # Convert DisasterAlert objects to RelevantDisasterEvent objects
        events = []
        for idx, disaster in enumerate(mock_disasters):
            # DisasterAlertとDisasterInfoの両方に対応
            if hasattr(disaster, 'alert_type'):
                # DisasterAlertオブジェクト
                event_time = disaster.issued_at if hasattr(disaster, 'issued_at') else datetime.now(timezone.utc)
                event_type = disaster.alert_type
                description = disaster.content
                area = disaster.affected_areas[0] if hasattr(disaster, 'affected_areas') and disaster.affected_areas else "Unknown"
            else:
                # DisasterInfoオブジェクト
                event_time = disaster.occurred_at if hasattr(disaster, 'occurred_at') else datetime.now(timezone.utc)
                event_type = disaster.type if hasattr(disaster, 'type') else 'general'
                description = disaster.description if hasattr(disaster, 'description') else ''
                area = disaster.area if hasattr(disaster, 'area') else "Unknown"
            
            event = RelevantDisasterEvent(
                event_id=f"{disaster_type}_{idx}",
                title=disaster.title,
                event_type=event_type,
                severity=disaster.severity,
                timestamp=event_time,
                event_time=event_time,
                location=area,
                description=description,
                distance_km=0.0,
                relevance_score=0.9  # High relevance for mock data
            )
            
            # Note: earthquake-specific data (magnitude, epicenter) is included in description
                
            events.append(event)
        
        # Store mock results as web search results for compatibility
        mock_search_results = []
        for disaster in mock_disasters:
            # DisasterAlertとDisasterInfoの両方に対応
            if hasattr(disaster, 'alert_type'):
                # DisasterAlertオブジェクト
                description = disaster.content
                area = disaster.affected_areas[0] if hasattr(disaster, 'affected_areas') and disaster.affected_areas else "Unknown"
                timestamp = disaster.issued_at if hasattr(disaster, 'issued_at') else datetime.now()
                url = disaster.url if hasattr(disaster, 'url') else 'https://www.jma.go.jp/mock'
                source = disaster.source if hasattr(disaster, 'source') else 'JMA'
            else:
                # DisasterInfoオブジェクト
                description = disaster.description if hasattr(disaster, 'description') else ''
                area = disaster.area if hasattr(disaster, 'area') else "Unknown"
                timestamp = disaster.occurred_at if hasattr(disaster, 'occurred_at') else datetime.now()
                url = disaster.url if hasattr(disaster, 'url') else 'https://www.jma.go.jp/mock'
                source = disaster.source if hasattr(disaster, 'source') else 'JMA'
            
            mock_search_results.append({
                'title': disaster.title,
                'description': description,
                'snippet': description[:200],
                'url': url,
                'area': area,
                'severity': disaster.severity,
                'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                'source': source
            })
        
        _update_state(state, 'web_search_results', mock_search_results)
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to collect disaster info: {e}", exc_info=True)
        return []

async def _process_disaster_info(
    events: List[RelevantDisasterEvent],
    state: AgentState
) -> Dict[str, Any]:
    """収集した災害情報を統合・評価

    Args:
        events: 収集した災害イベント
        state: 現在のAgentState

    Returns:
        {
            "events": List[RelevantDisasterEvent],  # 処理済みイベント
            "highest_alert_level": str,  # 最高アラートレベル
            "most_relevant_event": Optional[RelevantDisasterEvent],  # 最も関連性の高いイベント
            "summary": str  # 情報の概要
        }
    """

    if not events:
        logger.warning("⚠️ No events to process")
        # Get disaster type from analysis or state
        analysis_result = _get_state_value(state, 'analysis_result', {})
        disaster_type = 'unknown'
        if isinstance(analysis_result, dict):
            disaster_type = analysis_result.get('disaster_type', 'unknown')
        
        return {
            "events": [],
            "highest_alert_level": "none",
            "most_relevant_event": None,
            "summary": "No current disaster information available",
            "disaster_type": disaster_type
        }

    processed_events = []
    alert_levels = []

    # 1. 各イベントの処理
    for event in events:
        # アラートレベル評価 (テスト用にモック可能な形で呼び出し)
        alert_level = evaluate_alert_level_from_jma_event(event)
        
        # Convert AlertLevel enum to string for the event
        if hasattr(alert_level, 'value'):
            event.alert_level = alert_level.value
        elif hasattr(alert_level, 'name'):
            event.alert_level = alert_level.name.lower()
        else:
            event.alert_level = str(alert_level)
            
        alert_levels.append(alert_level)

        # ユーザー位置との関連性評価
        if state.get('user_location'):
            event.relevance_score = _calculate_event_relevance(
                event,
                state['user_location']
            )

        processed_events.append(event)

    # 2. 優先度付け (関連性スコアとアラートレベル)
    processed_events.sort(
        key=lambda x: (
            -x.relevance_score if hasattr(x, 'relevance_score') else 0,
            -_alert_level_to_priority(x.alert_level)
        )
    )

    # 3. サマリー生成
    summary = _generate_disaster_summary(processed_events, state)

    # Convert AlertLevel enum to string value for JSON serialization
    highest_alert = max(alert_levels, key=_alert_level_to_priority)
    if hasattr(highest_alert, 'value'):
        highest_alert_str = highest_alert.value
    elif hasattr(highest_alert, 'name'):
        highest_alert_str = highest_alert.name.lower()
    else:
        highest_alert_str = str(highest_alert)
    
    return {
        "events": processed_events,
        "highest_alert_level": highest_alert_str,
        "most_relevant_event": processed_events[0] if processed_events else None,
        "summary": summary,
        "disaster_type": _get_state_value(state, 'analysis_result', {}).get('disaster_type', 'unknown')
    }

def _calculate_event_relevance(
    event: RelevantDisasterEvent,
    user_location: Dict[str, float]
) -> float:
    """イベントとユーザー位置の関連性を計算

    スコア計算基準:
    - 距離が近いほど高スコア (0-1の範囲)
    - イベントタイプが緊急度高いほど高スコア
    - 発生時間が新しいほど高スコア
    """
    from app.utils.geo_utils import haversine_distance
    # timezone already imported at top

    # 基本スコア
    score = 0.5

    # 距離による調整 (0-30kmを考慮)
    if user_location and hasattr(event, 'distance_km'):
        distance = event.distance_km
        if distance <= 5:  # 5km以内
            score += 0.3
        elif distance <= 10:  # 10km以内
            score += 0.2
        elif distance <= 20:  # 20km以内
            score += 0.1

    # イベントタイプによる調整
    if event.event_type in ['earthquake', 'tsunami']:
        score += 0.2
    elif event.event_type in ['flood', 'fire']:
        score += 0.1

    # 時間による調整 (24時間以内ならボーナス)
    # event_timeがtimezone-awareであることを確認
    if event.event_time.tzinfo is None:
        # timezone-naiveの場合はUTCとして扱う
        event_time_aware = event.event_time.replace(tzinfo=timezone.utc)
    else:
        event_time_aware = event.event_time
    
    time_diff = (datetime.now(timezone.utc) - event_time_aware).total_seconds()
    if time_diff < 86400:  # 24時間以内
        score += 0.1 * (1 - (time_diff / 86400))

    # スコアを0-1の範囲にクリップ
    return max(0.0, min(1.0, score))

def _alert_level_to_priority(level: Union[str, object]) -> int:
    """アラートレベルを優先度数値に変換"""
    level_priority = {
        'critical': 5,
        'emergency': 4,
        'warning': 3,
        'alert': 2,
        'caution': 1,
        'info': 0,
        'none': 0
    }
    
    # AlertLevel Enumや他のオブジェクトの場合は値を取得
    if hasattr(level, 'value'):
        level_str = str(level.value)
    elif hasattr(level, 'name'):
        level_str = str(level.name)
    else:
        level_str = str(level)
    
    # 文字列に変換してから小文字にする
    return level_priority.get(level_str.lower(), 0)

def _generate_disaster_summary(
    events: List[RelevantDisasterEvent],
    state: AgentState
) -> str:
    """災害情報の概要を生成"""
    if not events:
        return "No disaster information available"
    
    event_count = len(events)
    
    # Get highest alert level efficiently
    from app.schemas.alert import AlertLevel
    highest_alert = "none"
    
    for event in events:
        if hasattr(event, 'alert_level'):
            if hasattr(event.alert_level, 'value'):
                # It's an enum
                current_priority = _alert_level_to_priority(event.alert_level)
            else:
                # It's a string
                current_priority = _alert_level_to_priority(str(event.alert_level))
            
            if current_priority > _alert_level_to_priority(highest_alert):
                highest_alert = str(event.alert_level).lower()
    
    # Get most relevant event types
    event_types = list(set(e.event_type for e in events[:3]))  # Top 3 event types
    types_str = ", ".join(event_types) if event_types else "various"
    
    return f"{event_count} disaster events found ({types_str}). Highest alert: {highest_alert}"

async def _generate_response_text(
    disaster_info: Dict[str, Any],
    state: AgentState
) -> str:
    """ユーザー向けの応答テキストを生成

    Args:
        disaster_info: _process_disaster_infoの結果
        state: 現在のAgentState

    Returns:
        ユーザー向けの自然言語応答
    """

    # ユーザーの言語設定を取得
    user_language = _get_state_value(state, 'user_language', 'ja')
    language_names = {
        'ja': 'Japanese',
        'en': 'English',
        'ko': 'Korean',
        'zh': 'Chinese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian'
    }
    target_language_name = language_names.get(user_language, 'Japanese')
    
    if not disaster_info.get("events"):
        logger.warning("No disaster events found for response generation")
        
        # 感情的コンテキストを取得
        emotional_context = _get_state_value(state, 'emotional_context', {})
        requires_emotional_support = _get_state_value(state, 'requires_emotional_support', False)
        user_language = _get_state_value(state, 'user_language', 'ja')
        
        
        # 感情的サポートが必要な場合は共感的な応答を生成
        if requires_emotional_support and emotional_context.get('emotional_state') != 'neutral':
            return await _generate_emotional_support_response(
                emotional_context, user_language, disaster_info.get('disaster_type', 'disaster')
            )
        
        # 災害タイプに基づく応答を生成
        user_input = _get_state_value(state, 'user_input', '')
        disaster_type = disaster_info.get('disaster_type', 'disaster')
        
        # 災害タイプに基づく特別な応答（言語対応）
        # LLMによる分析結果を使用し、キーワードマッチングは行わない
        if disaster_type == 'tsunami':
            # 内部処理は英語で統一
            return "No tsunami warnings or advisories are currently in effect. Please check the JMA website for the latest information. Stay safe."
        elif disaster_type == 'typhoon':
            # 内部処理は英語で統一
            return "No special typhoon information is currently available. Please check the JMA website for the latest weather information. Be aware of weather changes."
        elif disaster_type == 'landslide':
            # 内部処理は英語で統一
            return "No landslide warnings are currently in effect. During heavy rain, stay away from cliffs and steep slopes and evacuate to safe areas. Check the JMA website for latest information."
        
        # 防災準備関連のクエリに対する特別な処理
        user_input = _get_state_value(state, 'user_input', '')
        current_task_type = _get_state_value(state, 'current_task_type', '')
        primary_intent = _get_state_value(state, 'primary_intent', '')
        
        # 防災準備のクエリの場合は専用応答を生成
        if (primary_intent == 'disaster_preparation' or 
            current_task_type == 'disaster_preparation' or
            disaster_type == 'preparation' or
            disaster_type == 'seasonal'):
            
            return await _generate_disaster_preparation_response(user_input, user_language)
        
        # 内部処理は英語で統一
        return "No relevant disaster information was found. Please pay attention to safety information."

    # 通常のLLMベース応答生成を使用
    
    # 分析結果を取得 - directly from state, not intermediate_results
    analysis_result = _get_state_value(state, 'analysis_result', {})
    intermediate_results = _get_state_value(state, 'intermediate_results', {})
    response_type = intermediate_results.get('response_type', 'direct_answer')
    
    # 感情的コンテキストを取得
    emotional_context = _get_state_value(state, 'emotional_context', {})
    requires_emotional_support = _get_state_value(state, 'requires_emotional_support', False)
    user_language = _get_state_value(state, 'user_language', 'ja')
    
    # 検索結果をまとめる
    search_results = {
        "events": disaster_info.get("events", []),
        "highest_alert_level": disaster_info.get("highest_alert_level", "none"),
        "summary": disaster_info.get("summary", ""),
        "disaster_type": disaster_info.get('disaster_type', 'unknown')
    }
    
    # Use complete response handler for response generation
    llm = get_shared_llm()
    
    # Prepare data based on response type
    response_data = {}
    
    # Check if we have events to display
    events = search_results.get("events", [])
    if events:
        # Format events for web search news response type
        search_results_text = []
        for event in events[:5]:
            if hasattr(event, 'title'):
                # It's a RelevantDisasterEvent object
                search_results_text.append(f"- {event.title}\n  {event.description[:500] if len(event.description) > 500 else event.description}")
                if hasattr(event, 'location'):
                    search_results_text[-1] += f"\n  Location: {event.location}"
            elif isinstance(event, dict):
                # It's a dictionary
                title = event.get('title', 'Disaster Information')
                desc = event.get('description', event.get('snippet', ''))
                search_results_text.append(f"- {title}\n  {desc[:500] if len(desc) > 500 else desc}")
                if event.get('location'):
                    search_results_text[-1] += f"\n  Location: {event.get('location')}"
        
        response_data = {
            'search_results_text': '\n\n'.join(search_results_text),
            'region_context': f"Found {len(events)} disaster-related items for {search_results.get('disaster_type', 'general')} information."
        }
        response_type = 'web_search_news'
    else:
        # No events found
        response_data = {
            'fallback_text': "No specific disaster information found at this time. Please check official sources for the latest updates."
        }
        response_type = 'no_web_results'
    
    generated_text = await _generate_natural_response(
        llm=llm,
        data=response_data,
        response_type=response_type,
        detected_lang=user_language
    )
    
    
    # If generation failed, create a proper response directly
    if not generated_text or len(generated_text.strip()) == 0:
        logger.warning("⚠️ Empty response from _generate_natural_response, using direct generation")
        events = disaster_info.get("events", [])
        
        # Generate response based on disaster type and found information
        if events:
            llm = get_shared_llm()
            from langchain_core.messages import HumanMessage
            
            # Create event summaries
            event_details = []
            for i, event in enumerate(events[:5]):
                if isinstance(event, dict):
                    title = event.get('title', '')
                    snippet = event.get('description', event.get('snippet', ''))
                    url = event.get('url', '')
                    event_details.append(f"- {title}\n  {snippet[:150]}...\n  Source: {url}")
                elif hasattr(event, 'title'):
                    event_details.append(f"- {event.title}\n  {getattr(event, 'description', '')[:150]}...")
            
            prompt = GENERATE_DISASTER_INFO_RESPONSE_PROMPT.format(
                event_count=len(events),
                event_details=''.join(event_details[:5])
            )

            try:
                # 統一的なLLM呼び出しを使用
                from ..core.llm_singleton import ainvoke_llm
                
                generated_text = await ainvoke_llm(
                    prompt=prompt,
                    task_type="response_generation",
                    temperature=0.7,
                    max_tokens=1024
                )
            except Exception as e:
                logger.error(f"Failed to generate LLM response: {e}")
                # Simple fallback
                generated_text = f"I found {len(events)} disaster preparedness resources. These include information about emergency supplies, evacuation planning, and safety measures. Please check the official sources for detailed guidance on disaster preparation."
        else:
            generated_text = "No specific disaster news was found at this time. For the latest disaster information, please check official sources like JMA (Japan Meteorological Agency) or your local government's emergency management website."
    
    # 災害詳細情報をレスポンステキストに組み込む
    enhanced_text = _format_response_with_disaster_details(
        generated_text, 
        disaster_info, 
        analysis_result,
        user_language
    )
    
    return enhanced_text

async def _generate_suggestion_cards(
    disaster_info: Dict[str, Any],
    state: AgentState
) -> List[Dict[str, Any]]:
    """提案カードを生成

    Args:
        disaster_info: _process_disaster_infoの結果
        state: 現在のAgentState

    Returns:
        Flutterで表示可能な提案カードのリスト
    """
    
    # 準備に関する質問の場合はカードを生成しない
    analysis_result = _get_state_value(state, 'analysis_result', {})
    if analysis_result.get('time_range') == 'normal_time' or analysis_result.get('preparation_focus', False):
        return []
    
    # Check disaster type - if it's preparation or seasonal, don't generate cards
    disaster_type_from_analysis = analysis_result.get('disaster_type', '')
    if disaster_type_from_analysis in ['preparation', 'seasonal']:
        return []

    if not disaster_info.get("events"):
        return []

    # ユーザーの言語設定を取得
    user_language = _get_state_value(state, 'user_language', 'ja')
    
    cards = []

    # 1. 主要イベントに基づく基本カード（フロントエンド対応形式）
    main_event = disaster_info["most_relevant_event"]
    if main_event:
        # フロントエンドが認識する形式に変換
        main_card = {
            "card_type": "evacuation_info",  # フロントエンドが認識するタイプ
            "type": "shelter_info",  # フロントエンドが認識するタイプ
            "title": _get_localized_title(main_event.event_type, user_language),
            "description": f"{main_event.event_type}に関する重要情報",
            "priority": _alert_level_to_priority(main_event.alert_level),
            "data": {
                "event_type": main_event.event_type,
                "location": main_event.location,
                "time": main_event.event_time.isoformat(),
                "severity": main_event.alert_level,
                "description": main_event.description,
                "message": "詳細情報はメッセージ本文をご確認ください",
                "action_type": "view_details"
            },
            "actions": _get_suggested_actions(main_event, user_language)
        }
        cards.append(main_card)

    # 2. 避難所情報カード (地震/津波/洪水の場合)
    if main_event and main_event.event_type in ["earthquake", "tsunami", "flood"]:
        shelter_card = {
            "type": "shelter_info",
            "title": _get_localized_title("shelter_info", user_language),
            "priority": 2,
            "content": {
                "message": _get_localized_message("seek_shelter", user_language),
                "shelters": []  # 後で位置情報ベースで追加
            },
            "actions": [
                {
                    "type": "open_map",
                    "label": _get_localized_action("show_shelters", user_language),
                    "data": {"center": state.get("user_location")}
                }
            ]
        }
        cards.append(shelter_card)

    # 3. 緊急連絡カードは観光客向けアプリでは表示しない
    # 観光客は現地の緊急連絡システムに不慣れなため、混乱を避ける

    # 優先度でソート
    cards.sort(key=lambda x: -x["priority"])

    return cards

def _format_response_with_disaster_details(
    response_text: str,
    disaster_info: Dict[str, Any],
    analysis_result: Dict[str, Any],
    user_language: str = 'ja'
) -> str:
    """災害の詳細情報をレスポンステキストに組み込む
    
    Args:
        response_text: 元のレスポンステキスト
        disaster_info: 災害情報
        analysis_result: 分析結果
        user_language: ユーザーの言語
        
    Returns:
        詳細情報を含む強化されたレスポンステキスト
    """
    # 準備に関する質問の場合は詳細を追加しない
    if analysis_result.get('time_range') == 'normal_time' or analysis_result.get('preparation_focus', False):
        return response_text
    
    # Check disaster type - if it's preparation or seasonal, don't add details
    disaster_type_from_analysis = analysis_result.get('disaster_type', '')
    if disaster_type_from_analysis in ['preparation', 'seasonal']:
        return response_text
        
    if not disaster_info.get("events"):
        return response_text
    
    main_event = disaster_info.get("most_relevant_event")
    if not main_event:
        return response_text
    
    details = []
    disaster_type = analysis_result.get('primary_disaster_type', main_event.event_type)
    
    # 内部処理は英語で統一（後で自動翻訳される）
    details.append(f"\n【{disaster_type.title()} Details】")
    
    if disaster_type == "earthquake":
        if hasattr(main_event, 'event_time') and main_event.event_time:
            details.append(f"Time: {main_event.event_time.strftime('%B %d, %Y at %H:%M')}")
        if hasattr(main_event, 'location') and main_event.location:
            details.append(f"Epicenter: {main_event.location}")
        if hasattr(main_event, 'magnitude'):
            details.append(f"Magnitude: {main_event.magnitude}")
        if hasattr(main_event, 'max_intensity'):
            details.append(f"Maximum Seismic Intensity: {main_event.max_intensity}")
        if hasattr(main_event, 'depth'):
            details.append(f"Depth: {main_event.depth}")
            
    elif disaster_type == "tsunami":
        if hasattr(main_event, 'expected_height'):
            details.append(f"Expected Height: {main_event.expected_height}")
        if hasattr(main_event, 'arrival_time'):
            details.append(f"Expected Arrival Time: {main_event.arrival_time}")
        if hasattr(main_event, 'affected_areas'):
            details.append(f"Affected Areas: {', '.join(main_event.affected_areas)}")
            
    elif disaster_type == "typhoon":
        if hasattr(main_event, 'typhoon_name'):
            details.append(f"Typhoon Name: {main_event.typhoon_name}")
        if hasattr(main_event, 'central_pressure'):
            details.append(f"Central Pressure: {main_event.central_pressure}")
        if hasattr(main_event, 'max_wind_speed'):
            details.append(f"Maximum Wind Speed: {main_event.max_wind_speed}")
                
    # 詳細情報が存在する場合のみ追加
    if len(details) > 1:  # タイトル以外に情報がある場合
        details.append("")  # 空行を追加
        return "\n".join(details) + "\n" + response_text
    
    return response_text

def _get_disaster_type_name(disaster_type: str, language: str = 'ja') -> str:
    """災害タイプの表示名を取得"""
    names = {
        "earthquake": {"ja": "地震", "en": "Earthquake", "zh": "地震", "ko": "지진"},
        "tsunami": {"ja": "津波", "en": "Tsunami", "zh": "海啸", "ko": "쓰나미"},
        "typhoon": {"ja": "台風", "en": "Typhoon", "zh": "台风", "ko": "태풍"},
        "flood": {"ja": "洪水", "en": "Flood", "zh": "洪水", "ko": "홍수"},
        "landslide": {"ja": "土砂災害", "en": "Landslide", "zh": "山体滑坡", "ko": "산사태"},
        "volcanic": {"ja": "火山", "en": "Volcanic", "zh": "火山", "ko": "화산"}
    }
    return names.get(disaster_type, {}).get(language, disaster_type.title())

def _get_localized_title(event_type: str, language: str = 'ja') -> str:
    """Get localized title based on event type and language"""
    titles = {
        "earthquake": {
            "ja": "地震警報",
            "en": "Earthquake Alert",
            "ko": "지진 경보",
            "zh": "地震警报",
            "es": "Alerta de Terremoto",
            "fr": "Alerte Séisme",
            "de": "Erdbeben-Warnung",
            "it": "Allerta Terremoto",
            "pt": "Alerta de Terremoto",
            "ru": "Предупреждение о землетрясении"
        },
        "tsunami": {
            "ja": "津波警報",
            "en": "Tsunami Warning",
            "ko": "쓰나미 경보",
            "zh": "海啸警报",
            "es": "Alerta de Tsunami",
            "fr": "Alerte Tsunami",
            "de": "Tsunami-Warnung",
            "it": "Allerta Tsunami",
            "pt": "Alerta de Tsunami",
            "ru": "Предупреждение о цунами"
        },
        "flood": {
            "ja": "洪水警報",
            "en": "Flood Alert",
            "ko": "홍수 경보",
            "zh": "洪水警报",
            "es": "Alerta de Inundación",
            "fr": "Alerte Inondation",
            "de": "Hochwasser-Warnung",
            "it": "Allerta Alluvione",
            "pt": "Alerta de Inundação",
            "ru": "Предупреждение о наводнении"
        },
        "shelter_info": {
            "ja": "避難所情報",
            "en": "Shelter Information",
            "ko": "대피소 정보",
            "zh": "避难所信息",
            "es": "Información de Refugio",
            "fr": "Informations sur les Abris",
            "de": "Schutzraum-Informationen",
            "it": "Informazioni sui Rifugi",
            "pt": "Informações de Abrigo",
            "ru": "Информация об убежищах"
        },
        "emergency_contact": {
            "ja": "緊急連絡先",
            "en": "Emergency Contacts",
            "ko": "응급 연락처",
            "zh": "紧急联系方式",
            "es": "Contactos de Emergencia",
            "fr": "Contacts d'Urgence",
            "de": "Notfallkontakte",
            "it": "Contatti di Emergenza",
            "pt": "Contatos de Emergência",
            "ru": "Экстренные контакты"
        }
    }
    return titles.get(event_type, {}).get(language, titles.get(event_type, {}).get('en', event_type))

def _get_localized_message(message_key: str, language: str = 'ja') -> str:
    """Get localized message"""
    messages = {
        "seek_shelter": {
            "ja": "安全な場所に避難してください",
            "en": "Please evacuate to a safe place",
            "ko": "안전한 곳으로 대피하세요",
            "zh": "请撤离到安全地点",
            "es": "Por favor evacúe a un lugar seguro",
            "fr": "Veuillez évacuer vers un lieu sûr",
            "de": "Bitte begeben Sie sich an einen sicheren Ort",
            "it": "Si prega di evacuare in un luogo sicuro",
            "pt": "Por favor, evacue para um local seguro",
            "ru": "Пожалуйста, эвакуируйтесь в безопасное место"
        }
    }
    return messages.get(message_key, {}).get(language, messages.get(message_key, {}).get('en', message_key))

def _get_localized_action(action_key: str, language: str = 'ja') -> str:
    """Get localized action label"""
    actions = {
        "show_shelters": {
            "ja": "避難所を表示",
            "en": "Show Shelters",
            "ko": "대피소 표시",
            "zh": "显示避难所",
            "es": "Mostrar Refugios",
            "fr": "Afficher les Abris",
            "de": "Schutzräume anzeigen",
            "it": "Mostra Rifugi",
            "pt": "Mostrar Abrigos",
            "ru": "Показать убежища"
        },
        "call_emergency": {
            "ja": "緊急通報",
            "en": "Emergency Call",
            "ko": "응급 통화",
            "zh": "紧急呼叫",
            "es": "Llamada de Emergencia",
            "fr": "Appel d'Urgence",
            "de": "Notruf",
            "it": "Chiamata di Emergenza",
            "pt": "Chamada de Emergência",
            "ru": "Экстренный вызов"
        },
        "share_info": {
            "ja": "情報を共有",
            "en": "Share Information",
            "ko": "정보 공유",
            "zh": "分享信息",
            "es": "Compartir Información",
            "fr": "Partager les Informations",
            "de": "Informationen teilen",
            "it": "Condividi Informazioni",
            "pt": "Compartilhar Informações",
            "ru": "Поделиться информацией"
        },
        "drop_cover_hold": {
            "ja": "ドロップ・カバー・ホールド",
            "en": "Drop, Cover, Hold",
            "ko": "엎드려, 가리고, 잡아라",
            "zh": "趴下，掩护，抓牢",
            "es": "Agáchate, Cúbrete, Agárrate",
            "fr": "Se Baisser, Se Couvrir, S'Accrocher",
            "de": "Ducken, Schutz suchen, Festhalten",
            "it": "Abbassati, Copriti, Tieniti",
            "pt": "Abaixe, Cubra, Segure",
            "ru": "Лечь, Укрыться, Держаться"
        },
        "evacuate_high_ground": {
            "ja": "高台に避難",
            "en": "Evacuate to High Ground",
            "ko": "고지대로 대피",
            "zh": "撤离到高地",
            "es": "Evacuar a Terreno Alto",
            "fr": "Évacuer vers les Hauteurs",
            "de": "Zu höher gelegenen Gebieten evakuieren",
            "it": "Evacuare verso l'Alto",
            "pt": "Evacuar para Terreno Alto",
            "ru": "Эвакуироваться на возвышенность"
        }
    }
    return actions.get(action_key, {}).get(language, actions.get(action_key, {}).get('en', action_key))

def _select_tools_based_on_analysis(
    analysis: Dict[str, Any],
    state: AgentState
) -> List[str]:
    """分析結果に基づいて使用するツールを選択

    Args:
        analysis: ユーザー要求分析結果
        state: 現在のAgentState

    Returns:
        使用するツール名のリスト
    """
    tools = []

    # 常にJMAポーラーを使用
    tools.append('jma_disaster_information_poller')

    # 災害タイプに応じたツール追加（LLM分析結果に基づく）
    disaster_type = analysis.get('disaster_type', '').lower()
    if disaster_type == 'earthquake':
        tools.append('usgs_earthquake_event_lookup')
    elif disaster_type == 'tsunami':
        tools.append('ptwc_tsunami_warning_poller')
        tools.append('jma_tsunami_feed_poller')

    # 位置情報がある場合は位置ベースツールを優先
    if analysis.get('location_specific', False) and state.get('user_location'):
        tools.append('location_based_disaster_info_tool')

    # 常にWeb検索ツールを使用
    tools.append('web_search_tool')

    # 重複除去
    return list(set(tools))

async def _generate_emotional_support_response(
    emotional_context: Dict[str, Any],
    user_language: str,
    disaster_type: str
) -> str:
    """
    感情的サポートが必要な場合の専用応答生成
    
    Args:
        emotional_context: extract_emotional_context()の結果
        user_language: ユーザーの言語
        disaster_type: 災害タイプ
    
    Returns:
        共感的で支援的な応答テキスト
    """
    logger.info(f"🫂 Generating emotional support response for {emotional_context['emotional_state']}")
    
    emotional_state = emotional_context.get('emotional_state', 'anxious')
    intensity = emotional_context.get('intensity', 1)
    support_level = emotional_context.get('support_level', 'moderate')
    
    # 言語別の共感的開始フレーズ
    empathy_starters = {
        'ja': {
            'anxious': 'お気持ちとてもよくわかります。',
            'scared': 'お気持ちお察しします。',
            'worried': 'ご心配なお気持ち、よくわかります。',
            'stressed': 'お疲れさまです。大変な状況ですね。'
        },
        'en': {
            'anxious': 'I completely understand how you\'re feeling.',
            'scared': 'I can sense your fear, and that\'s completely natural.',
            'worried': 'Your worries are completely understandable.',
            'stressed': 'I can see you\'re going through a tough time.'
        }
    }
    
    # 言語別の安心感を与える中間部分
    reassurance_middle = {
        'ja': {
            'earthquake': '地震への不安は多くの方が感じている自然な感情です。まず深呼吸をして、少し落ち着きましょう。',
            'disaster': '災害について心配になるのは、とても自然なことです。あなたは一人ではありません。'
        },
        'en': {
            'earthquake': 'Fear of earthquakes is a natural response that many people share. Let\'s take a deep breath together.',
            'disaster': 'It\'s completely natural to worry about disasters. You\'re not alone in feeling this way.'
        }
    }
    
    # 言語別の励ましの終了部分
    encouragement_endings = {
        'ja': {
            'light': '私がサポートしますので、一緒に考えていきましょう。',
            'moderate': '一緒に準備していきましょう。きっと大丈夫です。',
            'strong': '私が全力でサポートします。いつでもお声かけください。',
            'crisis': '今すぐサポートが必要ですね。私がお手伝いします。安心してください。'
        },
        'en': {
            'light': 'I\'m here to support you. Let\'s work through this together.',
            'moderate': 'We\'ll prepare together step by step. You\'ve got this.',
            'strong': 'I\'m here to fully support you. Please reach out anytime.',
            'crisis': 'You need support right now, and I\'m here to help. You\'re safe.'
        }
    }
    
    # 実用的なアドバイス部分
    practical_advice = {
        'ja': {
            'earthquake': '不安を和らげるために、以下のことから始めてみませんか：\\n\\n• **今できる準備**: 防災グッズの確認、家具の固定など\\n• **正しい知識**: 地震発生時の行動を知っておく\\n• **つながり**: 家族や友人と防災について話し合う',
            'disaster': '不安な時こそ、できることから一つずつ始めていきましょう：\\n\\n• 今の安全を確認する\\n• 必要な情報を整理する\\n• 具体的な準備を少しずつ進める'
        },
        'en': {
            'earthquake': 'Here are some steps that can help you feel more prepared:\\n\\n• **Take control**: Check your emergency supplies and secure furniture\\n• **Knowledge is power**: Learn about earthquake safety\\n• **Connect**: Talk with family and friends about preparedness',
            'disaster': 'When we\'re anxious, taking small steps can help:\\n\\n• Check your current safety\\n• Gather reliable information\\n• Make preparations step by step'
        }
    }
    
    # 言語とサポートレベルに応じて応答を構築
    lang_key = user_language if user_language in empathy_starters else 'en'
    disaster_key = disaster_type if disaster_type in reassurance_middle[lang_key] else 'disaster'
    
    # 共感的開始
    starter = empathy_starters[lang_key].get(emotional_state, empathy_starters[lang_key]['anxious'])
    
    # 安心感を与える中間部
    middle = reassurance_middle[lang_key][disaster_key]
    
    # 実用的アドバイス
    advice = practical_advice[lang_key][disaster_key]
    
    # 励ましの終了
    ending = encouragement_endings[lang_key][support_level]
    
    # 応答を組み立て
    response = f"{starter}\\n\\n{middle}\\n\\n{advice}\\n\\n{ending}"
    
    # Generated emotional support response
    
    return response

def _get_suggested_actions(event: RelevantDisasterEvent, language: str = 'ja') -> List[Dict[str, Any]]:
    """イベントタイプに応じた推奨アクションを取得"""
    actions = []

    # 基本アクション
    actions.append({
        "type": "share",
        "label": _get_localized_action("share_info", language),
        "data": {"message": f"{event.event_type} alert: {event.location}"}
    })

    # イベント固有アクション
    if event.event_type == "earthquake":
        actions.append({
            "type": "instruction",
            "label": _get_localized_action("drop_cover_hold", language),
            "data": {"steps": ["drop", "cover", "hold"]}
        })
    elif event.event_type == "tsunami":
        actions.append({
            "type": "navigate",
            "label": _get_localized_action("evacuate_high_ground", language),
            "data": {"direction": "higher_ground"}
        })

    return actions

async def _generate_disaster_type_response(disaster_type: str, user_language: str) -> str:
    """Generate a response for specific disaster type when no current information is found."""
    llm = get_shared_llm()
    from langchain_core.messages import HumanMessage
    
    language_names = {
        'ja': 'Japanese',
        'en': 'English',
        'ko': 'Korean',
        'zh': 'Chinese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian'
    }
    target_language_name = language_names.get(user_language, 'Japanese')
    
    prompts = {
        'tsunami': TSUNAMI_NO_INFO_PROMPT,
        'typhoon': TYPHOON_NO_INFO_PROMPT,
        'landslide': LANDSLIDE_NO_INFO_PROMPT
    }
    
    prompt = prompts.get(disaster_type, TSUNAMI_NO_INFO_PROMPT)
    
    try:
        # 統一的なLLM呼び出しを使用
        from ..core.llm_singleton import ainvoke_llm
        
        response = await ainvoke_llm(
            prompt=prompt,
            task_type="response_generation",
            temperature=0.7,
            max_tokens=1024
        )
        return response.content.strip() if hasattr(response, 'content') else str(response).strip()
    except Exception as e:
        logger.error(f"Failed to generate disaster type response: {e}")
        # Fallback to English if generation fails
        fallbacks = {
            'tsunami': "No tsunami warnings or advisories are currently in effect. Please check the JMA website for the latest information.",
            'typhoon': "No special typhoon information is currently available. Please check the JMA website for the latest weather information.",
            'landslide': "No landslide warnings are currently in effect. During heavy rain, stay away from cliffs and steep slopes."
        }
        return fallbacks.get(disaster_type, "No relevant disaster information was found.")

async def _generate_no_info_response(user_language: str) -> str:
    """Generate a general no information response in user's language."""
    llm = get_shared_llm()
    from langchain_core.messages import HumanMessage
    
    language_names = {
        'ja': 'Japanese',
        'en': 'English',
        'ko': 'Korean', 
        'zh': 'Chinese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian'
    }
    target_language_name = language_names.get(user_language, 'Japanese')
    
    prompt = NO_INFORMATION_FOUND_RESPONSE_PROMPT
    
    try:
        # 統一的なLLM呼び出しを使用
        from ..core.llm_singleton import ainvoke_llm
        
        response = await ainvoke_llm(
            prompt=prompt,
            task_type="response_generation",
            temperature=0.7,
            max_tokens=1024
        )
        return response.content.strip() if hasattr(response, 'content') else str(response).strip()
    except Exception as e:
        logger.error(f"Failed to generate no info response: {e}")
        return "No relevant disaster information was found. Please pay attention to safety information."

async def _generate_error_response(user_language: str) -> str:
    """Generate an error response in user's language."""
    try:
        llm = get_shared_llm()
        from langchain_core.messages import HumanMessage
        
        language_names = {
            'ja': 'Japanese',
            'en': 'English',
            'ko': 'Korean',
            'zh': 'Chinese',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian'
        }
        target_language_name = language_names.get(user_language, 'Japanese')
        
        prompt = ERROR_RESPONSE_PROMPT
        
        # 統一的なLLM呼び出しを使用
        from ..core.llm_singleton import ainvoke_llm
        
        response = await ainvoke_llm(
            prompt=prompt,
            task_type="response_generation",
            temperature=0.7,
            max_tokens=1024
        )
        return response.content.strip() if hasattr(response, 'content') else str(response).strip()
    except:
        # If even error generation fails, return simple message
        return "Unable to generate response."

async def _generate_disaster_preparation_response(user_input: str, user_language: str) -> str:
    """防災準備専用の個別化された応答を生成"""
    from ..core.llm_singleton import get_shared_llm
    
    # ユーザーの具体的な状況を分析
    context_analysis = ""
    user_input_lower = user_input.lower()
    
    # LLMを使って家族構成や住環境を分析
    llm = get_shared_llm()
    
    context_prompt = CONTEXT_ANALYSIS_PROMPT.format(
        user_input=user_input
    )
    
    try:
        context_response = await llm.agenerate([context_prompt])
        context_modifier = context_response.generations[0][0].text.strip()
        context_analysis += context_modifier
    except Exception as e:
        logger.warning(f"Failed to analyze context: {e}")
        context_analysis += "general"
    
    # LLMを使って個別化された応答を生成
    llm = get_shared_llm()
    
    prompt = PERSONALIZED_DISASTER_PREPARATION_PROMPT.format(
        user_input=user_input,
        context_analysis=context_analysis
    )
    
    try:
        from langchain_core.messages import HumanMessage
        # 統一的なLLM呼び出しを使用
        from ..core.llm_singleton import ainvoke_llm
        
        response = await ainvoke_llm(
            prompt=prompt,
            task_type="response_generation",
            temperature=0.7,
            max_tokens=1024
        )
        
        if hasattr(response, 'content'):
            return str(response.content)
        else:
            return str(response)
    except Exception as e:
        logger.error(f"Failed to generate disaster preparation response: {e}")
        # 内部処理は英語で統一
        return "Thank you for your disaster preparation question. While I couldn't generate personalized advice, I recommend preparing basic emergency supplies (water, food, flashlight, radio, first aid kit, etc.)."

async def _is_news_query_semantic(user_input: str) -> bool:
    """真のLLMベースのニュース関連クエリ検出"""
    try:
        from ..core.llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import NEWS_QUERY_DETECTION_PROMPT
        
        prompt = NEWS_QUERY_DETECTION_PROMPT.format(user_input=user_input[:200])
        
        result = await ainvoke_llm(prompt, task_type="content_analysis", temperature=0.1, max_tokens=10)
        return result.strip().lower() == "true"
    except:
        # エラー時はニュースクエリではないと判定
        return False
