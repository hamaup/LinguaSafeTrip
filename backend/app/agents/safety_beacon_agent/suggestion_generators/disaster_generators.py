# backend/app/agents/safety_beacon_agent/suggestion_generators/disaster_generators.py
"""Disaster-related suggestion generators"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import random
import os

from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from .base import SuggestionGeneratorBase, get_language_name
from .prompt_templates import (
    DISASTER_NEWS_TEMPLATE,
    HAZARD_MAP_TEMPLATE,
    SHELTER_STATUS_TEMPLATE,
    get_json_template
)
from app.config.app_settings import app_settings

logger = logging.getLogger(__name__)

class DisasterSuggestionGenerator(SuggestionGeneratorBase):
    """災害関連提案生成器"""
    
    async def generate_disaster_news(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """災害ニュース提案生成（緊急時のみ）"""
        language_name = get_language_name(language_code)
        
        logger.info(f"   - is_emergency_mode: {context.is_emergency_mode}")
        logger.info(f"   - current_situation: {context.current_situation}")
        
        # 緊急時のみ生成
        emergency_condition = context.is_emergency_mode or context.current_situation == "alert_active"
        
        logger.info(f"   - emergency_condition: {emergency_condition}")
        
        if not emergency_condition:
            # 平常時はdisaster_preparednessを使用
            return await self.generate_disaster_preparedness(context, language_code)
        
        # 緊急時の処理
        if True:  # インデントを保つため
            # 緊急時：最新の災害ニュース・情報をチェックする提案
            # Create safe JSON template
            json_template = get_json_template(
                "Urgent disaster news suggestion in English, 1 sentence, 60 chars max",
                "SPECIFIC urgent question about current disaster in English",
                "Latest news (in English)"
            )
            
            prompt = DISASTER_NEWS_TEMPLATE.format(
                mode_type="an urgent",
                content_type="news checking",
                language_name="English",  # Internal processing in English
                mode_description="Emergency mode: Help users get the latest disaster information and breaking news about current emergencies.",
                action_type="urgently encourage checking latest disaster news and alerts",
                tone="urgent and actionable for immediate safety",
                focus="current breaking news and emergency information",
                examples='Examples: "Check latest earthquake updates", "Get emergency weather alerts"',
                query_type="question about current emergency information",
                query_action="directly ask for the information users need RIGHT NOW",
                japanese_examples='"私の地域の最新の地震情報を教えて", "この地域の避難指示状況は？", "私のエリアの災害警報を確認したい"',
                english_examples='"Show me latest earthquake information in my area", "What\'s the evacuation status in my location?", "Check disaster warnings for my area"',
                json_template=json_template
            )
            
            data = await self.generate_with_llm(prompt, "disaster_news_emergency")
            if data:
                return SuggestionItem(
                    type="disaster_news",
                    content=data.get("content", ""),
                    action_query=data.get("action_query", ""),
                    action_display_text=data.get("action_display_text", ""),
                    action_data={
                        "news_type": "breaking", 
                        "priority": "urgent", 
                        "content_focus": "current_emergency",
                        "emergency_mode": True,
                        "requires_translation": True
                    }
                )
            
            # 緊急時フォールバック
            fallback_content = "Check latest disaster alerts and emergency information now."
            action_query = "Find latest disaster news"
            action_display = "Latest News"
            
            return SuggestionItem(
                type="disaster_news",
                content=fallback_content,
                action_query=action_query,
                action_display_text=action_display,
                action_data={
                    "news_type": "breaking",
                    "priority": "urgent",
                    "content_focus": "current_emergency",
                    "emergency_mode": True,
                    "requires_translation": True
                }
            )
        
        # 緊急時のみのフォールバック
        return SuggestionItem(
            type="disaster_news",
            content=fallback_content,
            action_query=action_query,
            action_display_text=action_display,
            action_data={
                "news_type": "breaking",
                "priority": "urgent",
                "content_focus": "current_emergency",
                "emergency_mode": True,
                "requires_translation": True
            }
        )
    
    async def generate_disaster_preparedness(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """防災準備情報提案生成（平常時用）"""
        language_name = get_language_name(language_code)
        
        logger.info(f"📚 Generating disaster preparedness suggestion")
        
        # テストモードの場合はモックデータを使用
        if app_settings.use_testing_mode:
            logger.info("📚 Using mock data for disaster preparedness news")
            mock_item = await self._get_mock_preparedness_news(language_code)
            if mock_item:
                return mock_item
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Disaster preparedness tip in English, 1 sentence, 60 chars max",
            f"SPECIFIC question about disaster preparation in English",
            f"Learn more"
        )
        
        prompt = f"""Create a disaster preparedness suggestion in English.

Help users learn about disaster preparedness, prevention tips, and safety measures for daily life.

Requirements:
- content should encourage learning about disaster preparedness and prevention (max 60 characters)
- Make it informative and practical for daily preparation
- Focus on prevention and preparedness, not breaking news
- Examples: home safety tips, emergency kit preparation, evacuation planning

IMPORTANT for action_query:
- Must be a specific, actionable question users might ask the chatbot
- Should be clear and concrete about what information they want
- MUST match the specific topic mentioned in content
- If content is about "earthquake safety tips", query should ask about "earthquake safety tips" specifically
- Examples in Japanese: "地震対策の基本を教えて", "非常用持ち出し袋に何を入れるべき？", "家具の固定方法を知りたい"
- Examples in English: "Tell me about earthquake preparation basics", "What should I put in emergency kit?", "How to secure furniture?"

Return ONLY a valid JSON object:
{json_template}"""

        data = await self.generate_with_llm(prompt, "disaster_preparedness")
        if data:
            return SuggestionItem(
                type="disaster_preparedness",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={
                    "preparedness_type": "general", 
                    "priority": "normal", 
                    "content_focus": "prevention",
                    "emergency_mode": False,
                    "requires_translation": True
                }
            )
        
        # フォールバック
        fallback = self.get_fallback_content("disaster_preparedness", language_code)
        return SuggestionItem(
            type="disaster_preparedness",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={
                "preparedness_type": "general",
                "priority": "normal",
                "content_focus": "prevention",
                "emergency_mode": False,
                "requires_translation": True
            }
        )
    
    async def generate_hazard_map_url(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """ハザードマップURL提案生成"""
        language_name = get_language_name(language_code)
        
        # 位置情報に基づく地域特定
        location_info = "your area"
        if context.current_location:
            location_info = f"lat {context.current_location.latitude:.2f}, lon {context.current_location.longitude:.2f}"
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Risk awareness suggestion in English, 1 sentence, 60 chars max",
            f"SPECIFIC question about local hazards in English",
            f"Understand risks"
        )
        
        prompt = HAZARD_MAP_TEMPLATE.format(
            language_name=language_name,
            json_template=json_template
        )

        data = await self.generate_with_llm(prompt, "hazard_map_url")
        if data:
            # 位置情報に基づくハザードマップURLを生成
            hazard_map_url = "https://disaportal.gsi.go.jp/"
            if context.current_location:
                # 国土地理院のハザードマップポータルサイトに位置情報を含めたURL
                lat = context.current_location.latitude
                lon = context.current_location.longitude
                # ズームレベル14で位置を指定
                hazard_map_url = f"https://disaportal.gsi.go.jp/maps/index.html?ll={lat},{lon}&z=14&base=pale&vs=c1j0h0k0l0u0t0&d=m"
            
            return SuggestionItem(
                type="hazard_map_url",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={
                    "url": hazard_map_url,
                    "location_based": True,
                    "coordinates": {
                        "latitude": context.current_location.latitude if context.current_location else None,
                        "longitude": context.current_location.longitude if context.current_location else None
                    },
                    "requires_translation": True
                }
            )
        
        # フォールバック
        fallback = self.get_fallback_content("hazard_map_url", language_code)
        
        # フォールバック時も位置情報があれば使用
        fallback_url = "https://disaportal.gsi.go.jp/"
        if context.current_location:
            lat = context.current_location.latitude
            lon = context.current_location.longitude
            fallback_url = f"https://disaportal.gsi.go.jp/maps/index.html?ll={lat},{lon}&z=14&base=pale&vs=c1j0h0k0l0u0t0&d=m"
        
        return SuggestionItem(
            type="hazard_map_url",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={
                "url": fallback_url,
                "location_based": True,
                "coordinates": {
                    "latitude": context.current_location.latitude if context.current_location else None,
                    "longitude": context.current_location.longitude if context.current_location else None
                },
                "requires_translation": True
            }
        )
    
    async def generate_shelter_status_update(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """避難所情報提案生成（緊急時と平常時で内容を分ける）"""
        language_name = get_language_name(language_code)
        
        # Starting shelter suggestion generation
        logger.info(f"   - is_emergency_mode: {context.is_emergency_mode}")
        logger.info(f"   - current_situation: {context.current_situation}")
        
        # 緊急時と平常時で異なる内容を生成
        emergency_condition = context.is_emergency_mode or context.current_situation == "alert_active"
        
        logger.info(f"   - emergency_condition: {emergency_condition}")
        
        if emergency_condition:
            # 緊急時：即座に避難所を確認する緊急提案
            # Create safe JSON template - internal processing in English
            json_template = get_json_template(
                f"Urgent shelter suggestion in English, 1 sentence, 60 chars max",
                f"SPECIFIC urgent question about shelters in English",
                f"Find NOW"
            )
            
            prompt = SHELTER_STATUS_TEMPLATE.format(
                language_name="English",  # Internal processing in English
                json_template=json_template
            ).replace("Help users find and check the status of nearby evacuation shelters.", 
                     "EMERGENCY MODE: Help users immediately find and navigate to nearby evacuation shelters during active disasters.")\
              .replace("encourage checking shelter locations and status", 
                     "urgently encourage immediate shelter location checking")\
              .replace("Make it practical and helpful", 
                     "Make it urgent and action-oriented for immediate evacuation")\
              .replace("Focus on finding nearby shelters", 
                     "Emphasize immediate safety and evacuation readiness")
        else:
            # 平常時：事前確認のための提案
            # Create safe JSON template - internal processing in English
            json_template = get_json_template(
                f"Shelter preparedness suggestion in English, 1 sentence, 60 chars max",
                f"SPECIFIC question about shelter locations in English",
                f"View shelters"
            )
            
            prompt = SHELTER_STATUS_TEMPLATE.format(
                language_name="English",  # Internal processing in English
                json_template=json_template
            )

        data = await self.generate_with_llm(prompt, "shelter_status_update")
        if data:
            # Generated shelter suggestion data
            # Action query for shelter suggestion
            # Action display text for shelter suggestion
            
            return SuggestionItem(
                type="shelter_status_update",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={
                    "location_based": True,
                    "shelter_search": True,
                    "priority": "urgent" if emergency_condition else "normal",
                    "emergency_mode": emergency_condition,
                    "coordinates": {
                        "latitude": context.current_location.latitude if context.current_location else None,
                        "longitude": context.current_location.longitude if context.current_location else None
                    },
                    "requires_translation": True
                }
            )
        
        # フォールバック（内部処理は英語で統一、緊急度に応じて変更）
        if emergency_condition:
            fallback_content = "Find nearest evacuation shelter immediately!"
            fallback_action_query = "Where is the nearest evacuation shelter right now?"
            action_display = "Find NOW"
        else:
            fallback_content = "Check nearby evacuation shelters."
            fallback_action_query = "Where are evacuation shelters near me?"
            action_display = "View shelters"
        
        logger.warning(f"🏠 Using fallback for shelter suggestion - action_query: '{fallback_action_query}'")
        
        return SuggestionItem(
            type="shelter_status_update",
            content=fallback_content,
            action_query=fallback_action_query,
            action_display_text=action_display,
            action_data={
                "location_based": True, 
                "shelter_search": True, 
                "priority": "urgent" if emergency_condition else "normal",
                "emergency_mode": emergency_condition,
                "requires_translation": True
            }
        )
    
    async def generate_immediate_safety_action(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """即座の安全行動提案生成 - LLMによる自然言語理解で適切な行動を提供"""
        language_name = get_language_name(language_code)
        
        logger.info(f"   - is_emergency_mode: {context.is_emergency_mode}")
        logger.info(f"   - current_situation: {context.current_situation}")
        
        # Create safe JSON template for immediate safety action
        # For immediate safety action, we need a custom template with disaster_analysis field - internal processing in English
        json_template = json.dumps({
            "content": f"Urgent safety instruction in English, max 60 chars",
            "action_query": f"SPECIFIC question about this emergency in English",
            "action_display_text": f"Action label in English",
            "disaster_analysis": "Your reasoning about disaster type and appropriate response"
        }, ensure_ascii=False, indent=4)
        
        # LLMによる災害状況の自然言語理解と適切な安全行動生成
        prompt = f"""Analyze the emergency context and generate appropriate immediate safety action suggestions in English.

You are an expert disaster response advisor. Based on the emergency context, determine the most appropriate immediate safety actions and provide specific guidance.

[Emergency Context]
Emergency Mode: {context.is_emergency_mode}
Current Situation: {context.current_situation}
Location: {context.current_location.latitude if context.current_location else 'Unknown'}, {context.current_location.longitude if context.current_location else 'Unknown'}
Device Status: {context.device_status if context.device_status else 'No specific alerts'}

[Critical Safety Knowledge]
You must understand these key safety principles:
- TSUNAMI: Immediate vertical evacuation to high ground (10m+ elevation or 3rd floor+). Never wait to see waves.
- EARTHQUAKE: Drop, Cover, Hold On. Seek shelter under sturdy furniture during shaking.
- FLOOD: Move to higher ground or upper floors. Avoid flowing water.
- FIRE: Evacuate immediately via safe routes, stay low if smoke present.
- GENERAL EMERGENCY: Move to safe location, assess immediate dangers.

[Your Task]
1. Analyze the emergency context using your natural understanding
2. Determine the most likely disaster type and appropriate response
3. Generate urgent, actionable safety guidance
4. Ensure actions match the specific disaster type (tsunami ≠ earthquake actions)

Requirements:
- content: Urgent safety instruction (max 60 characters)
- action_query: Specific question users might ask about this emergency
- action_display_text: Brief action label
- disaster_analysis: Your reasoning about the situation

Return ONLY a valid JSON object:
{json_template}"""

        data = await self.generate_with_llm(prompt, "immediate_safety_action_llm")
        if data:
            # LLMの分析結果から災害タイプを抽出（フォールバック用）
            disaster_analysis = data.get("disaster_analysis", "")
            inferred_type = self._extract_disaster_type_from_analysis(disaster_analysis)
            
            return SuggestionItem(
                type="immediate_safety_action",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={
                    "priority": "critical",
                    "emergency": True,
                    "immediate": True,
                    "llm_analysis": disaster_analysis,
                    "inferred_disaster_type": inferred_type,
                    "requires_translation": True
                }
            )
        
        # LLM失敗時のフォールバック
        return SuggestionItem(
            type="immediate_safety_action",
            content="Move to a safe location immediately.",
            action_query="What should I do in an emergency?",
            action_display_text="Emergency Action",
            action_data={
                "priority": "critical", 
                "emergency": True, 
                "immediate": True, 
                "fallback": True,
                "requires_translation": True
            }
        )
    
    def _extract_disaster_type_from_analysis(self, analysis: str) -> str:
        """LLMの分析結果から災害タイプを抽出（フォールバック用のみ）"""
        try:
            analysis_lower = analysis.lower()
            # シンプルなキーワード抽出（LLMが主、これは補助のみ）
            if "tsunami" in analysis_lower or "津波" in analysis_lower:
                return "tsunami"
            elif "earthquake" in analysis_lower or "地震" in analysis_lower:
                return "earthquake"
            elif "flood" in analysis_lower or "洪水" in analysis_lower:
                return "flood"
            elif "fire" in analysis_lower or "火災" in analysis_lower:
                return "fire"
            else:
                return "general"
        except Exception:
            return "general"
    
    async def _get_mock_preparedness_news(self, language_code: str) -> Optional[SuggestionItem]:
        """モックの防災ニュースを取得"""
        try:
            # モックデータファイルを読み込み（Dockerコンテナ対応）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # /code/app/agents/safety_beacon_agent/suggestion_generators から /code/app へ
            app_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            mock_file_path = os.path.join(
                app_root,
                "resources", "mock_data", "disaster_preparedness_news.json"
            )
            
            # デバッグ用ログ
            logger.debug(f"Looking for mock preparedness news at: {mock_file_path}")
            if not os.path.exists(mock_file_path):
                logger.error(f"Mock preparedness news file not found at: {mock_file_path}")
                # アプリルートからのパスも試す
                alt_path = os.path.join("/code", "app", "resources", "mock_data", "disaster_preparedness_news.json")
                logger.debug(f"Trying alternative path: {alt_path}")
                if os.path.exists(alt_path):
                    mock_file_path = alt_path
                    logger.info(f"Found mock preparedness news at alternative path: {alt_path}")
                else:
                    logger.error(f"Alternative path also not found: {alt_path}")
                    raise FileNotFoundError(f"disaster_preparedness_news.json not found at {mock_file_path} or {alt_path}")
            
            with open(mock_file_path, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
            
            # ランダムにニュースを選択
            news_items = mock_data.get("disaster_preparedness_news", [])
            if not news_items:
                return None
                
            selected_news = random.choice(news_items)
            
            # 選択したニュースに基づいて提案を生成
            content = selected_news["title"]
            if len(content) > 60:
                content = content[:57] + "..."
            
            # action_queryをカテゴリに応じて生成
            action_queries = {
                "earthquake_preparation": "地震対策の基本を教えて",
                "emergency_kit": "非常用持ち出し袋に何を入れるべき？",
                "apartment_safety": "マンションの防災対策を知りたい",
                "typhoon_preparation": "台風対策の方法を教えて",
                "family_preparedness": "家族で防災計画を作る方法は？",
                "pet_safety": "ペットの防災対策を教えて",
                "home_evacuation": "在宅避難の準備方法を知りたい",
                "elderly_support": "高齢者の防災対策を教えて"
            }
            
            action_query = action_queries.get(
                selected_news["category"], 
                "防災準備の基本を教えて"
            )
            
            # 言語に応じて翻訳（シンプルなマッピング）
            if language_code == "en":
                content = self._translate_to_english(content)
                action_query = self._translate_query_to_english(action_query)
                action_display = "Learn more"
            elif language_code != "ja":
                # 他言語の場合は英語にフォールバック
                content = self._translate_to_english(content)
                action_query = self._translate_query_to_english(action_query)
                action_display = "Learn more"
                # LLMベース翻訳を使用するためのrequires_translationをtrueに
                return SuggestionItem(
                    type="disaster_preparedness",
                    content=content,
                    action_query=action_query,
                    action_display_text=action_display,
                    action_data={
                        "preparedness_type": selected_news["category"],
                        "priority": "normal",
                        "content_focus": "prevention",
                        "emergency_mode": False,
                        "mock_source": selected_news["source"],
                        "mock_url": selected_news["url"],
                        "requires_translation": True  # LLM翻訳が必要
                    }
                )
            else:
                action_display = "詳しく見る"
            
            return SuggestionItem(
                type="disaster_preparedness",
                content=content,
                action_query=action_query,
                action_display_text=action_display,
                action_data={
                    "preparedness_type": selected_news["category"],
                    "priority": "normal",
                    "content_focus": "prevention",
                    "emergency_mode": False,
                    "mock_source": selected_news["source"],
                    "mock_url": selected_news["url"],
                    "requires_translation": True  # 既に翻訳済み
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to load mock preparedness news: {e}")
            return None
    
    def _translate_to_english(self, japanese_text: str) -> str:
        """シンプルな英語翻訳マッピング"""
        translations = {
            "【防災の基本】地震への備え、今すぐできる5つのこと": "Earthquake Preparation: 5 Things You Can Do Now",
            "非常用持ち出し袋の中身リスト2024年版": "Emergency Kit Checklist 2024 Edition",
            "マンション住まいの防災対策ガイド": "Apartment Disaster Preparedness Guide",
            "【２０２４年夏】台風シーズンに備える準備リスト": "2024 Summer Typhoon Season Preparation",
            "子どもと一緒に学ぶ防災教育": "Family Disaster Education Guide",
            "ペットの防災対策完全ガイド": "Complete Pet Disaster Preparedness Guide",
            "在宅避難のススメ：自宅を避難所にする方法": "Home Evacuation: Shelter in Place Guide",
            "高齢者の防災対策：家族ができるサポート": "Elderly Disaster Support Guide"
        }
        return translations.get(japanese_text, japanese_text[:57] + "..." if len(japanese_text) > 60 else japanese_text)
    
    def _translate_query_to_english(self, japanese_query: str) -> str:
        """アクションクエリの英語翻訳"""
        query_translations = {
            "地震対策の基本を教えて": "Tell me about earthquake preparation basics",
            "非常用持ち出し袋に何を入れるべき？": "What should I put in emergency kit?",
            "マンションの防災対策を知りたい": "How to prepare for disasters in apartment?",
            "台風対策の方法を教えて": "How to prepare for typhoons?",
            "家族で防災計画を作る方法は？": "How to make family disaster plan?",
            "ペットの防災対策を教えて": "How to prepare pets for disasters?",
            "在宅避難の準備方法を知りたい": "How to prepare for sheltering at home?",
            "高齢者の防災対策を教えて": "How to help elderly prepare for disasters?",
            "防災準備の基本を教えて": "Tell me about disaster preparedness basics"
        }
        return query_translations.get(japanese_query, "Tell me about disaster preparedness")
    

# グローバルインスタンス
disaster_generator = DisasterSuggestionGenerator()