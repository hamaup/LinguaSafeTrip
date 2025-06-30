# backend/app/agents/safety_beacon_agent/suggestion_generators/unified_generator.py
"""Unified suggestion generation interface"""

import logging
from typing import Optional, Dict, Any

from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from .basic_generators import basic_generator
from .disaster_generators import disaster_generator

logger = logging.getLogger(__name__)

class UnifiedSuggestionGenerator:
    """統合提案生成器 - 全ての提案タイプを一元管理"""
    
    def __init__(self):
        self.basic_generator = basic_generator
        self.disaster_generator = disaster_generator
    
    async def generate_suggestion_by_type(
        self, 
        suggestion_type: str, 
        context: ProactiveSuggestionContext, 
        language_code: str = "ja"
    ) -> Optional[SuggestionItem]:
        """
        タイプ別の提案生成 - generate_single_suggestion_by_typeの後継
        
        Args:
            suggestion_type: 提案タイプ
            context: プロアクティブ提案コンテキスト
            language_code: 言語コード
            
        Returns:
            生成された提案、またはNone
        """
        try:
            # 基本的な提案タイプ
            if suggestion_type == "welcome_message":
                return await self.basic_generator.generate_welcome_message(context, language_code)
            elif suggestion_type == "emergency_contact_setup":
                return await self.basic_generator.generate_emergency_contact_setup(context, language_code)
            # guide_recommendation removed from suggestions
            # elif suggestion_type == "guide_recommendation":
            #     return await self.basic_generator.generate_guide_recommendation(context, language_code)
            elif suggestion_type == "seasonal_warning":
                return await self.basic_generator.generate_seasonal_warning(context, language_code)
            elif suggestion_type == "low_battery_warning":
                return await self.basic_generator.generate_low_battery_warning(context, language_code)
            elif suggestion_type == "quiz_reminder":
                return await self.basic_generator.generate_quiz_reminder(context, language_code)
            
            # 災害関連提案タイプ
            elif suggestion_type == "disaster_news":
                return await self.disaster_generator.generate_disaster_news(context, language_code)
            elif suggestion_type == "disaster_preparedness":
                return await self.disaster_generator.generate_disaster_preparedness(context, language_code)
            elif suggestion_type == "hazard_map_url":
                return await self.disaster_generator.generate_hazard_map_url(context, language_code)
            elif suggestion_type == "shelter_status_update":
                return await self.disaster_generator.generate_shelter_status_update(context, language_code)
            elif suggestion_type == "immediate_safety_action":
                return await self.disaster_generator.generate_immediate_safety_action(context, language_code)
            
            # 権限関連提案（フォールバック）
            elif suggestion_type == "location_permission_reminder":
                return await self._generate_permission_reminder(context, language_code, "location")
            elif suggestion_type == "notification_permission_reminder":
                return await self._generate_permission_reminder(context, language_code, "notification")
            
            # SMS提案（緊急時） - スマート制御
            elif suggestion_type == "safety_confirmation_sms_proposal":
                return await self._generate_sms_proposal(context, language_code)
            
            else:
                logger.warning(f"Unknown suggestion type: {suggestion_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating suggestion for type {suggestion_type}: {e}")
            return None
    
    async def _generate_permission_reminder(
        self, 
        context: ProactiveSuggestionContext, 
        language_code: str, 
        permission_type: str
    ) -> Optional[SuggestionItem]:
        """権限リマインダー生成（内部処理は英語で統一、翻訳は後で実行）"""
        # 内部処理は英語で統一、翻訳は後で実行
        content_map = {
            "location": "Please allow location access.",
            "notification": "Please allow notifications."
        }
        
        content = content_map.get(permission_type, "Please check permissions.")
        
        return SuggestionItem(
            type=f"{permission_type}_permission_reminder",
            content=content,
            action_query="",
            action_display_text="Settings",
            action_data={"permission_type": permission_type, "requires_translation": True}
        )
    
    async def _generate_sms_proposal(
        self, 
        context: ProactiveSuggestionContext, 
        language_code: str
    ) -> Optional[SuggestionItem]:
        """安否確認SMS提案生成（内部処理は英語で統一、翻訳は後で実行）"""
        # 緊急連絡先が登録されている場合のみ提案を生成
        logger.info(f"   - context.user_app_usage_summary: {context.user_app_usage_summary}")
        logger.info(f"   - user_app_usage_summary type: {type(context.user_app_usage_summary)}")
        
        emergency_contacts_count = getattr(context.user_app_usage_summary, 'local_contact_count', 0)
        logger.info(f"📞 Retrieved emergency_contacts_count for SMS: {emergency_contacts_count}")
        logger.info(f"📞 emergency_contacts_count type: {type(emergency_contacts_count)}")
        logger.info(f"📞 Condition check: {emergency_contacts_count} <= 0 = {emergency_contacts_count <= 0}")
        
        if emergency_contacts_count <= 0:
            logger.info(f"❌ SMS proposal skipped: no emergency contacts registered (count: {emergency_contacts_count})")
            # Return emergency contact setup suggestion instead
            return await self.basic_generator.generate_emergency_contact_setup(context, language_code)
        
        # 内部処理は英語で統一、翻訳は後で実行
        content = "Send safety confirmation message?"
        
        return SuggestionItem(
            type="safety_confirmation_sms_proposal",
            content=content,
            action_query="",
            action_display_text="Send",
            action_data={
                "sms_type": "safety_confirmation",
                "emergency": True,
                "template_available": True,
                "emergency_contacts_count": emergency_contacts_count,
                "requires_translation": True
            }
        )

# グローバルインスタンス - レガシー関数との互換性のため
unified_generator = UnifiedSuggestionGenerator()

# レガシー互換性関数
async def generate_single_suggestion_by_type(
    suggestion_type: str,
    context: ProactiveSuggestionContext,
    language_code: str = "ja"
) -> Optional[Dict[str, Any]]:
    """
    レガシー互換性のための関数
    ハートビートエンドポイントで使用される形式に合わせる
    """
    suggestion = await unified_generator.generate_suggestion_by_type(
        suggestion_type, context, language_code
    )
    
    if suggestion:
        return {
            "type": suggestion.type,
            "content": suggestion.content,
            "action_query": suggestion.action_query,
            "action_display_text": suggestion.action_display_text,
            "action_data": suggestion.action_data
        }
    
    return None