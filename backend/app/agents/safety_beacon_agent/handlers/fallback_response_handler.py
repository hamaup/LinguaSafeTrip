"""
Fallback Response Handler - Provides safe fallback responses when quality checks fail
"""
import logging
from typing import Dict, Any

from app.tools.translation_tool import TranslationTool
from app.utils.state_utils import get_state_value, ensure_dict_output

logger = logging.getLogger(__name__)

async def fallback_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates safe fallback responses when quality evaluation fails.
    
    Provides appropriate messages based on the rejection stage:
    - grounding: Hallucination detected
    - factual_safety: Safety issues detected
    - language_quality: Language quality issues (after max retries)
    """
    logger.info("🟠 NODE ENTRY: fallback_response_node")
    logger.info(f"🟠 NODE INPUT: quality_retry_count={state.get('quality_retry_count', 0)}")
    logger.info(f"🟠 NODE INPUT: quality_rejection_stage={state.get('quality_rejection_stage', 'unknown')}")
    logger.info("🛡️ Generating fallback response")
    
    try:
        # Get rejection details
        rejection_stage = get_state_value(state, "quality_rejection_stage", "unknown")
        rejection_reason = get_state_value(state, "quality_rejection_reason", "")
        user_language = get_state_value(state, "user_language", "ja")
        
        logger.info(f"🛡️ Fallback for stage: {rejection_stage}, reason: {rejection_reason}")
        
        # Generate appropriate fallback message (internal processing in English)
        if rejection_stage == "grounding":
            # Hallucination detected
            fallback_text = (
                "I apologize, but I cannot provide accurate information at this time. "
                "Please check official disaster information sources for the most reliable updates."
            )
        elif rejection_stage == "factual_safety":
            # Safety issues detected
            fallback_text = (
                "I apologize, but I cannot provide this information safely. "
                "Please consult official disaster management authorities for guidance on this matter."
            )
        elif rejection_stage == "language_quality":
            # Language quality issues after max retries
            fallback_text = (
                "I apologize for the confusion. "
                "Please try rephrasing your question, and I'll do my best to help you."
            )
        else:
            # General fallback
            fallback_text = (
                "I apologize, but I couldn't generate an appropriate response. "
                "Please try again or check official disaster information sources."
            )
        
        # Translate to user language if needed
        if user_language != "en":
            try:
                translation_tool = TranslationTool()
                translated_result = await translation_tool.ainvoke({
                    "text": fallback_text,
                    "target_language": user_language
                })
                fallback_text = translated_result.get("translated_text", fallback_text)
            except Exception as translation_error:
                logger.error(f"Translation failed: {translation_error}, using English fallback")
                # Keep English version if translation fails
        
        # Update state with fallback response
        result = {
            "final_response_text": fallback_text,
            "is_fallback": True,
            "fallback_reason": rejection_stage,
            "routing_decision": {"next": "END"}
        }
        
        logger.info("🟠 NODE EXIT: fallback_response_node")
        logger.info(f"🟠 NODE OUTPUT: final_response_text='{fallback_text[:50]}...'")
        logger.info(f"🟠 NODE OUTPUT: routing_decision={result['routing_decision']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in fallback response node: {e}", exc_info=True)
        
        # Ultimate fallback
        error_result = {
            "final_response_text": "I apologize, but an error occurred. Please try again later.",
            "is_fallback": True,
            "fallback_reason": "error",
            "routing_decision": {"next": "END"}
        }
        
        logger.info("🟠 NODE EXIT: fallback_response_node (ERROR)")
        logger.info(f"🟠 NODE OUTPUT: routing_decision={error_result['routing_decision']}")
        
        return error_result