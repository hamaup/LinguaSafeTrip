# backend/app/agents/safety_beacon_agent/suggestion_generators/base.py
"""Base utilities and classes for suggestion generation"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from app.tools.translation_tool import translation_tool
from ..core.llm_singleton import ainvoke_llm

logger = logging.getLogger(__name__)

# parse_llm_response function removed - no longer needed with unified LLM invocation

def get_language_name(language_code: str) -> str:
    """言語コードから言語名を取得"""
    language_mapping = {
        'ja': 'Japanese',
        'en': 'English', 
        'zh': 'Chinese',
        'zh_CN': 'Chinese (Simplified)',
        'zh_TW': 'Chinese (Traditional)',
        'ko': 'Korean',
        'it': 'Italian',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German'
    }
    return language_mapping.get(language_code, 'English')

class SuggestionGeneratorBase:
    """提案生成の基底クラス"""
    
    def __init__(self):
        self.translation_tool = None
    
    async def translate_text(self, text: str, target_language: str, source_language: str = "en") -> str:
        """テキストを翻訳（統一翻訳ツール使用）"""
        return await translation_tool.translate(text, target_language, source_language)
    
    async def translate_suggestion_consistently(self, suggestion: SuggestionItem, target_language: str) -> SuggestionItem:
        """提案の一貫性を保った翻訳"""
        if target_language == "en":
            return suggestion
        
        if not suggestion.action_data or not suggestion.action_data.get("requires_translation", False):
            return suggestion
        
        try:
            # バッチ翻訳で一貫性を保つ
            texts_to_translate = []
            if suggestion.content:
                texts_to_translate.append(suggestion.content)
            if suggestion.action_query:
                texts_to_translate.append(suggestion.action_query)
            if suggestion.action_display_text:
                texts_to_translate.append(suggestion.action_display_text)
            
            if not texts_to_translate:
                return suggestion
            
            # 一括翻訳実行
            translated_texts = []
            for text in texts_to_translate:
                translated = await self.translate_text(text, target_language)
                translated_texts.append(translated)
            
            # 翻訳結果を適用
            index = 0
            if suggestion.content:
                suggestion.content = translated_texts[index]
                index += 1
            if suggestion.action_query:
                suggestion.action_query = translated_texts[index]
                index += 1
            if suggestion.action_display_text:
                suggestion.action_display_text = translated_texts[index]
                index += 1
            
            # 翻訳後の一貫性再検証
            data = {
                'content': suggestion.content,
                'action_query': suggestion.action_query,
                'action_display_text': suggestion.action_display_text
            }
            fixed_data = self._validate_and_fix_content_query_alignment(data, suggestion.type)
            
            suggestion.content = fixed_data.get('content', suggestion.content)
            suggestion.action_query = fixed_data.get('action_query', suggestion.action_query)
            
            # 翻訳完了マーク
            if suggestion.action_data:
                suggestion.action_data["requires_translation"] = False
            
            # Translation completed for {suggestion.type}
            
        except Exception as e:
            logger.error(f"Translation error for suggestion {suggestion.type}: {e}")
        
        return suggestion
    
    async def generate_with_llm(self, prompt: str, suggestion_type: str) -> Optional[Dict[str, Any]]:
        """LLMを使用して提案を生成"""
        try:
            response_text = await ainvoke_llm(prompt, task_type="suggestion_generation", temperature=0.7)
            
            # JSON解析
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            # Validate and auto-fix content-query alignment
            if data and 'content' in data and 'action_query' in data:
                data = self._validate_and_fix_content_query_alignment(data, suggestion_type)
            
            return data
            
        except Exception as e:
            logger.error(f"LLM generation error for {suggestion_type}: {e}")
            return None
    
    def _validate_and_fix_content_query_alignment(self, data: Dict[str, Any], suggestion_type: str) -> Dict[str, Any]:
        """コンテンツとクエリの整合性を検証・自動修正"""
        
        # Skip validation for emergency contact setup (opens dialog)
        if suggestion_type in ['emergency_contact_setup', 'contact_registration_reminder']:
            return data
        
        content = data.get('content', '')
        query = data.get('action_query', '')
        
        if not content or not query:
            return data
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Auto-fix location references
        if 'your area' in content_lower:
            if 'my area' not in query_lower and 'my location' not in query_lower and 'near me' not in query_lower:
                # Replace or add location reference
                if 'area' in query_lower:
                    query = query.replace('your area', 'my area').replace('the area', 'my area')
                elif query:
                    query = f"{query.rstrip('?')} near me?"
                data['action_query'] = query
                # Auto-fixed location reference
        
        # Auto-fix disaster type consistency
        disaster_types = ['earthquake', 'tsunami', 'typhoon', 'flood', 'fire', 'landslide', 'storm', 'hurricane']
        content_disasters = [d for d in disaster_types if d in content_lower]
        query_disasters = [d for d in disaster_types if d in query_lower]
        
        if content_disasters and not query_disasters:
            primary_disaster = content_disasters[0]
            if query:
                query = f"{primary_disaster.title()}: {query}"
                data['action_query'] = query
                # Auto-fixed disaster type
        
        # Auto-fix urgency alignment
        urgent_words = ['immediate', 'now', 'urgent', 'emergency', 'quickly', 'asap']
        content_urgent = any(word in content_lower for word in urgent_words)
        query_urgent = any(word in query_lower for word in urgent_words)
        
        if content_urgent and not query_urgent:
            if query and not query.endswith('now?') and not query.endswith('immediately?'):
                query = f"{query.rstrip('?')} immediately?"
                data['action_query'] = query
                # Auto-fixed urgency
        
        # Ensure action_query is specific enough
        vague_queries = ['tell me more', 'learn about', 'information about', 'help with']
        if any(vague in query_lower for vague in vague_queries):
            # Try to make it more specific based on content
            if 'shelter' in content_lower:
                query = "Where are evacuation shelters near me?"
            elif 'hazard' in content_lower:
                query = "Show me hazard map for my area"
            elif 'contact' in content_lower:
                query = "How do I register emergency contacts?"
            elif 'prepare' in content_lower:
                if content_disasters:
                    query = f"How do I prepare for {content_disasters[0]}?"
                else:
                    query = "How do I prepare for disasters?"
            
            data['action_query'] = query
            # Auto-fixed vague query
        
        return data
    
    def get_fallback_content(self, suggestion_type: str, language_code: str) -> Dict[str, str]:
        """フォールバック用の定数メッセージ（内部処理は英語で統一）"""
        # 内部処理は英語で統一、翻訳は後で実行
        fallbacks = {
            "welcome_message": {
                "content": "Welcome to LinguaSafeTrip. Let's review your basic settings.",
                "action_query": "How do I use LinguaSafeTrip?",
                "action_display_text": "Get started"
            },
            "emergency_contact_setup": {
                "content": "Please register emergency contacts for safety preparedness.",
                "action_query": "",  # 通知タイプ
                "action_display_text": "Register"
            },
            "guide_recommendation": {
                "content": "Please review our disaster preparedness guides.",
                "action_query": "Show me disaster preparedness guides",
                "action_display_text": "View guides"
            },
            "seasonal_warning": {
                "content": "Prepare for current rainy season risks now.",
                "action_query": "How to prepare for June heavy rain and flooding?",
                "action_display_text": "Rainy season prep"
            },
            "low_battery_warning": {
                "content": "Battery level is low. We recommend charging your device.",
                "action_query": "How to save battery for emergencies?",
                "action_display_text": "Battery tips"
            },
            "quiz_reminder": {
                "content": "Test your disaster preparedness knowledge with our quiz!",
                "action_query": "Start disaster preparedness quiz",
                "action_display_text": "Start quiz"
            },
            "disaster_news": {
                "content": "Check latest disaster alerts and emergency information now.",
                "action_query": "Show me latest disaster news",
                "action_display_text": "Latest news"
            },
            "disaster_preparedness": {
                "content": "Check disaster preparedness tips you can start today.",
                "action_query": "Show me disaster preparedness tips",
                "action_display_text": "View tips"
            },
            "hazard_map_url": {
                "content": "Understanding your local disaster risks helps you prepare better.",
                "action_query": "Show me hazard map for my area",
                "action_display_text": "View map"
            }
        }
        
        fallback_data = fallbacks.get(suggestion_type, fallbacks["welcome_message"])
        return {
            "content": fallback_data["content"],
            "action_query": fallback_data["action_query"],
            "action_display_text": fallback_data["action_display_text"]
        }