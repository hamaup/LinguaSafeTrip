# backend/app/crud/jma_event_crud.py (想定される内容)
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
from app.schemas.disaster_info import JMAEventData
import os
from app.db.firestore_client import get_async_db

JMA_EVENTS_COLLECTION = os.getenv("JMA_EVENTS_COLLECTION_NAME", "jma_events")

async def get_jma_events(
    updated_after: Optional[datetime] = None,
    limit: int = 10,
    area_codes: Optional[List[str]] = None
) -> List[JMAEventData]:
    """
    FirestoreからJMAイベントを取得する。
    feed_type, updated_after, limit などでフィルタリングする。
    """
    db = await get_async_db()
    query = db.collection(JMA_EVENTS_COLLECTION)

    if updated_after:
        query = query.where(filter=FieldFilter("updated_at", ">=", updated_after))

    if area_codes:
        query = query.where(filter=FieldFilter("areas.code", "in", area_codes))

    query = query.order_by("updated_at", direction=firestore.Query.DESCENDING)
    query = query.limit(limit)

    docs = query.stream()
    events = []
    async for doc in docs:
        event_data = doc.to_dict()
        if event_data:
            try:
                events.append(JMAEventData(**event_data))
            except Exception as e:
                logging.error(f"Invalid event data format: {e}")
    return events


async def get_jma_event_by_id(event_id: str) -> Optional[JMAEventData]:
    """イベントIDで単一のJMAイベントを取得する"""
    db = await get_async_db()
    doc_ref = db.collection(JMA_EVENTS_COLLECTION).document(event_id)
    doc = await doc_ref.get()
    if doc.exists:
        try:
            return JMAEventData(**doc.to_dict())
        except Exception as e:
            logging.error(f"Invalid event data format: {e}")
    return None

async def save_jma_event(event_data: JMAEventData) -> bool:
    """JMAイベントデータをFirestoreに保存する"""
    db = await get_async_db()
    try:
        doc_ref = db.collection(JMA_EVENTS_COLLECTION).document(event_data.event_id)
        existing_doc = await doc_ref.get()

        if existing_doc.exists:
            existing_data = existing_doc.to_dict()
            existing_updated = existing_data.get("updated_at")
            # 「既存の更新時刻＋1秒」以内であれば更新不要とみなす
            from datetime import timedelta
            if event_data.updated_at and existing_updated:
                if event_data.updated_at <= existing_updated + timedelta(seconds=1):
                    msg = f"No update needed for event_id: {event_data.event_id}"
                    logging.warning(msg)  # WARNINGレベルで出力してcaplogでキャプチャ
                    return False

        await doc_ref.set(event_data.model_dump())
        return True
    except Exception as e:
        logging.error(f"Failed to save JMA event: {e}")
        return False
