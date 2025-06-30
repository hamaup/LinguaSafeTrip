#!/usr/bin/env python3
"""
Batch Suggestion Generator - LLM Optimization
バッチ提案生成器 - LLM効率化
"""

import logging
import json
from typing import List, Dict, Any, Optional
from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
from app.prompts.suggestion_prompts import BATCH_SUGGESTION_GENERATION_PROMPT

logger = logging.getLogger(__name__)

class BatchSuggestionGenerator:
    """バッチ提案生成器 - 複数の提案を1回のLLM呼び出しで生成"""
    
    def __init__(self):
        self.suggestion_types = {
            "welcome_message": "Welcome greeting for new users",  # 平常時のみ
            "emergency_contact_setup": "Reminder to set up emergency contacts",
            "seasonal_warning": "Warning about seasonal disasters and preparation",  # 平常時のみ
            "low_battery_warning": "Reminder to charge phone for emergency readiness",
            "quiz_reminder": "Interactive disaster preparedness quiz",
            "disaster_news": "Recent disaster news relevant to user location",
            "disaster_preparedness": "Disaster preparedness tips and prevention information",
            "hazard_map_url": "Local hazard maps and emergency information",
            "shelter_status_update": "Nearby evacuation shelter status",
            "immediate_safety_action": "Immediate safety actions for current situation",
            "location_permission_reminder": "Request location permission for better assistance",
            "notification_permission_reminder": "Request notification permission for alerts",
            "safety_confirmation_sms_proposal": "Propose sending safety confirmation SMS"  # 緊急時のみ
        }
    
    async def generate_batch_suggestions(
        self,
        suggestion_types: List[str],
        context: ProactiveSuggestionContext,
        language_code: str = "ja"
    ) -> Dict[str, Optional[SuggestionItem]]:
        """
        複数の提案を1回のLLM呼び出しで生成（効率化）
        
        Args:
            suggestion_types: 生成する提案タイプのリスト
            context: プロアクティブ提案コンテキスト
            language_code: 出力言語（翻訳は後で実行）
            
        Returns:
            提案タイプをキーとした提案アイテム辞書
        """
        try:
            # バッチ生成プロンプトを構築
            batch_prompt = self._build_batch_prompt(suggestion_types, context, language_code)
            
            # 1回のLLM呼び出しで全ての提案を生成
            response = await ainvoke_llm(
                prompt=batch_prompt,
                task_type="response_generation",
                temperature=0.7,
                max_tokens=2048
            )
            
            # 応答をパースして個別の提案に分割
            suggestions = await self._parse_batch_response(response, suggestion_types, context, language_code)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Batch suggestion generation failed: {e}")
            # フォールバック: 空の結果を返す
            return {suggestion_type: None for suggestion_type in suggestion_types}
    
    def _build_batch_prompt(
        self,
        suggestion_types: List[str],
        context: ProactiveSuggestionContext,
        language_code: str
    ) -> str:
        """バッチ生成用のプロンプトを構築"""
        
        # コンテキスト情報を整理
        context_info = self._format_context_info(context)
        
        # 各提案タイプの説明を準備
        type_descriptions = []
        for i, suggestion_type in enumerate(suggestion_types, 1):
            description = self.suggestion_types.get(suggestion_type, f"Generate {suggestion_type}")
            type_descriptions.append(f"{i}. {suggestion_type}: {description}")
        
        prompt = BATCH_SUGGESTION_GENERATION_PROMPT.format(
            context_info=context_info,
            type_descriptions=chr(10).join(type_descriptions),
            suggestion_count=len(suggestion_types)
        )
        
        return prompt
    
    def _format_context_info(self, context: ProactiveSuggestionContext) -> str:
        """コンテキスト情報をフォーマット"""
        info_parts = []
        
        # 緊急モード情報
        emergency_mode = False
        if hasattr(context, 'emergency_mode') and context.emergency_mode:
            emergency_mode = True
            info_parts.append("⚠️ EMERGENCY MODE ACTIVE")
        
        # 災害アラート情報
        if hasattr(context, 'disaster_alerts') and context.disaster_alerts:
            alert_count = len(context.disaster_alerts)
            info_parts.append(f"🚨 {alert_count} active disaster alert(s)")
        
        # 緊急時の制限情報を追加
        if emergency_mode:
            info_parts.append("🚫 EMERGENCY RESTRICTIONS: welcome_message and seasonal_warning are disabled")
        
        # 時刻情報
        if hasattr(context, 'current_time'):
            info_parts.append(f"Time: {context.current_time}")
        
        # 位置情報
        if hasattr(context, 'location') and context.location:
            info_parts.append(f"Location: {context.location}")
        
        # アプリ使用状況
        if hasattr(context, 'user_app_usage_summary') and context.user_app_usage_summary:
            usage = context.user_app_usage_summary
            if hasattr(usage, 'local_contact_count'):
                info_parts.append(f"Emergency contacts: {usage.local_contact_count}")
            if hasattr(usage, 'last_active_days'):
                info_parts.append(f"Last active: {usage.last_active_days} days ago")
        
        return "\n".join(info_parts) if info_parts else "No specific context available"
    
    async def _parse_batch_response(
        self,
        response: str,
        expected_types: List[str],
        context: ProactiveSuggestionContext,
        language_code: str
    ) -> Dict[str, Optional[SuggestionItem]]:
        """バッチ応答をパースして個別の提案に分割"""
        try:
            # JSONを抽出
            json_match = self._extract_json_from_response(response)
            if not json_match:
                logger.error("No valid JSON found in batch response")
                return {suggestion_type: None for suggestion_type in expected_types}
            
            data = json.loads(json_match)
            suggestions_data = data.get('suggestions', [])
            
            # 提案辞書を構築
            suggestions = {}
            
            for suggestion_data in suggestions_data:
                suggestion_type = suggestion_data.get('type')
                if suggestion_type in expected_types:
                    try:
                        suggestion_item = SuggestionItem(
                            type=suggestion_type,
                            content=suggestion_data.get('content', ''),
                            action_query=suggestion_data.get('action_query', ''),
                            action_display_text=suggestion_data.get('action_display_text', ''),
                            action_data=suggestion_data.get('action_data', {})
                        )
                        suggestions[suggestion_type] = suggestion_item
                    except Exception as e:
                        logger.error(f"Failed to create SuggestionItem for {suggestion_type}: {e}")
                        suggestions[suggestion_type] = None
                else:
                    logger.warning(f"Unexpected suggestion type in response: {suggestion_type}")
            
            # 不足している提案タイプを個別生成で補完
            for suggestion_type in expected_types:
                if suggestion_type not in suggestions or suggestions[suggestion_type] is None:
                    logger.warning(f"Missing suggestion for type: {suggestion_type}, attempting individual generation")
                    try:
                        fallback_suggestion = await self._generate_individual_fallback(
                            suggestion_type, context, language_code
                        )
                        suggestions[suggestion_type] = fallback_suggestion
                    except Exception as e:
                        logger.error(f"Individual fallback failed for {suggestion_type}: {e}")
                        suggestions[suggestion_type] = None
            
            return suggestions
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in batch response: {e}")
            return {suggestion_type: None for suggestion_type in expected_types}
        except Exception as e:
            logger.error(f"Error parsing batch response: {e}")
            return {suggestion_type: None for suggestion_type in expected_types}
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """応答からJSONを抽出"""
        import re
        
        # JSONブロックを探す
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # Markdownコードブロック
            r'```\s*(\{.*?\})\s*```',      # 汎用コードブロック
            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # ネストしたJSONオブジェクト
            r'(\{.*?\})'                   # シンプルなJSONオブジェクト
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1)
        
        return None
    
    async def _generate_individual_fallback(
        self, 
        suggestion_type: str, 
        context: ProactiveSuggestionContext, 
        language_code: str
    ) -> Optional[SuggestionItem]:
        """個別提案の生成（バッチ失敗時のフォールバック）"""
        try:
            # basic_generatorから個別生成メソッドを呼び出し
            from .basic_generators import basic_generator
            
            if suggestion_type == "safety_confirmation_sms_proposal":
                return await basic_generator.generate_safety_confirmation_sms_proposal(context, language_code)
            elif suggestion_type == "seasonal_warning":
                return await basic_generator.generate_seasonal_warning(context, language_code)
            elif suggestion_type == "welcome_message":
                return await basic_generator.generate_welcome_message(context, language_code)
            # 他の個別生成メソッドも必要に応じて追加
            else:
                logger.warning(f"No individual fallback available for {suggestion_type}")
                return None
                
        except Exception as e:
            logger.error(f"Individual fallback generation failed for {suggestion_type}: {e}")
            return None

# グローバルインスタンス
batch_generator = BatchSuggestionGenerator()