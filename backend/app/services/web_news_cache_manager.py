"""
Web検索ニュースキャッシュマネージャー
実際のWeb検索結果を保存し、デバッグ用モックデータとして活用
"""

import json
import logging
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from app.tools.web_search_tools import get_web_search_tool
from app.config import app_settings

logger = logging.getLogger(__name__)

@dataclass
class CachedNewsItem:
    """キャッシュされたニュース項目"""
    title: str
    content: str
    url: str
    source: str
    published_at: str
    collected_at: str
    search_query: str
    relevance_score: float = 0.0
    category: str = "general"

class WebNewsCacheManager:
    """Web検索ニュースのキャッシュ管理"""
    
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent / "resources" / "mock_data" / "web_news_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.normal_cache_file = self.cache_dir / "normal_web_news.json"
        self.emergency_cache_file = self.cache_dir / "emergency_web_news.json"
        
        self.web_search_tool = get_web_search_tool()
        
        # キャッシュ設定
        self.max_cache_items = 50
        self.cache_expiry_days = 7
        
        logger.info(f"WebNewsCacheManager initialized - Cache dir: {self.cache_dir}")
    
    async def collect_and_cache_normal_news(self, force_refresh: bool = False) -> List[CachedNewsItem]:
        """平常時ニュースを収集してキャッシュ"""
        try:
            # 既存キャッシュをチェック
            if not force_refresh:
                cached_news = self._load_cached_news("normal")
                if cached_news and len(cached_news) >= 10:
                    logger.info(f"Using cached normal news: {len(cached_news)} items")
                    return cached_news
            
            # 平常時の検索クエリ
            normal_queries = [
                "防災対策 備蓄 家庭",
                "地震対策 家具固定 安全",
                "台風対策 避難 準備",
                "防災グッズ おすすめ 必需品",
                "ハザードマップ 確認方法",
                "避難訓練 地域 参加",
                "非常食 備蓄 ローリングストック",
                "防災アプリ 災害情報"
            ]
            
            collected_news = []
            
            for query in normal_queries:
                try:
                    # Web検索実行
                    search_result = await self.web_search_tool.ainvoke({
                        "query": query,
                        "max_results": 5
                    })
                    
                    # 検索結果はリスト形式で返される
                    if search_result and isinstance(search_result, list):
                        for item in search_result:
                            news_item = CachedNewsItem(
                                title=item.get("title", ""),
                                content=item.get("snippet", ""),
                                url=str(item.get("link", "")),  # HttpUrlオブジェクトを文字列に変換
                                source=item.get("source_domain", ""),
                                published_at=datetime.now(timezone.utc).isoformat(),
                                collected_at=datetime.now(timezone.utc).isoformat(),
                                search_query=query,
                                relevance_score=item.get("relevance_score", 0.8),
                                category="prevention"
                            )
                            collected_news.append(news_item)
                    
                    # APIレート制限を考慮
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error searching for '{query}': {e}")
                    continue
            
            # キャッシュに保存
            self._save_cached_news(collected_news, "normal")
            
            logger.info(f"📰 Collected and cached {len(collected_news)} normal news items")
            return collected_news
            
        except Exception as e:
            logger.error(f"Error collecting normal news: {e}")
            return []
    
    async def collect_and_cache_emergency_news(self, force_refresh: bool = False) -> List[CachedNewsItem]:
        """緊急時ニュースを収集してキャッシュ"""
        try:
            # 既存キャッシュをチェック
            if not force_refresh:
                cached_news = self._load_cached_news("emergency")
                if cached_news and len(cached_news) >= 10:
                    logger.info(f"Using cached emergency news: {len(cached_news)} items")
                    return cached_news
            
            logger.warning("🚨 Collecting fresh emergency disaster news from web...")
            
            # 緊急時の検索クエリ
            emergency_queries = [
                "地震速報 最新 被害状況",
                "地震 余震 震度 情報",
                "地震 復旧 ライフライン 状況",
                "津波警報 避難指示",
                "台風 接近 交通情報",
                "豪雨 河川氾濫 避難",
                "停電 復旧情報 ライフライン",
                "避難所 開設 情報",
                "緊急事態宣言 災害",
                "安否確認 災害用伝言ダイヤル"
            ]
            
            collected_news = []
            
            for query in emergency_queries:
                try:
                    # Web検索実行
                    search_result = await self.web_search_tool.ainvoke({
                        "query": query,
                        "max_results": 5
                    })
                    
                    # 検索結果はリスト形式で返される
                    if search_result and isinstance(search_result, list):
                        for item in search_result:
                            news_item = CachedNewsItem(
                                title=item.get("title", ""),
                                content=item.get("snippet", ""),
                                url=str(item.get("link", "")),  # HttpUrlオブジェクトを文字列に変換
                                source=item.get("source_domain", ""),
                                published_at=datetime.now(timezone.utc).isoformat(),
                                collected_at=datetime.now(timezone.utc).isoformat(),
                                search_query=query,
                                relevance_score=item.get("relevance_score", 0.9),
                                category="emergency"
                            )
                            collected_news.append(news_item)
                    
                    # APIレート制限を考慮
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error searching for '{query}': {e}")
                    continue
            
            # キャッシュに保存
            self._save_cached_news(collected_news, "emergency")
            
            logger.warning(f"🚨 Collected and cached {len(collected_news)} emergency news items")
            return collected_news
            
        except Exception as e:
            logger.error(f"Error collecting emergency news: {e}")
            return []
    
    def _load_cached_news(self, news_type: str) -> List[CachedNewsItem]:
        """キャッシュからニュースを読み込み"""
        try:
            cache_file = self.normal_cache_file if news_type == "normal" else self.emergency_cache_file
            
            if not cache_file.exists():
                return []
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 期限切れチェック
            now = datetime.now(timezone.utc)
            valid_items = []
            
            for item_data in data.get("items", []):
                collected_at = datetime.fromisoformat(item_data["collected_at"].replace('Z', '+00:00'))
                if (now - collected_at).days < self.cache_expiry_days:
                    valid_items.append(CachedNewsItem(**item_data))
            
            logger.info(f"Loaded {len(valid_items)} valid cached {news_type} news items")
            return valid_items
            
        except Exception as e:
            logger.error(f"Error loading cached {news_type} news: {e}")
            return []
    
    def _save_cached_news(self, news_items: List[CachedNewsItem], news_type: str):
        """ニュースをキャッシュに保存"""
        try:
            cache_file = self.normal_cache_file if news_type == "normal" else self.emergency_cache_file
            
            # 既存データと統合
            existing_items = self._load_cached_news(news_type)
            
            # 重複除去（URLベース）
            existing_urls = {item.url for item in existing_items}
            new_items = [item for item in news_items if item.url not in existing_urls]
            
            # 統合リスト
            all_items = existing_items + new_items
            
            # 最大数に制限
            if len(all_items) > self.max_cache_items:
                # 新しいものから保持
                all_items = sorted(all_items, key=lambda x: x.collected_at, reverse=True)[:self.max_cache_items]
            
            # 保存
            cache_data = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "news_type": news_type,
                "total_items": len(all_items),
                "items": [asdict(item) for item in all_items]
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(all_items)} {news_type} news items to cache")
            
        except Exception as e:
            logger.error(f"Error saving {news_type} news cache: {e}")
    
    def _extract_domain(self, url: str) -> str:
        """URLからドメイン名を抽出"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # www.を除去
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def get_random_cached_news(self, news_type: str, count: int = 5) -> List[CachedNewsItem]:
        """キャッシュからランダムにニュースを取得"""
        import random
        
        cached_items = self._load_cached_news(news_type)
        if not cached_items:
            return []
        
        # ランダム選択
        selected_count = min(count, len(cached_items))
        selected_items = random.sample(cached_items, selected_count)
        
        logger.info(f"Selected {len(selected_items)} random {news_type} news items from cache")
        return selected_items
    
    def clear_cache(self, news_type: Optional[str] = None):
        """キャッシュをクリア"""
        try:
            if news_type is None or news_type == "normal":
                if self.normal_cache_file.exists():
                    self.normal_cache_file.unlink()
                    logger.info("Cleared normal news cache")
            
            if news_type is None or news_type == "emergency":
                if self.emergency_cache_file.exists():
                    self.emergency_cache_file.unlink()
                    logger.warning("Cleared emergency news cache")
                    
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    async def refresh_all_caches(self):
        """全キャッシュを更新"""
        logger.info("🔄 Refreshing all news caches...")
        
        # 並行して実行
        tasks = [
            self.collect_and_cache_normal_news(force_refresh=True),
            self.collect_and_cache_emergency_news(force_refresh=True)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results

# グローバルインスタンス
web_news_cache_manager = WebNewsCacheManager()