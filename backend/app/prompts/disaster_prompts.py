"""Disaster response prompt management module - defines prompt templates by disaster type"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ===== Emergency Level Analysis Prompts =====

# Emergency level judgment prompt  
EMERGENCY_LEVEL_ANALYSIS_PROMPT = """Analyze the emergency level of this response content.

Response: "{response_text}"

Return only "critical" or "warning":
- "critical": Immediate life-threatening situation requiring instant action
- "warning": Important safety information but not immediately life-threatening"""

# News query detection for current information requests
NEWS_QUERY_DETECTION_PROMPT = """Analyze if this user input is asking for news or current information updates.

User input: "{user_input}"

Return only "true" or "false" - is the user asking for news, updates, or current information?"""

# Uncertainty expression detection for reliability disclaimers
UNCERTAINTY_EXPRESSIONS_DETECTION_PROMPT = """Analyze if this response contains uncertainty expressions (predictions, forecasts, possibilities) that should include reliability notes.

Response: "{response_text}"
Language: {user_language}

Return only "true" or "false" - does this response contain predictions or uncertain information that would benefit from reliability disclaimers?"""

# Disaster type classification for fallback responses
DISASTER_TYPE_CLASSIFICATION_PROMPT = """Analyze the disaster type mentioned in this prompt for appropriate fallback response.

Prompt: "{prompt_text}"

Return only one word: "tsunami", "earthquake", "flood", or "general" - what type of disaster is being discussed?"""

# ===== Disaster Info Handler Prompts =====

# User request analysis prompt
ANALYZE_USER_REQUEST_PROMPT = """Use natural language understanding to analyze this disaster-related request.

User input: "{user_input}"
Current mode: {disaster_mode}

Understand the user's TRUE intent using semantic analysis, not keyword matching:

1. Temporal context analysis:
   - "during normal times" / "平常時" → User wants general preparation info, NOT current disasters
   - "during emergency" / "緊急時" → User wants current emergency information
   - "now" / "latest" / "current" → User wants real-time information

2. Request type understanding:
   - Questions about preparation/prevention → disaster_type="preparation"
   - Questions about current risks/dangers → disaster_type="general" with time_range="current"
   - Questions about specific disasters → Set appropriate disaster_type

3. IMPORTANT semantic rules:
   - "disaster news for normal times" → User wants general safety news, NOT current disasters
   - "evacuation center info" → This is NOT for this handler - return reject_reason

Return JSON with semantic understanding:
{{
  "disaster_type": "earthquake|tsunami|typhoon|flood|preparation|seasonal|general",
  "location_specific": true|false,
  "detail_level": "summary|detailed",
  "time_range": "current|recent|normal_time",
  "preparation_focus": true|false,
  "season_specific": "spring|summer|autumn|winter|none",
  "semantic_intent": "Brief description of what user really wants",
  "reject_reason": "evacuation_request|null"
}}"""

# Disaster information response generation prompt
GENERATE_DISASTER_INFO_RESPONSE_PROMPT = """Generate a helpful response in English about the following disaster-related information found:

Found {event_count} disaster-related items:
{event_details}

CRITICAL: Only use the information provided above. Do NOT:
- Invent additional sources or references
- Use placeholder text like "[name]" or "[distance]"
- Reference imaginary search results or apps
- Create fake data when information is missing

Requirements:
- For EMERGENCY situations: Lead with critical actions needed immediately
- For NON-EMERGENCY: Provide comprehensive educational coverage
- Include specific details and concrete examples as appropriate
- Explain significance based on urgency level
- Offer clear, actionable recommendations
- Include relevant safety tips prioritized by importance
- Mention these are disaster preparedness resources
- Match thoroughness to situation urgency

IMPORTANT: Only respond in English. Translation will be handled by response_generator."""

# No information found response prompt
NO_INFORMATION_FOUND_RESPONSE_PROMPT = """Generate a response in English indicating no relevant disaster information was found.

Requirements:
- Explain that no current disaster information was found
- Provide general disaster preparedness tips relevant to the query
- Include educational content about the type of disaster they asked about
- Suggest specific official sources and how to monitor them
- Offer proactive safety recommendations
- Be comprehensive and educational even without current alerts

IMPORTANT: Only respond in English. Translation will be handled by response_generator."""

# Error response prompt
ERROR_RESPONSE_PROMPT = """Generate a brief error message in English.

Requirements:
- Apologize for the error
- State that the system is unable to generate a response
- Suggest trying again later
- Be polite and brief

IMPORTANT: Only respond in English. Translation will be handled by response_generator."""

# Context analysis prompt
CONTEXT_ANALYSIS_PROMPT = """
Analyze the user's question about disaster preparation and identify their specific context:
- Family composition (babies, elderly, etc.)
- Living environment (apartment, high-rise, etc.)
- Special considerations (budget, season, etc.)

User input: {user_input}

Return only a short descriptive phrase in English like:
- "for families with infants"
- "for households with elderly"
- "for apartment/high-rise residents"
- "budget-conscious"
- "general"
"""

# Personalized disaster preparation prompt
PERSONALIZED_DISASTER_PREPARATION_PROMPT = """
Generate a specific and personalized response about disaster preparation in English.

User's question: {user_input}
Context: {context_analysis} disaster preparation

Consider the following points:
1. Content tailored to the user's specific situation (family composition, living environment, budget, etc.)
2. Practical and specific advice
3. Step-by-step clear explanations
4. Warm tone that provides reassurance

IMPORTANT: Generate response in English. Translation will be handled by response_generator.
"""

# Disaster-specific no information prompts
TSUNAMI_NO_INFO_PROMPT = """Generate a response in English indicating no current tsunami warnings.

Requirements:
- State that no tsunami warnings or advisories are currently in effect
- Recommend checking JMA website for latest information
- Include a safety reminder
- Be reassuring but informative

IMPORTANT: Only respond in English. Translation will be handled by response_generator."""

TYPHOON_NO_INFO_PROMPT = """Generate a response in English indicating no current typhoon information.

Requirements:
- State that no special typhoon information is currently available
- Recommend checking JMA website for latest weather information
- Remind to be aware of weather changes
- Be informative and helpful

IMPORTANT: Only respond in English. Translation will be handled by response_generator."""

LANDSLIDE_NO_INFO_PROMPT = """Generate a response in English indicating no current landslide warnings.

Requirements:
- State that no landslide warnings are currently in effect
- Provide safety advice about heavy rain situations
- Recommend checking JMA website for latest information
- Be safety-focused and informative

IMPORTANT: Only respond in English. Translation will be handled by response_generator."""


# Base prompt template
BASE_PROMPT = """You are a caring AI assistant specializing in disaster response who deeply values each user's safety and emotional well-being. 
Your mission is not just to provide information, but to be a compassionate companion during difficult times.
Based on the following disaster information and user state, please suggest appropriate responses that show genuine care and support.

[Disaster Information]
Type: {disaster_type}
Location: {location}
Scale: {magnitude}
Severity: {severity}
Latest Info: {latest_info}

[User State]
Last Update: {last_state_update}
Safety Reported: {safety_reported}
Shelter Info Requested: {shelter_requested}
Received Warnings: {received_warnings}

[Conversation History]
{chat_history}

[Output Format]
Please output strictly in the following JSON format. No explanatory text needed.
{{
  "response_text": "Text message to user",
  "action_cards": [
    {{
      "card_id": "unique_id",
      "title": "Card title",
      "content_markdown": "Content in Markdown format",
      "actions": [
        {{
          "label": "Action name",
          "action_type": "action_type",
          "payload": {}
        }}
      ],
      "priority": number
    }}
  ]
}}
"""

# Conversation routing supervisor prompt
ROUTING_SUPERVISOR_PROMPT = """\
You are a disaster prevention assistant conversation router. Follow these guidelines:

# Role
- Select the optimal processing node from user input and conversation history
- Explain the selection reason with clear justification and context

# Node Selection Guidelines
1. Route to initial_generic_handler_node in these cases:
   - Greetings (hello, thank you, etc.)
   - Small talk (weather, hobbies, etc.)
   - Confirmation messages after specialized processing

2. When disaster response context is determined:
   - Need to provide disaster information → disaster_info_handler_node
   - Need evacuation behavior support → evacuation_support_handler_node
   - Need disaster prevention knowledge/preparation info → information_guide_handler_node

3. For general conversation not matching above → initial_generic_handler_node

4. When unclassifiable → response_generator

# Constraints
- Output must strictly follow:
{{
  "next_node": "selected_node_name",
  "reason": "detailed decision reason with full context and justification"
}}
"""
# Disaster type-specific prompt templates
DISASTER_PROMPTS = {
    "earthquake": {
        "initial": BASE_PROMPT + "\nSuggest safety confirmation and initial response immediately after earthquake.",
        "ongoing": BASE_PROMPT + "\nSuggest preparation for aftershocks and continuous safety measures.",
        "urgent": BASE_PROMPT + "\nEmergency evacuation is required. Provide clear instructions."
    },
    "tsunami": {
        "initial": BASE_PROMPT + "\nTsunami warning issued. Prioritize evacuation to higher ground.",
        "ongoing": BASE_PROMPT + "\nSuggest safety measures based on tsunami arrival status."
    },
    "flood": {
        "initial": BASE_PROMPT + "\nFlood warning issued. Suggest moving to safe location.",
        "ongoing": BASE_PROMPT + "\nSuggest safety measures based on water level conditions."
    }
}

# Proactive suggestion prompt
PROACTIVE_PROMPT = """{time_elapsed} minutes have passed since the last interaction. Considering disaster situation and user state, make proactive suggestions if any of these cases apply:

1. User hasn't reported safety (prompt safety confirmation)
2. New warning information available (prompt information provision)
3. Situation is deteriorating (prompt emergency response)
4. Requested shelter info but not confirmed (follow-up)

[Output Format]
Please output in the same JSON format as above.
"""

def get_disaster_prompt(
    disaster_type: str,
    phase: str,
    disaster_context: Dict[str, Any],
    user_state: Dict[str, Any],
    chat_history: str
) -> str:
    """Get prompt based on disaster type and phase

    Args:
        disaster_type: Disaster type (earthquake/tsunami/flood etc.)
        phase: Disaster phase (initial/ongoing/urgent etc.)
        disaster_context: Disaster context information
        user_state: User state information
        chat_history: Conversation history string

    Returns:
        Generated prompt string
    """
    prompt_template = DISASTER_PROMPTS.get(
        disaster_type, {}).get(phase, BASE_PROMPT)

    try:
        return prompt_template.format(
            disaster_type=disaster_context.get("type", "Unknown"),
            location=disaster_context.get("location", "Unknown"),
            magnitude=disaster_context.get("magnitude", "Unknown"),
            severity=disaster_context.get("severity", "No info"),
            latest_info=disaster_context.get("warnings", []),
            last_state_update=user_state.get("last_interaction", "Unknown"),
            safety_reported="Yes" if user_state.get("reported_safety") else "No",
            shelter_requested="Yes" if user_state.get("requested_shelter_info") else "No",
            received_warnings=", ".join(user_state.get("received_warnings", []) or "None"),
            chat_history=chat_history
        )
    except KeyError as e:
        logger.error(f"Missing template variable: {e}")
        raise ValueError(f"Required template variable missing: {e}")

EVACUATION_ADVICE_PROMPT = """You are an AI assistant specializing in disaster response and disaster preparedness. Based on the following guidelines and user input, generate specific and practical evacuation advice and appropriate belongings list.

[User Input]
{user_input}

[Guidelines]
{guidelines}

[Context Recognition]
Determine from user input whether this is:
1. EMERGENCY SITUATION: Active disaster requiring immediate evacuation
2. PREPAREDNESS INQUIRY: Normal-time questions about evacuation routes, shelter locations, or disaster preparation

[Emergency-Specific Safety Guidelines]
For ACTIVE DISASTERS, always include these safety instructions:
- Tsunami: IMMEDIATELY evacuate to higher ground (at least 10m elevation or 3rd floor and above). Do NOT wait to see the wave. Move inland and uphill as quickly as possible.
- Flood/Heavy Rain: Seek vertical evacuation to upper floors (2nd floor or higher). Avoid basements and underground areas. Do NOT attempt to walk through flowing water.
- Earthquake: After shaking stops, move to open spaces away from buildings, power lines, and trees. Check for injuries before moving.
- Typhoon: Stay indoors in a sturdy building. Move to the center of the building away from windows. Have emergency supplies ready.
- Landslide: Evacuate perpendicular to the slope direction. Move to stable ground away from hillsides and cliffs.

[Preparedness Guidelines]
For NORMAL-TIME INQUIRIES about evacuation and shelters:
- Provide information about local evacuation routes and shelter locations
- Explain how to identify safe evacuation areas in advance
- Suggest creating family evacuation plans
- Recommend checking evacuation routes during non-emergency times
- Advise confirming shelter capacity and facilities

[Output Requirements]
- Determine situation type (emergency vs. preparedness), disaster type, and appropriate phase
- Present belongings list in item name and description list format
- Present advice in bullet points or step-by-step list format
- All output should be in the user's language ({user_language})
- For emergency tsunami: ALWAYS emphasize immediate evacuation to high ground as the first advice
- For emergency flood: ALWAYS emphasize vertical evacuation as the primary strategy
- For preparedness questions: Focus on planning, familiarization, and advance preparation

[Shelter Safety Evaluation]
When providing shelter information:
- For tsunami: Warn if any shelter appears to be in low-lying or coastal areas based on name/context
- For flood: Prioritize multi-story buildings and warn about single-story shelters
- If shelter safety is uncertain, advise users to confirm building height and location before evacuating
- Always remind users that moving to higher ground takes priority over reaching a specific shelter

[Output Format]
Please output strictly in the following JSON format. No explanatory text needed.
{{
  "disaster_type": "Determined disaster type (e.g., earthquake, tsunami, flood, volcano, heavy_rain, general_preparedness)",
  "phase": "Determined phase (e.g., emergency_evacuation, preparedness_planning, route_familiarization, shelter_inquiry, during_evacuation, post_evacuation)",
  "items": [
    {{
      "name": "Item name",
      "description": "Detailed description"
    }}
  ],
  "advice": [
    "Specific advice 1",
    "Specific advice 2"
  ]
}}
"""

def get_proactive_prompt(time_elapsed: int) -> str:
    """
    Generate proactive suggestion prompt

    Args:
        time_elapsed: Time elapsed since last interaction (minutes)

    Returns:
        Generated prompt string
    """
    return PROACTIVE_PROMPT.format(time_elapsed=time_elapsed)

def get_evacuation_advice_prompt(
    user_input: str,
    guidelines: str,
    language: str = "en"
) -> str:
    """
    Get evacuation advice generation prompt

    Args:
        user_input: User input text
        guidelines: Guidelines JSON string
        language: Output language

    Returns:
        Formatted prompt string
    """
    return EVACUATION_ADVICE_PROMPT.format(
        user_input=user_input,
        guidelines=guidelines,
        user_language=language
    )

# Evacuation support response generation prompt
EVACUATION_SUPPORT_RESPONSE_PROMPT = """You are an AI assistant specializing in disaster response. Integrate the following information and generate appropriate evacuation support message for the user.

[User Input]
{user_input}

[Shelter Information]
{shelter_info}

[Evacuation Advice]
{evacuation_advice}

[CRITICAL DATA RULES]
- Use ONLY the shelter information actually provided above
- Do NOT invent shelter names or distances
- Do NOT use placeholders like "[shelter name]" or "[distance]km"
- If shelter data is missing, acknowledge it honestly

[Output Requirements]
- Write in the user's language ({user_language}) with clear and empathetic tone
- Present up to 3 shelters concisely by distance order
- Provide clear action instructions based on urgency
- Provide comprehensive evacuation guidance with detailed steps and explanations

[Output Format]
{{
  "main_message": "Main evacuation support message",
  "shelter_summary": "Shelter information summary",
  "advice_summary": "Evacuation advice summary",
  "empathetic_statement": "Empathetic statement"
}}
"""

# Shelter suggestion card generation prompt
SHELTER_CARD_PROMPT = """Generate a suggestion card from the following shelter information.

[Shelter Information]
{name}
Address: {address}
Distance: {distance}m
Facilities: {facilities}
Capacity: {capacity}
Operation Status: {status}

[Output Requirements]
- Title: Shelter name and distance
- Content: Emphasize address and main facilities
- Action button: For map display
- Priority: Calculate from distance and operation status

[Output Format]
{{
  "title": "Shelter name ({distance}m)",
  "content": "Address: {address}\\nFacilities: {facilities}",
  "map_url": "{map_url}",
  "priority": number(1-5)
}}
"""

# Belongings checklist card generation prompt
CHECKLIST_CARD_PROMPT = """Generate a belongings checklist card from the following items.

[Item List]
{items}

[Output Requirements]
- Title: "Evacuation Belongings Checklist"
- Content: Items in checkbox list format
- Sort items by urgency
- Add supplementary explanation

[Output Format]
{{
  "title": "Evacuation Belongings Checklist",
  "items": [
    {{
      "name": "Item name",
      "description": "Detailed description",
      "is_critical": true/false
    }}
  ],
  "description": "Supplementary explanation"
}}
"""

def get_evacuation_response_prompt(
    user_input: str,
    shelter_info: str,
    evacuation_advice: str,
    language: str = "en"
) -> str:
    """
    避難支援応答生成用プロンプトを取得

    Args:
        user_input: ユーザーの入力テキスト
        shelter_info: 避難所情報JSON文字列
        evacuation_advice: 避難アドバイスJSON文字列
        language: 出力言語

    Returns:
        フォーマット済みプロンプト文字列
    """
    return EVACUATION_SUPPORT_RESPONSE_PROMPT.format(
        user_input=user_input,
        shelter_info=shelter_info,
        evacuation_advice=evacuation_advice,
        user_language=language
    )

def get_shelter_card_prompt(shelter: Dict[str, Any]) -> str:
    """
    避難所提案カード生成用プロンプトを取得

    Args:
        shelter: 避難所情報辞書

    Returns:
        フォーマット済みプロンプト文字列
    """
    return SHELTER_CARD_PROMPT.format(**shelter)

def get_checklist_card_prompt(items: List[Dict[str, Any]]) -> str:
    """
    持ち物リストカード生成用プロンプトを取得

    Args:
        items: 持ち物アイテムリスト

    Returns:
        フォーマット済みプロンプト文字列
    """
    return CHECKLIST_CARD_PROMPT.format(items="\n".join(
        f"- {item['name']}: {item.get('description', '')}"
        for item in items
    ))

def get_disaster_anniversary_card_prompt(
    anniversary_name: str,
    days_until: int
) -> str:
    """
    災害記念日接近時の提案カード生成用プロンプトを取得

    Args:
        anniversary_name: 災害記念日名 (例: "東日本大震災")
        days_until: 記念日までの残り日数

    Returns:
        フォーマット済みプロンプト文字列
    """
    return DISASTER_ANNIVERSARY_CARD_PROMPT.format(
        anniversary_name=anniversary_name,
        days_until=days_until
    )

# 災害記念日接近時の提案カード生成用プロンプト
DISASTER_ANNIVERSARY_CARD_PROMPT = """\
災害記念日「{anniversary_name}」が{days_until}日後に迫っています。
この機会に防災準備を見直す提案カードを生成してください。

【出力要件】
- タイトル: 記念日名と残り日数を明記
- 内容: 具体的な準備行動を3つ提案
- ボタン: 防災チェックリスト開始用
- 緊急度: 記念日までの日数に応じて設定

【出力フォーマット】
{{
  "title": "記念日タイトル ({days_until}日前)",
  "description": "具体的な準備提案",
  "buttons": [
    {{
      "label": "防災チェックを開始",
      "action_type": "start_checklist",
      "action_data": {{
        "checklist_type": "anniversary_prep"
      }}
    }}
  ],
  "urgency": 1-5
}}
"""

# プロンプト辞書
PROMPT_DICT = {
    "routing_supervisor": ROUTING_SUPERVISOR_PROMPT,
    "disaster_anniversary": DISASTER_ANNIVERSARY_CARD_PROMPT,
    "evacuation_support": EVACUATION_SUPPORT_RESPONSE_PROMPT,
    "checklist": CHECKLIST_CARD_PROMPT,
    "shelter": SHELTER_CARD_PROMPT
}
