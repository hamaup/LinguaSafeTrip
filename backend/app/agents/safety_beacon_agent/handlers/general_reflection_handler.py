"""
General Unified Reflection Handler
セルフリフレクション機能付き一般対応ハンドラー
"""
import logging
import json
from typing import Dict, Any
from langchain_core.messages import AIMessage
from app.schemas.agent_state import AgentState
from ..core.llm_singleton import ainvoke_llm

logger = logging.getLogger(__name__)

async def general_unified_reflection(state: AgentState) -> Dict[str, Any]:
    """セルフリフレクション機能付き一般対応ハンドラー"""
    
    logger.info("🤔 NODE ENTRY: general_unified_reflection")
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "ja")
    reflection_count = state.get("reflection_count", 0)
    
    logger.info(f"🤔 Processing: '{user_input[:50]}...' (reflection: {reflection_count})")
    
    # 第1段階: 初期応答生成
    if reflection_count == 0:
        response = await _generate_initial_response(user_input, user_language)
        
        # セルフリフレクション: この応答で十分か？
        reflection_result = await _self_reflect(user_input, response, user_language)
        
        if reflection_result["needs_deeper_analysis"]:
            # より深い分析が必要 - 同じ関数内で処理を継続
            logger.info("🤔 Needs deeper analysis - generating improved response")
            improved_response = await _generate_improved_response(
                user_input, response, reflection_result["feedback"], user_language
            )
            return _format_final_response(improved_response, user_language)
        else:
            # 初回応答で十分
            logger.info("✅ Initial response sufficient")
            return _format_final_response(response, user_language)
    
    # 第2段階: 深い分析後の応答
    elif reflection_count == 1:
        initial_response = state.get("initial_response", "")
        feedback = state.get("reflection_feedback", "")
        
        logger.info("🧠 Generating improved response after reflection")
        improved_response = await _generate_improved_response(
            user_input, initial_response, feedback, user_language
        )
        
        return _format_final_response(improved_response, user_language)
    
    # 最大2回まで
    else:
        logger.warning("🚫 Max reflections reached, using fallback")
        fallback_response = await _generate_fallback_response(user_input, user_language)
        return _format_final_response(fallback_response, user_language)

async def _generate_initial_response(user_input: str, user_language: str) -> str:
    """初期応答生成"""
    
    prompt = f"""You are SafetyBee, a disaster prevention assistant. A user asked something that may not be directly disaster-related.

User request: "{user_input}"
Response language: {user_language}

Generate a helpful initial response that:
1. Acknowledges their request
2. Gently guides them toward disaster preparedness if possible
3. Offers relevant SafetyBee features

Keep it friendly and helpful, around 2-3 sentences."""

    try:
        response = await ainvoke_llm(
            prompt,
            task_type="general_initial_response",
            temperature=0.7,
            max_tokens=200
        )
        return response.strip()
    except Exception as e:
        logger.error(f"Initial response generation failed: {e}")
        return _get_fallback_message(user_language)

async def _self_reflect(user_input: str, response: str, user_language: str) -> Dict[str, Any]:
    """セルフリフレクション分析"""
    
    reflection_prompt = f"""Analyze if this response adequately addresses the user's needs:

User: "{user_input}"
Current Response: "{response}"

Consider:
1. Could this request be related to disaster preparedness?
2. Is there a hidden safety concern?
3. Can we provide more helpful guidance?
4. Should we dig deeper into their actual needs?
5. Are there relevant SafetyBee features we should mention?

Return JSON:
{{
    "needs_deeper_analysis": true/false,
    "feedback": "specific improvement suggestions",
    "potential_safety_angle": "if any safety relevance found",
    "suggested_features": ["list of relevant SafetyBee features"]
}}"""
    
    try:
        result = await ainvoke_llm(
            reflection_prompt,
            task_type="reflection_analysis", 
            temperature=0.3,
            max_tokens=300
        )
        return json.loads(result.strip())
    except Exception as e:
        logger.error(f"Self reflection failed: {e}")
        return {
            "needs_deeper_analysis": False,
            "feedback": "Reflection failed, using initial response",
            "potential_safety_angle": "",
            "suggested_features": []
        }

async def _generate_improved_response(
    user_input: str, 
    initial_response: str, 
    feedback: str, 
    user_language: str
) -> str:
    """改善された応答生成"""
    
    prompt = f"""Based on reflection feedback, generate an improved response.

User request: "{user_input}"
Initial response: "{initial_response}"
Reflection feedback: "{feedback}"
Response language: {user_language}

Generate an improved response that:
1. Addresses the feedback points
2. Makes stronger connections to disaster preparedness
3. Suggests specific SafetyBee features
4. Maintains a helpful and engaging tone

Keep it concise but more comprehensive than the initial response."""

    try:
        response = await ainvoke_llm(
            prompt,
            task_type="improved_response",
            temperature=0.7,
            max_tokens=300
        )
        return response.strip()
    except Exception as e:
        logger.error(f"Improved response generation failed: {e}")
        return initial_response  # フォールバック

async def _generate_fallback_response(user_input: str, user_language: str) -> str:
    """フォールバック応答生成"""
    
    # English-only fallback message (per CLAUDE.md principles)
    return "I apologize, but I cannot answer that question. SafetyBee is a disaster prevention app. Please use our shelter search, disaster information, or preparedness guide features."

def _get_fallback_message(user_language: str) -> str:
    """最基本的フォールバックメッセージ"""
    
    # English-only fallback message (per CLAUDE.md principles)
    return "Thank you for using SafetyBee. Please ask me about disaster preparedness."

def _format_final_response(response_text: str, user_language: str) -> Dict[str, Any]:
    """最終応答のフォーマット"""
    
    # 基本的な機能紹介カード
    suggestion_cards = [
        {
            "card_type": "app_feature_recommendation",
            "card_id": "evacuation_search",
            "title": "避難所検索" if user_language == "ja" else "Shelter Search",
            "action_query": "最寄りの避難所を教えて" if user_language == "ja" else "Find nearest shelter"
        },
        {
            "card_type": "app_feature_recommendation", 
            "card_id": "disaster_info",
            "title": "災害情報" if user_language == "ja" else "Disaster Info",
            "action_query": "現在の災害情報を教えて" if user_language == "ja" else "Show current disaster information"
        },
        {
            "card_type": "app_feature_recommendation",
            "card_id": "preparedness_guide", 
            "title": "防災ガイド" if user_language == "ja" else "Preparedness Guide",
            "action_query": "防災の準備について教えて" if user_language == "ja" else "Tell me about disaster preparedness"
        }
    ]
    
    message = AIMessage(
        content=response_text,
        additional_kwargs={
            "cards": suggestion_cards[:2],  # 最大2枚
            "handler_type": "general_reflection",
            "reflection_used": True
        }
    )
    
    return {
        "messages": [message],
        "final_response_text": response_text,
        "last_response": response_text,
        "cards_to_display_queue": suggestion_cards[:2],
        "current_task_type": ["general_inquiry_with_reflection"],
        "handler_completed": True
    }