"""
TTL付きインメモリキャッシュユーティリティ
メモリリークを防ぐための自動クリーンアップ機能付き
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, TypeVar, Generic
import hashlib
import json
from collections import OrderedDict
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')

class TTLCache(Generic[T]):
    """TTL付きキャッシュクラス"""
    
    def __init__(
        self, 
        name: str,
        default_ttl_seconds: int = 3600,
        max_size: int = 1000,
        cleanup_interval_seconds: int = 300
    ):
        """
        Args:
            name: キャッシュ名（ログ用）
            default_ttl_seconds: デフォルトTTL（秒）
            max_size: 最大エントリ数
            cleanup_interval_seconds: クリーンアップ間隔（秒）
        """
        self.name = name
        self.default_ttl_seconds = default_ttl_seconds
        self.max_size = max_size
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # OrderedDictを使用してLRU的な動作を実現
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # 自動クリーンアップを開始
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """バックグラウンドクリーンアップタスクを開始"""
        try:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(self._periodic_cleanup())
            # 弱参照を使用してタスクがGCされないようにする
            weakref.finalize(self, self._stop_cleanup_task)
        except RuntimeError:
            # イベントループがない場合はスキップ
            pass
    
    def _stop_cleanup_task(self):
        """クリーンアップタスクを停止"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
    
    async def _periodic_cleanup(self):
        """定期的なクリーンアップ"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                expired_count = self._cleanup_expired()
                if expired_count > 0:
                    logger.info(f"{self.name} cache: Cleaned {expired_count} expired entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.name} cache cleanup error: {e}")
    
    def _cleanup_expired(self) -> int:
        """期限切れエントリをクリーンアップ"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry["expires_at"] < now:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1
        
        return len(expired_keys)
    
    def _evict_if_needed(self):
        """必要に応じて古いエントリを削除"""
        while len(self._cache) >= self.max_size:
            # 最も古いエントリを削除（FIFO）
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats["evictions"] += 1
    
    def get(self, key: str) -> Optional[T]:
        """キャッシュから値を取得"""
        entry = self._cache.get(key)
        
        if entry is None:
            self._stats["misses"] += 1
            return None
        
        # TTLチェック
        if entry["expires_at"] < datetime.utcnow():
            del self._cache[key]
            self._stats["expirations"] += 1
            self._stats["misses"] += 1
            return None
        
        # LRU: アクセスされたエントリを最後に移動
        self._cache.move_to_end(key)
        
        self._stats["hits"] += 1
        return entry["value"]
    
    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None):
        """キャッシュに値を設定"""
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # サイズ制限チェック
        if key not in self._cache:
            self._evict_if_needed()
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        
        # LRU: 新しいエントリを最後に移動
        self._cache.move_to_end(key)
        
        self._stats["sets"] += 1
        # Cache entry set: {key}
    
    def delete(self, key: str) -> bool:
        """キャッシュから削除"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """キャッシュをクリア"""
        self._cache.clear()
        logger.info(f"{self.name} cache cleared")
    
    def size(self) -> int:
        """現在のキャッシュサイズ"""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報"""
        hit_rate = 0
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests > 0:
            hit_rate = self._stats["hits"] / total_requests
        
        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate": hit_rate,
            "max_size": self.max_size
        }
    
    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """引数からキャッシュキーを生成"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_json.encode()).hexdigest()


# デコレータ版
def ttl_cache(
    ttl_seconds: int = 3600,
    max_size: int = 1000,
    key_prefix: str = ""
):
    """TTLキャッシュデコレータ"""
    cache_instance = None
    
    def decorator(func):
        nonlocal cache_instance
        
        async def wrapper(*args, **kwargs):
            nonlocal cache_instance
            
            # キャッシュインスタンスの遅延初期化
            if cache_instance is None:
                cache_name = f"{key_prefix}{func.__name__}"
                cache_instance = TTLCache(
                    name=cache_name,
                    default_ttl_seconds=ttl_seconds,
                    max_size=max_size
                )
            
            # キャッシュキー生成
            cache_key = TTLCache.make_key(*args, **kwargs)
            
            # キャッシュから取得
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 関数実行
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # キャッシュに保存
            cache_instance.set(cache_key, result)
            
            return result
        
        # キャッシュインスタンスへのアクセスを提供
        wrapper.cache = lambda: cache_instance
        wrapper.clear_cache = lambda: cache_instance.clear() if cache_instance else None
        
        return wrapper
    
    return decorator