# backend/app/agents/safety_beacon_agent/suggestion_generators/prompt_templates.py
"""Prompt templates for suggestion generation with proper JSON formatting"""

# Template for welcome message generation
WELCOME_MESSAGE_TEMPLATE = """Create a welcoming suggestion for new users in {language_name}.

Help new users get started with LinguaSafeTrip disaster preparedness app.

Requirements:
- content should be welcoming and encouraging in {language_name} (max 60 characters)
- Mention checking basic settings or getting started
- Make it friendly and helpful

IMPORTANT for action_query:
- Must be a SINGLE, specific question about getting started with the app in {language_name}
- ONLY ONE QUESTION - do not include multiple questions
- Should ask about basic features or initial setup
- MUST match what the content promises (if content says "check settings", query should ask about settings)
- Examples in Japanese: "LinguaSafeTripの使い方は？", "初期設定ガイドを見せて", "基本機能を教えて"
- Examples in English: "How to use LinguaSafeTrip?", "Show me initial setup guide", "Explain basic features"

Return ONLY a valid JSON object:
{json_template}"""

# Template for emergency contact setup
EMERGENCY_CONTACT_TEMPLATE = """Create {urgency}suggestion about emergency contact registration in {language_name}.

{context_description}

Requirements:
- content should {urgency_modifier}suggest registering contacts for safety messages in {language_name} (max 60 characters)
- {emphasis}
- Focus on {focus_area}

IMPORTANT for action_query:
- Since this opens a dialog, action_query should be empty or minimal in {language_name}
- The tap action opens emergency contact dialog directly
- Examples in Japanese: "" (empty) or "緊急連絡先を追加"
- Examples in English: "" (empty) or "Add emergency contacts"

Return ONLY a valid JSON object:
{json_template}"""

# Template for seasonal warning
SEASONAL_WARNING_TEMPLATE = """Create a timely disaster preparedness suggestion for the current period: {season} in {language_name}.

Current period: {season}
Immediate risks for this time of year: {risks}

Requirements:
- content should focus on CURRENT, IMMEDIATE preparation needs for {language_name} (max 60 characters)
- Make it urgent and actionable for THIS month/season
- Focus on what users should do RIGHT NOW based on current weather patterns
- Use specific, timely language (e.g., "this month", "now", "before next storm")
- Process internally in English, then translate to target language

CRITICAL REQUIREMENT for action_query:
- Must be a SINGLE question - ONLY ONE QUESTION, not multiple
- The action_query MUST be DIRECTLY RELATED to the CURRENT period mentioned in content
- If your content mentions "{season}" then your query MUST ask about preparation for THIS specific time period
- Be VERY SPECIFIC about the current time period and immediate risks
- Focus on CURRENT preparation, not general seasonal advice
- Generate in English first, then will be translated

Current Month Examples (June - Early Rainy Season):
- Content: "Prepare for rainy season flooding now" → Query: "How to prepare for June heavy rain and flooding?"
- Content: "Get ready for early typhoons this month" → Query: "How to prepare for June typhoons?"
- Content: "Flood prep needed before July" → Query: "What to do for rainy season flooding preparation?"

Bad Examples (DO NOT DO THIS):
- Content: "Rainy season prep" → Query: "What are weather risks?" (NOT SPECIFIC!)
- Content: "Seasonal preparation" → Query: "What are seasonal disasters?" (TOO GENERIC!)

Return ONLY a valid JSON object:
{json_template}"""

# Template for disaster news
DISASTER_NEWS_TEMPLATE = """Create {mode_type} disaster {content_type} suggestion in {language_name}.

{mode_description}

Requirements:
- content should {action_type} (max 60 characters)
- Make it {tone}
- Focus on {focus}
- {examples}

IMPORTANT for action_query:
- Must be a SINGLE, specific {query_type} - ONLY ONE QUESTION
- Should {query_action}
- MUST match the specific intent of the content (if content mentions "your area", query must say "my area")
- If content mentions specific disaster type, query MUST mention the same type
- Examples in Japanese: {japanese_examples}
- Examples in English: {english_examples}

Return ONLY a valid JSON object:
{json_template}"""

# Template for hazard map URL
HAZARD_MAP_TEMPLATE = """Create a hazard map viewing suggestion in {language_name}.

Help users access local hazard information and understand their disaster risks.

Requirements:
- content should encourage checking local hazard maps (max 60 characters)
- Make it informative and actionable
- Focus on understanding personal/local risks

IMPORTANT for action_query:
- Must be a SINGLE, specific question about hazard maps or local risks - ONLY ONE QUESTION
- Should clearly ask for hazard information
- MUST include location reference (my area, near me, local)
- Examples in Japanese: "私の地域のハザードマップを見せて", "この地域の災害リスクは？", "近くの危険エリアを教えて"
- Examples in English: "Show me hazard map for my area", "What are disaster risks near me?", "Display local danger zones"

Return ONLY a valid JSON object:
{json_template}"""

# Template for shelter status update
SHELTER_STATUS_TEMPLATE = """Create an evacuation shelter information suggestion in {language_name}.

Help users find and check the status of nearby evacuation shelters.

Requirements:
- content should encourage checking shelter locations and status (max 60 characters)
- Make it practical and helpful
- Focus on finding nearby shelters

IMPORTANT for action_query:
- Must be a SINGLE, specific question about evacuation shelters - ONLY ONE QUESTION
- Should ask for concrete shelter information
- MUST include location reference (near me, my area, nearby)
- Examples in Japanese: "近くの避難所はどこ？", "私の地域の避難所を教えて", "最寄りの避難場所を表示して"
- Examples in English: "Where are evacuation shelters near me?", "Show shelters in my area", "Find nearest evacuation sites"

Return ONLY a valid JSON object:
{json_template}"""

# Generic JSON template - note the careful escaping
SUGGESTION_JSON_TEMPLATE = '''{
    "content": "<content_text>",
    "action_query": "<action_query_text>",
    "action_display_text": "<display_text>"
}'''

def get_json_template(content_desc: str, query_desc: str, display_desc: str) -> str:
    """Generate a safe JSON template with descriptions"""
    # JSONテンプレートを安全に生成（エスケープ不要）
    template = {
        "content": content_desc,
        "action_query": query_desc, 
        "action_display_text": display_desc
    }
    # 辞書をJSON文字列に変換して返す
    import json
    return json.dumps(template, ensure_ascii=False, indent=4)