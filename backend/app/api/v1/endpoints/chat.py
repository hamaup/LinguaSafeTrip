from typing import List, Tuple, Optional, Dict, Any
import logging
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response
from pydantic import Field, ValidationError

from app.agents.safety_beacon_agent.managers.history_manager import ChatHistoryManager, get_chat_message_history
from app.agents.safety_beacon_agent.core.main_orchestrator import SafetyBeaconOrchestrator
from app.schemas.agent import AgentResponse, ErrorResponse
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.schemas.disaster_action_card_schemas import DisasterActionCardSchema
from app.config.timeout_config import TimeoutConfig, TimeoutType

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat")  # response_modelを一時的に削除
async def handle_chat(request: ChatRequest, response: Response):
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔵 API Request: chat/{request.session_id} - '{request.user_input[:50]}...' [{request.user_language}]")

    if not request.device_id:
        raise HTTPException(status_code=400, detail="Device ID is required")

    try:
        # Add location information if not provided in request
        if not request.user_location:
            try:
                from app.services.device_service import get_device_by_id
                device = await get_device_by_id(request.device_id)
                if device and device.current_location:
                    location_data = device.current_location
                    if isinstance(location_data, dict) and 'latitude' in location_data and 'longitude' in location_data:
                        request.user_location = {
                            "latitude": location_data['latitude'],
                            "longitude": location_data['longitude'],
                            "accuracy": location_data.get('accuracy', 0),
                            "timestamp": location_data.get('timestamp', datetime.utcnow().isoformat())
                        }
                        logger.info(f"📍 Added location to chat request: {location_data['latitude']}, {location_data['longitude']}")
            except Exception as e:
                logger.warning(f"Failed to get device location: {e}")
        
        # Add timeout to prevent hanging requests
        # Use optimized timeout from app_settings
        from app.config import app_settings
        chat_timeout = app_settings.timeouts.api_timeout  # 30秒に最適化
        agent_response: AgentResponse = await asyncio.wait_for(
            SafetyBeaconOrchestrator.process_request(request),
            timeout=chat_timeout
        )

        # 🧠 LangGraphメモリに履歴管理を完全委譲 - 手動操作は不要
        # agent_response.chat_historyにLangGraph統合履歴が含まれている
        
        # Chat history from LangGraph
        
        # カード処理の統一化
        processed_cards = []
        generated_cards = agent_response.generated_cards_for_frontend or []
        
        logger.info(f"🃏 Processing {len(generated_cards)} cards for frontend")
        
        for idx, card in enumerate(generated_cards):
            try:
                # cardが辞書でない場合の対処
                if isinstance(card, dict):
                    card_data = card
                else:
                    # オブジェクトの場合は辞書に変換
                    card_data = card.model_dump() if hasattr(card, 'model_dump') else card.dict() if hasattr(card, 'dict') else {}
                
                logger.info(f"🃏 Processing card {idx}: type={card_data.get('card_type', card_data.get('type', 'unknown'))}")
                # Log map_url and action_data if present
                if 'map_url' in card_data:
                    logger.info(f"   └─ map_url: {card_data['map_url'][:50]}...")
                if 'action_data' in card_data:
                    logger.info(f"   └─ action_data: {card_data['action_data']}")
                # Log location data for evacuation_info cards
                if card_data.get('card_type') == 'evacuation_info':
                    location = card_data.get('location', {})
                    logger.info(f"   └─ evacuation_info card: title={card_data.get('title')}")
                    logger.info(f"   └─ location: lat={location.get('latitude')}, lon={location.get('longitude')}")
                    logger.info(f"   └─ has map_url: {'map_url' in card_data}")
                processed_cards.append(card_data)
                
            except Exception as e:
                logger.error(f"❌ Failed to process card {idx}: {e}")
                continue
        
        # Return response directly with camelCase formatting to avoid validation issues
        from fastapi.responses import JSONResponse
        # current_task_typeを安全に文字列に変換
        try:
            if hasattr(agent_response.current_task_type, 'value'):
                task_type_str = agent_response.current_task_type.value
            elif agent_response.current_task_type:
                task_type_str = str(agent_response.current_task_type)
            else:
                task_type_str = "unknown"
        except Exception as e:
            logger.error(f"TaskType conversion failed: {e}")
            task_type_str = "unknown"
        
        # APIレベルでの言語強制翻訳
        response_text = agent_response.response_text or "応答が空です"
        
        # ユーザー言語が日本語以外の場合は翻訳
        if request.user_language and request.user_language != 'ja':
            try:
                from app.tools.translation_tool import translation_tool
                logger.info(f"🌐 API level translation: {request.user_language}")
                response_text = await translation_tool.translate(
                    text=response_text,
                    target_language=request.user_language,
                    source_language='ja'
                )
                logger.info(f"🌐 API translation successful")
            except Exception as e:
                logger.error(f"API level translation failed: {e}")
                # 翻訳失敗時は元のテキストを使用
        
        # レスポンスデータ構築
        response_data = {
            "sessionId": agent_response.session_id if hasattr(agent_response, 'session_id') else request.session_id,
            "responseText": response_text,
            "updatedChatHistory": agent_response.chat_history or [],
            "currentTaskType": task_type_str,
            "requiresAction": agent_response.requires_action,
            "actionData": agent_response.action_data,
            "debugInfo": agent_response.debug_info,
            "generatedCardsForFrontend": processed_cards,
            "isEmergencyResponse": agent_response.is_emergency_response,
            "emergencyLevel": agent_response.debug_info.get('emergency_level_int', 0) if agent_response.debug_info else 0,
            "emergencyActions": agent_response.emergency_actions
        }
        
        # レスポンステキストの検証
        if not response_data["responseText"] or response_data["responseText"].strip() == "":
            logger.error("❌ Empty responseText detected")
            # responseTextだけを修正し、他のフィールドは保持する
            response_data["responseText"] = "Unable to generate response."
        
        logger.info(f"🔴 API Response: {response_data['currentTaskType']} - {len(response_data.get('generatedCardsForFrontend', []))} cards")
        
        # 🔍 詳細なSMSフォーム関連ログ
        logger.info(f"🔍 Agent Response Debug:")
        logger.info(f"   └─ agent_response.requires_action: {agent_response.requires_action}")
        logger.info(f"   └─ agent_response.action_data: {agent_response.action_data is not None}")
        logger.info(f"   └─ response_data.requiresAction: {response_data.get('requiresAction')}")
        logger.info(f"   └─ response_data.actionData present: {'actionData' in response_data and response_data['actionData'] is not None}")
        
        if response_data.get('requiresAction'):
            logger.info(f"📱 SMS Form Action: {response_data['requiresAction']}")
            logger.info(f"📱 Action Data Present: {'actionData' in response_data and response_data['actionData'] is not None}")
            if response_data.get('actionData'):
                action_data = response_data['actionData']
                logger.info(f"📱 Action Data Type: {action_data.get('action_type') if isinstance(action_data, dict) else type(action_data)}")
        else:
            logger.warning(f"❌ requiresAction is None or False - SMS form will not open")
        
        # Log response size for debugging
        import json
        response_json = json.dumps(response_data, ensure_ascii=False)
        logger.info(f"📊 Response size: {len(response_json)} bytes")
        
        # Log first card details for debugging
        if response_data.get('generatedCardsForFrontend'):
            first_card = response_data['generatedCardsForFrontend'][0]
            logger.info(f"📍 First card details: type={first_card.get('card_type')}, has_map_url={'map_url' in first_card}, has_action_data={'action_data' in first_card}")
        
        return JSONResponse(content=response_data)
    except asyncio.TimeoutError:
        timeout_used = TimeoutConfig.get_timeout(TimeoutType.API_CALL, "extended")
        logger.error(f"request_timeout: Chat request timed out after {timeout_used} seconds")
        error_resp = ErrorResponse(
            error_type="timeout_error",
            error_code="TIMEOUT_ERROR",
            message="リクエストの処理がタイムアウトしました。もう一度お試しください。",
            details={"timeout_seconds": timeout_used}
        )
        raise HTTPException(
            status_code=504,
            detail=error_resp.model_dump()
        )
    except ValidationError as e:
        logger.error(f"request_validation_failed: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"chat_processing_failed: {str(e)}", exc_info=True)
        error_resp = ErrorResponse(
            error_type="internal_error",
            error_code="INTERNAL_ERROR",
            message="チャット処理中にエラーが発生しました",
            details={"original_error": str(e)}
        )
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )
