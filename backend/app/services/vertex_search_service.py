from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import retry
from typing import List, Dict, Optional
import redis
import json
import hashlib
import os
from datetime import datetime
import logging
from ..config.vertex_search_config import VertexSearchConfig
from .vertex_search_killswitch import VertexSearchKillSwitch

logger = logging.getLogger(__name__)

class VertexSearchService:
    """
    Vertex AI Search サービス実装
    キルスイッチとキャッシュ機能付き
    """
    
    def __init__(self):
        # 設定
        self.config = VertexSearchConfig()
        self.killswitch = VertexSearchKillSwitch()
        
        # クライアント初期化
        self.client = discoveryengine.SearchServiceClient()
        
        # Redis初期化
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        
        # サービング設定
        self.serving_config = (
            f"projects/{self.config.PROJECT_ID}/"
            f"locations/{self.config.LOCATION}/"
            f"dataStores/{self.config.DATA_STORE_ID}/"
            "servingConfigs/default_config"
        )
    
    def _get_cache_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """キャッシュキー生成"""
        cache_data = f"{query}:{json.dumps(filters or {}, sort_keys=True)}"
        return f"{self.config.CACHE_KEY_PREFIX}{hashlib.md5(cache_data.encode()).hexdigest()}"
    
    def _build_filter_expression(self, filters: Dict) -> str:
        """フィルター式を構築"""
        expressions = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                expressions.append(f'{key} = "{value}"')
            elif isinstance(value, (int, float)):
                expressions.append(f'{key} = {value}')
            elif isinstance(value, list):
                values_str = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                expressions.append(f'{key} IN ({values_str})')
        
        return ' AND '.join(expressions)
    
    @retry.Retry(deadline=30.0)
    def search(
        self, 
        query: str, 
        filters: Optional[Dict] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Vertex AI Search実行（キャッシュ・キルスイッチ付き）
        
        Args:
            query: 検索クエリ
            filters: フィルター条件
            top_k: 返す結果数
        
        Returns:
            検索結果リスト
        """
        # キルスイッチチェック
        if not self.killswitch.is_service_enabled():
            logger.warning("Vertex Search is disabled by killswitch")
            return []  # 空の結果を返す
        
        # キャッシュチェック
        cache_key = self._get_cache_key(query, filters)
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for query: {query}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {str(e)}")
        
        try:
            # Vertex AI Search リクエスト構築
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config,
                query=query,
                page_size=top_k or self.config.MAX_RESULTS,
                query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                    condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO
                ),
                spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                    mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
                ),
                # コンテンツ検索仕様
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True,
                        max_snippet_count=2
                    ),
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=3,
                        include_citations=True
                    ) if self.config.ENABLE_GENERATIVE_ANSWERS else None
                )
            )
            
            # フィルター適用
            if filters:
                request.filter = self._build_filter_expression(filters)
            
            # 検索実行
            logger.info(f"Executing Vertex Search for query: {query}")
            response = self.client.search(request=request)
            
            # 結果整形
            results = []
            for result in response.results:
                # ドキュメントデータ取得
                doc = result.document
                
                # 構造化データまたはJSONデータから情報抽出
                if hasattr(doc, 'struct_data') and doc.struct_data:
                    doc_data = dict(doc.struct_data)
                elif hasattr(doc, 'json_data') and doc.json_data:
                    doc_data = json.loads(doc.json_data)
                else:
                    doc_data = {}
                
                # スニペット取得
                snippets = []
                if hasattr(result, 'snippet') and result.snippet:
                    snippets = [result.snippet.snippet]
                
                results.append({
                    "id": doc.id if hasattr(doc, 'id') else doc.name,
                    "title": doc_data.get("title", ""),
                    "content": doc_data.get("content", ""),
                    "snippets": snippets,
                    "score": float(result.relevance_score) if hasattr(result, 'relevance_score') else 0.0,
                    "metadata": doc_data.get("metadata", {}),
                    "source": doc_data.get("source", "")
                })
            
            # キャッシュ保存
            try:
                self.redis_client.setex(
                    cache_key, 
                    self.config.CACHE_TTL, 
                    json.dumps(results)
                )
            except Exception as e:
                logger.warning(f"Cache write error: {str(e)}")
            
            # クエリカウント更新
            self._increment_query_count()
            
            # 成功を記録
            self.killswitch.record_request(success=True)
            
            logger.info(f"Vertex Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vertex Search error: {str(e)}")
            # エラーを記録
            self.killswitch.record_request(success=False)
            
            # エラー時は空の結果を返す（例外を投げない）
            return []
    
    def _increment_query_count(self):
        """クエリカウント更新"""
        today = datetime.now().strftime("%Y%m%d")
        count_key = f"{self.config.CACHE_KEY_PREFIX}query_count:{today}"
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(count_key)
            pipe.expire(count_key, 86400)  # 24時間後に自動削除
            pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to increment query count: {str(e)}")
    
    def clear_cache(self, query: Optional[str] = None):
        """キャッシュクリア"""
        if query:
            # 特定クエリのキャッシュクリア
            cache_key = self._get_cache_key(query)
            self.redis_client.delete(cache_key)
        else:
            # 全キャッシュクリア
            pattern = f"{self.config.CACHE_KEY_PREFIX}*"
            for key in self.redis_client.scan_iter(match=pattern):
                if not key.endswith("query_count:*"):
                    self.redis_client.delete(key)
    
    def get_stats(self) -> Dict:
        """統計情報取得"""
        today = datetime.now().strftime("%Y%m%d")
        daily_count_key = f"{self.config.CACHE_KEY_PREFIX}query_count:{today}"
        
        return {
            "daily_queries": int(self.redis_client.get(daily_count_key) or 0),
            "cache_keys": len(list(self.redis_client.scan_iter(
                match=f"{self.config.CACHE_KEY_PREFIX}*"
            ))),
            "killswitch_status": self.killswitch.get_status()
        }