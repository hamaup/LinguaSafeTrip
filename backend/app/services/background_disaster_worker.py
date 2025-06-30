# app/services/background_disaster_worker.py
"""
災害情報バックグラウンド更新ワーカー
Firestoreキューからリクエストを取得し、災害情報を非同期で更新
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import traceback

from google.cloud.firestore_v1 import FieldFilter
from app.db.firestore_client import get_db
from app.schemas.common.location import Location
from app.tools.disaster_info_tools import get_unified_disaster_info_for_location, disaster_info_tool

logger = logging.getLogger(__name__)

class BackgroundDisasterWorker:
    """災害情報バックグラウンド更新ワーカー"""
    
    def __init__(self):
        self.db = get_db()
        self.update_requests_collection = "disaster_update_requests"
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.max_concurrent_requests = 3  # 同時処理数制限
        self.poll_interval = 5  # ポーリング間隔（秒）
        self.max_retry_count = 3
    
    async def start(self):
        """ワーカーを開始"""
        if self.running:
            logger.warning("Background disaster worker already running")
            return
        
        self.running = True
        # メインワーカータスクを開始
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        # クリーンアップタスクを開始
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """ワーカーを停止"""
        if not self.running:
            return
        
        self.running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
    
    async def _worker_loop(self):
        """メインワーカーループ"""
        while self.running:
            try:
                # 処理待ちリクエストを取得
                requests = await self._get_pending_requests()
                
                if requests:
                    # 並行処理でリクエストを処理
                    tasks = []
                    for request in requests[:self.max_concurrent_requests]:
                        task = asyncio.create_task(self._process_request(request))
                        tasks.append(task)
                    
                    # すべてのタスク完了を待機
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
                # ポーリング間隔で待機
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(self.poll_interval)
    
    async def _get_pending_requests(self) -> List[Dict[str, Any]]:
        """処理待ちリクエストを取得"""
        try:
            # Check if collection exists and has documents first
            collection_ref = self.db.collection(self.update_requests_collection)
            
            # Simple existence check to avoid index error
            try:
                sample_docs = collection_ref.limit(1).get()
                if not sample_docs:
                    # Collection is empty, return empty list
                    return []
            except Exception:
                # Collection might not exist or have index issues
                logger.debug("disaster_update_requests collection not accessible, returning empty list")
                return []
            
            # 優先度順でソート（high > normal > low）
            priority_order = {'high': 1, 'normal': 2, 'low': 3}
            
            # Try the original query with proper error handling
            try:
                query = (self.db.collection(self.update_requests_collection)
                        .where(filter=FieldFilter('status', '==', 'pending'))
                        .where(filter=FieldFilter('retry_count', '<=', self.max_retry_count))
                        .order_by('requested_at')
                        .limit(10))
                
                docs = query.get()
            except Exception as index_error:
                # If composite index is missing, fall back to simpler query
                logger.warning(f"Composite index missing for disaster_update_requests, using simpler query: {index_error}")
                query = (self.db.collection(self.update_requests_collection)
                        .where(filter=FieldFilter('status', '==', 'pending'))
                        .limit(10))
                docs = query.get()
            
            requests = []
            
            for doc in docs:
                data = doc.to_dict()
                data['doc_id'] = doc.id
                # Additional check for retry_count if we used simpler query
                if data.get('retry_count', 0) <= self.max_retry_count:
                    requests.append(data)
            
            # 優先度でソート
            requests.sort(key=lambda x: (
                priority_order.get(x.get('priority', 'normal'), 2),
                x.get('requested_at', datetime.min)
            ))
            
            return requests
            
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
    
    async def _process_request(self, request: Dict[str, Any]):
        """個別リクエストを処理"""
        doc_id = request['doc_id']
        request_id = request.get('request_id', doc_id)
        
        try:
            logger.info(f"Processing disaster update request: {request_id}")
            
            # ステータスを「処理中」に更新
            await self._update_request_status(doc_id, 'processing')
            
            # 位置情報を取得
            location_data = request['location']
            location = Location(
                latitude=location_data['latitude'],
                longitude=location_data['longitude']
            )
            radius_km = request.get('radius_km', 10.0)
            
            # 災害情報を取得（時間のかかる処理）
            logger.info(f"Fetching disaster info for location: {location.latitude}, {location.longitude}")
            start_time = datetime.now()
            
            unified_info = await get_unified_disaster_info_for_location(
                location=location,
                radius_km=radius_km,
                force_refresh=True  # バックグラウンド更新では強制リフレッシュ
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # キャッシュに保存
            cache_key = await disaster_info_tool.set_cached_disaster_info(
                location=location,
                radius_km=radius_km,
                disaster_alerts=unified_info.disaster_alerts,
                shelter_info=unified_info.shelter_info
            )
            
            # 緊急アラートがある場合は、関連デバイスに通知
            if unified_info.disaster_alerts:
                await self._notify_emergency_alerts(request, unified_info.disaster_alerts)
            
            # 処理完了
            await self._update_request_status(
                doc_id, 
                'completed',
                extra_data={
                    'completed_at': datetime.now(timezone.utc),
                    'processing_time_seconds': processing_time,
                    'cache_key': cache_key,
                    'alert_count': len(unified_info.disaster_alerts),
                    'shelter_count': len(unified_info.shelter_info)
                }
            )
            
            logger.info(f"Successfully processed disaster update request: {request_id}")
            
        except Exception as e:
            logger.error(f"Error processing disaster update request {request_id}: {e}")
            logger.error(traceback.format_exc())
            
            # リトライ回数を増やして失敗としてマーク
            retry_count = request.get('retry_count', 0) + 1
            status = 'failed' if retry_count > self.max_retry_count else 'pending'
            
            await self._update_request_status(
                doc_id,
                status,
                extra_data={
                    'retry_count': retry_count,
                    'last_error': str(e),
                    'last_error_at': datetime.now(timezone.utc)
                }
            )
    
    async def _update_request_status(
        self, 
        doc_id: str, 
        status: str, 
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """リクエストのステータスを更新"""
        try:
            doc_ref = self.db.collection(self.update_requests_collection).document(doc_id)
            
            update_data = {
                'status': status,
                'updated_at': datetime.now(timezone.utc)
            }
            
            if extra_data:
                update_data.update(extra_data)
            
            doc_ref.update(update_data)
            
        except Exception as e:
            logger.error(f"Error updating request status: {e}")
    
    async def _notify_emergency_alerts(self, request: Dict[str, Any], alerts: List[Any]):
        """緊急アラートをデバイスに通知"""
        try:
            device_id = request.get('device_id')
            if not device_id:
                return
            
            # TODO: Push通知やWebSocket通知の実装
            logger.info(f"Emergency alerts detected for device {device_id}: {len(alerts)} alerts")
            
            # 現在はログ出力のみ
            for alert in alerts:
                logger.warning(f"Emergency alert: {getattr(alert, 'title', 'Unknown')} - {getattr(alert, 'severity', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error notifying emergency alerts: {e}")
    
    async def _cleanup_loop(self):
        """定期クリーンアップループ"""
        while self.running:
            try:
                # 24時間間隔でクリーンアップ
                await asyncio.sleep(24 * 3600)
                
                if self.running:
                    await self._cleanup_old_requests()
                    await disaster_info_tool.cleanup_old_cache()
                    
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_old_requests(self, max_age_hours: int = 48):
        """古い処理済みリクエストを削除"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            
            # 完了済みまたは失敗したリクエストを削除
            for status in ['completed', 'failed']:
                query = (self.db.collection(self.update_requests_collection)
                        .where('status', '==', status)
                        .where('updated_at', '<', cutoff_time))
                
                docs = query.get()
                deleted_count = 0
                
                for doc in docs:
                    doc.reference.delete()
                    deleted_count += 1
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old {status} requests")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old requests: {e}")

# グローバルワーカーインスタンス
background_disaster_worker = BackgroundDisasterWorker()