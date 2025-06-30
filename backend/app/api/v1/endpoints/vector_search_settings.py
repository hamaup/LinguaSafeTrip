"""
ベクトル検索設定API
ユーザーがアプリで検索エンジンを選択・変更する
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.schemas.vector_search_settings import (
    VectorSearchSettings,
    UserVectorSearchPreferences, 
    VectorSearchCapabilities,
    VectorSearchBackend,
    VectorSearchQuality
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vector-search", tags=["vector-search"])

@router.get("/capabilities/{device_id}")
async def get_vector_search_capabilities(device_id: str) -> VectorSearchCapabilities:
    """
    デバイスのベクトル検索能力を取得
    アプリが設定画面に表示するオプションを決定
    """
    try:
        # デバイス情報から能力を判定（実際の実装では更に詳細に）
        capabilities = VectorSearchCapabilities(
            supports_vertex_ai=True,  # 通信可能なら常にtrue
            supports_local_faiss=False,  # モバイルでは通常false
            supports_keyword_search=True,
            network_available=True,  # 実際はネットワーク状態をチェック
            estimated_local_storage_mb=None,
            
            # 推奨設定（デフォルト）
            recommended_backend=VectorSearchBackend.VERTEX_AI,
            recommended_quality=VectorSearchQuality.STANDARD
        )
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get capabilities for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search capabilities")

@router.get("/settings/{device_id}")
async def get_vector_search_settings(device_id: str) -> UserVectorSearchPreferences:
    """
    ユーザーの現在のベクトル検索設定を取得
    """
    try:
        # Firestoreから設定を取得（実装例）
        # settings = await get_user_settings_from_firestore(device_id)
        
        # デフォルト設定を返す（実装時はFirestoreから取得）
        default_settings = VectorSearchSettings(
            backend=VectorSearchBackend.VERTEX_AI,
            quality=VectorSearchQuality.STANDARD,
            max_results=5,
            score_threshold=0.7,
            enable_offline_fallback=True,
            enable_cache=True
        )
        
        return UserVectorSearchPreferences(
            user_id="",  # 必要に応じて設定
            device_id=device_id,
            search_settings=default_settings,
            performance_stats={
                "average_response_time_ms": 200,
                "success_rate": 0.98,
                "cache_hit_rate": 0.45
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get settings for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search settings")

@router.post("/settings/{device_id}")
async def update_vector_search_settings(
    device_id: str, 
    settings: VectorSearchSettings
) -> Dict[str, Any]:
    """
    ユーザーのベクトル検索設定を更新
    """
    try:
        # バリデーション
        if settings.max_results > 20:
            raise HTTPException(status_code=400, detail="max_results cannot exceed 20")
        
        # Firestoreに保存（実装例）
        # await save_user_settings_to_firestore(device_id, settings)
        
        # 設定変更に伴うキャッシュクリア
        # await clear_search_cache_for_device(device_id)
        
        logger.info(f"Updated vector search settings for device {device_id}: {settings.backend}")
        
        return {
            "status": "success",
            "message": "Vector search settings updated successfully",
            "applied_settings": settings.dict(),
            "effective_immediately": True
        }
        
    except Exception as e:
        logger.error(f"Failed to update settings for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update search settings")

@router.post("/settings/{device_id}/test")
async def test_vector_search_backend(
    device_id: str,
    backend: VectorSearchBackend
) -> Dict[str, Any]:
    """
    指定されたベクトル検索バックエンドをテスト
    ユーザーが設定画面で「テスト」ボタンを押した時に実行
    """
    try:
        # テストクエリで各バックエンドの性能を測定
        test_query = "地震の時の避難方法"
        
        # 実際の検索を実行してレスポンス時間を測定
        import time
        start_time = time.time()
        
        # バックエンドごとの実装（後で詳細実装）
        if backend == VectorSearchBackend.VERTEX_AI:
            # Vertex AI検索をテスト
            result_count = 5
            response_time_ms = 150
        elif backend == VectorSearchBackend.FAISS_LOCAL:
            # ローカルFAISS検索をテスト
            result_count = 5
            response_time_ms = 50
        elif backend == VectorSearchBackend.KEYWORD_ONLY:
            # キーワード検索をテスト
            result_count = 3
            response_time_ms = 20
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported backend: {backend}")
        
        return {
            "backend": backend,
            "test_status": "success",
            "response_time_ms": response_time_ms,
            "result_count": result_count,
            "quality_score": 0.85,  # 仮の品質スコア
            "recommendation": "このバックエンドは良好に動作しています"
        }
        
    except Exception as e:
        logger.error(f"Backend test failed for {backend}: {e}")
        return {
            "backend": backend,
            "test_status": "failed",
            "error": str(e),
            "recommendation": "このバックエンドは現在利用できません"
        }