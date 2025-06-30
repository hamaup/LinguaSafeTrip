"""
意図不明時の質問返しハンドラー
ユーザーの意図が不明確な場合に、適切な質問を返して明確化を促す
"""
import logging
from typing import Dict, Any
from app.schemas.agent_state import AgentState
from ..core.llm_singleton import ainvoke_llm

logger = logging.getLogger(__name__)

async def clarification_handler(state: AgentState) -> Dict[str, Any]:
    """意図不明時の質問返しハンドラー"""
    
    logger.info("❓ NODE ENTRY: clarification_handler")
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "ja")
    intent_confidence = state.get("intent_confidence", 0.0)
    primary_intent = state.get("primary_intent", "unknown")
    context_requirements = state.get("context_requirements", {})
    
    # 会話履歴から文脈を取得
    chat_history = state.get("chat_history", [])
    recent_context = ""
    if chat_history:
        # 直近の会話から文脈を抽出
        recent_messages = chat_history[-3:] if len(chat_history) > 3 else chat_history
        recent_context = "Recent conversation: " + str(recent_messages)
    
    # LLMで適切な質問を生成
    clarification_prompt = f"""You are a disaster prevention assistant helping to clarify user intent.

User input: "{user_input}"
Detected intent: {primary_intent} (confidence: {intent_confidence})
Required context: {context_requirements}
{recent_context}

The user's intent is unclear. Generate a natural, helpful clarifying question.

Guidelines:
1. Be conversational and friendly
2. Focus on disaster/safety related possibilities if relevant
3. Offer 2-3 specific options if possible
4. Keep it concise
5. Generate response in English (will be translated by system)

For example:
- If user says "Is it safe?" → "Are you asking about current disaster conditions in your area, or about general safety preparations?"
- If user says "Help" → "I'm here to help! Are you in an emergency situation, or looking for disaster preparedness information?"
- If user says "Tomorrow" → "Are you asking about tomorrow's weather warnings, or planning for disaster preparedness?"

Generate a clarifying question:"""

    try:
        clarification_text = await ainvoke_llm(
            prompt=clarification_prompt,
            task_type="clarification",
            temperature=0.7
        )
        
        # 質問返し用のカード生成
        suggestion_cards = []
        
        # 低信頼度の意図に基づいて選択肢を提供
        if primary_intent == "disaster_information":
            suggestion_cards = [
                {
                    "type": "action",
                    "text": "Check current disasters" if user_language == "en" else "現在の災害情報を確認",
                    "action": "check_disasters"
                },
                {
                    "type": "action", 
                    "text": "View disaster alerts" if user_language == "en" else "災害警報を見る",
                    "action": "view_alerts"
                }
            ]
        elif primary_intent == "evacuation_support":
            suggestion_cards = [
                {
                    "type": "action",
                    "text": "Find shelters" if user_language == "en" else "避難所を探す",
                    "action": "find_shelters"
                },
                {
                    "type": "action",
                    "text": "Evacuation guidance" if user_language == "en" else "避難ガイダンス",
                    "action": "evacuation_guide"
                }
            ]
        else:
            # 一般的な選択肢
            suggestion_cards = [
                {
                    "type": "action",
                    "text": "Disaster information" if user_language == "en" else "災害情報",
                    "action": "disaster_info"
                },
                {
                    "type": "action",
                    "text": "Find shelters" if user_language == "en" else "避難所検索",
                    "action": "find_shelters"
                },
                {
                    "type": "action",
                    "text": "Safety guide" if user_language == "en" else "防災ガイド",
                    "action": "safety_guide"
                }
            ]
        
        logger.info(f"❓ Generated clarification with {len(suggestion_cards)} options")
        
        return {
            **state,
            "final_response_text": clarification_text,
            "suggestion_cards": suggestion_cards,
            "requires_action": False,
            "waiting_for_clarification": True,
            "clarification_count": state.get("clarification_count", 0) + 1,
            "last_response": clarification_text,
            "response_metadata": {
                "response_type": "clarification",
                "intent_was_unclear": True,
                "original_confidence": intent_confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Clarification generation failed: {e}")
        
        # フォールバックメッセージ（英語で生成、システムが翻訳）
        fallback_message = "I'm sorry, I didn't quite understand. Could you tell me more about what you're looking for? I can help with disaster information, finding shelters, or safety guidance."
        
        return {
            **state,
            "final_response_text": fallback_message,
            "requires_action": False,
            "clarification_error": str(e)
        }

def should_request_clarification(state: AgentState) -> bool:
    """質問返しが必要かどうかを判定"""
    
    confidence = state.get("intent_confidence", 0.0)
    clarification_count = state.get("clarification_count", 0)
    emergency_detected = state.get("emergency_detected", False)
    
    # 緊急時は質問返しをスキップ
    if emergency_detected:
        return False
    
    # 質問返しの回数制限（無限ループ防止）
    if clarification_count >= 2:
        return False
    
    # 信頼度が閾値以下
    if confidence < 0.5:
        return True
    
    return False