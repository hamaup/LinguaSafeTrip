"""
Enhanced Intent Router - 統合意図ルーター
旧initial_analyzer + context_routerを統合した高性能ルーター
"""
import logging
import json
from typing import Dict, Any
from app.schemas.agent_state import AgentState
from .llm_singleton import ainvoke_llm
from app.prompts.intent_prompts import INTENT_ROUTER_UNIFIED_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

async def intent_router(state: AgentState) -> Dict[str, Any]:
    """
    統合意図ルーター（旧initial_analyzer + context_router）
    1回のLLM呼び出しで完全分析を実行
    CLAUDE.md準拠: 入り口翻訳でuser_input→EN
    """
    logger.info("🎯 Node: intent_router")
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "ja")
    location = state.get("user_location")
    emergency_contacts = state.get("emergency_contacts_count", 0)
    
    # 新フロー: 元言語で意図分析を実行
    unified_analysis_prompt = INTENT_ROUTER_UNIFIED_ANALYSIS_PROMPT.format(
        user_input=user_input,  # 元言語のuser_inputを使用
        user_language=user_language,
        location_available=bool(location),
        emergency_contacts=emergency_contacts
    )
    
    try:
        # 1回のLLM呼び出しで全分析完了
        result = await ainvoke_llm(
            unified_analysis_prompt,
            task_type="unified_intent_analysis",
            temperature=0.2,  # 一貫性重視
            max_tokens=1000  # Increased for Gemini 1.5
        )
        
        # Debug logging
        logger.debug(f"Raw LLM result: {result[:200]}...")
        
        # Check for empty result
        if not result or result.strip() == "":
            raise ValueError("Empty response from LLM")
        
        # Handle JSON wrapped in markdown code blocks
        cleaned_result = result.strip()
        if cleaned_result.startswith('```json'):
            cleaned_result = cleaned_result[7:]  # Remove ```json
        if cleaned_result.endswith('```'):
            cleaned_result = cleaned_result[:-3]  # Remove ```
        cleaned_result = cleaned_result.strip()
        
        analysis = json.loads(cleaned_result)
        
        # ログ出力
        logger.info(f"🎯 Analysis result: {analysis['primary_intent']} (confidence: {analysis['confidence']:.2f})")
        logger.info(f"🎯 Routing to: {analysis['routing_decision']}")
        logger.info(f"🎯 Emergency: {analysis['emergency_detected']}, Urgency: {analysis['urgency_level']}")
        
        # 新フロー: 意図分析後に英語翻訳を実行
        english_user_input = user_input
        if user_language != "en":
            try:
                from app.tools.translation_tool import translation_tool
                english_user_input = await translation_tool.translate(
                    text=user_input,
                    target_language="en",
                    source_language=user_language
                )
                logger.info(f"🌐 Post-analysis translation to EN: '{english_user_input[:50]}...'")
            except Exception as e:
                logger.error(f"❌ Post-analysis translation failed: {e}, using original input")
                english_user_input = user_input
        
        return {
            **state,
            "user_input": english_user_input,  # 翻訳済みuser_inputで更新
            "original_user_input": user_input,  # 元の入力を保存
            "primary_intent": analysis["primary_intent"],
            "intent_confidence": analysis["confidence"],
            "urgency_level": analysis["urgency_level"],
            "emergency_detected": analysis["emergency_detected"],
            "routing_decision": analysis["routing_decision"],
            "context_requirements": analysis["context_requirements"],
            "processing_hints": analysis["processing_hints"],
            "fallback_strategy": analysis["fallback_strategy"],
            "analysis_reasoning": analysis["reasoning"]
        }
        
    except json.JSONDecodeError as je:
        logger.error(f"Enhanced intent router JSON parse failed: {je}")
        logger.error(f"Raw result was: {result if 'result' in locals() else 'No result'}")
        
        # フォールバック時も翻訳を実行
        english_user_input = user_input
    except Exception as e:
        logger.error(f"Enhanced intent router failed: {e}")
        
        # フォールバック時も翻訳を実行
        english_user_input = user_input
        if user_language != "en":
            try:
                from app.tools.translation_tool import translation_tool
                english_user_input = await translation_tool.translate(
                    text=user_input,
                    target_language="en",
                    source_language=user_language
                )
                logger.info(f"🌐 Fallback translation to EN: '{english_user_input[:50]}...'")
            except Exception as translation_error:
                logger.error(f"❌ Fallback translation failed: {translation_error}, using original input")
                english_user_input = user_input
        
        # フォールバック: 安全な一般対応
        return {
            **state,
            "user_input": english_user_input,  # 翻訳済みuser_inputで更新
            "original_user_input": user_input,  # 元の入力を保存
            "primary_intent": "general_inquiry",
            "routing_decision": "process_general",
            "intent_confidence": 0.3,
            "urgency_level": "normal",
            "emergency_detected": False,
            "analysis_error": str(e),
            "analysis_reasoning": f"Router failed with error: {str(e)}, defaulting to general handler"
        }

def route_from_intent_router(state: AgentState) -> str:
    """統合ルーターからの直接ルーティング（質問返し判定付き）"""
    
    routing_decision = state.get("routing_decision", "process_general")
    emergency_detected = state.get("emergency_detected", False)
    confidence = state.get("intent_confidence", 0.0)
    # clarification_count removed - no clarification step in expected flow
    
    logger.info(f"🎯 ROUTING: decision={routing_decision}, emergency={emergency_detected}, confidence={confidence:.2f}")
    
    # 緊急時は最優先ルーティング（質問返しスキップ）
    if emergency_detected:
        logger.warning(f"🚨 Emergency detected - priority routing to {routing_decision}")
        return routing_decision
    
    # 質問返しステップを削除（期待フローチャートに合わせて）
    
    # 低信頼度の場合は質問返し
    if confidence < 0.5:
        logger.info(f"❓ Low confidence ({confidence:.2f}) - routing to clarification")
        return "clarify_intent"
    
    # 高信頼度は直接ルーティング
    if confidence >= 0.8:
        # High confidence - routing to handler
        return routing_decision
    
    # 低信頼度ロジックは上で処理済み
    
    # 中信頼度は通常ルーティング
    # Medium confidence - routing to handler
    return routing_decision