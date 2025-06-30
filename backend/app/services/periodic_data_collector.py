"""
定期的データ収集サービス
バックエンド側で災害・避難所情報を定期的に取得・更新する仕組み
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import os

from app.tools.disaster_info_tools import (
    disaster_info_tool as enhanced_disaster_monitor,
    get_unified_disaster_info_for_location
)
from app.schemas.common.location import Location
from app.db.firestore_client import get_db
from app.utils.fcm_sender import send_fcm_multicast_notification
from app.crud.device_crud import get_all_devices

logger = logging.getLogger(__name__)

@dataclass
class CollectionArea:
    """データ収集エリア"""
    area_id: str
    name: str
    location: Location
    radius_km: float
    priority: int = 1  # 1=最高, 5=最低
    last_collected: Optional[datetime] = None
    collection_interval_minutes: int = 5  # デフォルト5分
    active_users: Set[str] = None  # このエリアのアクティブユーザーID
    
    def __post_init__(self):
        if self.active_users is None:
            self.active_users = set()

class PeriodicDataCollector:
    """定期的データ収集サービス"""
    
    def __init__(self):
        self.is_running = False
        self._collector_task: Optional[asyncio.Task] = None
        
        # 収集エリア管理
        self.collection_areas: Dict[str, CollectionArea] = {}
        
        # 環境設定
        self.environment = os.getenv("ENVIRONMENT", "production").lower()
        
        # .envファイルから間隔設定を取得
        self.default_interval_minutes = float(os.getenv("PERIODIC_DATA_COLLECTOR_INTERVAL_MINUTES", "5.0"))
        
        # テスト環境用のデフォルト値上書き
        if self.environment == "test":
            self.default_interval_minutes = float(os.getenv("PERIODIC_DATA_COLLECTOR_INTERVAL_MINUTES", "0.25"))  # 15秒 = 0.25分
        
        # データキャッシュ
        self.latest_data_cache: Dict[str, Any] = {}
        
        # 通知管理
        self.notification_throttle: Dict[str, datetime] = {}
        self.min_notification_interval_minutes = 10
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Periodic Data Collector initialized - Environment: {self.environment}, "
                       f"Default interval: {self.default_interval_minutes} minutes")

    async def start_collection(self):
        """定期収集を開始"""
        if self.is_running:
            logger.warning("Periodic data collection is already running")
            return
        
        self.is_running = True
        
        # 拡張災害監視も同時に開始
        await enhanced_disaster_monitor.start_unified_monitoring()
        
        # 定期収集タスク開始
        self._collector_task = asyncio.create_task(self._collection_loop())
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
    async def stop_collection(self):
        """定期収集を停止"""
        self.is_running = False
        
        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        
        await enhanced_disaster_monitor.stop_unified_monitoring()
        if logger.isEnabledFor(logging.DEBUG):
            pass
    def add_collection_area(
        self, 
        area_id: str, 
        name: str, 
        location: Location, 
        radius_km: float = 10.0,
        priority: int = 1,
        interval_minutes: Optional[int] = None
    ):
        """データ収集エリアを追加"""
        area = CollectionArea(
            area_id=area_id,
            name=name,
            location=location,
            radius_km=radius_km,
            priority=priority,
            collection_interval_minutes=interval_minutes or self.default_interval_minutes
        )
        
        self.collection_areas[area_id] = area
        if logger.isEnabledFor(logging.DEBUG):
            pass
        else:
            logger.info(f"Added collection area: {name} ({area_id}) at {location.latitude}, {location.longitude}")

    def remove_collection_area(self, area_id: str):
        """データ収集エリアを削除"""
        if area_id in self.collection_areas:
            area_name = self.collection_areas[area_id].name
            del self.collection_areas[area_id]
            if logger.isEnabledFor(logging.DEBUG):
                pass
            else:
                logger.info(f"Removed collection area: {area_name} ({area_id})")

    def add_user_to_area(self, area_id: str, user_id: str):
        """ユーザーをエリアに追加"""
        if area_id in self.collection_areas:
            self.collection_areas[area_id].active_users.add(user_id)
    def remove_user_from_area(self, area_id: str, user_id: str):
        """ユーザーをエリアから削除"""
        if area_id in self.collection_areas:
            self.collection_areas[area_id].active_users.discard(user_id)
    async def _collection_loop(self):
        """定期収集ループ"""
        while self.is_running:
            try:
                await self._collect_all_areas()
                
                # 次の収集まで待機（最小間隔を使用）
                min_interval = min(
                    area.collection_interval_minutes 
                    for area in self.collection_areas.values()
                ) if self.collection_areas else self.default_interval_minutes
                
                wait_seconds = min_interval * 60
                await asyncio.sleep(wait_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # エラー時は1分待機

    async def _collect_all_areas(self):
        """全エリアのデータを収集"""
        if not self.collection_areas:
            return
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
        else:
            pass
        # 収集が必要なエリアを特定
        areas_to_collect = []
        current_time = datetime.now()
        
        for area in self.collection_areas.values():
            if area.last_collected is None:
                areas_to_collect.append(area)
            else:
                elapsed_minutes = (current_time - area.last_collected).total_seconds() / 60
                if elapsed_minutes >= area.collection_interval_minutes:
                    areas_to_collect.append(area)
        
        if not areas_to_collect:
            return
        
        # 優先度順でソート
        areas_to_collect.sort(key=lambda x: x.priority)
        
        # 並行してデータ収集
        tasks = []
        for area in areas_to_collect:
            task = asyncio.create_task(self._collect_area_data(area))
            tasks.append(task)
        
        # 全エリアの収集完了を待機
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果処理
        for i, result in enumerate(results):
            area = areas_to_collect[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to collect data for area {area.name}: {result}")
            else:
                area.last_collected = current_time
                if logger.isEnabledFor(logging.DEBUG):
                    pass
                else:
                    pass
    
    async def _collect_area_data(self, area: CollectionArea) -> Dict[str, Any]:
        """特定エリアのデータを収集"""
        try:
            # 統合災害・避難所情報を取得
            unified_info = await get_unified_disaster_info_for_location(
                location=area.location,
                radius_km=area.radius_km,
                force_refresh=True  # 定期収集では常に最新データを取得
            )
            
            # データをキャッシュに保存
            cache_key = area.area_id
            self.latest_data_cache[cache_key] = {
                "area_id": area.area_id,
                "area_name": area.name,
                "collected_at": datetime.now().isoformat(),
                "unified_info": unified_info.to_dict(),
                "active_users_count": len(area.active_users)
            }
            
            # 重要な災害情報があれば通知
            await self._check_and_notify(area, unified_info)
            
            return self.latest_data_cache[cache_key]
            
        except Exception as e:
            logger.error(f"Error collecting data for area {area.name}: {e}")
            raise

    async def _check_and_notify(self, area: CollectionArea, unified_info):
        """重要な災害情報をチェックして通知"""
        try:
            # 緊急度の高い災害警報をチェック
            critical_alerts = [
                alert for alert in unified_info.disaster_alerts
                if alert.severity in ["emergency", "critical"]
            ]
            
            if not critical_alerts:
                return
            
            # 通知スロットリングチェック
            throttle_key = f"{area.area_id}_critical"
            last_notification = self.notification_throttle.get(throttle_key)
            
            if last_notification:
                elapsed_minutes = (datetime.now() - last_notification).total_seconds() / 60
                if elapsed_minutes < self.min_notification_interval_minutes:
                    return
            
            # エリア内のアクティブユーザーに通知
            if area.active_users:
                await self._send_area_notifications(area, critical_alerts)
                self.notification_throttle[throttle_key] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in notification check for area {area.name}: {e}")

    async def _send_area_notifications(self, area: CollectionArea, alerts: List):
        """エリア内ユーザーに通知送信"""
        try:
            db = get_db()
            
            # アクティブユーザーのデバイス情報を取得
            devices = await get_all_devices()
            target_devices = [
                device for device in devices
                if device.get("device_id") in area.active_users and device.get("fcm_token")
            ]
            
            if not target_devices:
                return
            
            # 通知メッセージ作成
            alert_count = len(alerts)
            severity = max(alerts, key=lambda x: ["advisory", "warning", "critical", "emergency"].index(x.severity)).severity
            
            title = f"【{area.name}】緊急災害情報"
            body = f"{alert_count}件の{severity}レベル災害情報があります"
            
            # FCM送信
            tokens = [device["fcm_token"] for device in target_devices]
            device_languages = {device["fcm_token"]: device.get("language", "ja") for device in target_devices}
            
            from app.utils.fcm_sender import send_fcm_multicast_notification
            success_count, failure_count = send_fcm_multicast_notification(
                tokens,
                title,
                body,
                {
                    "area_id": area.area_id,
                    "alert_count": str(alert_count),
                    "severity": severity,
                    "click_action": "/disaster_info"
                },
                device_languages
            )
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Sent notifications to area {area.name}: "
                           f"Success: {success_count}, Failed: {failure_count}")
            else:
                logger.info(f"Sent notifications to area {area.name}: "
                           f"Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error sending area notifications: {e}")

    def get_latest_data(self, area_id: str) -> Optional[Dict[str, Any]]:
        """エリアの最新データを取得"""
        return self.latest_data_cache.get(area_id)

    def get_all_latest_data(self) -> Dict[str, Any]:
        """全エリアの最新データを取得"""
        return self.latest_data_cache.copy()

    def get_collection_status(self) -> Dict[str, Any]:
        """収集ステータスを取得"""
        return {
            "is_running": self.is_running,
            "environment": self.environment,
            "default_interval_minutes": self.default_interval_minutes,
            "collection_areas_count": len(self.collection_areas),
            "cached_data_count": len(self.latest_data_cache),
            "areas": [
                {
                    "area_id": area.area_id,
                    "name": area.name,
                    "active_users_count": len(area.active_users),
                    "last_collected": area.last_collected.isoformat() if area.last_collected else None,
                    "interval_minutes": area.collection_interval_minutes
                }
                for area in self.collection_areas.values()
            ]
        }

# グローバルインスタンス
periodic_data_collector = PeriodicDataCollector()

# ヘルパー関数
async def start_periodic_collection():
    """定期収集を開始"""
    await periodic_data_collector.start_collection()

async def stop_periodic_collection():
    """定期収集を停止"""
    await periodic_data_collector.stop_collection()

def add_collection_area(area_id: str, name: str, location: Location, **kwargs):
    """収集エリアを追加"""
    periodic_data_collector.add_collection_area(area_id, name, location, **kwargs)

def get_latest_area_data(area_id: str) -> Optional[Dict[str, Any]]:
    """エリアの最新データを取得"""
    return periodic_data_collector.get_latest_data(area_id)