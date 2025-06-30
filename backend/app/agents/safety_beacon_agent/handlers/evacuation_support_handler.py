"""避難支援要求を処理するLangGraphノードハンドラー"""
import logging
import json
import asyncio  # 並列処理のために追加
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.schemas.agent import AgentState
from app.agents.safety_beacon_agent.core.llm_singleton import get_shared_llm
from app.tools.location_tools import NearbyShelterInfoTool
from app.tools.guide_tools import get_contextual_advice
from app.prompts.disaster_prompts import get_evacuation_advice_prompt
from app.schemas.shelter import ShelterInfo
from app.schemas.disaster_action_card_schemas import ShelterCard, ChecklistCard
from .complete_response_handlers import CompleteResponseGenerator

logger = logging.getLogger(__name__)


class UserSituationAnalysis(BaseModel):
    """ユーザー状況分析結果"""
    is_injured: Optional[bool] = None
    has_companions: Optional[bool] = None
    companion_details: Optional[List[str]] = None
    special_needs: Optional[List[str]] = None
    safety_level: Optional[str] = None
    requires_immediate_evacuation: bool = False

class EvacuationAdviceOutput(BaseModel):
    """避難アドバイス出力"""
    items: List[Dict[str, str]]
    advice: List[str]
    disaster_type: str
    phase: str

class EvacuationSupportResponse(BaseModel):
    """避難支援応答"""
    main_message: str
    shelter_summary: Optional[str] = None
    advice_summary: Optional[str] = None
    empathetic_statement: Optional[str] = None

def _get_state_value(state, key, default=None):
    """統一された状態値取得メソッド"""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)

async def _analyze_evacuation_context_with_llm(user_input: str, active_warnings: List[Dict], recent_disasters: List) -> Dict[str, Any]:
    """LLM-based natural language understanding for evacuation context analysis"""
    from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
    
    # Build context for LLM analysis
    warning_context = "\n".join([f"- {w.get('warning_type', 'unknown')}: {w.get('description', '')}" for w in active_warnings]) if active_warnings else "No active warnings"
    disaster_context = "\n".join([f"- Earthquake M{d.magnitude}" for d in recent_disasters]) if recent_disasters else "No recent major disasters"
    
    prompt = f"""You are an expert disaster evacuation analyst. Analyze the evacuation context using natural language understanding.

User Input: "{user_input}"

Active Warnings:
{warning_context}

Recent Disasters:
{disaster_context}

Your task:
1. Understand the evacuation context naturally from the user's words and situation
2. Determine the most relevant disaster type for evacuation planning
3. Assess the urgency and safety requirements

Important guidelines:
- Focus on the user's PRIMARY need - are they asking WHERE to evacuate or WHAT disaster is happening?
- If the user asks "where" to go, "nearest" shelter, or mentions "evacuation center", focus on shelter location needs
- Consider both explicit requests ("Where is the nearest evacuation center?") and implicit needs
- Use context clues to understand urgency without relying on specific keywords

Respond with JSON:
{{
    "disaster_type": "flood|tsunami|earthquake|fire|general",
    "urgency_level": "immediate|high|moderate|low",
    "safety_priority": "vertical_evacuation|horizontal_evacuation|shelter_in_place|general_safety",
    "reasoning": "Brief explanation of your analysis"
}}

Focus on natural language understanding rather than keyword matching."""
    
    try:
        response = await ainvoke_llm(prompt, task_type="evacuation_context_analysis", temperature=0.3)
        # Parse JSON response
        import json
        result = json.loads(response.strip())
        return result
    except Exception as e:
        logger.warning(f"LLM evacuation context analysis failed: {e}")
        return {
            "disaster_type": "general",
            "urgency_level": "moderate", 
            "safety_priority": "general_safety",
            "reasoning": "Fallback due to analysis error"
        }

async def _evaluate_shelter_safety_with_llm(shelters: List[Dict], disaster_context: Dict) -> List[Dict]:
    """LLM-based shelter safety evaluation using natural language understanding"""
    from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
    
    if not shelters:
        return []
    
    # Prepare shelter data for LLM analysis
    shelter_data = []
    for shelter in shelters:
        hazard_safety = shelter.get('hazard_safety', {})
        shelter_info = {
            'name': shelter.get('name', 'Unknown'),
            'elevation': hazard_safety.get('elevation', shelter.get('elevation')),
            'safety_score': hazard_safety.get('safety_score', 0.8),
            'capacity': shelter.get('capacity', 'Unknown'),
            'distance_km': shelter.get('distance_km', 'Unknown')
        }
        shelter_data.append(shelter_info)
    
    # Get current season for seasonal considerations
    from app.utils.season_utils import get_current_season
    current_season = get_current_season()
    
    prompt = f"""You are an expert evacuation safety analyst. Evaluate which shelters are safe for the given disaster situation.

Disaster Context:
- Type: {disaster_context.get('disaster_type', 'general')}
- User Situation: "{disaster_context.get('user_input', '')}"
- Location Warnings: {len(disaster_context.get('active_warnings', []))} active warnings
- Current Season: {current_season}

Shelters to Evaluate:
{json.dumps(shelter_data, indent=2, ensure_ascii=False)}

Evaluation Criteria (use your natural understanding):
- For floods/tsunamis: Higher elevation is critical for safety
- For earthquakes: Structural safety and evacuation routes matter
- For fires: Quick access and distance from danger zones
- Consider capacity, accessibility, and overall safety scores

IMPORTANT Seasonal Considerations:
- Winter (冬): Avoid outdoor shelters due to cold exposure risk
- Summer (夏): Consider heat/cooling needs, especially for outdoor areas
- Rainy season (6-7月): Outdoor shelters may be unsuitable due to flooding/rain
- Always prioritize indoor facilities with proper climate control during extreme weather

For outdoor shelters (floors = 0), include seasonal warnings in reasoning.

Respond with JSON array of safe shelter names:
{{
    "safe_shelters": ["shelter_name_1", "shelter_name_2", ...],
    "reasoning": "Brief explanation of safety evaluation including seasonal factors"
}}

Use intelligent analysis, not rigid rules."""
    
    try:
        response = await ainvoke_llm(prompt, task_type="shelter_safety_evaluation", temperature=0.3)
        
        if not response or not response.strip():
            logger.warning("Empty response from LLM for shelter safety evaluation")
            return [s for s in shelters if s.get('hazard_safety', {}).get('safety_score', 0.8) > 0.5]
        
        logger.debug(f"LLM shelter evaluation response: {response[:200]}...")
        result = json.loads(response.strip())
        safe_shelter_names = result.get('safe_shelters', [])
        
        # Filter original shelters based on LLM evaluation
        safe_shelters = [s for s in shelters if s.get('name') in safe_shelter_names]
        
        logger.info(f"LLM shelter evaluation: {len(safe_shelters)}/{len(shelters)} shelters deemed safe")
        return safe_shelters
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed for shelter evaluation. Response: {response[:200] if 'response' in locals() else 'No response'}")
        return [s for s in shelters if s.get('hazard_safety', {}).get('safety_score', 0.8) > 0.5]
    except Exception as e:
        logger.warning(f"LLM shelter safety evaluation failed: {e}")
        return [s for s in shelters if s.get('hazard_safety', {}).get('safety_score', 0.8) > 0.5]

async def _analyze_user_situation(state: AgentState) -> UserSituationAnalysis:
    """Analyze user situation using LLM-based natural language understanding"""
    from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
    
    user_input = _get_state_value(state, 'user_input', '')
    
    # LLM-based situation analysis (following CLAUDE.md principles)
    analysis_prompt = f"""
    Analyze the user's situation from their input using natural language understanding.
    
    User input: {user_input}
    
    Please extract the following information:
    1. Is the user injured? (true/false/unknown)
    2. Does the user have companions? (true/false/unknown)
    3. Companion details (if any): children, elderly, etc.
    4. Special needs: mobility assistance, medication, etc.
    
    Return JSON format:
    {{
        "is_injured": true/false/null,
        "has_companions": true/false/null,
        "companion_details": ["list of companions"],
        "special_needs": ["list of special needs"]
    }}
    """
    
    try:
        # 統一的なLLM呼び出しを使用
        from ..core.llm_singleton import ainvoke_llm
        
        response_content = await ainvoke_llm(
            prompt=analysis_prompt,
            task_type="analysis",
            temperature=0.5,
            max_tokens=200
        )
        
        import json
        
        # Clean up the response to ensure valid JSON
        response_content = response_content.strip()
        
        # Try to find JSON content in the response
        if '```json' in response_content:
            # Extract JSON from markdown code block
            start = response_content.find('```json') + 7
            end = response_content.find('```', start)
            if end != -1:
                response_content = response_content[start:end].strip()
        elif '```' in response_content:
            # Extract JSON from generic code block
            start = response_content.find('```') + 3
            end = response_content.find('```', start)
            if end != -1:
                response_content = response_content[start:end].strip()
        
        # Try to parse JSON with better error handling
        try:
            analysis_result = json.loads(response_content)
        except json.JSONDecodeError as json_error:
            logger.warning(f"JSON parsing failed: {json_error}. Response: {response_content[:200]}...")
            # Try to fix common JSON issues
            cleaned_response = response_content.replace('\n', '').replace('\r', '').replace('\t', ' ')
            # Fix Japanese punctuation that might interfere with JSON
            cleaned_response = cleaned_response.replace('、', ',').replace('。', '.')
            # Remove any trailing commas
            cleaned_response = cleaned_response.replace(',}', '}').replace(',]', ']')
            # Fix unterminated strings by ensuring quotes are properly closed
            if cleaned_response.count('"') % 2 != 0:
                cleaned_response += '"'
            try:
                analysis_result = json.loads(cleaned_response)
            except json.JSONDecodeError:
                logger.warning("Failed to parse cleaned JSON, using fallback")
                analysis_result = {}
        
        is_injured = analysis_result.get("is_injured")
        has_companions = analysis_result.get("has_companions")
        companion_details = analysis_result.get("companion_details", [])
        special_needs = analysis_result.get("special_needs", [])
        
    except Exception as e:
        logger.warning(f"LLM analysis failed, using basic fallback: {e}")
        # Simple fallback without keyword matching
        is_injured = None
        has_companions = None
        companion_details = []
        special_needs = []
    
    # Determine evacuation urgency based on disaster type, external alerts, and keywords
    requires_immediate_evacuation = False
    
    # Check external alerts first
    external_alerts = _get_state_value(state, 'external_alerts', [])
    if external_alerts and isinstance(external_alerts, list):
        for alert in external_alerts:
            if isinstance(alert, dict):
                alert_type = alert.get("alert_type", "").lower()
                severity = alert.get("severity", "").lower()
                if alert_type in ["tsunami", "nuclear_emergency", "fire"] or severity in ["major", "critical"]:
                    requires_immediate_evacuation = True
                    break
    
    # Check current disaster info and user input urgency using natural language understanding
    current_disaster_info = _get_state_value(state, 'current_disaster_info')
    if current_disaster_info:
        disaster_type = current_disaster_info.get("disaster_type", "") if isinstance(current_disaster_info, dict) else getattr(current_disaster_info, 'disaster_type', '')
        
        # High-risk disaster types that typically require immediate evacuation
        if disaster_type in ["tsunami", "fire", "flood", "nuclear_emergency"]:
            requires_immediate_evacuation = True
        
        # Analyze user input for urgency using natural language understanding
        if user_input and not requires_immediate_evacuation:
            try:
                urgency_prompt = f"""
                Analyze if this user input indicates an urgent or emergency situation requiring immediate evacuation:
                
                User input: {user_input}
                
                Return only "true" if urgent/emergency, "false" if not urgent.
                """
                # 統一的なLLM呼び出しを使用
                from ..core.llm_singleton import ainvoke_llm
                
                response_text = await ainvoke_llm(
                    prompt=urgency_prompt,
                    task_type="analysis",
                    temperature=0.3,
                    max_tokens=50
                )
                if "true" in response_text.lower():
                    requires_immediate_evacuation = True
            except Exception as e:
                # No keyword fallback - maintain conservative approach
                pass
    
    return UserSituationAnalysis(
        is_injured=is_injured,
        has_companions=has_companions,
        companion_details=companion_details if companion_details else None,
        special_needs=special_needs if special_needs else None,
        safety_level="unknown",
        requires_immediate_evacuation=requires_immediate_evacuation
    )

async def _get_nearby_shelters(state: AgentState, situation: UserSituationAnalysis) -> List[ShelterInfo]:
    """近隣の避難所情報を取得"""
    # Getting nearby shelters based on user situation
    user_location = _get_state_value(state, 'user_location')
    # Processing user location data
    if not user_location:
        logger.warning("No user location found")
        return []

    from app.tools.location_tools import NearbyShelterInfoTool

    # user_locationが辞書形式の場合の処理
    if isinstance(user_location, dict):
        latitude = user_location.get('latitude')
        longitude = user_location.get('longitude')
    else:
        latitude = getattr(user_location, 'latitude', None)
        longitude = getattr(user_location, 'longitude', None)
    
    if not latitude or not longitude:
        logger.warning(f"Invalid coordinates: lat={latitude}, lon={longitude}")
        return []

    # Valid coordinates found for shelter search
    
    # Check for disaster type from multiple sources
    disaster_type = None
    current_disaster_info = _get_state_value(state, 'current_disaster_info')
    if current_disaster_info:
        disaster_type = current_disaster_info.get("disaster_type") if isinstance(current_disaster_info, dict) else getattr(current_disaster_info, 'disaster_type', None)
    
    # Also check external alerts for disaster type
    external_alerts = _get_state_value(state, 'external_alerts', [])
    if external_alerts and isinstance(external_alerts, list) and not disaster_type:
        for alert in external_alerts:
            if isinstance(alert, dict) and alert.get("alert_type"):
                disaster_type = alert.get("alert_type")
                break
    
    # Check for active disasters from location-based info
    if not disaster_type:
        try:
            from app.tools.disaster_info_tools import disaster_info_tool
            # Get recent disaster info for the location
            location_dict = {"latitude": latitude, "longitude": longitude}
            recent_earthquakes = await disaster_info_tool.get_latest_earthquake_info(location_dict)
            recent_tsunamis = []  # Tsunami info is included in general disaster info
            
            # Check for active tsunami
            if recent_tsunamis and len(recent_tsunamis) > 0:
                # Active tsunami detected from recent alerts
                disaster_type = "tsunami"
            # Check for significant earthquake that might cause secondary disasters
            elif recent_earthquakes and len(recent_earthquakes) > 0:
                for eq in recent_earthquakes:
                    if eq.magnitude and eq.magnitude >= 7.0:  # Only very large earthquakes trigger tsunami risk
                        # Major earthquake detected, considering tsunami risk
                        disaster_type = "tsunami"  # Precautionary for coastal areas
                        break
                    elif eq.magnitude and eq.magnitude >= 6.0:
                        # Significant earthquake detected, not automatically considering tsunami risk
                        # Don't set disaster_type for general shelter search
                        pass
            
            # Check active warnings and risk assessment
            risk_assessment = await disaster_info_tool.get_dynamic_risk_assessment(location_dict)
            # Risk assessment completed
            
            # Get warnings for LLM analysis
            active_warnings = risk_assessment.get('active_warnings', [])
            # Use LLM-based natural language understanding for disaster context
            user_input = _get_state_value(state, 'user_input', '')
            disaster_analysis = await _analyze_evacuation_context_with_llm(
                user_input=user_input,
                active_warnings=active_warnings,
                recent_disasters=[eq for eq in recent_earthquakes if eq.magnitude and eq.magnitude >= 6.0]
            )
            disaster_type = disaster_analysis.get('disaster_type')
            # For general shelter searches, don't set disaster_type to allow all shelters
        except Exception as e:
            logger.warning(f"Failed to check active disasters: {e}")
    
    # Progressive search - start small and expand if needed
    # Use consistent search radius regardless of risk level
    # Disaster-specific filtering handles safety, not distance
    search_radii = [3.0, 5.0, 10.0]  # Standard progressive search
    # Using standard progressive search radius
    
    shelter_tool = NearbyShelterInfoTool()
    all_results = []
    
    # Progressive search - expand radius if no safe shelters found
    for radius in search_radii:
        # Searching for shelters
        
        tool_input_data = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius,
            "current_disaster_type": disaster_type
        }
        
        result = await shelter_tool.ainvoke(tool_input_data)
        result_list = result if isinstance(result, list) else []
        
        # Filter for truly safe shelters based on disaster type
        safe_shelters = []
        # Get risk assessment for warning context in shelter evaluation
        local_risk_assessment = {}
        try:
            from app.tools.disaster_info_tools import UnifiedDisasterInfoTool
            disaster_tool = UnifiedDisasterInfoTool()
            location_dict = {'latitude': latitude, 'longitude': longitude}
            local_risk_assessment = await disaster_tool.get_dynamic_risk_assessment(location_dict)
        except Exception as e:
            logger.warning(f"Could not get local risk assessment for shelter evaluation: {e}")
        
        # Use LLM to evaluate shelter safety based on disaster context
        safe_shelters = await _evaluate_shelter_safety_with_llm(
            shelters=result_list,
            disaster_context={
                'disaster_type': disaster_type,
                'user_input': _get_state_value(state, 'user_input', ''),
                'location': {'latitude': latitude, 'longitude': longitude},
                'active_warnings': local_risk_assessment.get('active_warnings', [])
            }
        )
        
        # Found safe shelters in search radius
        
        # 海外など対象地域外の場合の処理
        if len(result_list) == 0 and radius == search_radii[0]:  # 最初の検索で0件の場合
            logger.warning(f"No shelter data available for location: lat={latitude}, lon={longitude}")
            # 海外や対象地域外の場合は適切なメッセージを返す
            from app.agents.safety_beacon_agent.handlers.complete_response_handlers import generate_complete_response
            
            complete_text = await generate_complete_response(
                intent_type="evacuation_support",
                user_input=_get_state_value(state, 'user_input', ''),
                location={'latitude': latitude, 'longitude': longitude},
                custom_message="申し訳ございませんが、現在の位置では避難所情報を取得できません。日本国内のサービス対象地域でご利用ください。"
            )
            
            response_data = {
                'message': complete_text,
                'cards': [],
                'emergency_level': _get_state_value(state, 'emergency_level', 0),
                'requires_followup': False
            }
            
            state['agent_response'] = response_data
            return state
        
        # If we found enough safe shelters, stop searching
        if len(safe_shelters) >= 3:
            return safe_shelters[:5]  # Return top 5
        
        # Otherwise, keep the results and continue searching wider
        all_results.extend(safe_shelters)
    
    # If still no safe shelters after maximum radius, return what we found
    # Total safe shelters found after search
    if not all_results and disaster_type in ["flood", "tsunami"]:
        logger.warning(f"No safe shelters found even at {search_radii[-1]}km - recommending evacuation to higher ground")
    
    return all_results[:5] if all_results else []


async def _get_evacuation_advice(
    state: AgentState,
    situation: UserSituationAnalysis
) -> EvacuationAdviceOutput:
    """避難アドバイスを取得"""
    # Use English user input for internal processing
    user_input_for_advice = _get_state_value(state, 'user_input', '')
    disaster_type_from_state = "general" # デフォルト
    current_disaster_info = _get_state_value(state, 'current_disaster_info')
    if current_disaster_info:
        # current_disaster_info が辞書であることを想定して .get() を使用
        if isinstance(current_disaster_info, dict):
            disaster_type_from_state = current_disaster_info.get('disaster_type', "general")
        else:
            disaster_type_from_state = getattr(current_disaster_info, 'disaster_type', "general")
        user_input_for_advice += f" (現在の災害: {disaster_type_from_state})"

    # get_contextual_advice は辞書を返すので、EvacuationAdviceOutputでラップする
    # get_contextual_advice が非同期の場合は await を使用
    language = _get_state_value(state, 'user_language', 'ja')
    try:
        # Check if get_contextual_advice is async
        import inspect
        if inspect.iscoroutinefunction(get_contextual_advice):
            raw_advice_data = await get_contextual_advice(
                user_input=user_input_for_advice,
                language=language
            )
        else:
            raw_advice_data = get_contextual_advice(
                user_input=user_input_for_advice,
                language=language
            )
    except Exception as e:
        logger.warning(f"Failed to get contextual advice: {e}")
        raw_advice_data = {
            "items": [],
            "advice": ["Follow official evacuation guidance for your area"],
            "disaster_type": "general",
            "phase": "evacuation"
        }

    # 入力データを辞書型に統一
    advice_dict: Dict[str, Any]
    if isinstance(raw_advice_data, dict):
        advice_dict = raw_advice_data
    else:
        # 辞書以外の型が返ってきた場合は変換を試みる
        try:
            advice_dict = raw_advice_data.dict() if hasattr(raw_advice_data, 'dict') else {}
        except Exception as e:
            logger.error(f"Failed to convert advice data: {str(e)}")
            advice_dict = {
                "items": [],
                "advice": ["Failed to retrieve evacuation advice. Please check official emergency sources."],
                "disaster_type": "unknown",
                "phase": "general"
            }

    # 必須フィールドのデフォルト値を設定
    advice_dict.setdefault("items", [])
    advice_dict.setdefault("disaster_type", "unknown")
    advice_dict.setdefault("phase", "general")
    
    # advice フィールドの型変換：List[Dict] -> List[str]
    raw_advice = advice_dict.get("advice", [])
    if raw_advice and isinstance(raw_advice, list) and len(raw_advice) > 0:
        if isinstance(raw_advice[0], dict):
            # 辞書のリストから文字列のリストに変換
            advice_strings = []
            for item in raw_advice:
                if isinstance(item, dict):
                    # 辞書の内容を文字列として結合
                    title = item.get("title", "")
                    content = item.get("content", "")
                    if title and content:
                        advice_strings.append(f"{title}: {content}")
                    elif content:
                        advice_strings.append(content)
                    elif title:
                        advice_strings.append(title)
                else:
                    advice_strings.append(str(item))
            advice_dict["advice"] = advice_strings if advice_strings else ["Unable to generate evacuation advice. Please follow official guidance."]
        elif isinstance(raw_advice[0], str):
            # 既に文字列のリストなのでそのまま使用
            advice_dict["advice"] = raw_advice
        else:
            # その他の型の場合は文字列に変換
            advice_dict["advice"] = [str(item) for item in raw_advice]
    else:
        advice_dict["advice"] = ["Unable to generate evacuation advice. Please follow official guidance."]

    # Pydanticモデルに変換して返す
    return EvacuationAdviceOutput(**advice_dict)

async def _generate_response( # Made async for LLM-based generation
    shelters: List[Dict[str, Any]], # ShelterInfo.model_dump() list
    advice: Dict[str, Any], # EvacuationAdviceOutput.model_dump()
    user_input: str = "",
    emotional_context: Dict[str, Any] = None,
    language: str = "ja"
) -> str:
    """
    Generate contextual, empathetic evacuation response using LLM.
    Returns compassionate message considering user's emotional state and situation.
    Internal processing in English, final output will be translated to user language.
    """
    from app.agents.safety_beacon_agent.core.llm_singleton import get_llm_client
    from ..core.llm_singleton import ainvoke_llm
    
    try:
        # Prepare context for LLM
        shelter_summary = ""
        if shelters:
            shelter_count = len(shelters)
            nearest_shelter = shelters[0]
            shelter_name = nearest_shelter.get("name", "Nearby shelter")
            distance = nearest_shelter.get("distance_km", 0)
            shelter_summary = f"Found {shelter_count} evacuation shelters. Nearest: {shelter_name} ({distance:.1f}km away)."
        else:
            shelter_summary = "No specific shelter data available for this location."
        
        # Emotional context
        emotional_state = emotional_context.get('emotional_state', 'neutral') if emotional_context else 'neutral'
        support_level = emotional_context.get('support_level', 'light') if emotional_context else 'light'
        
        # Generate empathetic response using LLM
        prompt = f"""You are SafetyBeacon AI, a compassionate disaster support assistant.

User request: "{user_input}"
Emotional state: {emotional_state}
Support needed: {support_level}

Shelter information: {shelter_summary}

Generate a brief, empathetic response (2-3 sentences max) that:
1. Acknowledges the user's concern with appropriate empathy
2. Provides clear, actionable information about shelters
3. Reassures the user while being honest about the situation
4. Directs them to check detailed cards below

Keep it concise but caring. Respond in English (translation will be handled separately).
Example good response: "I understand you're looking for nearby evacuation shelters. I found 3 safe locations near you, with the closest being Central Sports Center just 1.4km away. Please check the detailed cards below for addresses and accessibility information to help you choose the best option."
"""

        response = await ainvoke_llm(
            prompt=prompt,
            task_type="evacuation_support",
            temperature=0.7,
            max_tokens=150
        )
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"LLM-based response generation failed: {e}")
        # Fallback to template-based response
        if shelters:
            shelter_count = len(shelters)
            nearest_shelter = shelters[0]
            shelter_name = nearest_shelter.get("name", "Nearby shelter")
            distance = nearest_shelter.get("distance_km", 0)
            return f"Found {shelter_count} evacuation shelters nearby. Nearest: {shelter_name} ({distance:.1f}km). Check cards below for details."
        else:
            return "Location data needed. Please check cards below for general evacuation advice."

def _generate_suggestion_cards(
    shelters: List[Dict[str, Any]], # ShelterInfo.model_dump() のリストを期待
    advice: Dict[str, Any] # EvacuationAdviceOutput.model_dump() を期待
) -> List[Dict[str, Any]]:
    """
    提案カードを生成する
      ・避難所カード（shelters があれば最大上位2件）
      ・持ち物チェックリストカード（advice['items'] から1枚）
    を返す。
    """
    logger.info(f"=== GENERATING SUGGESTION CARDS ===")
    logger.info(f"Number of shelters to process: {len(shelters)}")
    
    # Load shelter metadata for enhanced information
    import json
    from pathlib import Path
    
    metadata_path = Path(__file__).parent.parent.parent.parent / "resources" / "shelter_metadata.json"
    shelter_metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            shelter_metadata = data.get("shelters", {})
    
    cards: List[Dict[str, Any]] = []

    # ■ 避難所カード（メタデータで拡張）
    for i, shelter_data in enumerate(shelters[:5]):  # Display up to 5 shelters
        logger.info(f"--- Processing shelter {i+1} ---")
        logger.info(f"Shelter data keys: {list(shelter_data.keys())}")
        
        # ShelterCard Pydanticモデルを使って構築し、dictに変換する方が型安全
        # ここではユーザー提案の簡易ロジックに合わせる
        # 基本スキーマに準拠したカード作成（位置情報を含む）
        shelter_name = shelter_data.get("name", "Unknown Shelter")
        logger.info(f"Shelter name: {shelter_name}")
        
        card = {
            "card_type": "evacuation_shelter",  # Flutterのフィルタリングに合わせて変更
            "card_id": f"shelter_{shelter_data.get('id', 'unknown')}",
            "title": shelter_name,
            # Add action_data to match suggestion card behavior
            "action_data": {
                "shelter_search": True,
                "location_based": True
            }
        }
        
        # 位置情報をGoogle Maps表示用に追加（必須フィールド）
        latitude = shelter_data.get("latitude")
        longitude = shelter_data.get("longitude")
        logger.info(f"Latitude: {latitude}, Longitude: {longitude}")
        
        if latitude is not None and longitude is not None:
            card["location"] = {
                "latitude": float(latitude),
                "longitude": float(longitude)
            }
            # Generate Google Maps URL for direct map access
            card["map_url"] = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            logger.info(f"Generated map_url: {card['map_url']}")
            # Location added to card
        else:
            logger.warning(f"Missing location data for shelter: {shelter_name}")
            # Still create card but mark as location unavailable
            card["location_unavailable"] = True
            
        # 基本情報を追加
        if shelter_data.get("distance_km") is not None:
            card["distance_km"] = shelter_data.get("distance_km")
        if shelter_data.get("shelter_type"):
            card["shelter_type"] = shelter_data.get("shelter_type")
        if shelter_data.get("status"):
            card["status"] = shelter_data.get("status")
            
        # メタデータから詳細情報を追加
        if shelter_name in shelter_metadata:
            meta = shelter_metadata[shelter_name]
            card["details"] = {
                "floors": meta.get("floors", 0),
                "capacity": meta.get("capacity", 0),
                "is_tsunami_shelter": meta.get("is_tsunami_shelter", False),
                "facilities": meta.get("facilities", []),
                "accessibility": meta.get("accessibility", []),
                "pet_allowed": meta.get("pet_allowed", False),
                "phone": meta.get("phone", ""),
                "notes": meta.get("notes", "")
            }
        
        logger.info(f"Final card structure for {shelter_name}:")
        logger.info(f"  - card_type: {card.get('card_type')}")
        logger.info(f"  - card_id: {card.get('card_id')}")
        logger.info(f"  - title: {card.get('title')}")
        logger.info(f"  - location: {card.get('location')}")
        logger.info(f"  - map_url: {card.get('map_url', 'NOT GENERATED')}")
        logger.info(f"  - distance_km: {card.get('distance_km')}")
        logger.info(f"  - shelter_type: {card.get('shelter_type')}")
        logger.info(f"  - status: {card.get('status')}")
        logger.info(f"  - has_details: {'details' in card}")
        
        cards.append(card)

    # ■ 持ち物チェックリストカード
    advice_items = advice.get("items", [])
    if advice_items and isinstance(advice_items, list):
        checklist_items_for_card = [
            {"name": it.get("name", "Unknown Item"), "description": it.get("description", "")}
            for it in advice_items
        ]
        if checklist_items_for_card: # アイテムが実際に存在する場合のみカード生成
            # 基本スキーマに準拠したチェックリストカード作成
            cards.append({
                "card_type": "preparedness_tip",  # 統一されたcard_type
                "card_id": "evacuation_checklist",
                "title": "Evacuation Checklist"
            })
    # Final validation and summary
    logger.info(f"=== CARDS GENERATION SUMMARY ===")
    logger.info(f"Total cards generated: {len(cards)}")
    
    for i, card in enumerate(cards):
        card_type = card.get('card_type', 'unknown')
        title = card.get('title', 'no title')
        location = card.get('location', {})
        map_url = card.get('map_url')
        
        logger.info(f"Card {i+1}: {card_type} - {title}")
        
        if card_type == "evacuation_info":
            if location:
                logger.info(f"  ✓ Has location: lat={location.get('latitude')}, lon={location.get('longitude')}")
            else:
                logger.error(f"  ✗ MISSING LOCATION DATA for Google Maps!")
            
            if map_url:
                logger.info(f"  ✓ Has map_url: {map_url[:50]}...")
            else:
                logger.error(f"  ✗ MISSING MAP_URL!")
        
        # Log all fields in the card for debugging
        logger.debug(f"Full card data: {json.dumps(card, ensure_ascii=False, indent=2)}")
    
    logger.info(f"=== END CARDS GENERATION ===")
    return cards


# Removed _is_advice_only_request function - always provide shelters when location is available

def _generate_error_response(state: AgentState, error: Exception) -> str:
    """Generate error response without LLM for efficiency"""
    # Simple error response in English (translation handled by response_generator)
    return f"Error occurred while retrieving evacuation support information: {str(error)}. Please move to a safe location and check official information sources."

async def handle_evacuation_support_request(state: AgentState) -> Dict[str, Any]:
    """避難支援要求を処理するLangGraphノード - 統合バッチ処理版

    Args:
        state: 現在のAgentState

    Returns:
        更新されたAgentStateの辞書表現 (messagesフィールドを含む)
    """
    # NODE ENTRY: evacuation_unified
    # Processing user input for evacuation support
    
    # enhance_qualityからのフィードバック取得・活用
    improvement_feedback = _get_state_value(state, 'improvement_feedback', '')
    if improvement_feedback:
        # Processing with improvement feedback
        pass
    else:
        # Initial processing (no improvement feedback)
        pass
    
    # バッチ処理版の実行
    return await _evacuation_support_node_batch(state)
    
async def _evacuation_support_node_batch(state: AgentState) -> Dict[str, Any]:
    """避難支援ハンドラー - バッチ処理版"""
    try:
        user_input = _get_state_value(state, 'user_input', '')
        user_language = _get_state_value(state, 'user_language', 'ja')
        primary_intent = _get_state_value(state, 'primary_intent', 'evacuation_support')
        is_disaster_mode = _get_state_value(state, 'is_disaster_mode', False)
        user_location = _get_state_value(state, 'user_location')
        
        # Using batch processing for evacuation support handler
        
        # 位置情報がない場合の処理
        if not user_location:
            logger.warning("No location data available - prompting to enable GPS")
            
            # GPSオン促進メッセージを生成
            gps_prompt_message = "To find the nearest evacuation shelters, please enable GPS location services on your device. This will help us provide accurate shelter information for your area."
            
            # 位置情報権限カードを生成
            location_permission_card = {
                "card_type": "action",
                "title": "Enable Location Services",
                "content": "We need your location to show nearby evacuation shelters",
                "action_query": "location_permission",
                "action_data": {
                    "action_type": "request_permission",
                    "permission_type": "location"
                }
            }
            
            # feedback活用チェック
            improvement_feedback = _get_state_value(state, 'improvement_feedback', '')
            
            # GPS有効化を促す応答を生成
            response_data = await CompleteResponseGenerator.generate_complete_response(
                user_input=user_input,
                intent=primary_intent,
                user_language=user_language,
                context_data={
                    "no_location": True,
                    "gps_required": True,
                    "custom_message": gps_prompt_message
                },
                handler_type="evacuation",
                improvement_feedback=improvement_feedback,
                state=state
            )
            
            # 位置情報がない場合は必ずGPS有効化カードを追加
            response_data["suggestion_cards"] = [
                location_permission_card,  # 上で定義した位置情報権限カード
                {
                    "card_type": "action",
                    "title": "GPSをオンにする" if user_language == "ja" else "Turn on GPS",
                    "content": "正確な避難所情報のため" if user_language == "ja" else "For accurate shelter info",
                    "action_query": "GPSの設定方法" if user_language == "ja" else "How to enable GPS",
                    "action_data": {
                        "action_type": "open_settings",
                        "settings_type": "location"
                    }
                }
            ]
            
            from langchain_core.messages import AIMessage
            message = AIMessage(
                content=response_data["main_response"],
                additional_kwargs={
                    "cards": response_data["suggestion_cards"],
                    "follow_up_questions": response_data["follow_up_questions"],
                    "priority": response_data["priority_level"],
                    "handler_type": "evacuation",
                    "no_location_warning": "Location data required for shelter recommendations"
                }
            )
            
            return {
                "messages": [message],
                "final_response_text": response_data["main_response"],
                "last_response": response_data["main_response"],
                "current_task_type": ["task_complete_evacuation_support"],
                "secondary_intents": [],
                "intermediate_results": {"batch_processing_used": True, "no_location": True},
                "cards_to_display_queue": response_data["suggestion_cards"],
                "quality_self_check": response_data.get("quality_self_check", {}),
                "handler_completed": True
            }
        
        # 避難所データ収集
        situation = await _analyze_user_situation(state)
        shelters = await _get_nearby_shelters(state, situation)
        
        # コンテキストデータを準備
        context_data = {
            "emotional_context": _get_state_value(state, 'emotional_context', {}),
            "location_info": user_location,
            "is_emergency_mode": is_disaster_mode,
            "shelter_context": {
                "shelters_found": len(shelters),
                "nearest_shelter": shelters[0] if shelters else None,
                "user_situation": situation.model_dump() if situation else {}
            }
        }
        
        # 避難所データを検索結果として準備
        shelter_dicts = []
        logger.info(f"Preparing shelter data: {len(shelters)} shelters to process")
        for s in shelters:
            if hasattr(s, 'model_dump'):
                shelter_dict = s.model_dump()
                logger.debug(f"Shelter (model_dump): {shelter_dict.get('name')} - lat={shelter_dict.get('latitude')}, lon={shelter_dict.get('longitude')}")
                shelter_dicts.append(shelter_dict)
            elif isinstance(s, dict):
                logger.debug(f"Shelter (dict): {s.get('name')} - lat={s.get('latitude')}, lon={s.get('longitude')}")
                shelter_dicts.append(s)
            else:
                shelter_dict = {
                    "id": getattr(s, 'id', 'unknown'),
                    "name": getattr(s, 'name', 'Unknown Shelter'),
                    "latitude": getattr(s, 'latitude', None),
                    "longitude": getattr(s, 'longitude', None),
                    "distance_km": getattr(s, 'distance_km', None)
                }
                logger.debug(f"Shelter (object): {shelter_dict.get('name')} - lat={shelter_dict.get('latitude')}, lon={shelter_dict.get('longitude')}")
                shelter_dicts.append(shelter_dict)
        
        # feedback活用チェック
        improvement_feedback = _get_state_value(state, 'improvement_feedback', '')
        
        # 完全応答生成（バッチ処理）- ただし避難所カードは別途生成
        response_data = await CompleteResponseGenerator.generate_complete_response(
            user_input=user_input,
            intent=primary_intent,
            user_language=user_language,
            context_data=context_data,
            handler_type="evacuation",
            search_results=shelter_dicts,
            improvement_feedback=improvement_feedback,
            state=state
        )
        
        # 避難所の位置情報付きカードを生成（バッチ処理のsuggestion_cardsを上書き）
        logger.info("Calling _generate_suggestion_cards with shelter data...")
        evacuation_cards = _generate_suggestion_cards(shelter_dicts, {})
        response_data["suggestion_cards"] = evacuation_cards
        logger.info(f"Assigned {len(evacuation_cards)} cards to response_data['suggestion_cards']")
        
        # Verify map_url is present in response cards
        for idx, card in enumerate(evacuation_cards):
            if card.get('card_type') == 'evacuation_info':
                has_map_url = 'map_url' in card
                logger.info(f"Response card {idx+1}: has_map_url={has_map_url}, map_url={card.get('map_url', 'NONE')[:50] if has_map_url else 'MISSING'}")
        # Generated evacuation_info cards with location data
        
        # メッセージ構築
        from langchain_core.messages import AIMessage
        message = AIMessage(
            content=response_data["main_response"],
            additional_kwargs={
                "cards": response_data["suggestion_cards"],
                "follow_up_questions": response_data["follow_up_questions"],
                "priority": response_data["priority_level"],
                "handler_type": "evacuation",
                "shelters": shelter_dicts,
                "is_emergency": response_data["priority_level"] == "critical"
            }
        )
        
        # 緊急度が高い場合の特別処理
        is_emergency_response = (
            is_disaster_mode or 
            response_data["priority_level"] == "critical" or
            (situation and situation.requires_immediate_evacuation)
        )
        
        # バッチ処理使用フラグを設定
        intermediate_results = _get_state_value(state, 'intermediate_results', {})
        intermediate_results.update({
            "batch_processing_used": True,
            "evacuation_support_summary": response_data["main_response"],
            "shelters_found": shelter_dicts,
            "user_situation": situation.model_dump() if situation else {}
        })
        
        return {
            "messages": [message],
            "final_response_text": response_data["main_response"],
            "last_response": response_data["main_response"],
            "current_task_type": ["task_complete_evacuation_support"],
            "secondary_intents": [],
            "is_emergency_response": is_emergency_response,
            "intermediate_results": intermediate_results,
            "cards_to_display_queue": response_data["suggestion_cards"],
            "quality_self_check": response_data.get("quality_self_check", {}),
            "handler_completed": True
        }
        
    except Exception as e:
        logger.error(f"Batch evacuation support processing failed: {e}")
        return await _evacuation_support_fallback_response(state, str(e))

async def _evacuation_support_fallback_response(state: AgentState, error_message: str) -> Dict[str, Any]:
    """避難支援ハンドラーのフォールバック応答"""
    user_language = _get_state_value(state, 'user_language', 'ja')
    is_disaster_mode = _get_state_value(state, 'is_disaster_mode', False)
    
    # English-only fallback message (per CLAUDE.md principles)
    fallback_message = "Sorry, an error occurred while retrieving evacuation support information. Please move to a safe location and check official evacuation information."
    
    from langchain_core.messages import AIMessage
    error_message_obj = AIMessage(
        content=fallback_message,
        additional_kwargs={
            "error": error_message,
            "requires_immediate_attention": True
        }
    )
    
    return {
        "messages": [error_message_obj],
        "final_response_text": fallback_message,
        "last_response": fallback_message,
        "current_task_type": ["error"],
        "intermediate_results": {"error": error_message},
        "cards_to_display_queue": [],
        "is_emergency_response": is_disaster_mode,
        "secondary_intents": []
    }
