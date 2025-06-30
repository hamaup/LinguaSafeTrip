# backend/app/api/v1/endpoints/debug.py
import logging
import json
from fastapi import APIRouter, HTTPException, status, Body, Query
from pydantic import BaseModel, Field
from google.cloud.firestore_v1 import FieldFilter
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

# FCM送信ツールをインポート (P2-B02で実装想定)
# 実際のパスに合わせて調整が必要な場合があります
from app.tools.notification_tools import trigger_fcm_push
from app.schemas.agent.suggestions import ProactiveSuggestionContext, UserAppUsageSummary
from app.schemas.heartbeat import HeartbeatRequest
from app.agents.safety_beacon_agent.suggestion_generators.basic_generators import basic_generator

logger = logging.getLogger(__name__)
router = APIRouter()

class MockAlertRequest(BaseModel):
    """デバッグ用模擬アラートリクエストのスキーマ"""
    device_id: Optional[str] = Field(None, description="プッシュ通知を送信する対象のデバイスID (省略時は全デバイス)") # user_id を device_id に変更し、Optional に
    alert_type: str = Field(default="earthquake", description="アラート種別 (例: earthquake, tsunami)")
    severity: str = Field(default="Warning", description="深刻度 (例: Warning, Emergency)")
    title: str = Field(default="デバッグ用アラート", description="通知タイトル")
    description: str = Field(default="これはデバッグ目的で送信された模擬アラートです。", description="通知本文")
    # フロントエンドが期待する可能性のある追加データフィールド
    event_id: str = Field(default_factory=lambda: f"debug-{datetime.now().isoformat()}", description="一意のイベントID")
    report_datetime: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec='seconds'), description="レポート日時 (UTC)")


@router.post(
    "/force-emergency-mode-reset",
    summary="Force reset emergency mode for debugging",
    description="Forcefully resets emergency mode for the specified device ID",
    status_code=status.HTTP_200_OK,
    tags=["Debug"]
)
async def force_emergency_mode_reset(
    device_id: str = Query(..., description="Device ID to reset emergency mode")
):
    """デバッグ用: 指定デバイスの緊急モードを強制解除"""
    try:
        logger.info(f"Force emergency mode reset requested for device: {device_id}")
        
        # Firestoreから該当デバイスの災害アラート履歴を削除
        from app.db.firestore_client import get_db
        db = get_db()
        
        # デバイス関連の緊急状態をリセット
        device_emergency_ref = db.collection("device_emergency_overrides").document(device_id)
        device_emergency_ref.set({
            "force_normal_mode": True,
            "override_until": datetime.now(timezone.utc) + timedelta(minutes=5),  # 5分間強制normal
            "reset_timestamp": datetime.now(timezone.utc),
            "reset_by": "debug_api"
        })
        
        return {
            "status": "success",
            "message": f"緊急モードを強制解除しました（デバイス: {device_id}）",
            "device_id": device_id,
            "override_duration": "5分間",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset emergency mode for device {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"緊急モード解除に失敗しました: {str(e)}"
        )


@router.post(
    "/complete-app-reset",
    summary="Complete app reset for debugging",
    description="Completely resets all app data including Firebase data for the specified device",
    status_code=status.HTTP_200_OK,
    tags=["Debug"]
)
async def complete_app_reset(
    device_id: str = Query(..., description="Device ID to completely reset")
):
    """デバッグ用: 指定デバイスのアプリデータを完全リセット"""
    try:
        logger.info(f"Complete app reset requested for device: {device_id}")
        
        from app.db.firestore_client import get_db
        db = get_db()
        
        reset_operations = []
        
        # 1. デバイス提案履歴の完全削除
        try:
            device_history_ref = db.collection("device_suggestion_history").document(device_id)
            
            # サブコレクション「suggestions」のすべてのドキュメントを削除
            suggestions_collection = device_history_ref.collection("suggestions").get()
            for doc in suggestions_collection:
                doc.reference.delete()
            
            # メインドキュメントを削除
            device_history_ref.delete()
            reset_operations.append("device_suggestion_history")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete suggestion history: {e}")
        
        # 2. デバイス緊急オーバーライドの削除
        try:
            emergency_override_ref = db.collection("device_emergency_overrides").document(device_id)
            emergency_override_ref.delete()
            reset_operations.append("device_emergency_overrides")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete emergency overrides: {e}")
        
        # 3. オンボーディング進捗の削除
        try:
            onboarding_query = db.collection("onboarding_progress").where(filter=FieldFilter("device_id", "==", device_id)).get()
            deleted_count = 0
            for doc in onboarding_query:
                doc.reference.delete()
                deleted_count += 1
            if deleted_count > 0:
                reset_operations.append(f"onboarding_progress_({deleted_count}docs)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete onboarding progress: {e}")
        
        # 4. ユーザーアクション履歴の削除
        try:
            user_actions_query = db.collection("user_actions").where(filter=FieldFilter("device_id", "==", device_id)).get()
            deleted_count = 0
            for doc in user_actions_query:
                doc.reference.delete()
                deleted_count += 1
            if deleted_count > 0:
                reset_operations.append(f"user_actions_({deleted_count}docs)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete user actions: {e}")
        
        # 5. 緊急連絡先の削除（device_idに関連付けられている場合）
        try:
            emergency_contacts_query = db.collection("emergency_contacts").where(filter=FieldFilter("device_id", "==", device_id)).get()
            deleted_count = 0
            for doc in emergency_contacts_query:
                doc.reference.delete()
                deleted_count += 1
            if deleted_count > 0:
                reset_operations.append(f"emergency_contacts_({deleted_count}docs)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete emergency contacts: {e}")
        
        # 6. テストアラートの削除（デバッグモード用）
        try:
            test_alerts_query = db.collection("test_alerts").get()
            deleted_count = 0
            for doc in test_alerts_query:
                doc.reference.delete()
                deleted_count += 1
            if deleted_count > 0:
                reset_operations.append(f"test_alerts_({deleted_count}docs)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete test alerts: {e}")
        
        # 7. その他の実際に存在するコレクションをチェック
        collections_to_clean = [
            "devices",
            "users", 
            "chat_sessions"
        ]
        
        for collection_name in collections_to_clean:
            try:
                docs_query = db.collection(collection_name).where(filter=FieldFilter("device_id", "==", device_id)).get()
                deleted_count = 0
                for doc in docs_query:
                    doc.reference.delete()
                    deleted_count += 1
                if deleted_count > 0:
                    reset_operations.append(f"{collection_name}_({deleted_count}docs)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean {collection_name}: {e}")
        
        return {
            "status": "success",
            "message": f"アプリデータを完全リセットしました（デバイス: {device_id}）",
            "device_id": device_id,
            "reset_operations": reset_operations,
            "reset_count": len(reset_operations),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "next_steps": [
                "フロントエンドでローカルストレージをクリア",
                "アプリを再起動してオンボーディングを開始"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to complete app reset for device {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"アプリ完全リセットに失敗しました: {str(e)}"
        )

@router.get(
    "/interval-config",
    summary="Get current interval configuration",
    description="Shows all configured intervals for different services and modes",
    status_code=status.HTTP_200_OK,
    tags=["Debug"]
)
async def get_interval_config():
    """現在の間隔設定を取得"""
    try:
        import os
        from app.config import app_settings
        
        # テストモードかどうか
        test_mode = app_settings.is_test_mode()
        
        # 環境変数から全ての間隔設定を取得
        config = {
            "current_mode": "TEST" if test_mode else "PRODUCTION",
            "test_mode_active": test_mode,
            "intervals": {}
        }
        
        if test_mode:
            # テストモード時の間隔（秒単位）
            config["intervals"]["test_mode"] = {
                "news_collection": app_settings.test_intervals["news_collection"],
                "disaster_monitor": app_settings.test_intervals["disaster_monitor"],
                "periodic_data": app_settings.test_intervals["periodic_data"]
            }
            config["intervals"]["test_mode_minutes"] = {
                k: f"{v/60:.1f}分" for k, v in config["intervals"]["test_mode"].items()
            }
        else:
            # 本番モード時の間隔（秒単位）
            config["intervals"]["normal_mode"] = {
                "news_collection": int(os.getenv("NORMAL_NEWS_COLLECTION_INTERVAL", "3600")),
                "disaster_monitor": int(os.getenv("NORMAL_DISASTER_MONITOR_INTERVAL", "300")),
                "periodic_data": int(os.getenv("NORMAL_PERIODIC_DATA_INTERVAL", "300"))
            }
            config["intervals"]["emergency_mode"] = {
                "news_collection": int(os.getenv("EMERGENCY_NEWS_COLLECTION_INTERVAL", "900")),
                "disaster_monitor": int(os.getenv("EMERGENCY_DISASTER_MONITOR_INTERVAL", "60")),
                "periodic_data": int(os.getenv("EMERGENCY_PERIODIC_DATA_INTERVAL", "300"))
            }
            
            # 分単位表示も追加
            config["intervals"]["normal_mode_minutes"] = {
                k: f"{v/60:.0f}分" for k, v in config["intervals"]["normal_mode"].items()
            }
            config["intervals"]["emergency_mode_minutes"] = {
                k: f"{v/60:.0f}分" for k, v in config["intervals"]["emergency_mode"].items()
            }
        
        # 説明を追加
        config["descriptions"] = {
            "news_collection": "ニュース収集間隔 - 災害関連ニュースを外部APIから取得する頻度",
            "disaster_monitor": "災害監視間隔 - JMA等から災害情報を確認する頻度",
            "periodic_data": "定期データ収集間隔 - 避難所情報等の更新頻度",
            "heartbeat": "ハートビート間隔 - デバイスがサーバーと同期する頻度",
            "heartbeat_critical": "緊急時ハートビート間隔 - 重大アラート時の同期頻度",
            "suggestion_cooldown": "提案クールダウン - 同じ提案を再表示するまでの待機時間"
        }
        
        logger.info(f"Interval configuration retrieved: {config}")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get interval configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"間隔設定の取得に失敗しました: {str(e)}"
        )


@router.post(
    "/reset-suggestion-cooldowns",
    summary="Reset suggestion cooldowns for a device",
    description="Clears all suggestion cooldown history for the specified device, making all suggestions immediately available",
    status_code=status.HTTP_200_OK,
    tags=["Debug"]
)
async def reset_suggestion_cooldowns(
    device_id: str = Query(..., description="Device ID to reset suggestion cooldowns")
):
    """デバッグ用: 指定デバイスの提案クールダウンをリセット"""
    try:
        logger.info(f"Resetting suggestion cooldowns for device: {device_id}")
        
        from app.db.firestore_client import get_db
        db = get_db()
        
        # デバイスの提案履歴を削除
        device_history_ref = db.collection("device_suggestion_history").document(device_id)
        
        # サブコレクション「suggestions」のすべてのドキュメントを削除
        suggestions_collection = device_history_ref.collection("suggestions").get()
        deleted_count = 0
        for doc in suggestions_collection:
            doc.reference.delete()
            deleted_count += 1
        
        # メインドキュメントも削除
        device_history_ref.delete()
        
        logger.info(f"Successfully reset suggestion cooldowns for device {device_id}. Deleted {deleted_count} suggestion records.")
        
        return {
            "status": "success",
            "message": f"提案クールダウンをリセットしました（デバイス: {device_id}）",
            "device_id": device_id,
            "deleted_suggestions": deleted_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "すべての提案が即座に利用可能になりました"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset suggestion cooldowns for device {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"提案クールダウンのリセットに失敗しました: {str(e)}"
        )


@router.post(
    "/trigger-mock-alert",
    summary="Trigger a mock alert push notification for debugging",
    description="Sends a simulated alert via FCM push notification to the specified device ID or all devices.", # 説明を修正
    status_code=status.HTTP_202_ACCEPTED, # 非同期処理を示唆
    tags=["Debug"] # デバッグ用エンドポイントとしてタグ付け
)
async def trigger_mock_alert_endpoint(
    request: MockAlertRequest = Body(...)
):
    """
    指定されたデバイスID、または全デバイスに模擬アラートのプッシュ通知を送信します。
    """
    target_info = f"device_id: {request.device_id}" if request.device_id else "all devices"
    logger.info(f"Received request to trigger mock alert for {target_info}")
    
    # デバッグモード：テストアラートをFirestoreに記録
    try:
        from app.config import app_settings
        if app_settings.is_test_mode():
            from app.db.firestore_client import get_db
            db = get_db()
            
            # テストアラートをFirestoreに保存
            test_alert_data = {
                "event_id": request.event_id,
                "alert_type": request.alert_type,
                "severity": request.severity,
                "title": request.title,
                "description": request.description,
                "device_id": request.device_id,
                "created_at": datetime.now(timezone.utc),
                "location": "テストエリア",
                "is_test": True
            }
            
            # test_alertsコレクションに保存
            db.collection("test_alerts").add(test_alert_data)
            logger.info(f"🧪 DEBUG: Test alert saved to Firestore: {request.event_id}")
    except Exception as e:
        logger.error(f"Failed to save test alert to Firestore: {e}")

    # FCMペイロードを作成 (FcmAlertInfoスキーマに合わせる)
    fcm_payload_data = {
        "id": request.event_id,
        "title": f"🚨 {request.title}",
        "body": request.description,
        "disaster_level": request.severity.lower(),
        "disaster_type": request.alert_type,
        "timestamp": request.report_datetime,
        "data": {
            "id": request.event_id,
            "type": "alert",
            "alert_type": request.alert_type,
            "severity": request.severity,
            "event_id": request.event_id,
            "report_datetime": request.report_datetime,
            "disaster_proposals": json.dumps([{
                "id": f"debug-prop-{request.event_id}",
                "type": "disaster_proposal",
                "content": f"[デバッグ] {request.description}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "alertLevel": request.severity,
                "sourceName": "デバッグシステム",
                "sourceUrl": "https://example.com/debug",
                "shelterName": "テスト避難所",
                "shelterStatus": "open",
                "shelterLatitude": 35.6895,
                "shelterLongitude": 139.6917
            }])
        }
    }

    try:
        # logger.info(f"Attempting to send mock alert push notification to user: {request.user_id} with data: {fcm_payload_data}") # 古いログ出力を削除または修正
        logger.info(f"Attempting to send mock alert push notification for {target_info} with data: {fcm_payload_data}") # target_info を使用するように修正
        # FCM送信関数を呼び出す
        # trigger_fcm_push ツールは、整形済みのアラート情報を含む辞書を単一の引数として受け取る
        # ツール内部でユーザーIDや通知内容を処理する
        # ユーザーIDは fcm_payload_data に含めてツールに渡す必要があるかもしれないが、
        # 現在の trigger_fcm_push の実装は Firestore から全ユーザーを取得しているため、
        # ここで user_id を直接渡す必要はない（ツール内部でフィルタリングが必要）
        # ただし、デバッグ目的で特定のユーザーに送りたい場合は、ツールを修正するか、
        # ツールにユーザーIDを処理させるようにペイロードを調整する必要がある。
        # ここでは、ツールがペイロード内の情報を使って適切に処理すると仮定し、
        # device_id が指定されている場合のみ、dataに含める
        if request.device_id:
            fcm_payload_data["data"]["user_id"] = request.device_id

        # trigger_fcm_push ツールを .invoke() メソッドで呼び出す
        tool_input = {"alert_info": fcm_payload_data}
        # trigger_fcm_push は同期関数なので await は不要
        result_message = trigger_fcm_push.invoke(tool_input)
        logger.info(f"Successfully triggered mock alert push notification for {target_info}")
        
        # デバイスの緊急状態を更新
        if request.device_id:
            try:
                logger.info(f"🔄 Updating device emergency state to {request.alert_type} for device {request.device_id}")
                
                from app.db.firestore_client import get_db
                db = get_db()
                
                # デバイスの緊急状態を更新
                emergency_data = {
                    "device_id": request.device_id,
                    "disaster_type": request.alert_type,
                    "severity": request.severity.lower(),
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                    "is_active": True,
                    "source": "debug_mock_alert"
                }
                
                device_emergency_ref = db.collection("device_emergency_states").document(request.device_id)
                device_emergency_ref.set(emergency_data)
                
                logger.info(f"✅ Updated device emergency state to {request.alert_type} for device {request.device_id}")
                
            except Exception as e:
                logger.error(f"⚠️ Failed to update device emergency state: {e}")
        
        # デバッグモードで緊急アラートを鳴らした場合、クールダウンもリセット
        cooldown_reset_message = ""
        if request.device_id:
            try:
                logger.info(f"🔄 Resetting suggestion cooldowns for device {request.device_id} after triggering emergency alert")
                
                from app.db.firestore_client import get_db
                db = get_db()
                
                # デバイスの提案履歴を削除
                device_history_ref = db.collection("device_suggestion_history").document(request.device_id)
                
                # サブコレクション「suggestions」のすべてのドキュメントを削除
                suggestions_collection = device_history_ref.collection("suggestions").get()
                deleted_count = 0
                for doc in suggestions_collection:
                    doc.reference.delete()
                    deleted_count += 1
                
                # メインドキュメントも削除
                device_history_ref.delete()
                
                logger.info(f"Successfully reset {deleted_count} suggestion cooldowns for device {request.device_id}")
                cooldown_reset_message = f" Suggestion cooldowns reset ({deleted_count} records cleared)."
                
            except Exception as e:
                logger.error(f"⚠️ Failed to reset suggestion cooldowns: {e}")
                cooldown_reset_message = " (Cooldown reset failed)"
        
        # ツールからの結果をレスポンスに含めることも検討可能
        return {
            "message": f"Mock alert push notification triggered for {target_info}. Tool result: {result_message}{cooldown_reset_message}",
            "cooldown_reset": bool(cooldown_reset_message and "Success" in cooldown_reset_message)
        }

    except Exception as e: # 発生した例外をまとめて捕捉
        logger.error(f"Failed to trigger mock alert push notification for {target_info}: {e}", exc_info=True)
        # エラー詳細をクライアントに返す
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger mock alert push notification for {target_info}: {e}"
        )


@router.post(
    "/test-emergency-contact-suggestion",
    summary="Test emergency contact setup suggestion",
    description="Tests emergency contact setup suggestion generation with different contact counts",
    status_code=status.HTTP_200_OK,
    tags=["Debug"]
)
async def test_emergency_contact_suggestion(
    emergency_contacts_count: int = Query(0, description="Number of emergency contacts to simulate"),
    language_code: str = Query("ja", description="Language code for the suggestion")
):
    """緊急連絡先設定提案のテスト"""
    try:
        logger.info(f"Testing emergency contact suggestion with count: {emergency_contacts_count}")
        
        # テスト用のコンテキストを作成
        user_usage_summary = UserAppUsageSummary(
            is_new_user=True,
            last_app_open_days_ago=0,
            local_contact_count=emergency_contacts_count
        )
        
        context = ProactiveSuggestionContext(
            device_id="test-device-123",
            language_code=language_code,
            current_situation="normal",
            is_emergency_mode=False,
            current_location=None,
            device_status={"battery_level": 80},
            suggestion_history_summary=[],
            last_suggestion_timestamp=None,
            user_app_usage_summary=user_usage_summary,
            permissions={}
        )
        
        # 緊急連絡先設定提案を生成
        suggestion = await basic_generator.generate_emergency_contact_setup(context, language_code)
        
        result = {
            "emergency_contacts_count": emergency_contacts_count,
            "language_code": language_code,
            "suggestion_generated": suggestion is not None,
            "suggestion_data": suggestion.model_dump() if suggestion else None,
            "expected_behavior": "Should generate suggestion only when emergency_contacts_count <= 0"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing emergency contact suggestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test emergency contact suggestion: {e}"
        )


@router.post(
    "/initialize-pdf-rag",
    summary="Initialize PDF RAG system with existing PDFs",
    description="Process all existing PDF files in the guide directory for RAG search",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Debug"]
)
async def initialize_pdf_rag():
    """既存PDFファイルを使ってPDF RAGシステムを初期化"""
    try:
        logger.info("🔄 Initializing PDF RAG system with existing PDFs")
        
        from app.services.pdf_rag_service import pdf_rag_service
        from app.services.pdf_rag_service import PDFProcessingConfig, PDFProcessingMode, ChunkingStrategy
        
        # 既存PDFファイルの確認
        guide_dir = pdf_rag_service.base_path / "guide"
        if not guide_dir.exists():
            return {
                "status": "error",
                "message": "Guide directory not found",
                "guide_dir": str(guide_dir)
            }
        
        pdf_files = list(guide_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
        
        if not pdf_files:
            return {
                "status": "success",
                "message": "No PDF files found to process",
                "guide_dir": str(guide_dir),
                "pdf_count": 0
            }
        
        # 処理設定（災害防災文書に最適化）
        config = PDFProcessingConfig(
            processing_mode=PDFProcessingMode.HYBRID,
            chunking_strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=800,  # 防災情報は短めのチャンクで
            chunk_overlap=150,
            extract_images=False,
            extract_tables=True,  # 防災データの表は重要
            preserve_formatting=True
        )
        
        # 各PDFファイルを処理
        processing_results = []
        for pdf_file in pdf_files:
            try:
                logger.info(f"🔄 Processing {pdf_file.name}...")
                metadata = await pdf_rag_service.process_pdf(str(pdf_file), config)
                
                processing_results.append({
                    "file_name": pdf_file.name,
                    "status": "success",
                    "file_hash": metadata.file_hash,
                    "page_count": metadata.page_count,
                    "keywords": metadata.keywords,
                    "content_summary": metadata.content_summary
                })
            except Exception as e:
                logger.error(f"❌ Failed to process {pdf_file.name}: {e}")
                processing_results.append({
                    "file_name": pdf_file.name,
                    "status": "error",
                    "error": str(e)
                })
        
        # PDF RAGシステムを既存のガイド検索ツールと統合テスト
        try:
            from app.tools.guide_tools import UnifiedGuideSearchTool, VectorStoreBackend
            
            # PDF RAGバックエンドを優先して初期化
            search_tool = UnifiedGuideSearchTool(
                backend_preference=[VectorStoreBackend.PDF_RAG, VectorStoreBackend.JSON]
            )
            
            # テスト検索
            test_query = "地震 避難"
            test_results = await search_tool.search_guides(test_query, max_results=3)
            
            integration_test = {
                "search_backend": search_tool.backend.value if search_tool.backend else "none",
                "test_query": test_query,
                "test_results_count": len(test_results),
                "test_success": len(test_results) > 0
            }
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            integration_test = {
                "search_backend": "error",
                "test_error": str(e),
                "test_success": False
            }
        
        successful_count = len([r for r in processing_results if r["status"] == "success"])
        
        return {
            "status": "completed",
            "message": f"PDF RAG initialization completed: {successful_count}/{len(pdf_files)} files processed successfully",
            "guide_directory": str(guide_dir),
            "total_files": len(pdf_files),
            "successful_files": successful_count,
            "failed_files": len(pdf_files) - successful_count,
            "processing_results": processing_results,
            "processing_config": {
                "processing_mode": config.processing_mode.value,
                "chunking_strategy": config.chunking_strategy.value,
                "chunk_size": config.chunk_size,
                "chunk_overlap": config.chunk_overlap
            },
            "integration_test": integration_test
        }
        
    except Exception as e:
        logger.error(f"❌ PDF RAG initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF RAG initialization failed: {str(e)}"
        )


@router.get(
    "/pdf-rag-status",
    summary="Check PDF RAG system status",
    description="Get the current status of the PDF RAG system",
    status_code=status.HTTP_200_OK,
    tags=["Debug"]
)
async def pdf_rag_status():
    """PDF RAGシステムの状態確認"""
    try:
        from app.services.pdf_rag_service import pdf_rag_service
        from app.tools.guide_tools import UnifiedGuideSearchTool, VectorStoreBackend
        
        # PDFサービス状態
        pdf_list = await pdf_rag_service.get_pdf_list()
        
        # ガイド検索ツール状態
        search_tool = UnifiedGuideSearchTool()
        
        status_info = {
            "pdf_rag_service": {
                "total_pdfs": len(pdf_list),
                "pdf_files": [pdf["file_name"] for pdf in pdf_list],
                "vector_store_type": "FAISS" if pdf_rag_service.vector_store else "Simple",
                "documents_count": len(pdf_rag_service.documents) if pdf_rag_service.documents else 0,
                "vector_db_path": str(pdf_rag_service.vector_db_path),
                "pdf_storage_path": str(pdf_rag_service.pdf_storage_path)
            },
            "unified_guide_search": {
                "active_backend": search_tool.backend.value if search_tool.backend else "none",
                "pdf_rag_available": search_tool.pdf_rag_service is not None
            }
        }
        
        # 簡単なテスト検索
        try:
            test_results = await pdf_rag_service.search("災害", max_results=1)
            status_info["search_test"] = {
                "status": "success",
                "results_count": len(test_results)
            }
        except Exception as e:
            status_info["search_test"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_status": status_info
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get PDF RAG status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PDF RAG status: {str(e)}"
        )
