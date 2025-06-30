"""
LLM-based emotional state detection service for LinguaSafeTrip
Uses natural language understanding instead of keyword matching
"""
import logging
from typing import Dict, Optional
from app.agents.safety_beacon_agent.core.llm_singleton import get_llm_client
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# Emotion support levels
SUPPORT_LEVELS = {
    'neutral': 'none',
    'low': 'light',
    'medium': 'moderate',
    'high': 'strong',
    'critical': 'crisis'
}

async def detect_emotional_state_llm(
    user_input: str,
    language: str = 'ja',
    context: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Detect emotional state using LLM-based natural language understanding
    
    Returns:
        Dict containing:
        - emotional_state: detected emotion
        - intensity: 0-4
        - confidence: 0.0-1.0
        - support_level: required support level
        - should_prioritize: whether emotional support should be prioritized
    """
    try:
        llm = get_llm_client()
        
        # Construct prompt based on context
        disaster_context = ""
        if context and context.get('is_disaster_mode'):
            disaster_context = "Context: The user is currently experiencing or aware of an ongoing disaster situation."
        
        prompt = f"""
Analyze the emotional state in this message:
"{user_input}"

{disaster_context}

Classify the emotional state and intensity. Consider:
1. The overall emotional tone
2. Specific words or phrases indicating distress
3. The urgency or desperation in the message
4. Cultural context (language: {language})
5. IMPORTANT: Distinguish between information-seeking questions and emotional distress
   - Asking "How to prepare for typhoons?" is neutral (seeking information)
   - Saying "I'm scared of typhoons" is anxious/worried (emotional support needed)

Response format (JSON only):
{{
    "emotional_state": "anxious|scared|worried|stressed|sad|neutral",
    "intensity": 0-4 (0=none, 1=low, 2=medium, 3=high, 4=critical),
    "confidence": 0.0-1.0,
    "support_level": "none|light|moderate|strong|crisis",
    "reasoning": "Brief explanation of detection"
}}

Examples:
- "I'm a bit worried about the earthquake" -> anxious, intensity: 1
- "I'm terrified! Help me!" -> scared, intensity: 4
- "I don't know what to do" -> stressed, intensity: 2
- "Tell me about typhoon preparedness" -> neutral, intensity: 0
- "What should I do during earthquakes?" -> neutral, intensity: 0
- "夏の台風対策について教えて" -> neutral, intensity: 0
"""
        
        # 統一的なLLM呼び出しを使用
        from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
        
        content = await ainvoke_llm(
            prompt=prompt,
            task_type="emotional_detection",
            temperature=0.3,  # 感情検出は低い温度で安定した結果を得る
            max_tokens=200
        )
        
        # Parse JSON response
        import json
        try:
            
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Validate and set defaults
            emotional_state = result.get('emotional_state', 'neutral')
            intensity = max(0, min(4, result.get('intensity', 0)))
            confidence = max(0.0, min(1.0, result.get('confidence', 0.5)))
            support_level = result.get('support_level', SUPPORT_LEVELS.get(
                'high' if intensity >= 3 else 'medium' if intensity >= 2 else 'low' if intensity >= 1 else 'neutral'
            ))
            
            # Determine if emotional support should be prioritized
            should_prioritize = intensity >= 2 or emotional_state in ['scared', 'stressed']
            
            # Emotional detection log removed for cleaner output
            
            return {
                'emotional_state': emotional_state,
                'intensity': intensity,
                'confidence': confidence,
                'support_level': support_level,
                'should_prioritize': should_prioritize,
                'reasoning': result.get('reasoning', '')
            }
            
        except json.JSONDecodeError:
            content = response.content if hasattr(response, 'content') else str(response)
            logger.error(f"Failed to parse LLM response as JSON: {content}")
            return _get_fallback_emotion_result()
            
    except Exception as e:
        logger.error(f"Error in LLM emotional detection: {e}")
        return _get_fallback_emotion_result()

def _get_fallback_emotion_result():
    """Fallback result when LLM detection fails"""
    return {
        'emotional_state': 'neutral',
        'intensity': 0,
        'confidence': 0.0,
        'support_level': 'none',
        'should_prioritize': False,
        'reasoning': 'Fallback - detection failed'
    }

def extract_emotional_context(user_input: str, language: str = 'ja') -> Dict[str, any]:
    """
    Synchronous wrapper for backward compatibility
    Returns a simplified result for non-async contexts
    """
    # For synchronous contexts, return a basic analysis
    # This should ideally be replaced with async calls
    logger.warning("Using synchronous emotional detection - consider using async version")
    
    # For now, return neutral state for synchronous calls
    # The async version should be used for actual detection
    return {
        'emotional_state': 'neutral',
        'intensity': 0,
        'confidence': 0.5,
        'support_level': 'none',
        'should_prioritize': False
    }

def should_prioritize_emotional_support(emotional_context: Dict[str, any]) -> bool:
    """
    Determine if emotional support should be prioritized
    """
    return emotional_context.get('should_prioritize', False)