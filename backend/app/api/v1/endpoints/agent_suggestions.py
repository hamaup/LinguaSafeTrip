# app/api/v1/endpoints/agent_suggestions.py (新規作成例)
from fastapi import APIRouter, Depends, HTTPException, status, Request
# from pydantic import BaseModel, Field # ローカル定義を削除するためコメントアウト
from typing import List, Dict, Any, Optional # List, Dict, Any, Optional はスキーマインポートでカバーされるか確認
import logging
# Depends, HTTPException はPOSTエンドポイントで使用するためインポート
# from fastapi import Depends, HTTPException # 重複インポートなので削除
# from pydantic import BaseModel, Field # ローカル定義を削除するためコメントアウト

# 依存関係のインポート
from app.agents.safety_beacon_agent.proactive_suggester import invoke_proactive_agent
# 正しいスキーマをインポート
from app.schemas.agent.suggestions import ProactiveSuggestionContext, SuggestionItem, ProactiveSuggestionResponse
from app.schemas.unified_event import UnifiedEventData # UnifiedEventData をインポート
from app.services.event_filter_service import filter_events_by_location # イベントフィルタリング関数
from app.db.firestore_client import get_db # Firestoreクライアント
from google.cloud.firestore_v1 import FieldFilter
from datetime import datetime, timedelta, timezone # 日時操作
from app.services.device_service import get_device_by_id
# Removed unused user_crud import
from app.tools.jma_poller_tool import get_current_disaster_context

logger = logging.getLogger(__name__)
router = APIRouter()

async def classify_suggestions_with_llm(suggestions: List[SuggestionItem], language_code: str) -> Optional[Dict[str, Any]]:
    """
    LLMを使用して提案リストを自然言語で分類し、災害関連度と深刻度を判定
    """
    try:
        from app.agents.safety_beacon_agent.core.llm_singleton import get_llm_client
        
        llm = get_llm_client()
        
        # 提案内容をテキストとして整理
        suggestions_text = []
        for i, suggestion in enumerate(suggestions, 1):
            suggestion_info = f"{i}. Type: {suggestion.type}\n   Content: {suggestion.content}"
            if suggestion.action_query:
                suggestion_info += f"\n   Action: {suggestion.action_query}"
            suggestions_text.append(suggestion_info)
        
        suggestions_summary = "\n\n".join(suggestions_text)
        
        prompt = f"""You are analyzing proactive suggestions from a disaster safety app to classify their disaster-relatedness and severity.

Language for analysis: {language_code}

Suggestions to analyze:
{suggestions_summary}

Your task:
1. Analyze ALL suggestions as a group and determine if ANY of them are disaster-related
2. If disaster-related, assess the HIGHEST severity level among all suggestions
3. Extract any disaster event IDs mentioned in ANY of the suggestions

Classification criteria:
- Disaster-related: Suggestions about emergency response, disaster preparation, evacuation, safety alerts, emergency contacts, shelter information, disaster news, etc.
- Non disaster-related: General app features, welcome messages, settings, unrelated recommendations

Severity levels (in order of urgency):
- "緊急" (Critical): Immediate danger, active disaster, emergency evacuation
- "高い" (High): Warning alerts, disaster preparation during alert
- "中程度" (Medium): General disaster preparation, safety reminders
- "低い" (Low): Educational content, routine safety tips

Return a SINGLE JSON object that represents the OVERALL classification of ALL suggestions combined:
{{
    "is_disaster_related": boolean,
    "disaster_severity": "緊急|高い|中程度|低い" or null,
    "disaster_event_ids": [list of event IDs found],
    "reasoning": "brief explanation of classification"
}}

IMPORTANT: 
- Return ONE JSON object, NOT an array
- Do not analyze suggestions individually
- Do not include any text before or after the JSON
- Return ONLY the JSON object"""

        response = await llm.ainvoke(prompt)
        
        # デバッグ: レスポンスの型と内容をログ出力
        # レスポンスの型を確認してテキストを抽出
        if hasattr(response, 'content'):
            response_text = response.content
        elif isinstance(response, list) and len(response) > 0:
            # リスト形式の場合、最初の要素を使用
            first_item = response[0]
            if hasattr(first_item, 'content'):
                response_text = first_item.content
            else:
                response_text = str(first_item)
        else:
            response_text = str(response)
            
        # JSONをパース
        import json
        cleaned_response = response_text.strip()
        # Remove code block markers if present
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Extract JSON if there's extra text
        import re
        json_match = re.search(r'\{[^{}]*\}', cleaned_response, re.DOTALL)
        if json_match:
            cleaned_response = json_match.group(0)
        
        classification = json.loads(cleaned_response)
        
        # 分類結果の型チェック
        if isinstance(classification, dict):
            logger.info(f"LLM suggestion classification: {classification.get('reasoning', 'No reasoning provided')}")
            return classification
        else:
            logger.warning(f"Unexpected classification format: {type(classification)}")
            return None
        
    except Exception as e:
        logger.error(f"Failed to classify suggestions with LLM: {e}")
        return None

# Pydanticモデル定義は schemas からインポートするため削除

# --- ★ デバッグ用ヘルスチェックエンドポイント (コメントアウト) ---
# @router.get("/api/v1/agent/health", status_code=status.HTTP_200_OK, tags=["Agent Health"])
# async def agent_health_check():
#     """シンプルなヘルスチェックエンドポイント"""
#     logger.info("Agent suggestions router health check endpoint hit.")
#     return {"status": "OK", "message": "Agent suggestions router is active"}
# ---------------------------------------------

# --- POSTエンドポイント (invoke_proactive_agent呼び出しを有効化) ---
@router.post(
    "/agent/proactive-suggestions", # 相対パスに戻す
    response_model=ProactiveSuggestionResponse,
    summary="Get proactive suggestions based on current context (Deprecated - Use /sync/heartbeat instead)",
    tags=["Agent"],
    deprecated=True
)
async def get_proactive_suggestions(
    context: ProactiveSuggestionContext,
    request: Request,
):
    return await _handle_proactive_suggestions(context, request)

# レガシー互換性エンドポイントは削除済み
# 使用するエンドポイント: POST /api/v1/sync/heartbeat

# 共通処理関数
async def _handle_proactive_suggestions(
    context: ProactiveSuggestionContext,
    request: Request,
):
    # リクエストトレース情報をログに記録
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"API Request from IP: {client_ip}")
    log_message_device_id = f"Received proactive suggestion request for device: {context.device_id}"
    logger.critical(f"--- CRITICAL LOG: Device ID: {context.device_id} ---") # CRITICALレベルで目立たせる
    logger.info(f"Request received at: {datetime.now(timezone.utc).isoformat()}")

    # current_situation の値を明確にログ出力
    log_message_situation = f"Received current_situation: {context.current_situation}"
    logger.critical(f"--- CRITICAL LOG: {log_message_situation} ---")
    # is_emergency_mode の値をログ出力
    log_message_emergency = f"Received is_emergency_mode: {context.is_emergency_mode}"
    logger.critical(f"--- CRITICAL LOG: Emergency Mode: {context.is_emergency_mode} ---")
    if context.latest_alert_summary:
        alert_summary_json = context.latest_alert_summary.model_dump_json(indent=2)
        log_message_alert = f"Received latest_alert_summary (type: {type(context.latest_alert_summary)}): {alert_summary_json}"
        logger.critical(f"--- CRITICAL LOG: Latest Alert Summary: {alert_summary_json} ---")
    else:
        log_message_alert_none = "Received latest_alert_summary is None."
        logger.critical(f"--- CRITICAL LOG: {log_message_alert_none} ---")
    full_context_json = context.model_dump_json(indent=2)
    log_message_full_context = f"Full ProactiveSuggestionContext: {full_context_json}"
    logger.info(f"--- INFO LOG: Full Context: {full_context_json} ---") # INFOレベルに戻す（CRITICALは多用しない）
    # --- Firestoreから正規化済みイベントを取得し、フィルタリングしてコンテキストに追加 ---
    try:
        db = get_db()
        # unified_disaster_events コレクションから直近のイベントを取得 (例: 過去24時間)
        # このコレクション名は event_normalizer.py での保存先と合わせる
        events_ref = db.collection("unified_disaster_events")

        # Firestoreのタイムスタンプ比較のために、datetimeオブジェクトを準備
        # ここでは例として過去24時間のイベントを取得
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)

        # 'fetched_at' フィールドで降順ソートし、新しいものから取得、その後時間でフィルタリング
        # query = events_ref.order_by("fetched_at", direction="DESCENDING").where("fetched_at", ">=", time_threshold).limit(50) # 例: 最大50件
        # Firestoreのwhere句は >= と orderBy の組み合わせに注意が必要な場合がある。
        # fetched_at はISO文字列で保存されている想定なので、文字列比較になる。
        # より堅牢なのは、FirestoreのTimestamp型で保存すること。
        # 今回は event_normalizer.py でISO文字列で保存する想定なので、文字列で比較。
        query = events_ref.where(filter=FieldFilter("fetched_at", ">=", time_threshold.isoformat())).limit(50) # limitは適宜調整

        # query.stream() は同期ジェネレータのため async for で直接使えない
        # query.get() は同期メソッドのため、asyncio.to_thread を使って非同期に実行する
        import asyncio # asyncio をインポート
        docs_snapshot = await asyncio.to_thread(query.get)

        all_recent_unified_events: List[UnifiedEventData] = []
        for doc in docs_snapshot: # 取得したスナップショットをループ処理
            try:
                event_dict = doc.to_dict()
                # Firestoreから読み込んだreported_at, fetched_atは文字列なのでdatetimeに変換
                if event_dict.get("reported_at"):
                    event_dict["reported_at"] = datetime.fromisoformat(event_dict["reported_at"])
                if event_dict.get("fetched_at"):
                    event_dict["fetched_at"] = datetime.fromisoformat(event_dict["fetched_at"])
                all_recent_unified_events.append(UnifiedEventData(**event_dict))
            except Exception as parse_e:
                logger.error(f"Error parsing UnifiedEventData from Firestore doc {doc.id}: {parse_e}", exc_info=True)

        logger.info(f"Fetched {len(all_recent_unified_events)} recent unified events from Firestore.")

        if context.current_location:
            # current_area_codes がリクエストで提供されていればそれを使用
            # なければ、current_location から逆ジオコーディングで取得する処理が必要 (今回は省略し、Noneのまま)
            target_codes = context.current_area_codes

            filtered_events = filter_events_by_location(
                events=all_recent_unified_events,
                current_location=context.current_location,
                target_area_codes=target_codes
                # radius_km は event_filter.py のデフォルト値を使用
            )
            context.recent_normalized_events = filtered_events
            logger.info(f"Filtered down to {len(filtered_events)} relevant events for context.")
        else:
            # 現在地がない場合はフィルタリングせず、取得したイベントをそのまま利用 (または空にする)
            # ここでは、フィルタリングなしで全件渡すか、あるいは提案の質を考慮して渡さないか検討
            # 今回は、現在地がない場合は normalized_events は None のままにする
            logger.warning("Current location not provided in context, skipping event filtering for recent_normalized_events.")
            context.recent_normalized_events = None # または all_recent_unified_events をそのまま入れるか

    except Exception as db_e:
        logger.error(f"Error fetching or filtering unified events from Firestore: {db_e}", exc_info=True)
        # エラーが発生しても、recent_normalized_events は None のまま処理を続行
        context.recent_normalized_events = None
    # --- ここまでイベント取得・フィルタリング処理 ---

    # --- チャット履歴を取得して言語検出用に設定 ---
    try:
        if not context.suggestion_history_summary:
            # Firestoreからチャット履歴を取得
            db = get_db()
            chat_history_ref = db.collection("chat_sessions").where(filter=FieldFilter("device_id", "==", context.device_id))
            
            # 最新のチャット履歴を取得（最大10件）
            import asyncio
            chat_docs = await asyncio.to_thread(chat_history_ref.order_by("created_at", direction="DESCENDING").limit(10).get)
            
            recent_user_inputs = []
            for doc in chat_docs:
                try:
                    chat_data = doc.to_dict()
                    # チャット履歴からユーザー入力を抽出
                    if chat_data.get("messages"):
                        for msg in reversed(chat_data["messages"]):  # 最新から検索
                            if msg.get("role") == "human" and msg.get("content"):
                                recent_user_inputs.append(msg["content"])
                                if len(recent_user_inputs) >= 3:  # 最新3件で十分
                                    break
                        if len(recent_user_inputs) >= 3:
                            break
                except Exception as parse_e:
                    logger.error(f"Error parsing chat history from doc {doc.id}: {parse_e}")
            
            if recent_user_inputs:
                # 疑似的なsuggestion_history_summaryを作成
                from types import SimpleNamespace
                fake_history = []
                for user_input in recent_user_inputs:
                    fake_history.append(SimpleNamespace(content=user_input, user_input=user_input))
                context.suggestion_history_summary = fake_history
                logger.info(f"Retrieved {len(recent_user_inputs)} recent user inputs from chat history for language detection")
            else:
                logger.info("No recent chat history found for language detection")
    
    except Exception as history_e:
        logger.error(f"Error retrieving chat history for language detection: {history_e}")
        # エラーが発生してもプロアクティブ提案処理は続行
    # --- ここまでチャット履歴取得処理 ---

    try:
        # ページネーション処理: limitが指定されている場合は適用
        if context.limit:
            logger.info(f"Applying limit parameter: {context.limit}")

        # 差分更新処理: last_suggestion_timestampが指定されている場合は適用
        if context.last_suggestion_timestamp:
            logger.info(f"Filtering suggestions newer than: {context.last_suggestion_timestamp}")

        # 新しいニュース取得チェック
        from app.services.adaptive_news_collector import adaptive_news_collector
        new_news_info = adaptive_news_collector.get_new_news_info()
        
        # invoke_proactive_agent を呼び出し、結果を取得 (List[SuggestionItem])
        suggestions_list_items = await invoke_proactive_agent(context)
        
        # 新しいニュースがある場合、ニュース関連の提案を追加
        if new_news_info and context.current_situation == "normal":
            await _add_news_based_suggestions(suggestions_list_items, new_news_info, context)

        # 提案履歴の処理を強化
        if context.suggestion_history_summary:
            logger.info(f"Processing suggestion history with {len(context.suggestion_history_summary)} items")

        # LLMを使用した自然言語分類で災害関連提案を識別
        is_disaster_related = False
        disaster_severity = None
        disaster_event_ids = set()

        # 1. コンテキストに災害イベントがあるかチェック
        if context.recent_normalized_events:
            is_disaster_related = True
            disaster_event_ids.update(e.event_id for e in context.recent_normalized_events if e.event_id)

            # 深刻度計算: イベントの深刻度を考慮
            event_severities = []
            for event in context.recent_normalized_events:
                if hasattr(event, 'severity_level'):
                    event_severities.append(event.severity_level)
                if hasattr(event, 'action_data') and event.action_data and 'severity' in event.action_data:
                    event_severities.append(event.action_data['severity'])

            if event_severities:
                severity_order = ["緊急", "高い", "中程度", "低い"]
                disaster_severity = min(
                    event_severities,
                    key=lambda x: severity_order.index(x) if x in severity_order else len(severity_order)
                )

        # 2. LLMによる自然言語分類で災害関連提案をチェック
        if suggestions_list_items:
            disaster_classification = await classify_suggestions_with_llm(suggestions_list_items, context.language_code)
            
            if disaster_classification:
                is_disaster_related = disaster_classification.get("is_disaster_related", False)
                llm_severity = disaster_classification.get("disaster_severity")
                llm_event_ids = disaster_classification.get("disaster_event_ids", [])
                
                # LLMから取得した情報をマージ
                if llm_severity:
                    severity_order = ["緊急", "高い", "中程度", "低い"]
                    if disaster_severity is None or (llm_severity in severity_order and 
                        (disaster_severity not in severity_order or 
                         severity_order.index(llm_severity) < severity_order.index(disaster_severity))):
                        disaster_severity = llm_severity
                
                disaster_event_ids.update(llm_event_ids)

        # setをlistに変換
        disaster_event_ids = list(disaster_event_ids)

        # Calculate next check time based on context
        next_check_minutes = 60  # Default
        if suggestions_list_items:
            # In disaster mode, check more frequently
            if context.current_situation == "alert_active":
                next_check_minutes = 15
            else:
                next_check_minutes = 30
        
        next_check_after = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        next_check_after = next_check_after.replace(
            minute=(next_check_after.minute + next_check_minutes) % 60
        )
        if (next_check_after.minute < datetime.now(timezone.utc).minute):
            next_check_after = next_check_after + timedelta(hours=1)
        
        # ProactiveSuggestionResponse形式で返す
        response = {
            "suggestions": suggestions_list_items,
            "is_disaster_related": is_disaster_related,
            "disaster_severity": disaster_severity,
            "disaster_event_ids": disaster_event_ids,
            "has_more_items": False,  # 初期値はFalse、実際の値はinvoke_proactive_agentで設定
            "next_check_after": next_check_after
        }

        # ページネーション情報をログに記録
        logger.info(f"Returning {len(response['suggestions'])} suggestions (has_more_items: {response['has_more_items']})")
        return response
    except Exception as e:
        logger.error(f"Error generating proactive suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")
# ---------------------------------------------------------

# --- デバイス単位のエンドポイントは統合ハートビートAPIで置き換え ---
# 削除済み: /agent/proactive-suggestions/device/{device_id}
# 新しいエンドポイントを使用: POST /api/v1/sync/heartbeat

# --- 提案承認エンドポイントは統合ハートビートAPIで置き換え ---
# 削除済み: POST /agent/proactive-suggestions/{suggestion_id}/acknowledge
# 理由: 提案承認はハートビートAPIのclient_context.acknowledged_suggestionsで管理
# フロントエンドは承認済みIDをハートビート送信時に含めることで同じ機能を実現

async def _add_news_based_suggestions(suggestions_list: List, new_news_info: Dict[str, Any], context):
        """新しいニュースに基づく提案を追加"""
        try:
            from app.schemas.agent.suggestions import SuggestionItem
            from datetime import datetime
            import uuid
            
            new_articles_count = new_news_info.get("new_articles_count", 0)
            latest_articles = new_news_info.get("latest_articles", [])
            
            if new_articles_count > 0 and latest_articles:
                # ニュース関連の提案を生成
                # LLMでアプリ指定言語の災害ニュース提案を生成
                from app.services.proactive_suggester import generate_disaster_news_content_with_llm
                
                news_content_llm = await generate_disaster_news_content_with_llm(
                    context.language_code, new_articles_count, latest_articles
                )
                
                news_suggestion = SuggestionItem(
                    type="disaster_news",
                    content=news_content_llm["content"],
                    action_data={
                        "news_articles_count": new_articles_count,
                        "latest_update": new_news_info.get("last_update_time"),
                        "news_trigger": True
                    },
                    suggestion_id=str(uuid.uuid4()),
                    action_query=news_content_llm["action_query"],
                    action_display_text=news_content_llm["action_display_text"],
                    created_at=datetime.now()
                )
                
                # リストの先頭に追加（優先表示）
                suggestions_list.insert(0, news_suggestion)
                logger.info(f"💡 Added news-based suggestion: {new_articles_count} new articles")
                
        except Exception as e:
            logger.error(f"Error adding news-based suggestions: {e}")
            # エラーが発生しても既存の提案は維持
