from fastapi import APIRouter, HTTPException
from typing import Dict
from ..services.vertex_search_killswitch import VertexSearchKillSwitch
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/vertex-search/killswitch/status")
async def get_killswitch_status() -> Dict:
    """
    キルスイッチの現在状態を取得
    """
    try:
        killswitch = VertexSearchKillSwitch()
        return killswitch.get_status()
    except Exception as e:
        logger.error(f"Failed to get killswitch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vertex-search/killswitch/enable")
async def enable_vertex_search() -> Dict:
    """
    Vertex AI Searchを手動で有効化
    """
    try:
        killswitch = VertexSearchKillSwitch()
        killswitch.enable_service()
        return {"status": "enabled", "message": "Vertex AI Search has been enabled"}
    except Exception as e:
        logger.error(f"Failed to enable Vertex Search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vertex-search/killswitch/disable")
async def disable_vertex_search() -> Dict:
    """
    Vertex AI Searchを手動で無効化
    """
    try:
        killswitch = VertexSearchKillSwitch()
        killswitch.disable_service()
        return {"status": "disabled", "message": "Vertex AI Search has been disabled"}
    except Exception as e:
        logger.error(f"Failed to disable Vertex Search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vertex-search/killswitch/reset-counters")
async def reset_error_counters() -> Dict:
    """
    エラーカウンターをリセット（エラー率が原因で停止した場合の復旧用）
    """
    try:
        killswitch = VertexSearchKillSwitch()
        killswitch.redis_client.delete(f"{killswitch.KEY_PREFIX}error_count")
        killswitch.redis_client.delete(f"{killswitch.KEY_PREFIX}total_count")
        return {"status": "success", "message": "Error counters have been reset"}
    except Exception as e:
        logger.error(f"Failed to reset counters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))