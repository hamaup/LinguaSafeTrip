"""
JMA定期ポーリングサービス
気象庁のAtomフィードを定期的に取得してFirestoreに保存
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.tools.jma_poller_tool import JMAPollerTool
from app.config import app_settings

logger = logging.getLogger(__name__)


class JMAPollingService:
    """JMA定期ポーリングサービス"""
    
    def __init__(self):
        self.is_running = False
        self._polling_task: Optional[asyncio.Task] = None
        self.jma_poller = JMAPollerTool()
        
        # 環境設定
        self.environment = app_settings.environment
        
        # ポーリング間隔（分）
        if self.environment in ["test", "development"]:
            self.polling_interval_minutes = app_settings.external_apis.jma_polling_interval_test_minutes
        else:
            self.polling_interval_minutes = app_settings.external_apis.jma_polling_interval_minutes
        
        # 最後のポーリング時刻
        self.last_poll_time: Optional[datetime] = None
        
        # エラー回数
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        logger.info(
            f"JMA Polling Service initialized - "
            f"Environment: {self.environment}, "
            f"Interval: {self.polling_interval_minutes} minutes"
        )
    
    async def start(self):
        """ポーリングサービスを開始"""
        if self.is_running:
            logger.warning("JMA polling service is already running")
            return
        
        # テストモードではJMAポーリングを実行しない
        if app_settings.test_mode:
            logger.info(
                "JMA polling service is disabled in TEST_MODE. "
                "Set TEST_MODE=false to enable JMA data collection."
            )
            return
        
        # JMAフィードURLが設定されているか確認
        jma_feed_urls = app_settings.external_apis.jma_feed_urls
        if not jma_feed_urls:
            logger.warning(
                "JMA feed URLs not configured. JMA polling service will not start."
            )
            return
        
        self.is_running = True
        self._polling_task = asyncio.create_task(self._polling_loop())
        logger.info("JMA polling service started")
    
    async def stop(self):
        """ポーリングサービスを停止"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        logger.info("JMA polling service stopped")
    
    async def _polling_loop(self):
        """ポーリングループ"""
        # 初回は即座に実行
        await self._poll_jma_feeds()
        
        while self.is_running:
            try:
                # 次回実行まで待機
                await asyncio.sleep(self.polling_interval_minutes * 60)
                
                if not self.is_running:
                    break
                
                # JMAフィードをポーリング
                await self._poll_jma_feeds()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in JMA polling loop: {e}", exc_info=True)
                self.consecutive_errors += 1
                
                # 連続エラーが多い場合は長めに待機
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.error(
                        f"Too many consecutive errors ({self.consecutive_errors}). "
                        f"Waiting 30 minutes before retry."
                    )
                    await asyncio.sleep(1800)  # 30分待機
                    self.consecutive_errors = 0
                else:
                    await asyncio.sleep(60)  # 1分待機
    
    async def _poll_jma_feeds(self):
        """JMAフィードをポーリング"""
        try:
            logger.info("Starting JMA feed polling...")
            start_time = datetime.now()
            
            # JMAPollerToolを実行
            result = await self.jma_poller._arun()
            
            # 成功したらエラーカウントをリセット
            self.consecutive_errors = 0
            self.last_poll_time = datetime.now()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"JMA feed polling completed in {elapsed:.2f} seconds: {result}")
            
        except Exception as e:
            logger.error(f"Failed to poll JMA feeds: {e}", exc_info=True)
            self.consecutive_errors += 1
    
    def get_status(self) -> Dict[str, Any]:
        """サービスのステータスを取得"""
        return {
            "is_running": self.is_running,
            "environment": self.environment,
            "polling_interval_minutes": self.polling_interval_minutes,
            "last_poll_time": self.last_poll_time.isoformat() if self.last_poll_time else None,
            "consecutive_errors": self.consecutive_errors,
            "jma_feed_urls_configured": bool(os.getenv("JMA_FEED_URLS"))
        }


# シングルトンインスタンス
jma_polling_service = JMAPollingService()


async def start_jma_polling():
    """JMAポーリングを開始（main.pyから呼び出す用）"""
    await jma_polling_service.start()


async def stop_jma_polling():
    """JMAポーリングを停止（main.pyから呼び出す用）"""
    await jma_polling_service.stop()