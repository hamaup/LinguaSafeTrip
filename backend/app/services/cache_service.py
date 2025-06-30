"""
統合キャッシュサービス
リアルタイム情報の効率的なキャッシュ管理
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import json

from app.db.firestore_client import get_db
from app.config.app_settings import app_settings

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """キャッシュタイプ"""
    # Firestore永続キャッシュ
    WARNING = "warning"  # 警報・注意報（1分）
    HAZARD = "hazard"  # ハザードマップ（24時間）
    ELEVATION = "elevation"  # 標高情報（30日）
    RISK_ASSESSMENT = "risk_assessment"  # リスク評価（5分）
    AREA_CODE = "area_code"  # 地域コード（永続）
    SHELTER = "shelter"  # 避難所情報（30日）
    
    # 政府API統合キャッシュ
    GOV_API_SHELTER = "gov_api_shelter"  # 政府API避難所（30日）
    GOV_API_HAZARD = "gov_api_hazard"  # 政府APIハザード（30分）
    GOV_API_ELEVATION = "gov_api_elevation"  # 政府API標高（24時間）
    GOV_API_HEALTH = "gov_api_health"  # APIヘルス状態（5分）
    
    # インメモリキャッシュ
    TRANSLATION = "translation"  # 翻訳結果（24時間）
    LANGUAGE_DETECTION = "language_detection"  # 言語検出（30分）
    LLM_CLIENT = "llm_client"  # LLMクライアント（永続）
    NEWS = "news"  # ニュース情報（7日）


class CacheService:
    """統合キャッシュサービス"""
    
    # インメモリキャッシュタイプ
    MEMORY_CACHE_TYPES = {
        CacheType.TRANSLATION,
        CacheType.LANGUAGE_DETECTION,
        CacheType.LLM_CLIENT,
        CacheType.NEWS
    }
    
    def __init__(self):
        """サービスの初期化"""
        self.firestore_db = get_db()
        self.cache_collection = self.firestore_db.collection("unified_cache")
        
        # インメモリキャッシュの初期化
        self.memory_caches: Dict[CacheType, Dict[str, Any]] = {
            cache_type: {} for cache_type in self.MEMORY_CACHE_TYPES
        }
        self.memory_cache_metadata: Dict[str, Dict[str, Any]] = {}
        
    def _generate_cache_key(self, cache_type: CacheType, params: Dict[str, Any]) -> str:
        """キャッシュキーを生成"""
        # パラメータを正規化してハッシュ化
        normalized_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(normalized_params.encode()).hexdigest()[:8]
        return f"{cache_type.value}_{param_hash}"
    
    async def get(
        self, 
        cache_type: CacheType, 
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """キャッシュからデータを取得"""
        try:
            cache_key = self._generate_cache_key(cache_type, params)
            
            # インメモリキャッシュの場合
            if cache_type in self.MEMORY_CACHE_TYPES:
                return self._get_from_memory(cache_type, cache_key)
            
            # Firestoreキャッシュの場合
            doc = self.cache_collection.document(cache_key).get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            
            # TTLチェック（永続キャッシュ以外）
            ttl_config = app_settings.cache.ttl_minutes.get(cache_type.value, 0)
            if ttl_config > 0:
                expires_at = data.get('expires_at')
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    
                    if expires_at < datetime.now(timezone.utc):
                        # 期限切れデータを削除
                        self.cache_collection.document(cache_key).delete()
                        return None
            
            logger.info(f"Cache hit: {cache_key}")
            return data.get('data')
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        cache_type: CacheType, 
        params: Dict[str, Any], 
        data: Any,
        custom_ttl_minutes: Optional[int] = None
    ) -> bool:
        """キャッシュにデータを保存"""
        try:
            cache_key = self._generate_cache_key(cache_type, params)
            
            # インメモリキャッシュの場合
            if cache_type in self.MEMORY_CACHE_TYPES:
                return self._set_to_memory(cache_type, cache_key, data, custom_ttl_minutes)
            
            # TTL計算（設定ファイルから取得）
            ttl_minutes = custom_ttl_minutes or app_settings.cache.ttl_minutes.get(
                cache_type.value, 
                1440  # デフォルト24時間
            )
            expires_at = None
            if ttl_minutes > 0:
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
            
            cache_data = {
                'cache_type': cache_type.value,
                'params': params,
                'data': data,
                'cached_at': datetime.now(timezone.utc),
                'expires_at': expires_at,
                'hit_count': 0
            }
            
            # Firestoreに保存
            self.cache_collection.document(cache_key).set(cache_data)
            logger.info(f"Cache set: {cache_key} (TTL: {ttl_minutes}min)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, cache_type: CacheType, params: Optional[Dict[str, Any]] = None):
        """キャッシュを無効化"""
        try:
            # インメモリキャッシュの場合
            if cache_type in self.MEMORY_CACHE_TYPES:
                cache = self.memory_caches.get(cache_type, {})
                if params:
                    cache_key = self._generate_cache_key(cache_type, params)
                    cache.pop(cache_key, None)
                    self.memory_cache_metadata.pop(cache_key, None)
                    logger.info(f"Memory cache invalidated: {cache_key}")
                else:
                    # タイプ全体をクリア
                    cache.clear()
                    # 該当するメタデータも削除
                    keys_to_remove = [k for k, v in self.memory_cache_metadata.items() 
                                     if v.get('cache_type') == cache_type.value]
                    for key in keys_to_remove:
                        self.memory_cache_metadata.pop(key, None)
                    logger.info(f"All {cache_type.value} memory caches invalidated")
                return
            
            # Firestoreキャッシュの場合
            if params:
                # 特定のキャッシュを削除
                cache_key = self._generate_cache_key(cache_type, params)
                self.cache_collection.document(cache_key).delete()
                logger.info(f"Cache invalidated: {cache_key}")
            else:
                # タイプ全体を削除
                docs = self.cache_collection.where('cache_type', '==', cache_type.value).stream()
                for doc in docs:
                    doc.reference.delete()
                logger.info(f"All {cache_type.value} caches invalidated")
                
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得"""
        try:
            stats = {
                'total_items': 0,
                'by_type': {},
                'expired_count': 0,
                'total_hit_count': 0,
                'memory_cache_stats': {}
            }
            
            docs = self.cache_collection.stream()
            now = datetime.now(timezone.utc)
            
            for doc in docs:
                data = doc.to_dict()
                cache_type = data.get('cache_type', 'unknown')
                
                stats['total_items'] += 1
                stats['by_type'][cache_type] = stats['by_type'].get(cache_type, 0) + 1
                stats['total_hit_count'] += data.get('hit_count', 0)
                
                # 期限切れチェック
                expires_at = data.get('expires_at')
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    if expires_at < now:
                        stats['expired_count'] += 1
            
            # メモリキャッシュの統計も追加
            for cache_type in self.MEMORY_CACHE_TYPES:
                cache = self.memory_caches.get(cache_type, {})
                memory_stats = {
                    'items': len(cache),
                    'hit_count': sum(
                        self.memory_cache_metadata.get(k, {}).get('hit_count', 0)
                        for k in cache.keys()
                    )
                }
                stats['memory_cache_stats'][cache_type.value] = memory_stats
                stats['total_items'] += memory_stats['items']
                stats['total_hit_count'] += memory_stats['hit_count']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def cleanup_expired(self) -> int:
        """期限切れキャッシュをクリーンアップ"""
        try:
            deleted_count = 0
            now = datetime.now(timezone.utc)
            
            # 期限切れドキュメントを検索
            docs = self.cache_collection.where('expires_at', '<', now).stream()
            
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} expired cache items")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0
    
    async def increment_hit_count(self, cache_type: CacheType, params: Dict[str, Any]):
        """ヒットカウントをインクリメント"""
        try:
            cache_key = self._generate_cache_key(cache_type, params)
            doc_ref = self.cache_collection.document(cache_key)
            
            # トランザクションでカウントを更新
            @firestore.transactional
            def update_hit_count(transaction):
                doc = doc_ref.get(transaction=transaction)
                if doc.exists:
                    transaction.update(doc_ref, {
                        'hit_count': (doc.to_dict().get('hit_count', 0) + 1),
                        'last_accessed': datetime.now(timezone.utc)
                    })
            
            # Firestoreトランザクションを実行
            from google.cloud import firestore
            update_hit_count(self.firestore_db.transaction())
            
        except Exception as e:
            pass

    def _get_from_memory(self, cache_type: CacheType, cache_key: str) -> Optional[Any]:
        """インメモリキャッシュから取得"""
        cache = self.memory_caches.get(cache_type, {})
        
        if cache_key not in cache:
            return None
        
        # TTLチェック
        metadata = self.memory_cache_metadata.get(cache_key, {})
        expires_at = metadata.get('expires_at')
        
        if expires_at and expires_at < datetime.now(timezone.utc):
            # 期限切れデータを削除
            cache.pop(cache_key, None)
            self.memory_cache_metadata.pop(cache_key, None)
            return None
        
        logger.info(f"Memory cache hit: {cache_key}")
        # ヒットカウントを増やす
        metadata['hit_count'] = metadata.get('hit_count', 0) + 1
        metadata['last_accessed'] = datetime.now(timezone.utc)
        
        return cache[cache_key]
    
    def _set_to_memory(
        self, 
        cache_type: CacheType, 
        cache_key: str, 
        data: Any,
        custom_ttl_minutes: Optional[int] = None
    ) -> bool:
        """インメモリキャッシュに保存"""
        cache = self.memory_caches.get(cache_type, {})
        
        # TTL計算（設定ファイルから取得）
        ttl_minutes = custom_ttl_minutes or app_settings.cache.ttl_minutes.get(
            cache_type.value,
            1440  # デフォルト24時間
        )
        expires_at = None
        if ttl_minutes > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        
        # データを保存
        cache[cache_key] = data
        
        # メタデータを保存
        self.memory_cache_metadata[cache_key] = {
            'cache_type': cache_type.value,
            'cached_at': datetime.now(timezone.utc),
            'expires_at': expires_at,
            'hit_count': 0,
            'last_accessed': datetime.now(timezone.utc)
        }
        
        logger.info(f"Memory cache set: {cache_key} (TTL: {ttl_minutes}min)")
        
        # メモリサイズ制限チェック
        max_items = app_settings.cache.memory_cache_limits.get(cache_type.value, 1000)
        if len(cache) > max_items:
            # クリーンアップ闾値まで削減
            cleanup_target = int(max_items * app_settings.cache.cleanup_threshold)
            self._cleanup_memory_cache(cache_type, max_items=cleanup_target)
        
        return True
    
    def _cleanup_memory_cache(self, cache_type: CacheType, max_items: int = 800):
        """メモリキャッシュのクリーンアップ"""
        cache = self.memory_caches.get(cache_type, {})
        
        # 最終アクセス時刻でソート
        sorted_keys = sorted(
            cache.keys(),
            key=lambda k: self.memory_cache_metadata.get(k, {}).get('last_accessed', datetime.min),
            reverse=False
        )
        
        # 古いエントリを削除
        for key in sorted_keys[max_items:]:
            cache.pop(key, None)
            self.memory_cache_metadata.pop(key, None)

# グローバルインスタンス
cache_service = CacheService()


# ヘルパー関数
async def get_cached_or_fetch(
    cache_type: CacheType,
    params: Dict[str, Any],
    fetch_func,
    custom_ttl_minutes: Optional[int] = None
) -> Any:
    """キャッシュまたはフェッチのヘルパー関数"""
    # キャッシュから取得
    cached_data = await cache_service.get(cache_type, params)
    if cached_data is not None:
        await cache_service.increment_hit_count(cache_type, params)
        return cached_data
    
    # フェッチして保存
    data = await fetch_func()
    if data is not None:
        await cache_service.set(cache_type, params, data, custom_ttl_minutes)
    
    return data