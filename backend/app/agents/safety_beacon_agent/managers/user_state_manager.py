"""デバイスステート管理モジュール - 災害セッション中のデバイス状態を管理"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from google.cloud import firestore
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Firestoreクライアント初期化
try:
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    if not gcp_project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is not set")

    db = firestore.AsyncClient(project=gcp_project_id)
    logger.info("Firestore client initialized for user state manager")
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {e}")
    raise

async def get_user_disaster_state(device_id: str, event_id: str) -> Dict[str, Any]:
    """
    指定されたデバイスIDと災害イベントIDのデバイスステートを取得

    Args:
        device_id: デバイスID
        event_id: 災害イベントID

    Returns:
        ユーザーステートの辞書:
        {
            "last_interaction": datetime,
            "reported_safety": bool,
            "requested_shelter_info": bool,
            "received_warnings": List[str],
            "custom_data": Dict[str, Any]
        }

    Raises:
        HTTPException: ステート取得失敗時
    """
    try:
        doc_ref = db.collection("devices").document(device_id) \
            .collection("disaster_sessions").document(event_id)
        doc = await doc_ref.get()

        if not doc.exists:
            logger.info(f"No state found for device {device_id}, event {event_id}")
            return {
                "last_interaction": datetime.now(),
                "reported_safety": False,
                "requested_shelter_info": False,
                "received_warnings": [],
                "custom_data": {}
            }

        return doc.to_dict()

    except Exception as e:
        logger.error(f"Error getting device state for {device_id}/{event_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"デバイスステートの取得に失敗しました: {str(e)}"
        )

async def update_user_disaster_state(
    device_id: str,
    event_id: str,
    new_state: Dict[str, Any]
) -> None:
    """
    デバイスの災害セッション状態を更新

    Args:
        device_id: デバイスID
        event_id: 災害イベントID
        new_state: 更新する状態データ

    Raises:
        HTTPException: ステート更新失敗時
    """
    try:
        doc_ref = db.collection("devices").document(device_id) \
            .collection("disaster_sessions").document(event_id)

        # 最終更新時刻を自動設定
        new_state["last_updated"] = datetime.now()

        await doc_ref.set(new_state, merge=True)
        logger.info(f"Updated state for device {device_id}, event {event_id}")

    except Exception as e:
        logger.error(f"Error updating device state for {device_id}/{event_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"デバイスステートの更新に失敗しました: {str(e)}"
        )
