"""災害ガイド提案サービス - ベクトル検索から動的に提案を生成"""
import logging
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from app.utils.season_utils import get_current_season
from app.agents.safety_beacon_agent.core.llm_singleton import get_llm_client
from app.tools.guide_tools import UnifiedGuideSearchTool, get_guide_search_tool

logger = logging.getLogger(__name__)

class DisasterGuideSuggestionService:
    """災害ガイド提案を管理するサービス - ベクトルDB版"""
    
    def __init__(self):
        """初期化"""
        # ベクトル検索ツールを初期化
        try:
            self.guide_search_tool = UnifiedGuideSearchTool()
        except Exception as e:
            logger.warning(f"Failed to initialize guide search tool: {e}")
            self.guide_search_tool = None
        
        # 提案生成用のカテゴリとキーワード
        self.suggestion_categories = {
            "earthquake_preparation": {
                "keywords": ["地震対策", "地震準備", "耐震"],
                "priority": 0.9
            },
            "emergency_kit": {
                "keywords": ["非常用持ち出し袋", "防災グッズ", "備蓄"],
                "priority": 0.85
            },
            "family_safety": {
                "keywords": ["家族防災", "家族の安全", "子供の防災"],
                "priority": 0.8
            },
            "evacuation_planning": {
                "keywords": ["避難計画", "避難経路", "避難場所"],
                "priority": 0.85
            },
            "seasonal_disasters": {
                "keywords": ["季節災害", "台風", "大雨", "熱中症", "雪害"],
                "priority": 0.75
            },
            "home_safety": {
                "keywords": ["自宅防災", "家具固定", "室内安全"],
                "priority": 0.7
            }
        }
        
        # ランダム性を向上させるためのシード設定
        random.seed(time.time())
    
    async def _search_guides_by_category(self, category: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """カテゴリに基づいてガイドを検索"""
        try:
            category_info = self.suggestion_categories.get(category, {})
            keywords = category_info.get("keywords", [])
            
            if not keywords:
                return []
            
            # ランダムにキーワードを選択して検索
            search_keyword = random.choice(keywords)
            
            # guide_search_toolが利用可能か確認
            if not self.guide_search_tool:
                logger.warning("Guide search tool not available, returning empty results")
                return []
                
            results = await self.guide_search_tool.search_guides(
                query=search_keyword,
                max_results=max_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"ガイド検索エラー: {e}")
            return []
    
    def _calculate_relevance_score(self, 
                                 guide: Dict[str, Any], 
                                 category: str,
                                 context: ProactiveSuggestionContext) -> float:
        """ガイドの関連性スコアを計算"""
        category_info = self.suggestion_categories.get(category, {})
        base_score = category_info.get("priority", 0.5)
        
        # ユーザーの閲覧履歴を考慮
        user_summary = context.user_app_usage_summary
        viewed_guides = []
        is_new_user = False
        
        if user_summary:
            if hasattr(user_summary, 'viewed_guides'):
                viewed_guides = user_summary.viewed_guides or []
            elif isinstance(user_summary, dict):
                viewed_guides = user_summary.get("viewed_guides", [])
                
            if hasattr(user_summary, 'is_new_user'):
                is_new_user = user_summary.is_new_user or False
            elif isinstance(user_summary, dict):
                is_new_user = user_summary.get("is_new_user", False)
        
        # 既に見たガイドの場合はスコアを下げる
        if guide.get("id") in viewed_guides:
            base_score *= 0.3
            
        # 新規ユーザーの場合は基本的な提案を優先
        if is_new_user and category in ["emergency_kit", "family_safety", "evacuation_planning"]:
            base_score *= 1.2
                
        return min(1.0, base_score)
    
    async def _create_suggestion_from_guide(self, 
                                          guide: Dict[str, Any], 
                                          category: str,
                                          context: ProactiveSuggestionContext) -> Dict[str, Any]:
        """ガイドから提案を生成"""
        try:
            llm = get_llm_client()
            
            # 現在の季節を取得
            current_season = get_current_season()
            
            # プロンプトで提案を生成
            prompt = f"""Based on this disaster guide, create a proactive suggestion in Japanese.

Guide Title: {guide.get('title', '')}
Guide Summary: {guide.get('summary', '')}
Category: {category}
Current Season: {current_season}

Create a suggestion that:
1. Is a question or recommendation that prompts user action
2. Is relevant to the current season if applicable
3. Is concise (1-2 sentences)
4. Includes a clear call-to-action

IMPORTANT for action_query:
- Must be a SPECIFIC question users would ask to learn about this topic
- Should be concrete and directly related to the guide content
- NOT vague like "夏の災害に備えて" but SPECIFIC like "夏の台風対策について教えて"
- Examples based on categories:
  - Earthquake: "地震に備えた家具固定の方法を教えて", "地震時の行動手順を知りたい"
  - Emergency kit: "非常用持ち出し袋に何を入れるべき？", "3日分の備蓄品リストを見たい"
  - Family safety: "子供に災害時の行動を教える方法は？", "家族の連絡方法を決めたい"
  - Seasonal: "台風接近時の準備チェックリストを教えて", "熱中症予防の具体的な方法は？"

Return ONLY a JSON object with this structure:
{{
    "content": "The suggestion content in Japanese (question or recommendation)",
    "action_query": "SPECIFIC question about this topic (in Japanese)",
    "action_display_text": "The action button text (e.g., 詳しく見る, 確認する)",
    "preview_info": "Brief preview of what they'll learn (1 sentence)"
}}"""

            response = await llm.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON
            import json
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            suggestion_data = json.loads(cleaned.strip())
            
            # Add metadata
            suggestion_data.update({
                "guide_id": guide.get("id", ""),
                "category": category,
                "suggestion_id": f"{category}_{guide.get('id', '')}_{int(time.time())}",
                "priority_score": self._calculate_relevance_score(guide, category, context),
                "target_season": current_season if category == "seasonal_disasters" else None
            })
            
            return suggestion_data
            
        except Exception as e:
            logger.error(f"提案生成エラー: {e}")
            # フォールバック提案
            return {
                "content": f"{guide.get('title', 'ガイド')}について確認しませんか？",
                "action_query": guide.get('title', '防災ガイド'),
                "action_display_text": "詳しく見る",
                "preview_info": guide.get('summary', '')[:50] + "...",
                "guide_id": guide.get("id", ""),
                "category": category,
                "suggestion_id": f"{category}_{guide.get('id', '')}_{int(time.time())}",
                "priority_score": 0.5
            }
    
    def _get_language_name(self, language_code: str) -> str:
        """言語コードから言語名を取得"""
        language_names = {
            'ja': '日本語', 'en': 'English', 
            'zh': '中文', 'zh_CN': '简体中文', 'zh_TW': '繁體中文',
            'ko': '한국어', 'fr': 'Français', 'es': 'Español', 
            'de': 'Deutsch', 'it': 'Italiano', 'pt': 'Português', 
            'ru': 'Русский', 'ar': 'العربية', 'hi': 'हिन्दी',
            'th': 'ไทย', 'vi': 'Tiếng Việt'
        }
        return language_names.get(language_code, language_names.get('en', 'English'))
    
    async def _translate_suggestion(self, suggestion: Dict[str, Any], language_code: str) -> Dict[str, Any]:
        """提案を指定言語に翻訳"""
        if language_code == 'ja':
            return suggestion
            
        try:
            language_name = self._get_language_name(language_code)
            llm = get_llm_client()
            
            prompt = f"""Translate this disaster safety suggestion to {language_name}.
Make it natural and culturally appropriate for {language_name} speakers.

Original:
- content: {suggestion['content']}
- action_query: {suggestion['action_query']}
- action_display_text: {suggestion.get('action_display_text', '詳しく見る')}

Return ONLY a JSON object:
{{
    "content": "translated content in {language_name}",
    "action_query": "translated action_query in {language_name}",
    "action_display_text": "translated action_display_text in {language_name}"
}}"""

            response = await llm.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            import json
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            translation_data = json.loads(cleaned.strip())
            
            translated_suggestion = suggestion.copy()
            translated_suggestion.update(translation_data)
            
            return translated_suggestion
            
        except Exception as e:
            logger.warning(f"翻訳エラー: {e}")
            return suggestion
    
    async def get_guide_suggestions(self, 
                                  context: ProactiveSuggestionContext,
                                  max_suggestions: int = 3) -> List[SuggestionItem]:
        """災害ガイド提案を取得"""
        try:
            # カテゴリをランダムに選択（多様性のため）
            categories = list(self.suggestion_categories.keys())
            
            # 季節に応じてカテゴリを調整
            current_season = get_current_season()
            if current_season == "夏":
                categories.append("seasonal_disasters")  # 熱中症対策を増やす
            elif current_season == "冬":
                categories.append("seasonal_disasters")  # 雪害対策を増やす
            
            # クールダウンチェック
            if context.suggestion_history_summary:
                cooldown_types = set()
                for hist_item in context.suggestion_history_summary:
                    if isinstance(hist_item, dict) and 'type' in hist_item:
                        cooldown_types.add(hist_item['type'])
                
                # クールダウン中のカテゴリを除外
                if "guide_recommendation" in cooldown_types:
                    categories = [c for c in categories if c == "seasonal_disasters"]
                if "seasonal_warning" in cooldown_types:
                    categories = [c for c in categories if c != "seasonal_disasters"]
            
            if not categories:
                logger.info("利用可能なカテゴリがありません（クールダウン中）")
                return []
            
            # ランダムにカテゴリを選択
            random.shuffle(categories)
            selected_categories = categories[:max_suggestions]
            
            # 各カテゴリから提案を生成
            suggestions = []
            for category in selected_categories:
                guides = await self._search_guides_by_category(category, max_results=3)
                if guides:
                    # ランダムにガイドを選択
                    guide = random.choice(guides)
                    suggestion = await self._create_suggestion_from_guide(guide, category, context)
                    suggestions.append(suggestion)
            
            # 言語に応じて翻訳
            language_code = context.language_code or 'ja'
            if language_code != 'ja':
                translated_suggestions = []
                for suggestion in suggestions:
                    translated = await self._translate_suggestion(suggestion, language_code)
                    translated_suggestions.append(translated)
                suggestions = translated_suggestions
            
            # SuggestionItemに変換
            result = []
            for suggestion in suggestions:
                suggestion_type = "seasonal_warning" if suggestion.get("category") == "seasonal_disasters" else "guide_recommendation"
                
                item = SuggestionItem(
                    type=suggestion_type,
                    content=suggestion["content"],
                    action_query=suggestion["action_query"],
                    action_display_text=suggestion.get("action_display_text", "詳しく見る"),
                    priority="high" if suggestion.get("priority_score", 0) > 0.85 else "normal",
                    action_data={
                        "guide_id": suggestion["guide_id"],
                        "category": suggestion["category"],
                        "preview": suggestion.get("preview_info", ""),
                        "suggestion_id": suggestion["suggestion_id"],
                        "language_code": language_code
                    }
                )
                result.append(item)
            
            logger.info(f"ベクトル検索から{len(result)}件の提案を生成しました")
            return result
            
        except Exception as e:
            logger.error(f"提案生成エラー: {e}")
            return []
    
    async def get_guide_suggestion_by_category(self, 
                                              category: str,
                                              context: Optional[ProactiveSuggestionContext] = None) -> Optional[SuggestionItem]:
        """特定カテゴリの災害ガイド提案を1つ取得"""
        try:
            guides = await self._search_guides_by_category(category, max_results=5)
            if not guides:
                return None
            
            # ランダムにガイドを選択
            guide = random.choice(guides)
            
            # デフォルトコンテキストを作成
            if not context:
                context = ProactiveSuggestionContext(
                    language_code='ja',
                    user_app_usage_summary=None,
                    suggestion_history_summary=[]
                )
            
            suggestion = await self._create_suggestion_from_guide(guide, category, context)
            
            # 翻訳
            language_code = context.language_code or 'ja'
            if language_code != 'ja':
                suggestion = await self._translate_suggestion(suggestion, language_code)
            
            # SuggestionItemに変換
            return SuggestionItem(
                type="guide_recommendation",
                content=suggestion["content"],
                action_query=suggestion["action_query"],
                action_display_text=suggestion.get("action_display_text", "詳しく見る"),
                priority="high" if suggestion.get("priority_score", 0) > 0.85 else "normal",
                action_data={
                    "guide_id": suggestion["guide_id"],
                    "category": suggestion["category"],
                    "preview": suggestion.get("preview_info", ""),
                    "suggestion_id": suggestion["suggestion_id"],
                    "language_code": language_code
                }
            )
            
        except Exception as e:
            logger.error(f"カテゴリ別提案生成エラー: {e}")
            return None