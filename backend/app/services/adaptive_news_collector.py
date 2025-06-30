"""
適応的災害ニュース収集サービス
平常時: 災害予防・一般的災害ニュース
緊急時: 被災地の最新災害情報（位置特化型）
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from app.tools.web_search_tools import get_web_search_tool
from app.collectors.official_news_collector import collect_official_news_periodically
from app.schemas.common.location import Location
from app.utils.geo_utils import get_location_string
from app.db.firestore_client import get_db
# Mock news manager removed - using web_news_cache_manager instead
from app.services.web_news_cache_manager import web_news_cache_manager
from app.config import app_settings

logger = logging.getLogger(__name__)

class CollectionMode(str, Enum):
    """収集モード"""
    NORMAL = "normal"      # 平常時
    EMERGENCY = "emergency" # 緊急時

@dataclass
class NewsCollectionConfig:
    """ニュース収集設定"""
    mode: CollectionMode
    interval_minutes: int
    max_articles_per_cycle: int
    search_keywords: List[str]
    trusted_sources: List[str]
    location_specific: bool = False
    target_location: Optional[Location] = None

@dataclass
class CollectedNews:
    """収集されたニュース"""
    article_id: str
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    collected_at: datetime
    mode: CollectionMode
    location: Optional[Location] = None
    relevance_score: float = 0.0
    urgency_level: str = "normal"  # normal, high, critical, emergency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "collected_at": self.collected_at.isoformat(),
            "mode": self.mode,
            "location": {
                "latitude": self.location.latitude,
                "longitude": self.location.longitude
            } if self.location else None,
            "relevance_score": self.relevance_score,
            "urgency_level": self.urgency_level
        }

class AdaptiveNewsCollector:
    """適応的災害ニュース収集クラス"""
    
    def __init__(self):
        self.web_search_tool = get_web_search_tool()
        self.current_mode = CollectionMode.NORMAL
        self.is_running = False
        self._collector_task: Optional[asyncio.Task] = None
        
        # 環境設定
        self.environment = os.getenv("ENVIRONMENT", "production").lower()
        
        # .envファイルから間隔設定を取得
        normal_interval = int(os.getenv("NEWS_COLLECTION_NORMAL_INTERVAL_MINUTES", "60"))
        emergency_interval = int(os.getenv("NEWS_COLLECTION_EMERGENCY_INTERVAL_MINUTES", "2"))
        
        # 収集設定
        self.normal_config = NewsCollectionConfig(
            mode=CollectionMode.NORMAL,
            interval_minutes=normal_interval,
            max_articles_per_cycle=10,
            search_keywords=[
                "災害対策", "防災", "備蓄", "避難訓練", "地震対策",
                "台風対策", "洪水対策", "火災予防", "救急法",
                "防災グッズ", "非常食", "ハザードマップ"
            ],
            trusted_sources=[
                "bousai.go.jp",      # 内閣府防災
                "fdma.go.jp",        # 消防庁
                "jma.go.jp",         # 気象庁
                "nhk.or.jp",         # NHK
                "asahi.com",         # 朝日新聞
                "mainichi.jp",       # 毎日新聞
                "yomiuri.co.jp",     # 読売新聞
                "nikkei.com"         # 日経新聞
            ]
        )
        
        self.emergency_config = NewsCollectionConfig(
            mode=CollectionMode.EMERGENCY,
            interval_minutes=emergency_interval,
            max_articles_per_cycle=20,
            search_keywords=[
                "地震速報", "津波警報", "避難指示", "緊急事態",
                "被害状況", "道路状況", "交通情報", "避難所",
                "停電", "断水", "ライフライン", "救援",
                "安否確認", "災害対策本部"
            ],
            trusted_sources=[
                "jma.go.jp",         # 気象庁（最優先）
                "bousai.go.jp",      # 内閣府防災
                "nhk.or.jp",         # NHK
                "yahoo.co.jp",       # Yahoo!防災速報
                "weathernews.jp",    # ウェザーニュース
                "fdma.go.jp",        # 消防庁
                "kantei.go.jp",      # 首相官邸
                "cao.go.jp"          # 内閣府
            ],
            location_specific=True
        )
        
        # 収集データキャッシュ
        self.collected_news: Dict[str, CollectedNews] = {}
        self.emergency_locations: Set[str] = set()  # 緊急監視中の位置（緯度経度のハッシュ）
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Adaptive News Collector initialized - Environment: {self.environment}, "
                       f"Normal interval: {normal_interval}min, Emergency interval: {emergency_interval}min")

    async def start_collection(self):
        """ニュース収集を開始"""
        if self.is_running:
            logger.warning("Adaptive news collection is already running")
            return
        
        self.is_running = True
        self._collector_task = asyncio.create_task(self._collection_loop())
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
    async def stop_collection(self):
        """ニュース収集を停止"""
        self.is_running = False
        
        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
    def switch_to_emergency_mode(self, emergency_location: Location):
        """緊急モードに切り替え"""
        self.current_mode = CollectionMode.EMERGENCY
        self.emergency_config.target_location = emergency_location
        
        # 緊急位置を記録
        location_hash = f"{emergency_location.latitude:.4f}_{emergency_location.longitude:.4f}"
        self.emergency_locations.add(location_hash)
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
        else:
            logger.warning(f"🚨 Switched to EMERGENCY mode for location: {get_location_string(emergency_location)}")

    def switch_to_normal_mode(self):
        """平常モードに切り替え"""
        self.current_mode = CollectionMode.NORMAL
        self.emergency_locations.clear()
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
    async def add_emergency_location(self, location: Location):
        """緊急監視位置を追加"""
        location_hash = f"{location.latitude:.4f}_{location.longitude:.4f}"
        self.emergency_locations.add(location_hash)
        
        if self.current_mode == CollectionMode.NORMAL:
            self.switch_to_emergency_mode(location)
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
    
    async def remove_emergency_location(self, location: Location):
        """緊急監視位置を削除"""
        location_hash = f"{location.latitude:.4f}_{location.longitude:.4f}"
        self.emergency_locations.discard(location_hash)
        
        # 緊急位置がなくなったら平常モードに戻す
        if not self.emergency_locations and self.current_mode == CollectionMode.EMERGENCY:
            self.switch_to_normal_mode()
        
        if logger.isEnabledFor(logging.DEBUG):
            pass
    
    async def _collection_loop(self):
        """ニュース収集ループ"""
        while self.is_running:
            try:
                current_config = self._get_current_config()
                await self._collect_news(current_config)
                
                # 収集間隔に応じて待機
                wait_seconds = current_config.interval_minutes * 60
                await asyncio.sleep(wait_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in news collection loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # エラー時は1分待機

    def _get_current_config(self) -> NewsCollectionConfig:
        """現在の設定を取得"""
        return self.emergency_config if self.current_mode == CollectionMode.EMERGENCY else self.normal_config

    async def _collect_news(self, config: NewsCollectionConfig):
        """ニュースを収集"""
        try:
            if logger.isEnabledFor(logging.DEBUG):
                pass
            
            collected_articles = []
            
            if config.mode == CollectionMode.NORMAL:
                # 平常時: 一般的な災害予防ニュース
                collected_articles = await self._collect_general_disaster_news(config)
            else:
                # 緊急時: 位置特化型災害情報
                collected_articles = await self._collect_emergency_disaster_info(config)
            
            # 収集結果をキャッシュに保存
            new_articles_count = 0
            for article in collected_articles:
                if article.article_id not in self.collected_news:
                    new_articles_count += 1
                self.collected_news[article.article_id] = article
            
            # 古いニュースを削除（24時間以上古い）
            await self._cleanup_old_news()
            
            if logger.isEnabledFor(logging.DEBUG):
                pass
            # 新しい記事が追加された場合、フラグを設定（フロントエンドが次回APIコール時に提案生成）
            if new_articles_count > 0:
                await self._mark_new_news_for_proactive_suggestions(collected_articles, config.mode)
            
        except Exception as e:
            logger.error(f"Error collecting news: {e}", exc_info=True)

    async def _collect_general_disaster_news(self, config: NewsCollectionConfig) -> List[CollectedNews]:
        """一般的な災害予防ニュースを収集"""
        articles = []
        
        try:
            # 災害予防関連のキーワードで検索
            for keyword in config.search_keywords[:3]:  # 主要キーワードのみ
                search_query = f"{keyword} 対策 最新"
                
                try:
                    results = await self.web_search_tool._arun(
                        query=search_query,
                        max_results=3
                    )
                    
                    for result in results:
                        article = await self._convert_to_news_article(result, config, keyword)
                        if article:
                            articles.append(article)
                
                except Exception as e:
                    logger.error(f"Search failed for keyword '{keyword}': {e}")
            
            # 重複除去
            unique_articles = {}
            for article in articles:
                if article.url not in unique_articles:
                    unique_articles[article.url] = article
            
            return list(unique_articles.values())[:config.max_articles_per_cycle]
            
        except Exception as e:
            logger.error(f"Error collecting general disaster news: {e}")
            return []

    async def _collect_emergency_disaster_info(self, config: NewsCollectionConfig) -> List[CollectedNews]:
        """緊急時の位置特化型災害情報を収集"""
        articles = []
        
        try:
            if not config.target_location:
                logger.warning("No target location set for emergency collection")
                return []
            
            location_str = get_location_string(config.target_location)
            
            # 位置特化型の緊急情報検索
            for keyword in config.search_keywords[:5]:  # より多くのキーワードを使用
                search_query = f"{location_str} {keyword} 速報 最新"
                
                try:
                    results = await self.web_search_tool._arun(
                        query=search_query,
                        max_results=5  # 緊急時はより多く取得
                    )
                    
                    for result in results:
                        article = await self._convert_to_news_article(
                            result, config, keyword, config.target_location
                        )
                        if article:
                            # 緊急時は関連度と緊急度を評価
                            article.relevance_score = await self._calculate_relevance_score(article, keyword)
                            article.urgency_level = self._determine_urgency_level(article)
                            articles.append(article)
                
                except Exception as e:
                    logger.error(f"Emergency search failed for keyword '{keyword}': {e}")
            
            # 関連度でソートして重複除去
            articles.sort(key=lambda x: x.relevance_score, reverse=True)
            unique_articles = {}
            for article in articles:
                if article.url not in unique_articles:
                    unique_articles[article.url] = article
            
            return list(unique_articles.values())[:config.max_articles_per_cycle]
            
        except Exception as e:
            logger.error(f"Error collecting emergency disaster info: {e}")
            return []

    async def _convert_to_news_article(
        self, 
        search_result: Dict[str, Any], 
        config: NewsCollectionConfig,
        keyword: str,
        location: Optional[Location] = None
    ) -> Optional[CollectedNews]:
        """検索結果をニュース記事に変換"""
        try:
            title = search_result.get("title", "")
            content = search_result.get("snippet", "")
            url = search_result.get("link", "")
            source = search_result.get("source_domain", "")
            
            # 災害関連でない結果をフィルタ
            if not await self._is_disaster_related(title + " " + content, config.mode):
                return None
            
            # 記事IDを生成
            import hashlib
            article_id = hashlib.md5(f"{url}_{datetime.now().strftime('%Y%m%d%H')}".encode()).hexdigest()[:12]
            
            article = CollectedNews(
                article_id=article_id,
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=datetime.now(),  # 実際の公開日時は取得困難なため現在時刻
                collected_at=datetime.now(),
                mode=config.mode,
                location=location
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to convert search result to news article: {e}")
            return None

    async def _is_disaster_related(self, content: str, mode: CollectionMode) -> bool:
        """災害関連コンテンツかどうか判定（LLM自然言語理解を使用）"""
        try:
            from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
            
            if mode == CollectionMode.NORMAL:
                mode_context = "disaster preparedness, safety planning, and general disaster information"
            else:
                mode_context = "emergency disaster response, damage reports, evacuation information, and immediate safety updates"
            
            prompt = f"""Determine if this content is related to {mode_context} using natural language understanding.

Content: {content[:300]}...

Is this content relevant to disaster safety and management in the current context?

Respond with only: YES or NO"""

            response = await ainvoke_llm(prompt, task_type="disaster_relevance", temperature=0.1)
            return response.strip().upper() == "YES"
            
        except Exception as e:
            logger.warning(f"LLM disaster relevance classification failed: {e}")
            # フォールバック: 保守的判定（災害関連と仮定）
            return True

    async def _calculate_relevance_score(self, article: CollectedNews, keyword: str) -> float:
        """関連度スコアを計算"""
        score = 0.0
        content = (article.title + " " + article.content).lower()
        
        # LLMベースの関連度分析（CLAUDE.md原則に従い自然言語理解を使用）
        try:
            from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
            
            # 短縮版コンテンツで分析
            short_content = content[:800]  # LLM効率化
            
            # 簡潔なプロンプトで関連度判定
            prompt = f"""Rate disaster relevance (0.0-1.0) for: "{keyword}"
Article: {short_content}
Respond with number only (e.g. 0.7)"""

            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 非同期コンテキスト内の場合はスキップしてフォールバック使用
                raise Exception("Skip LLM in async context")
            
            response = await ainvoke_llm(prompt, task_type="relevance", temperature=0.3)
            llm_score = float(response.strip())
            score += max(0.0, min(0.6, llm_score))  # LLMスコアを最大0.6に制限
            
        except Exception:
            # フォールバック: 基本判定（自然言語理解なしの暫定措置）
            if keyword.lower() in content:
                score += 0.3
        
        # 信頼できるソース
        trusted_domains = ["jma.go.jp", "nhk.or.jp", "bousai.go.jp"]
        if any(domain in article.source for domain in trusted_domains):
            score += 0.3
        
        return min(score, 1.0)

    async def _determine_urgency_level(self, article: CollectedNews) -> str:
        """緊急度レベルを判定（LLM自然言語分類を使用）"""
        try:
            from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
            
            prompt = f"""Analyze the urgency level of this disaster news article using natural language understanding.

Article Title: {article.title}
Article Content: {article.content[:500]}...

Determine the urgency level based on the severity and immediacy of the disaster situation described:

- "emergency": Immediate life-threatening situations requiring urgent action
- "critical": Serious situations requiring prompt attention  
- "high": Important information that needs attention soon
- "normal": General information or updates

Consider the overall context and severity, not just specific keywords.

Respond with only one word: emergency, critical, high, or normal"""

            response = await ainvoke_llm(prompt, task_type="urgency_classification", temperature=0.2)
            level = response.strip().lower()
            
            if level in ["emergency", "critical", "high", "normal"]:
                return level
            else:
                return "normal"
                
        except Exception as e:
            logger.warning(f"LLM urgency classification failed: {e}")
            # フォールバック: デフォルト判定
            return "normal"

    async def _cleanup_old_news(self):
        """古いニュースを削除"""
        current_time = datetime.now()
        expired_ids = []
        
        for article_id, article in self.collected_news.items():
            age_hours = (current_time - article.collected_at).total_seconds() / 3600
            if age_hours > 24:  # 24時間以上古い
                expired_ids.append(article_id)
        
        for article_id in expired_ids:
            del self.collected_news[article_id]
        
        if expired_ids:
            pass
    async def _mark_new_news_for_proactive_suggestions(self, new_articles: List[CollectedNews], mode: CollectionMode):
        """新しいニュースが取得されたことをマークし、次回プロアクティブ提案で使用可能にする"""
        try:
            # 新しいニュースが取得された時刻を記録
            self.last_news_update = datetime.now()
            self.new_articles_count = len([
                article for article in new_articles
                if self._is_news_disaster_related(article)
            ])
            
            if logger.isEnabledFor(logging.DEBUG):
                pass
        except Exception as e:
            logger.error(f"Error marking new news for proactive suggestions: {e}")

    def _is_news_disaster_related(self, article: CollectedNews) -> bool:
        """ニュース記事が災害関連かどうかLLMで判定（CLAUDE.md原則準拠）"""
        try:
            # 効率化のため短縮版を使用
            content = f"{article.title} {article.content[:500]}"
            
            # 信頼できるソースからの記事は災害関連として扱う（効率化）
            trusted_domains = ["jma.go.jp", "nhk.or.jp", "bousai.go.jp", "fdma.go.jp"]
            if any(domain in article.source for domain in trusted_domains):
                return True
            
            # TODO: 将来的にはLLMベース分類を実装
            # 現在は効率化のため基本判定を使用（暫定措置）
            disaster_indicators = [
                "災害", "防災", "地震", "津波", "台風", "警報", "避難", "緊急"
            ]
            content_lower = content.lower()
            return any(indicator in content_lower for indicator in disaster_indicators)
        except:
            return False

    def has_new_news_for_suggestions(self) -> bool:
        """プロアクティブ提案用の新しいニュースがあるかチェック"""
        if not hasattr(self, 'last_news_update') or not hasattr(self, 'new_articles_count'):
            return False
        
        # 過去30分以内の新しいニュースがある場合
        if self.last_news_update and self.new_articles_count > 0:
            time_diff = (datetime.now() - self.last_news_update).total_seconds() / 60
            return time_diff <= 30  # 30分以内
        
        return False

    def get_new_news_info(self) -> Dict[str, Any]:
        """新しいニュース情報を取得"""
        # デバッグモード時はWeb検索キャッシュデータを使用
        if app_settings.is_test_mode():
            return self._get_web_cache_news_info()
        
        if not self.has_new_news_for_suggestions():
            return {}
        
        return {
            "new_articles_count": getattr(self, 'new_articles_count', 0),
            "last_update_time": getattr(self, 'last_news_update', None).isoformat() if hasattr(self, 'last_news_update') else None,
            "latest_articles": self.get_latest_news(mode=self.current_mode, limit=3)
        }
    
    def _get_web_cache_news_info(self) -> Dict[str, Any]:
        """Web検索キャッシュからニュース情報を取得（デバッグ用）"""
        try:
            from app.config import app_settings
            
            news_type = "emergency" if self.current_mode == CollectionMode.EMERGENCY else "normal"
            cached_items = web_news_cache_manager.get_random_cached_news(news_type, count=5)
            
            # テストモード時の新しいニュース判定にクールダウンを追加
            if app_settings.is_test_mode():
                # 最後の更新から十分時間が経過している場合のみ「新しい」とする
                now = datetime.now()
                if hasattr(self, 'last_news_update') and self.last_news_update:
                    time_since_last = (now - self.last_news_update).total_seconds()
                    cooldown_seconds = 30  # 30秒のクールダウン
                    if time_since_last < cooldown_seconds:
                        # クールダウン中は「新しいニュースなし」
                        if logger.isEnabledFor(logging.DEBUG):
                            pass
                        self.new_articles_count = 0
                        return {
                            "new_articles_count": 0,
                            "has_new_articles": False,
                            "last_update_time": self.last_news_update.isoformat(),
                            "latest_articles": [],
                            "articles": []
                        }
                
                # クールダウン完了、更新時刻をリセット
                self.last_news_update = now
                if logger.isEnabledFor(logging.DEBUG):
                    pass
            else:
                # 本番モードでは従来通り
                self.last_news_update = datetime.now()
            
            if not cached_items:
                logger.warning(f"No cached {news_type} news found, using fallback")
                self.new_articles_count = 0  # フォールバック時も0に変更
                return {
                    "new_articles_count": 0,
                    "last_update_time": datetime.now(timezone.utc).isoformat(),
                    "latest_articles": []
                }
            
            # CachedNewsItemをCollectedNewsに変換
            latest_articles = []
            for item in cached_items[:3]:
                article = CollectedNews(
                    article_id=f"web_cache_{item.search_query.replace(' ', '_')}_{int(datetime.now().timestamp())}",
                    title=item.title,
                    content=item.content,
                    url=item.url,
                    source=item.source,
                    published_at=datetime.fromisoformat(item.published_at.replace('Z', '+00:00')),
                    collected_at=datetime.fromisoformat(item.collected_at.replace('Z', '+00:00')),
                    mode=self.current_mode
                )
                latest_articles.append(article)
            
            # テストモード用の属性設定
            self.new_articles_count = len(cached_items)
            
            if logger.isEnabledFor(logging.DEBUG):
                pass
            return {
                "new_articles_count": len(cached_items),
                "last_update_time": datetime.now(timezone.utc).isoformat(),
                "latest_articles": latest_articles
            }
            
        except Exception as e:
            logger.error(f"Error getting web cache news info: {e}")
            # エラー時もテストモード用の属性設定
            self.new_articles_count = 0
            return {
                "new_articles_count": 0,
                "last_update_time": datetime.now(timezone.utc).isoformat(),
                "latest_articles": []
            }

    async def _trigger_proactive_suggestions_for_new_news(self, new_articles: List[CollectedNews], mode: CollectionMode):
        """新しいニュースが収集された際に既存のプロアクティブ提案システムを使用して提案を送信"""
        try:
            if logger.isEnabledFor(logging.DEBUG):
                pass
            
            # 全アクティブデバイスを取得
            from app.crud.device_crud import get_all_devices
            devices = await get_all_devices()
            
            # FCMトークンを持つデバイスのみ対象
            active_devices = [
                device for device in devices
                if device.get("fcm_token") and device.get("is_active", True)
            ]
            
            if not active_devices:
                return
            
            if logger.isEnabledFor(logging.DEBUG):
                pass
            
            # 既存のプロアクティブ提案システムを使用
            from app.services.trigger_evaluator import TriggerEvaluator
            from app.agents.safety_beacon_agent.suggestion_generators.template_generator import SuggestionGenerator
            from app.schemas.agent.suggestions import DeviceContext, UserContext
            
            trigger_evaluator = TriggerEvaluator()
            suggestion_generator = SuggestionGenerator()
            
            # 各デバイスに対してプロアクティブ提案を生成・送信
            for device in active_devices[:10]:  # 最大10件まで（レート制限）
                try:
                    await self._send_standard_proactive_suggestion(
                        device, new_articles, mode, trigger_evaluator, suggestion_generator
                    )
                except Exception as e:
                    logger.error(f"Failed to send proactive suggestion to device {device.get('device_id')}: {e}")
            
        except Exception as e:
            logger.error(f"Error triggering proactive suggestions: {e}")

    async def _send_standard_proactive_suggestion(
        self, 
        device: Dict[str, Any], 
        new_articles: List[CollectedNews], 
        mode: CollectionMode,
        trigger_evaluator,
        suggestion_generator
    ):
        """既存のプロアクティブ提案システムを使用して個別デバイスに提案を送信"""
        try:
            device_id = device.get("device_id")
            fcm_token = device.get("fcm_token")
            language = device.get("language", "ja")
            
            # デバイスコンテキストを構築
            from app.schemas.agent.suggestions import DeviceContext, UserContext
            
            device_context = DeviceContext(
                device_id=device_id,
                platform=device.get("platform", "unknown"),
                battery_level=device.get("status", {}).get("battery_level"),
                is_charging=device.get("status", {}).get("is_charging", False),
                network_type=device.get("status", {}).get("network_type"),
                language=language
            )
            
            user_context = UserContext(
                user_id=device.get("user_id"),
                is_in_disaster_mode=(mode == CollectionMode.EMERGENCY),
                language=language,
                has_emergency_contacts=False,  # デフォルト値
                emergency_contacts_count=0,
                viewed_guides=[],
                last_quiz_date=None,
                last_active_date=None
            )
            
            # 新しいニューストリガーを評価
            news_trigger_evaluation = await trigger_evaluator.evaluate_new_news_trigger(
                device_context, user_context, new_articles
            )
            
            if not news_trigger_evaluation:
                return
            
            # プロアクティブ提案を生成
            suggestions = await suggestion_generator.generate_suggestions([news_trigger_evaluation])
            
            if not suggestions:
                return
            
            # 最初の提案をFCMで送信
            suggestion = suggestions[0]
            await self._send_fcm_standard_notification(fcm_token, suggestion, language, new_articles)
            
            if logger.isEnabledFor(logging.DEBUG):
                pass
        except Exception as e:
            logger.error(f"Error sending standard proactive suggestion to device {device.get('device_id')}: {e}")

    async def _send_fcm_standard_notification(self, fcm_token: str, suggestion, language: str, new_articles: List[CollectedNews]):
        """標準的なプロアクティブ提案をFCMで送信"""
        try:
            from app.utils.fcm_sender import send_fcm_notification
            
            # 追加データ
            data = {
                "type": "proactive_suggestion",
                "suggestion_id": suggestion.id,
                "trigger_type": suggestion.trigger_type,
                "action_type": suggestion.action_type.value if suggestion.action_type else None,
                "action_label": suggestion.action_label,
                "news_count": str(len(new_articles)),
                "click_action": "/news"
            }
            
            # FCM送信
            result = send_fcm_notification(
                token=fcm_token,
                title=suggestion.title,
                body=suggestion.message,
                data=data,
                language=language
            )
            
            if result:
                if logger.isEnabledFor(logging.DEBUG):
                    pass
            else:
                logger.warning(f"❌ FCM standard proactive notification failed")
                
        except Exception as e:
            logger.error(f"Error sending FCM standard notification: {e}")

    async def _send_fcm_proactive_notification(self, fcm_token: str, suggestion: Any, language: str, new_articles: List[CollectedNews]):
        """FCMプッシュ通知でプロアクティブ提案を送信"""
        try:
            from app.utils.fcm_sender import send_fcm_notification
            
            # 通知内容を言語に応じて生成
            if language == "ja":
                title = "💡 新しい防災情報"
                body = suggestion.content[:100] + ("..." if len(suggestion.content) > 100 else "")
            else:
                title = "💡 New Disaster Prevention Info"
                body = suggestion.content[:100] + ("..." if len(suggestion.content) > 100 else "")
            
            # 追加データ
            data = {
                "type": "proactive_suggestion",
                "suggestion_id": suggestion.suggestion_id,
                "suggestion_type": suggestion.type,
                "action_query": suggestion.action_query,
                "news_count": str(len(new_articles)),
                "click_action": "/suggestions"
            }
            
            # FCM送信
            result = send_fcm_notification(
                token=fcm_token,
                title=title,
                body=body,
                data=data,
                language=language
            )
            
            if result:
                if logger.isEnabledFor(logging.DEBUG):
                    pass
            else:
                logger.warning(f"❌ FCM proactive notification failed")
                
        except Exception as e:
            logger.error(f"Error sending FCM proactive notification: {e}")

    def get_latest_news(self, mode: Optional[CollectionMode] = None, limit: int = 10) -> List[CollectedNews]:
        """最新ニュースを取得"""
        articles = list(self.collected_news.values())
        
        # モードでフィルタ
        if mode:
            articles = [a for a in articles if a.mode == mode]
        
        # 収集時刻でソート
        articles.sort(key=lambda x: x.collected_at, reverse=True)
        
        return articles[:limit]

    def get_collection_status(self) -> Dict[str, Any]:
        """収集ステータスを取得"""
        return {
            "is_running": self.is_running,
            "current_mode": self.current_mode,
            "environment": self.environment,
            "normal_config": {
                "interval_minutes": self.normal_config.interval_minutes,
                "max_articles": self.normal_config.max_articles_per_cycle,
                "keywords_count": len(self.normal_config.search_keywords)
            },
            "emergency_config": {
                "interval_minutes": self.emergency_config.interval_minutes,
                "max_articles": self.emergency_config.max_articles_per_cycle,
                "keywords_count": len(self.emergency_config.search_keywords),
                "target_location": {
                    "latitude": self.emergency_config.target_location.latitude,
                    "longitude": self.emergency_config.target_location.longitude
                } if self.emergency_config.target_location else None
            },
            "emergency_locations_count": len(self.emergency_locations),
            "cached_articles_count": len(self.collected_news),
            "articles_by_mode": {
                "normal": len([a for a in self.collected_news.values() if a.mode == CollectionMode.NORMAL]),
                "emergency": len([a for a in self.collected_news.values() if a.mode == CollectionMode.EMERGENCY])
            }
        }

# グローバルインスタンス
adaptive_news_collector = AdaptiveNewsCollector()

# ヘルパー関数
async def start_adaptive_news_collection():
    """適応的ニュース収集を開始"""
    await adaptive_news_collector.start_collection()

async def stop_adaptive_news_collection():
    """適応的ニュース収集を停止"""
    await adaptive_news_collector.stop_collection()

def add_emergency_location(location: Location):
    """緊急監視位置を追加"""
    return adaptive_news_collector.add_emergency_location(location)

def remove_emergency_location(location: Location):
    """緊急監視位置を削除"""
    return adaptive_news_collector.remove_emergency_location(location)

def get_latest_news(mode: Optional[CollectionMode] = None, limit: int = 10) -> List[CollectedNews]:
    """最新ニュースを取得"""
    return adaptive_news_collector.get_latest_news(mode, limit)