# backend/app/agents/safety_beacon_agent/suggestion_generators/basic_generators.py
"""Basic suggestion generators for common suggestion types"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json

from app.schemas.agent.suggestions import SuggestionItem
from app.schemas.agent.suggestions import ProactiveSuggestionContext
from .base import SuggestionGeneratorBase, get_language_name
from .prompt_templates import (
    WELCOME_MESSAGE_TEMPLATE,
    EMERGENCY_CONTACT_TEMPLATE,
    SEASONAL_WARNING_TEMPLATE,
    get_json_template
)

logger = logging.getLogger(__name__)

class BasicSuggestionGenerator(SuggestionGeneratorBase):
    """基本的な提案生成器"""
    
    async def generate_welcome_message(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """Welcome message generation - internal processing in English"""
        logger.info(f"🎉 Generating welcome message for language: {language_code}")
        language_name = get_language_name(language_code)
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Welcome message in English, 1 sentence, 60 chars max",
            f"SPECIFIC question about getting started in English",
            f"Get started"
        )
        
        prompt = WELCOME_MESSAGE_TEMPLATE.format(
            language_name="English",  # Internal processing in English
            json_template=json_template
        )

        data = await self.generate_with_llm(prompt, "welcome_message")
        if data:
            suggestion = SuggestionItem(
                type="welcome_message",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={"onboarding": True, "requires_translation": True}
            )
            
            # Translate to target language if needed
            if language_code != "en":
                suggestion = await self.translate_suggestion_consistently(suggestion, language_code)
            
            return suggestion
        
        # Fallback with translation
        fallback = self.get_fallback_content("welcome_message", language_code)
        fallback_suggestion = SuggestionItem(
            type="welcome_message",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={"onboarding": True, "requires_translation": True}
        )
        
        # Translate fallback if needed
        if language_code != "en":
            fallback_suggestion = await self.translate_suggestion_consistently(fallback_suggestion, language_code)
        
        return fallback_suggestion
    
    async def generate_emergency_contact_setup(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """緊急連絡先設定提案生成"""
        # 緊急連絡先が既に登録されている場合は提案を生成しない
        logger.info(f"   - context.user_app_usage_summary: {context.user_app_usage_summary}")
        logger.info(f"   - user_app_usage_summary type: {type(context.user_app_usage_summary)}")
        
        emergency_contacts_count = getattr(context.user_app_usage_summary, 'local_contact_count', 0)
        logger.info(f"📞 Retrieved emergency_contacts_count: {emergency_contacts_count}")
        logger.info(f"📞 emergency_contacts_count type: {type(emergency_contacts_count)}")
        logger.info(f"📞 Condition check: {emergency_contacts_count} > 0 = {emergency_contacts_count > 0}")
        
        if emergency_contacts_count > 0:
            logger.info(f"Emergency contact setup skipped: contacts already registered (count: {emergency_contacts_count})")
            return None
        
        language_name = get_language_name(language_code)
        
        # Check if we're in emergency mode
        is_emergency = context.is_emergency_mode if hasattr(context, 'is_emergency_mode') else False
        
        if is_emergency:
            # Create safe JSON template - internal processing in English
            json_template = get_json_template(
                f"Emergency contact suggestion in English, 1 sentence, 60 chars max",
                f"Empty or minimal query in English",
                f"Register contacts"
            )
            
            prompt = EMERGENCY_CONTACT_TEMPLATE.format(
                urgency="an URGENT ",
                language_name="English",  # Internal processing in English
                context_description="This is during an emergency/disaster. Users need to register contacts NOW for safety confirmations.",
                urgency_modifier="urgently ",
                emphasis="Emphasize immediate need during disaster",
                focus_area="sending safety confirmations",
                json_template=json_template
            )
        else:
            # Create safe JSON template - internal processing in English
            json_template = get_json_template(
                f"Emergency contact suggestion in English, 1 sentence, 60 chars max",
                f"Empty or minimal query in English",
                f"Register contacts"
            )
            
            prompt = EMERGENCY_CONTACT_TEMPLATE.format(
                urgency="a ",
                language_name="English",  # Internal processing in English
                context_description="Help users register family and friends for emergency safety confirmation.",
                urgency_modifier="",
                emphasis="Make it actionable and urgent but not scary",
                focus_area="safety confirmation benefits",
                json_template=json_template
            )

        data = await self.generate_with_llm(prompt, "emergency_contact_setup")
        if data:
            return SuggestionItem(
                type="emergency_contact_setup",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={"setup_type": "contacts", "requires_translation": True}
            )
        
        # フォールバック
        fallback = self.get_fallback_content("emergency_contact_setup", language_code)
        return SuggestionItem(
            type="emergency_contact_setup",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={"setup_type": "contacts", "requires_translation": True}
        )
    
    async def generate_guide_recommendation(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """ガイド推奨生成"""
        language_name = get_language_name(language_code)
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Guide recommendation in English, 1 sentence, 60 chars max",
            f"SPECIFIC question about disaster preparation in English",
            f"View guides"
        )
        
        prompt = f"""Create a suggestion about disaster preparedness guides in English.

Help users learn about disaster preparedness through comprehensive guides.

Requirements:
- content should encourage learning about disaster preparedness (max 60 characters)
- Make it educational and helpful
- Focus on being prepared

IMPORTANT for action_query:
- Must be a specific question about disaster preparedness
- Should ask about specific preparation topics
- MUST match the specific topic mentioned in content
- If content is about "home safety tips", query should ask about "home safety tips" specifically
- Examples in Japanese: "災害への備え方を教えて", "防災の基本を知りたい", "家庭でできる防災対策は？"
- Examples in English: "How to prepare for disasters?", "Show me disaster prep basics", "What can I do at home for safety?"

Return ONLY a valid JSON object:
{json_template}"""

        data = await self.generate_with_llm(prompt, "guide_recommendation")
        if data:
            return SuggestionItem(
                type="guide_recommendation",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={"guide_type": "general", "guide_id": "basic_disaster_guide", "requires_translation": True}
            )
        
        # フォールバック
        fallback = self.get_fallback_content("guide_recommendation", language_code)
        return SuggestionItem(
            type="guide_recommendation",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={"guide_type": "general", "guide_id": "basic_disaster_guide", "requires_translation": True}
        )
    
    async def generate_seasonal_warning(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """Current season warning generation - internal processing in English"""
        logger.info(f"🌸 Generating seasonal warning for language: {language_code}")
        language_name = get_language_name(language_code)
        
        # Get current season information
        month = datetime.now().month
        season_info = self._get_seasonal_info(month)
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Current seasonal warning in English, 1 sentence, 60 chars max",
            f"SPECIFIC question about current seasonal risks in English",
            f"View tips"
        )
        
        prompt = SEASONAL_WARNING_TEMPLATE.format(
            season=season_info['season'],
            language_name="English",  # Internal processing in English
            risks=season_info['risks'],
            json_template=json_template
        )

        data = await self.generate_with_llm(prompt, "seasonal_warning")
        if data:
            suggestion = SuggestionItem(
                type="seasonal_warning",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={"season": season_info['season'], "risks": season_info['risks'], "requires_translation": True}
            )
            
            # Translate to target language if needed
            if language_code != "en":
                suggestion = await self.translate_suggestion_consistently(suggestion, language_code)
            
            return suggestion
        
        # Fallback with translation
        fallback = self.get_fallback_content("seasonal_warning", language_code)
        fallback_suggestion = SuggestionItem(
            type="seasonal_warning",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={"season": season_info['season'], "risks": season_info['risks'], "requires_translation": language_code != "en"}
        )
        
        # Translate fallback if needed
        if language_code != "en":
            fallback_suggestion = await self.translate_suggestion_consistently(fallback_suggestion, language_code)
        
        return fallback_suggestion
    
    async def generate_low_battery_warning(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """低バッテリー警告生成"""
        battery_level = context.device_status.get("battery_level", 100) if context.device_status else 100
        
        # バッテリー残量が45%以上の場合は提案を生成しない
        if battery_level >= 45:
            logger.info(f"🔋 Low battery warning skipped: battery level {battery_level}% is above 45% threshold")
            return None
        
        language_name = get_language_name(language_code)
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Battery warning in English, 1 sentence, 60 chars max",
            f"SPECIFIC question about emergency battery tips in English",
            f"Battery tips"
        )
        
        prompt = f"""Create a low battery warning suggestion in English.

Current battery level: {battery_level}%

Requirements:
- content should alert about low battery and recommend charging (max 60 characters)
- Make it urgent but not alarming
- Focus on maintaining device readiness for emergencies

IMPORTANT for action_query:
- Must be a specific question about battery management for emergencies
- Should ask about power saving or emergency battery tips
- MUST relate to the urgency level in content
- If content warns about low battery urgently, query should reflect that urgency
- Examples in Japanese: "緊急時のバッテリー節約方法を教えて", "停電時の充電対策は？", "モバイルバッテリーの準備方法"
- Examples in English: "How to save battery for emergencies?", "Power outage charging tips?", "Mobile battery preparation guide"

Return ONLY a valid JSON object:
{json_template}"""

        data = await self.generate_with_llm(prompt, "low_battery_warning")
        if data:
            return SuggestionItem(
                type="low_battery_warning",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={"battery_level": battery_level, "urgent": battery_level < 20, "requires_translation": True}
            )
        
        # フォールバック
        fallback = self.get_fallback_content("low_battery_warning", language_code)
        return SuggestionItem(
            type="low_battery_warning",
            content=fallback["content"],
            action_query=fallback["action_query"],
            action_display_text=fallback["action_display_text"],
            action_data={"battery_level": battery_level, "urgent": battery_level < 20, "requires_translation": True}
        )
    
    async def generate_quiz_reminder(self, context: ProactiveSuggestionContext, language_code: str) -> Optional[SuggestionItem]:
        """防災クイズリマインダー提案生成 - 無効化"""
        logger.info("🚫 Quiz reminder disabled - no suggestion generated")
        return None
    
    def _get_seasonal_info(self, month: int) -> Dict[str, str]:
        """現在の時期に特化した季節情報を取得"""
        current_date = datetime.now()
        
        # より具体的な月別リスク情報
        if month == 1:
            return {"season": "Winter (January)", "risks": "Heating fire hazards, Dry air fires"}
        elif month == 2:
            return {"season": "Late Winter (February)", "risks": "Heating fires, Strong winds, Temperature swings"}
        elif month == 3:
            return {"season": "Early Spring (March)", "risks": "Strong spring winds, Wildfire risk"}
        elif month == 4:
            return {"season": "Spring (April)", "risks": "Spring storms, Sudden weather changes"}
        elif month == 5:
            return {"season": "Late Spring (May)", "risks": "Early summer preparation, Strong winds"}
        elif month == 6:
            return {"season": "Early Rainy Season (June)", "risks": "Heavy rain, Flooding, Early typhoons"}
        elif month == 7:
            return {"season": "Peak Rainy Season (July)", "risks": "Severe flooding, Landslides, Typhoons"}
        elif month == 8:
            return {"season": "Late Summer (August)", "risks": "Peak typhoon season, Extreme heat"}
        elif month == 9:
            return {"season": "Autumn Typhoons (September)", "risks": "Major typhoons, Autumn floods"}
        elif month == 10:
            return {"season": "Mid Autumn (October)", "risks": "Late typhoons, Temperature drops"}
        elif month == 11:
            return {"season": "Late Autumn (November)", "risks": "Strong winds, Early winter preparation"}
        else:  # month == 12
            return {"season": "Early Winter (December)", "risks": "Winter heating setup, Year-end preparation"}

    async def generate_safety_confirmation_sms_proposal(self, context: ProactiveSuggestionContext, language_code: str = "ja") -> Optional[SuggestionItem]:
        """安否確認SMS送信提案の生成"""
        # Generating safety confirmation SMS proposal
        
        # 緊急連絡先の確認
        emergency_contacts_count = getattr(context.user_app_usage_summary, 'local_contact_count', 0)
        if emergency_contacts_count == 0:
            logger.warning("❌ No emergency contacts found - cannot generate SMS proposal")
            return None
        
        logger.info(f"📞 Found {emergency_contacts_count} emergency contact(s)")
        
        # Create safe JSON template - internal processing in English
        json_template = get_json_template(
            f"Suggest sending safety confirmation SMS to emergency contacts in English, 40 chars max",
            f"Send safety confirmation SMS now",
            f"Send SMS"
        )
        
        prompt = f"""Generate an emergency safety confirmation SMS proposal in English.

Context:
- Emergency situation is active
- User has {emergency_contacts_count} emergency contact(s) registered
- Need to propose sending safety confirmation message

Requirements:
- Content: Brief suggestion to send safety SMS (40 chars max)
- Action query: "Send safety confirmation SMS now"
- Action display text: "Send SMS"
- Tone: Urgent but caring

{json_template}"""

        data = await self.generate_with_llm(prompt, "safety_confirmation_sms_proposal")
        if data:
            suggestion = SuggestionItem(
                type="safety_confirmation_sms_proposal",
                content=data.get("content", ""),
                action_query=data.get("action_query", ""),
                action_display_text=data.get("action_display_text", ""),
                action_data={
                    "contact_count": emergency_contacts_count,
                    "requires_translation": True
                }
            )
            
            # Translate to target language if needed
            if language_code != "en":
                suggestion = await self.translate_suggestion_consistently(suggestion, language_code)
            
            return suggestion
        
        # Fallback in English only (CLAUDE.md principle)
        fallback_suggestion = SuggestionItem(
            type="safety_confirmation_sms_proposal",
            content="Send safety confirmation to family",
            action_query="Send safety confirmation SMS now",
            action_display_text="Send SMS",
            action_data={
                "contact_count": emergency_contacts_count,
                "requires_translation": language_code != "en"
            }
        )
        
        # Translate fallback if needed
        if language_code != "en":
            fallback_suggestion = await self.translate_suggestion_consistently(fallback_suggestion, language_code)
        
        return fallback_suggestion

# グローバルインスタンス
basic_generator = BasicSuggestionGenerator()