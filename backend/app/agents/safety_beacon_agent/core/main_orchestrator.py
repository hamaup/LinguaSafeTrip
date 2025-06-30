# backend/app/agents/safety_beacon_agent/main_orchestrator.py
import logging
import os
import uuid
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from functools import lru_cache
from app.schemas.agent import AgentResponse
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
import asyncio

from langgraph.graph import END # LangGraphの終了状態をインポート

# LangChain Core & Google & Firestore
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, trim_messages
from langchain_google_firestore import FirestoreChatMessageHistory # history_manager経由で利用

# このパッケージ内のモジュール
from ..managers.disaster_context_manager import update_context # update_contextをインポート
from ..managers.user_state_manager import get_user_disaster_state, update_user_disaster_state
from app.prompts.disaster_prompts import get_disaster_prompt, get_proactive_prompt
# Translation tool is imported inside functions to avoid circular import
# from .emergency_integration import check_and_handle_emergency  # 削除：緊急検知統合
from app.config import app_settings
from app.config.timeout_settings import TimeoutSettings
from .llm_singleton import get_llm_client # LLMクライアント取得
from app.prompts.prompts import SYSTEM_PROMPT_TEXT # メインのシステムプロンプト
from ..tool_definitions import tools # ツールリスト
from ..managers.history_manager import get_chat_message_history # チャット履歴管理
from ..managers.integrated_memory_manager import IntegratedMemoryManager # 統合メモリ管理
from ..callbacks import SmsToolResultCallbackHandler # SMSツール用コールバック
from .graph_builder import create_unified_graph as create_safety_beacon_agent_graph # 統合graph使用
# Import removed - analysis now done in LangGraph
# from ..handlers.off_topic_handler import ImprovedOffTopicHandler

# ロガー初期化
logger = logging.getLogger(__name__)

# アプリケーションスキーマ
from app.schemas.agent import AgentStateModel
from app.schemas.agent.suggestions import SuggestionItem, SuggestionCard
# Note: AgentUserLocation, AgentUserProfile removed as they were not found in codebase
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from app.schemas.chat_schemas import ChatRequest

# --- LangGraphアプリケーションの初期化（LRUキャッシュ化） ---
@lru_cache(maxsize=1)
def get_compiled_graph():
    """グラフを一度だけコンパイルしてLRUキャッシュ（メモリ効率最適化）"""
    try:
        # キャッシュされたLLMクライアントを使用
        llm = get_llm_client(task_type="response_generation")
        compiled_graph = create_safety_beacon_agent_graph(llm)
        logger.info("SafetyBeacon LangGraph compiled and cached with LRU")
        return compiled_graph
    except Exception as e_graph_compile:
        logger.error(f"Failed to compile SafetyBeacon LangGraph: {e_graph_compile}", exc_info=True)
        raise RuntimeError(f"Graph compilation failed: {e_graph_compile}")

def clear_graph_cache():
    """グラフキャッシュをクリア（テスト用）"""
    get_compiled_graph.cache_clear()
    logger.info("Graph cache cleared")

async def run_agent_interaction(request: ChatRequest) -> AgentResponse:
    """
    統合メモリマネージャーを使用したLangGraphベースのエージェント実行
    """
    start_time_utc = datetime.now(timezone.utc)
    device_identifier = request.device_id

    # Starting agent interaction with integrated memory
    logger.info(f"Running agent interaction for device: {device_identifier}")

    if not app_settings.gcp_project_id:
         logger.error("GCP_PROJECT_ID is not set. Cannot proceed.")
         return AgentResponse(
             response_text="システム設定エラーにより応答できません。",
             session_id=request.session_id or "error",
             current_task_type="error",
             is_emergency_response=False
         )

    compiled_agent_graph = get_compiled_graph()
    if not compiled_agent_graph:
        logger.error("Agent graph is not compiled. Cannot process request.")
        return AgentResponse(
             response_text="エージェントの初期化に失敗しました。しばらくしてから再度お試しください。",
             session_id=request.session_id or "error", 
             current_task_type="error",
             is_emergency_response=False
         )

    # --- 統合メモリマネージャー初期化 ---
    memory_manager = IntegratedMemoryManager(compiled_agent_graph)
    
    # スレッドID生成とセッションID決定
    thread_id = memory_manager.generate_thread_id(request.session_id, device_identifier)
    session_id = memory_manager.extract_session_id(thread_id)
    
    # --- 統合履歴取得 ---
    # 初期段階の並列処理実装（2-3倍高速化）
    async def get_integrated_history():
        try:
            history = await memory_manager.sync_histories(
                thread_id, session_id, device_identifier
            )
            return history
        except Exception as e_hist:
            logger.error(f"Failed to get integrated history: {e_hist}", exc_info=True)
            return []
    
    async def parse_user_location():
        if not request.user_location:
            return None
            
        loc_data = request.user_location
        try:
            # AgentUserLocation class not found - using dict instead
            return {
                'latitude': loc_data.get('latitude'),
                'longitude': loc_data.get('longitude'),
                'accuracy': loc_data.get('accuracy'),
                'source': loc_data.get('source'),
                'last_updated': loc_data.get('timestamp') or start_time_utc.isoformat()
            }
        except Exception as e_loc_parse:
            logger.error(f"Could not parse user location data: {loc_data}. Error: {e_loc_parse}", exc_info=True)
            return None
    
    async def get_device_data():
        try:
            from app.services.device_service import get_device_by_id
            return await get_device_by_id(device_identifier)
        except Exception as e:
            logger.warning(f"デバイス状況取得失敗: {e}")
            return None
    
    # 並列実行（タイムアウト付き）
    
    async def with_timeout(coro, timeout_seconds, default=None):
        """タイムアウト付きで実行"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(f"Task timed out after {timeout_seconds}s")
            return default
    
    # 各タスクに現実的なタイムアウトを設定
    parallel_tasks = await asyncio.gather(
        with_timeout(get_integrated_history(), TimeoutSettings.HISTORY_FETCH, []),  # 履歴は5秒
        with_timeout(parse_user_location(), TimeoutSettings.LOCATION_PARSE, None),  # 位置情報は3秒
        with_timeout(get_device_data(), TimeoutSettings.DEVICE_DATA_FETCH, None),  # デバイスデータは4秒
        return_exceptions=True
    )
    
    integrated_history = parallel_tasks[0] if not isinstance(parallel_tasks[0], Exception) else []
    user_location_pydantic = parallel_tasks[1] if not isinstance(parallel_tasks[1], Exception) else None
    device_data_from_parallel = parallel_tasks[2] if not isinstance(parallel_tasks[2], Exception) else None
    
    if user_location_pydantic:
        pass
    
    # user_profile_pydantic removed - AgentUserProfile class not found in codebase
    user_profile_pydantic = None

    # 入力検証
    if not request.user_input or not isinstance(request.user_input, str):
        logger.error(f"Invalid user input: {request.user_input}")
        # エラーメッセージもユーザー言語に対応
        error_msg = "Invalid input."
        if request.user_language:
            from app.tools.translation_tool import TranslationTool
            translator = TranslationTool()
            try:
                error_msg = await translator.translate(
                    text=error_msg,
                    target_language=request.user_language,
                    source_language="en"
                )
            except:
                pass  # 翻訳失敗時は英語のまま
        # エラー時もAgentResponseを返す
        from app.schemas.common.enums import TaskType
        return AgentResponse(
            response_text=error_msg,
            current_task_type=TaskType.ERROR,
            status="error",
            is_emergency_response=False,
            session_id=session_id
        )

    # 言語コードを正規化（zh-CN -> zh_CN, zh-TW -> zh_TW など）
    def normalize_language_code(lang_code: str) -> str:
        """言語コードを正規化 - ハイフンをアンダースコアに変換"""
        # ハイフンをアンダースコアに置換
        normalized = lang_code.replace('-', '_')
        
        # 短縮形の処理
        if normalized == 'zh':
            return 'zh_CN'  # デフォルトで簡体中文
        
        # 既知の言語コードマッピング
        language_mapping = {
            'zh_CN': 'zh_CN',  # 簡体中文
            'zh_TW': 'zh_TW',  # 繁体中文
            'pt_BR': 'pt',     # ポルトガル語（ブラジル）-> pt
            'ko_KR': 'ko',     # 韓国語
            'ja_JP': 'ja',     # 日本語
            'en_US': 'en',     # 英語
            'en_GB': 'en',     # 英語
            'es_ES': 'es',     # スペイン語
            'fr_FR': 'fr',     # フランス語
            'de_DE': 'de',     # ドイツ語
            'it_IT': 'it',     # イタリア語
            'ru_RU': 'ru',     # ロシア語
        }
        
        # マッピングに存在する場合は変換、なければそのまま返す
        return language_mapping.get(normalized, normalized)
    
    # Language settings
    
    normalized_user_language = normalize_language_code(request.user_language)
    detected_language = normalize_language_code(getattr(request, 'detected_language', request.user_language))
    
    # --- キャッシュチェック ---
    # response_cache module was deleted, so we skip template checking

    
    # Analysis will be performed within LangGraph to avoid duplication
    user_input_for_processing = request.user_input
    
    # Set defaults - actual analysis will happen in LangGraph nodes
    is_disaster_mode_computed = request.is_disaster_mode
    
    # 並列処理で取得したデバイスデータを使用
    if device_data_from_parallel and hasattr(device_data_from_parallel, 'current_mode'):
        device_current_mode = device_data_from_parallel.current_mode
        # デバイスが緊急モードの場合は優先
        if device_current_mode == "emergency":
            is_disaster_mode_computed = True
        # Device mode: {device_current_mode}
    else:
        # No device data or mode information
        pass
    
    mapped_task_type = "unknown"  # Will be determined by LangGraph
    
    # Request parameters processed

    # 分析結果を使って初期状態を設定 - 多言語のまま処理
    initial_agent_state = AgentStateModel(
        device_id=device_identifier,
        session_id=session_id,
        user_input=user_input_for_processing,  # 多言語のまま処理
        current_user_input=user_input_for_processing,  # 多言語のまま処理
        messages=[HumanMessage(content=user_input_for_processing)],  # 多言語で処理
        chat_history=integrated_history,
        user_language=normalized_user_language,
        detected_language=detected_language,
        is_disaster_mode=is_disaster_mode_computed,  # 計算済みの災害モード
        user_location=request.user_location,  # 直接辞書形式で渡す
        user_profile=user_profile_pydantic,
        local_contact_count=request.local_contact_count if request.local_contact_count is not None else 0,
        current_datetime_utc=start_time_utc.isoformat(),
        current_task_type=mapped_task_type,  # Will be determined by LangGraph
        primary_intent="unknown",  # Will be determined by LangGraph
        external_alerts=request.external_alerts or [],  # 緊急アラート追加
        extracted_entities={"search_keywords": []},  # Will be populated by LangGraph
        disaster_relevance=0.0,  # Will be determined by LangGraph
        emotional_tone="neutral",
        required_action="none",  # Will be determined by LangGraph
        secondary_intents=[],
        final_response_text=None,
        cards_to_display_queue=[],
        requires_action_data=None,
        generated_cards_for_frontend=[],
        intermediate_results={},  # Will be populated by LangGraph
        disaster_context_evaluation={
            "needs_location": False  # Will be determined by LangGraph
        },
        chat_records=[],
        language_confidence=1.0 if request.user_language else 0.0
    )
    # 初期状態ログは削除

    # --- 2. 履歴トリミング (messagesチャネルはLangGraphが自動で管理するため、chat_history_lcをトリミング) ---
    system_prompt_approx_tokens = count_tokens_approximated(SYSTEM_PROMPT_TEXT)
    user_input_tokens = count_tokens_approximated(initial_agent_state.user_input)
    effective_max_history_tokens = app_settings.tokens.max_history_tokens - system_prompt_approx_tokens - user_input_tokens

    if effective_max_history_tokens < 0 : effective_max_history_tokens = 0
    # History token trimming: effective_max={effective_max_history_tokens}

    trimmed_history = trim_messages(
        messages=initial_agent_state.chat_history,
        max_tokens=effective_max_history_tokens,
        strategy="last",
        token_counter=lambda x: count_tokens_approximated(str(x.content if hasattr(x, 'content') else x)),
    )
    initial_agent_state.chat_history = trimmed_history
    # History trimmed: {len(integrated_history)} -> {len(trimmed_history)} messages

    # --- 3. 最適化: 事前分析済みなのでスキップ ---
    # 並列分析で既に災害コンテキストと意図は分析済み
    # テンプレート応答のチェック（高速化）


    # --- 3.5. 緊急検知 ---
    # emergency_info = await check_and_handle_emergency({
    #     "user_input": request.user_input,  # オリジナルの入力を使用
    #     "user_location": request.user_location,
    #     "external_alerts": request.external_alerts or [],
    #     "recent_alerts": []
    # })
    emergency_info = {"is_emergency": False, "emergency_level": 0, "emergency_actions": None}
    
    if emergency_info["is_emergency"]:
        logger.warning(f"🚨 Emergency detected: level={emergency_info['emergency_level']}, actions={len(emergency_info.get('emergency_actions', []))}")
    
    # --- 4. LangGraph エージェントの実行 ---
    final_state: Optional[AgentStateModel] = None
    try:
        # 状態オブジェクトの型チェックとフォールバック
        if not isinstance(initial_agent_state, (dict, AgentStateModel)):
            logger.error(
                f"Invalid initial state type: {type(initial_agent_state)}. "
                f"Content: {str(initial_agent_state)[:200]}... "
                f"Converting to dict"
            )
            initial_agent_state = initial_agent_state.dict() if hasattr(initial_agent_state, 'dict') else {}

        graph_config = {"configurable": {"thread_id": thread_id}}

        # Invoking agent graph for session: {session_id}
        
        # 分析結果から既に得られた情報を使用
        input_state = {
            # 必須フィールド
            "conversation_id": request.session_id,
            "device_id": device_identifier,  # デバイスIDを追加
            "session_id": session_id,  # セッションIDも追加
            "user_input": user_input_for_processing,  # 多言語のまま使用
            "current_user_input": user_input_for_processing,
            "chat_history": integrated_history,
            "messages": [],  # messagesフィールドの初期化
            "is_disaster_mode": is_disaster_mode_computed,  # 計算済みの値を使用
            "user_location": request.user_location,  # 位置情報を追加
            "secondary_intents": [],
            "chat_records": [],
            "current_task_type": mapped_task_type,
            "generated_cards_for_frontend": [],
            "cards_to_display_queue": [],
            "recent_alerts": request.external_alerts or [],  
            "external_alerts": request.external_alerts or [],  
            "suggested_actions": [],  # Will be determined by LangGraph
            "primary_intent": "unknown",  # Will be determined by LangGraph
            "turn_count": 0,
            "is_disaster_related": False,  # Will be determined by LangGraph
            "intent_confidence": 0.5,  # Default to 0.5 to avoid low confidence routing
            # 言語検出フィールドの初期化
            "user_language": normalized_user_language,  
            "detected_language": detected_language,  
            "language_confidence": 1.0 if request.user_language else 0.0,  
            # その他の必須フィールド
            "parallel_updates": [],
            "required_action": "none",  # Will be determined by LangGraph  
            "emotional_tone": "neutral",
            "extracted_entities": {"search_keywords": []},  # Will be populated by LangGraph
            "disaster_relevance": 0.0,  # Will be determined by LangGraph
            # Optional fields from AgentState
            "current_disaster_info": None,
            "error_message": None,
            "requires_professional_handling": False,
            # Missing fields
            "routing_decision": None,
            "last_askuser_reason": None,
            "intermediate_results": {},  # Will be populated by LangGraph
            "final_response_text": None,
            "off_topic_response": None,
            # Emergency detection fields
            "is_emergency_response": emergency_info["is_emergency"],
            "emergency_level": emergency_info["emergency_level"],
            "emergency_actions": emergency_info["emergency_actions"],
            "emergency_message": emergency_info.get("emergency_message"),
            # User app status - CRITICAL: This was missing!
            "local_contact_count": request.local_contact_count if request.local_contact_count is not None else 0
        }

        try:
            # Starting LangGraph execution
            
            # Execute graph with timeout
            events = []
            start_time = asyncio.get_event_loop().time()
            
            # Create trace file
            trace_file = f"/tmp/langgraph_trace_{session_id}.log"
            with open(trace_file, "w") as f:
                f.write(f"LangGraph Execution Trace - Session: {session_id}\n")
                f.write(f"Start time: {datetime.now(timezone.utc)}\n")
                f.write(f"="*60 + "\n")
            
            try:
                # Try invoke instead of astream to see if it completes
                # Use invoke with timeout
                # 統合メモリ対応のconfig設定
                config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "session_id": session_id,
                        "device_id": device_identifier
                    },
                    "recursion_limit": app_settings.graph.recursion_limit,
                    "max_retries": app_settings.graph.max_retries,
                }
                
                final_state = await asyncio.wait_for(
                    compiled_agent_graph.ainvoke(
                        input_state,
                        config=config
                    ),
                    timeout=app_settings.graph.timeout
                )
                
                elapsed = asyncio.get_event_loop().time() - start_time
                # Graph execution completed
                
                with open(trace_file, "a") as f:
                    f.write(f"\nExecution completed in {elapsed:.1f}s\n")
                    f.write(f"Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'Not a dict'}\n")
                    
            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.error(f"Graph execution timeout after {elapsed:.1f} seconds")
                with open(trace_file, "a") as f:
                    f.write(f"\nTIMEOUT after {elapsed:.1f}s\n")
                raise Exception("Graph execution timeout")
            
            # LangGraph execution completed
        except Exception as e:
            logger.error(f"Error during agent graph execution: {e}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            if hasattr(e, '__cause__') and e.__cause__:
                logger.error(f"Caused by: {e.__cause__}")
            raise

        # グラフから最終状態を取得
        # LangGraphの状態を取得
        graph_final_state_snapshot = compiled_agent_graph.get_state(config=graph_config)
        if graph_final_state_snapshot and graph_final_state_snapshot.values:
            final_state_raw = graph_final_state_snapshot.values
            
            with open("/tmp/orchestrator_debug.log", "w") as f:
                f.write(f"Final state keys: {list(final_state_raw.keys())}\n")
                f.write(f"final_response_text: {final_state_raw.get('final_response_text', 'NOT FOUND')}\n")
                f.write(f"off_topic_response: {final_state_raw.get('off_topic_response', 'NOT FOUND')}\n")
                f.write(f"Full state (truncated):\n")
                for key, value in final_state_raw.items():
                    value_str = str(value)[:200] if value else "None"
                    f.write(f"  {key}: {value_str}\n")
            
            # LangGraphの状態から必要な情報を抽出
            try:
                # 最終応答テキストを取得
                final_response_text = final_state_raw.get("final_response_text", "")
                off_topic_response = final_state_raw.get("off_topic_response", "")
                
                # messagesから応答を取得（災害情報ハンドラーからの応答）
                messages = final_state_raw.get("messages", [])
                message_response = ""
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        message_response = last_message.content
                
                # 応答テキストを決定（final_response_textを優先）
                response_text = final_response_text or off_topic_response or message_response or "Unable to generate response."
                
                # 削除: 翻訳はenhance_qualityノードで実行済み
                
                # カード情報を取得（cards_to_display_queueが主要なソース）
                cards = final_state_raw.get("cards_to_display_queue", [])
                if not cards:
                    # フォールバックとしてgenerated_cards_for_frontendを確認
                    cards = final_state_raw.get("generated_cards_for_frontend", [])
                
                # Card counts: display_queue={len(final_state_raw.get('cards_to_display_queue', []))}, generated={len(final_state_raw.get('generated_cards_for_frontend', []))}, final={len(cards)}
                
                # Card validation completed
                
                # 会話情報を更新
                session_info = {
                    "turn_count": int(final_state_raw.get("turn_count", 0)),
                    "is_disaster_mode": final_state_raw.get("is_disaster_mode", False),
                    "primary_intent": str(final_state_raw.get("primary_intent", "unknown")).replace("IntentCategory.", "").lower()
                }
                
                # Response extracted successfully
                
                # デバッグ: 利用可能なキーを確認
                # 利用可能キーログは削除
                
                # 緊急時応答情報を取得
                is_emergency_response = final_state_raw.get("is_emergency_response", False)
                emergency_level = final_state_raw.get("emergency_level", None)
                emergency_actions = final_state_raw.get("emergency_actions", None)
                
                # SMS意図を検出してカードを動的生成
                primary_intent = final_state_raw.get("primary_intent", "unknown")
                extracted_entities = final_state_raw.get("extracted_entities", {})
                
                # CLAUDE.md原則: 文字列マッチングではなくLLMの意図分類結果を信頼
                # intent_routerが既に正確に分類しているため、追加の文字列チェックは不要
                is_sms_intent = (
                    primary_intent == "safety_confirmation" or
                    str(primary_intent) == "safety_confirmation"
                )
                
                # LLMベースのSMS意図検出（CLAUDE.md原則準拠）
                user_input = final_state_raw.get("user_input", "") or final_state_raw.get("current_user_input", "") or request.user_input
                has_sms_keywords = await _detect_sms_intent_with_llm(user_input)
                
                if is_sms_intent or has_sms_keywords:
                    logger.info(f"SMS intent detected: is_sms_intent={is_sms_intent}, has_sms_keywords={has_sms_keywords}")
                    # SMS確認ハンドラーを直接呼び出して requires_action と action_data を取得
                    from ..handlers.sms_confirmation_handler import handle_sms_confirmation_request
                    
                    # SMS確認ハンドラー用の状態を準備
                    sms_state = final_state_raw.copy()
                    sms_state["primary_intent"] = "safety_confirmation"  # Force SMS intent
                    sms_state["user_input"] = request.user_input  # Use original request input
                    sms_state["user_location"] = request.user_location  # Ensure location is available
                    sms_state["is_disaster_mode"] = final_state_raw.get("is_disaster_mode", False)
                    sms_state["local_contact_count"] = final_state_raw.get("local_contact_count", request.local_contact_count or 0)
                    
                    try:
                        # Pass user language for multilingual SMS support
                        user_language = request.user_language or 'ja'
                        sms_result = await handle_sms_confirmation_request(sms_state, target_language=user_language)
                        
                        logger.info(f"SMS handler result: requires_action={sms_result.get('requires_action')}")
                        # SMS結果から requires_action と action_data を抽出
                        if sms_result.get("requires_action"):
                            final_state_raw["requires_action"] = sms_result["requires_action"]
                            final_state_raw["action_data"] = sms_result["action_data"]
                            logger.info(f"Set requires_action: {final_state_raw['requires_action']}")
                            # レスポンステキストもSMSハンドラーからのものを使用
                            if sms_result.get("final_response_text"):
                                response_text = sms_result["final_response_text"]
                                final_state_raw["final_response_text"] = response_text
                                
                    except Exception as sms_error:
                        logger.error(f"Error calling SMS confirmation handler: {sms_error}", exc_info=True)
                else:
                    # SMS意図非検出ログは削除
                    pass
                
                # 緊急応答コンテンツの検出による代替手段 - LLMベースの自然言語分析
                if not is_emergency_response and response_text:
                    emergency_content_detected = await _detect_emergency_content_semantic(response_text)
                    
                    # 外部アラートの存在確認
                    has_alerts = (final_state_raw.get("recent_alerts") or 
                                final_state_raw.get("external_alerts") or 
                                request.external_alerts)
                    
                    if emergency_content_detected and has_alerts:
                        # Emergency response detected by content analysis
                        is_emergency_response = True
                        emergency_level = await _determine_emergency_level_semantic(response_text)
                        emergency_actions = ["直ちに安全を確保してください", "避難指示に従ってください"]
                
                if is_emergency_response:
                    logger.info(f"Emergency detected: level={emergency_level}")
                
                # 必要な情報を含むオブジェクトを作成
                # 緊急レベルの統合
                final_emergency_level = emergency_level or final_state_raw.get("emergency_level")
                emergency_level_int = emergency_info["emergency_level"] if emergency_info["is_emergency"] else 0
                if final_emergency_level and not emergency_info["is_emergency"]:
                    emergency_level_int = _convert_emergency_level_to_int(final_emergency_level)
                
                final_state = {
                    "final_response_text": response_text,  # 統一したフィールド名を使用
                    "cards": cards,
                    "session_info": session_info,
                    "is_emergency_response": is_emergency_response or emergency_info["is_emergency"],
                    "emergency_level": final_emergency_level or emergency_info["emergency_level"],
                    "emergency_actions": emergency_actions or emergency_info["emergency_actions"],
                    "emergency_level_int": emergency_level_int
                }
            except Exception as e_extract:
                logger.error(f"Error extracting data from graph state: {e_extract}", exc_info=True)
                final_state = None
        else:
            logger.error("Failed to obtain final state snapshot or its values from graph execution.")
            final_state = None

        if not final_state:
            logger.error("Failed to obtain or validate final_state from graph execution stream.")
            from app.schemas.common.enums import TaskType
            return AgentResponse(
                response_text="エージェント処理中にエラーが発生しました(状態取得失敗)。",
                current_task_type=TaskType.ERROR,
                status="error",
                is_emergency_response=emergency_info["is_emergency"],
                emergency_actions=emergency_info["emergency_actions"],
                debug_info={
                    "error": "Failed to obtain final state",
                    "emergency_level_int": emergency_info["emergency_level"]
                },
                session_id=session_id
            )

    except Exception as e_graph_run:
        logger.error(f"Error during agent graph execution for {session_id}: {e_graph_run}", exc_info=True)
        error_message = {
            "role": "system",
            "content": f"Agent processing error: {str(e_graph_run)}",
            "name": "error_handler"
        }
        try:
            error_message = initial_agent_state.validate_messages([error_message])[0]
        except Exception:
            error_message = {
                "role": "system",
                "content": "An error occurred during agent processing",
                "name": "error_handler"
            }
        from app.schemas.common.enums import TaskType
        return AgentResponse(
            response_text=error_message["content"],
            current_task_type=TaskType.ERROR,
            status="error",
            is_emergency_response=emergency_info["is_emergency"],
            emergency_actions=emergency_info["emergency_actions"],
            debug_info={
                "error": str(e_graph_run),
                "error_type": type(e_graph_run).__name__,
                "emergency_level_int": emergency_info["emergency_level"]
            },
            session_id=session_id
        )

    # final_stateは辞書形式のデータ
    # 最終状態データのダンプは削除

    # --- 5. 最終応答の組み立て ---
    # Handle both dict and AddableValuesDict (LangGraph output)
    if hasattr(final_state, 'get') or isinstance(final_state, dict):
        response_text_to_user = final_state.get("final_response_text", "")
        # Final response prepared: length={len(response_text_to_user)}
        # Use cards from the enhanced processing above (not directly from final_state)
        api_cards: List[Dict[str, Any]] = cards if 'cards' in locals() else final_state.get("cards_to_display_queue", [])
        # API cards: count={len(api_cards)}
    else:
        # final_stateが辞書のようなオブジェクトでない場合
        logger.warning(f"Unexpected final_state type: {type(final_state)}")
        response_text_to_user = ""
        api_cards = []
        
    if not response_text_to_user:
        response_text_to_user = "Processing completed but no message to display."
        # Using default response text
    
    # Ensure all cards are serialized to dictionaries to prevent JSON serialization errors
    serialized_api_cards = []
    for card in api_cards:
        try:
            if hasattr(card, 'model_dump'):
                # Pydantic v2 model
                serialized_api_cards.append(card.model_dump())
            elif hasattr(card, 'dict'):
                # Pydantic v1 model
                serialized_api_cards.append(card.dict())
            elif isinstance(card, dict):
                # Already a dictionary
                serialized_api_cards.append(card)
            else:
                # Try to convert to dict manually
                logger.warning(f"Unknown card type: {type(card)}, attempting manual conversion")
                card_dict = {
                    "card_id": getattr(card, 'card_id', str(id(card))),
                    "card_type": getattr(card, 'card_type', 'unknown'),
                    "title": getattr(card, 'title', 'Unknown'),
                    "items": getattr(card, 'items', [])
                }
                serialized_api_cards.append(card_dict)
        except Exception as card_error:
            logger.error(f"Failed to serialize card: {card_error}, card type: {type(card)}")
            continue
    
    api_cards = serialized_api_cards
    
    # Extract requires_action and action_data from final_state_raw (graph state)
    final_requires_action = None
    final_action_data = None
    if isinstance(final_state_raw, dict):
        final_requires_action = final_state_raw.get("requires_action")
        final_action_data = final_state_raw.get("action_data")
        
        # Debug logging for action data
        if final_requires_action:
            logger.info(f"Final requires_action: {final_requires_action}")
        if final_action_data:
            logger.info(f"Final action_data keys: {list(final_action_data.keys())}")
    
    # --- 6. 履歴の保存 ---
    # 履歴保存は統合メモリマネージャーで自動実行される

    # 緊急レベルの変換（数値に変換）
    # final_stateが辞書でない場合の対処
    if isinstance(final_state, dict):
        # final_stateに既にemergency_level_intがある場合はそれを使用
        emergency_level_int = final_state.get("emergency_level_int")
        if emergency_level_int is None:
            emergency_level_int = _convert_emergency_level_to_int(final_state.get("emergency_level"))
    else:
        logger.error(f"final_state is not a dict, it's a {type(final_state)}")
        emergency_level_int = None
    
    # AgentResponseオブジェクトを作成
    from app.schemas.common.enums import TaskType
    
    # current_task_typeの変換
    if isinstance(final_state, dict):
        task_type_str = map_intent_to_task_type(final_state.get("session_info", {}).get("primary_intent", "unknown"))
        is_emergency_response = final_state.get("is_emergency_response", False)
        emergency_actions = final_state.get("emergency_actions")
        session_info = final_state.get("session_info", {})
    else:
        # final_stateが辞書でない場合のデフォルト値
        task_type_str = "unknown"
        is_emergency_response = False
        emergency_actions = None
        session_info = {}
    
    # emergency_infoからの値も考慮
    final_is_emergency = is_emergency_response or emergency_info["is_emergency"]
    final_emergency_actions = emergency_actions or emergency_info["emergency_actions"]
    final_emergency_level_int = emergency_level_int if emergency_level_int is not None else emergency_info["emergency_level"]
    
    try:
        current_task_type = TaskType(task_type_str)
    except ValueError:
        current_task_type = TaskType.UNKNOWN
    
    # --- 統合メモリから最終履歴を取得 ---
    try:
        # データベース操作の並列処理（2倍高速化）
        async def update_firestore():
            return await memory_manager.update_firestore_with_new_message(
                session_id, device_identifier, 
                request.user_input, response_text_to_user
            )
        
        async def get_final_history():
            return await memory_manager.sync_histories(
                thread_id, session_id, device_identifier
            )
        
        # 並列実行
        _, final_integrated_history = await asyncio.gather(
            update_firestore(),
            get_final_history(),
            return_exceptions=True
        )
        
        # エラーハンドリング
        if isinstance(final_integrated_history, Exception):
            logger.error(f"Failed to get final history: {final_integrated_history}")
            final_integrated_history = []
        
        # レスポンス形式に変換
        formatted_chat_history = memory_manager.format_for_response(final_integrated_history)
        
    except Exception as e_final_hist:
        logger.error(f"Failed to get final integrated history: {e_final_hist}")
        formatted_chat_history = []

    api_response = AgentResponse(
        response_text=response_text_to_user,
        current_task_type=current_task_type,
        status="success",
        generated_cards_for_frontend=api_cards,
        requires_action=final_requires_action,
        action_data=final_action_data,
        is_emergency_response=final_is_emergency,
        emergency_level=None,  # AgentResponseではemergency_levelはEmergencyLevel enumが必要なのでNoneに
        emergency_actions=final_emergency_actions,
        chat_history=formatted_chat_history,  # 統合された履歴を含める
        turn_count=session_info.get("turn_count"),
        debug_info={
            "final_task_type": task_type_str,
            "primary_intent": str(session_info.get("primary_intent", "unknown")),
            "elapsed_time_ms": (datetime.now(timezone.utc) - start_time_utc).total_seconds() * 1000,
            "emergency_level_int": final_emergency_level_int,  # 数値はdebug_infoに含める
            "memory_manager": memory_manager.get_thread_statistics()
        },
        session_id=session_id  # 統合メモリで決定されたセッションID
    )
    
    logger.info(f"API response prepared for session: {session_id}")
    return api_response

def _convert_emergency_level_to_int(level) -> Optional[int]:
    """Convert emergency level to int for API response."""
    if level is None:
        return None
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        # String to int mapping
        level_map = {
            "normal": 0,
            "advisory": 1,
            "warning": 2,
            "critical": 3,
            "emergency": 4
        }
        return level_map.get(level.lower(), 0)
    return 0

def count_tokens_approximated(text: str) -> int:
    return len(text.split())

def map_response_type_to_task_type(response_type: str) -> str:
    """Map response_type from disaster analysis to valid TaskType."""
    response_type_mapping = {
        "educational_explanation": "disaster_related",
        "function_demonstration": "information_guide",
        "safety_status_check": "disaster_info",
        "hazard_map_display": "information_guide",
        "shelter_search": "evacuation_support",
        "information_lookup": "disaster_info",
        "guide_provision": "information_guide",
        "emergency_response": "emergency_response",
        "direct_answer": "disaster_related",
        "disaster_preparation": "disaster_preparation",  # Added mapping for disaster preparation
        # Add any other response_type values that might exist
        "general_knowledge_handler": "information_guide"  # Fallback for legacy values
    }
    
    # Return mapped value or default to "unknown" if not found
    return response_type_mapping.get(response_type, "unknown")

def map_intent_to_task_type(intent_value) -> str:
    """Map IntentCategory to TaskType string value."""
    # Convert enum to string if needed
    intent_str = str(intent_value) if hasattr(intent_value, 'value') else str(intent_value)
    
    # Map intent categories to task types
    # Support both underscore and non-underscore versions for compatibility
    intent_mapping = {
        # Basic intents
        "greeting": "greeting",
        "small_talk": "small_talk", 
        "off_topic": "off_topic",
        "unknown": "unknown",
        
        # Disaster-related intents (with multiple naming variations)
        "disaster_information": "disaster_info",
        "disaster_info_query": "disaster_info",
        "disaster_info": "disaster_info",
        
        "evacuation_support": "evacuation_support",
        "evacuation_support_request": "evacuation_support",
        "shelter_search": "evacuation_support",
        
        "emergency_help": "emergency_response",
        "emergency_help_request": "emergency_response",
        
        "disaster_preparation": "disaster_preparation",
        "disaster_preparation_guide": "disaster_preparation",
        
        "safety_confirmation": "safety_confirmation",
        "safety_confirmation_query": "safety_confirmation",
        
        "information_request": "information_guide",
        "communication_request": "communication",
    }
    
    return intent_mapping.get(intent_str, "unknown")

class SafetyBeaconOrchestrator:
    """SafetyBeaconエージェントのメインオーケストレータークラス"""

    @classmethod
    async def process_request(cls, request: ChatRequest) -> AgentResponse:
        # Processing request via SafetyBeaconOrchestrator
        
        try:
            response = await run_agent_interaction(request)
            # run_agent_interactionがAgentResponseを直接返すようになったので、そのまま返す
            if isinstance(response, AgentResponse):
                return response
            
            # 後方互換性のため、辞書の場合は変換
            return AgentResponse(
                response_text=response.get("response_text", response.get("responseText", "")),  # 両方のキーに対応
                current_task_type=response.get("debug_info", {}).get("final_task_type", "unknown"),
                requires_action=response.get("requires_action"),
                debug_info=response.get("debug_info", {}),
                generated_cards_for_frontend=response.get("generated_cards_for_frontend", []),
                # 緊急時応答フィールドを追加
                is_emergency_response=response.get("is_emergency_response", False),
                emergency_level=response.get("emergency_level"),
                emergency_actions=response.get("emergency_actions")
            )
        except Exception as e:
            logger.error(f"Error in SafetyBeaconOrchestrator: {str(e)}", exc_info=True)
            return AgentResponse(
                response_text=f"System error: {str(e)}",
                current_task_type="error",
                debug_info={
                    "error": str(e),
                    "conversation_id": getattr(request, "session_id", None)
                },
                is_emergency_response=False
            )

async def _detect_sms_intent_with_llm(user_input: str) -> bool:
    """LLMベースのSMS意図検出（CLAUDE.md原則準拠）"""
    try:
        if not user_input or len(user_input.strip()) < 5:
            return False
            
        from .llm_singleton import ainvoke_llm
        
        prompt = f"""Analyze if this user input expresses intent to send SMS/message for safety confirmation:

User input: "{user_input}"

Does this express intent to:
- Send safety confirmation to family/friends
- Contact someone about their safety status  
- Send message saying they are safe
- Notify others about their condition

Respond with only: true or false"""

        response = await ainvoke_llm(prompt, task_type="sms_intent_detection", temperature=0.1)
        return response.strip().lower() == "true"
        
    except Exception as e:
        logger.warning(f"LLM SMS intent detection failed: {e}")
        # CLAUDE.md原則: キーワードマッチングは使用しない
        # LLM判定が失敗した場合はFalseを返す（キーワードフォールバックなし）
        return False

async def _generate_dynamic_sms_cards(
    intent: str, 
    entities: dict, 
    user_language: str,
    existing_cards: list
) -> list:
    """
    SMS functionality has been removed - handled by frontend
    """
    logger.info(f"SMS intent detected but functionality removed: {intent}")
    return existing_cards

async def _detect_emergency_content_semantic(response_text: str) -> bool:
    """真のLLMベースの緊急コンテンツ検出"""
    try:
        from .llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import EMERGENCY_CONTENT_DETECTION_PROMPT
        
        prompt = EMERGENCY_CONTENT_DETECTION_PROMPT.format(response_text=response_text[:300])
        
        result = await ainvoke_llm(prompt, task_type="content_analysis", temperature=0.1, max_tokens=10)
        return result.strip().lower() == "true"
    except:
        # エラー時は安全側に倒す
        return False

async def _determine_emergency_level_semantic(response_text: str) -> str:
    """真のLLMベースの緊急レベル判定"""
    try:
        from .llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import EMERGENCY_LEVEL_ANALYSIS_PROMPT
        
        prompt = EMERGENCY_LEVEL_ANALYSIS_PROMPT.format(response_text=response_text[:300])
        
        result = await ainvoke_llm(prompt, task_type="emergency_level_analysis", temperature=0.1, max_tokens=10)
        level = result.strip().lower()
        return "critical" if level == "critical" else "warning"
    except:
        # エラー時は保守的に"warning"を返す
        return "warning"
