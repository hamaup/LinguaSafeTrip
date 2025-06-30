from typing import Dict, Optional
import redis
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VertexSearchKillSwitch:
    """
    Vertex AI Search用のキルスイッチ実装
    コスト超過やエラー多発時に自動的にサービスを停止
    """
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        # キルスイッチ設定
        self.COST_THRESHOLD = float(os.getenv("VERTEX_SEARCH_COST_THRESHOLD", "5.0"))  # $5
        self.ERROR_RATE_THRESHOLD = float(os.getenv("VERTEX_SEARCH_ERROR_RATE", "0.1"))  # 10%
        self.QUERY_LIMIT_DAILY = int(os.getenv("VERTEX_SEARCH_DAILY_LIMIT", "300"))
        self.QUERY_LIMIT_MONTHLY = int(os.getenv("VERTEX_SEARCH_MONTHLY_LIMIT", "9000"))
        
        self.KEY_PREFIX = "vertex_search:killswitch:"
    
    def is_service_enabled(self) -> bool:
        """
        サービスが有効かチェック
        複数の条件をチェックして、いずれかに該当したらFalse
        """
        # 手動キルスイッチ
        if self._is_manually_disabled():
            logger.warning("Vertex Search is manually disabled")
            return False
        
        # コスト制限チェック
        if self._is_cost_exceeded():
            logger.error("Vertex Search cost limit exceeded")
            self._disable_service("cost_exceeded")
            return False
        
        # クエリ数制限チェック
        if self._is_query_limit_exceeded():
            logger.error("Vertex Search query limit exceeded")
            self._disable_service("query_limit_exceeded")
            return False
        
        # エラー率チェック
        if self._is_error_rate_high():
            logger.error("Vertex Search error rate too high")
            self._disable_service("high_error_rate")
            return False
        
        return True
    
    def _is_manually_disabled(self) -> bool:
        """手動で無効化されているかチェック"""
        return self.redis_client.get(f"{self.KEY_PREFIX}manual_disable") == b"1"
    
    def _is_cost_exceeded(self) -> bool:
        """コスト超過チェック"""
        estimated_cost = self._estimate_current_cost()
        return estimated_cost > self.COST_THRESHOLD
    
    def _is_query_limit_exceeded(self) -> bool:
        """クエリ数制限チェック"""
        # 日次チェック
        today = datetime.now().strftime("%Y%m%d")
        daily_count = int(self.redis_client.get(f"vertex_search:query_count:{today}") or 0)
        if daily_count > self.QUERY_LIMIT_DAILY:
            return True
        
        # 月次チェック
        monthly_count = self._get_monthly_query_count()
        return monthly_count > self.QUERY_LIMIT_MONTHLY
    
    def _is_error_rate_high(self) -> bool:
        """エラー率チェック（直近100リクエスト）"""
        error_count = int(self.redis_client.get(f"{self.KEY_PREFIX}error_count") or 0)
        total_count = int(self.redis_client.get(f"{self.KEY_PREFIX}total_count") or 1)
        
        if total_count < 100:
            return False  # サンプル数が少ない場合はチェックしない
        
        error_rate = error_count / total_count
        return error_rate > self.ERROR_RATE_THRESHOLD
    
    def _estimate_current_cost(self) -> float:
        """現在の推定コスト計算（月初からの累計）"""
        monthly_queries = self._get_monthly_query_count()
        
        # 無料枠を超えた分のコスト計算
        billable_queries = max(0, monthly_queries - 10000)
        
        # Standard料金: $1.50 per 1000 queries
        query_cost = (billable_queries / 1000) * 1.5
        
        # ストレージコスト（10GB超過分）
        # 現時点では10GB未満想定なので0
        storage_cost = 0
        
        return query_cost + storage_cost
    
    def _get_monthly_query_count(self) -> int:
        """月次クエリ数取得"""
        month = datetime.now().strftime("%Y%m")
        total = 0
        
        # 月の各日のカウントを集計
        for day in range(1, 32):
            day_key = f"vertex_search:query_count:{month}{day:02d}"
            count = self.redis_client.get(day_key)
            if count:
                total += int(count)
        
        return total
    
    def _disable_service(self, reason: str):
        """サービスを無効化"""
        pipe = self.redis_client.pipeline()
        pipe.set(f"{self.KEY_PREFIX}disabled", "1")
        pipe.set(f"{self.KEY_PREFIX}disabled_reason", reason)
        pipe.set(f"{self.KEY_PREFIX}disabled_at", datetime.now().isoformat())
        pipe.execute()
        
        logger.critical(f"Vertex Search disabled: {reason}")
    
    def enable_service(self):
        """サービスを手動で有効化"""
        pipe = self.redis_client.pipeline()
        pipe.delete(f"{self.KEY_PREFIX}disabled")
        pipe.delete(f"{self.KEY_PREFIX}manual_disable")
        pipe.delete(f"{self.KEY_PREFIX}disabled_reason")
        pipe.delete(f"{self.KEY_PREFIX}disabled_at")
        pipe.execute()
        
        logger.info("Vertex Search manually enabled")
    
    def disable_service(self):
        """サービスを手動で無効化"""
        self.redis_client.set(f"{self.KEY_PREFIX}manual_disable", "1")
        logger.info("Vertex Search manually disabled")
    
    def record_request(self, success: bool):
        """リクエスト結果を記録（エラー率計算用）"""
        pipe = self.redis_client.pipeline()
        
        # 総リクエスト数をインクリメント
        pipe.incr(f"{self.KEY_PREFIX}total_count")
        
        # エラーの場合はエラーカウントもインクリメント
        if not success:
            pipe.incr(f"{self.KEY_PREFIX}error_count")
        
        # カウンターをリセット（100件ごと）
        total = int(self.redis_client.get(f"{self.KEY_PREFIX}total_count") or 0)
        if total >= 100:
            pipe.set(f"{self.KEY_PREFIX}total_count", "0")
            pipe.set(f"{self.KEY_PREFIX}error_count", "0")
        
        pipe.execute()
    
    def get_status(self) -> Dict:
        """キルスイッチの現在状態を取得"""
        is_enabled = self.is_service_enabled()
        
        status = {
            "enabled": is_enabled,
            "cost": {
                "current": self._estimate_current_cost(),
                "threshold": self.COST_THRESHOLD
            },
            "queries": {
                "daily": {
                    "current": int(self.redis_client.get(
                        f"vertex_search:query_count:{datetime.now().strftime('%Y%m%d')}"
                    ) or 0),
                    "limit": self.QUERY_LIMIT_DAILY
                },
                "monthly": {
                    "current": self._get_monthly_query_count(),
                    "limit": self.QUERY_LIMIT_MONTHLY
                }
            },
            "error_rate": {
                "errors": int(self.redis_client.get(f"{self.KEY_PREFIX}error_count") or 0),
                "total": int(self.redis_client.get(f"{self.KEY_PREFIX}total_count") or 0),
                "threshold": self.ERROR_RATE_THRESHOLD
            }
        }
        
        # 無効化されている場合は理由を追加
        if not is_enabled:
            status["disabled_reason"] = self.redis_client.get(
                f"{self.KEY_PREFIX}disabled_reason"
            ).decode() if self.redis_client.get(f"{self.KEY_PREFIX}disabled_reason") else None
            status["disabled_at"] = self.redis_client.get(
                f"{self.KEY_PREFIX}disabled_at"
            ).decode() if self.redis_client.get(f"{self.KEY_PREFIX}disabled_at") else None
        
        return status