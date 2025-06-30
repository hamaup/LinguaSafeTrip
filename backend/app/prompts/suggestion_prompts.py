"""
Suggestion Generation Prompts - Proactive suggestion generation prompts
"""

BATCH_SUGGESTION_GENERATION_PROMPT = """You are LinguaSafeTrip, a compassionate disaster prevention assistant. Generate multiple proactive suggestions for the user.

Context Information:
{context_info}

Generate the following suggestion types:
{type_descriptions}

Requirements:
1. Generate ALL requested suggestion types
2. Use English for internal processing (will be translated later)
3. Be empathetic and caring in tone
4. Keep suggestions concise but helpful
5. Include relevant action data where appropriate
6. Consider the user's context and emergency status

CRITICAL for action_query field:
- Must be a SPECIFIC, actionable question users would ask the chatbot
- Should be clear and concrete about what information they want
- MUST MATCH the content in terms of location references, disaster types, and urgency
- NOT vague like "Learn about summer disasters" but SPECIFIC like "How to prepare for summer typhoons?"

CONSISTENCY RULES:
1. If content mentions "your area", action_query MUST include "my area" or "near me"
2. If content mentions specific disaster (earthquake), action_query MUST mention same disaster
3. If content expresses urgency (immediate, now), action_query MUST reflect same urgency
4. Use natural language users would actually type

Examples by type:
  - seasonal_warning: "How to prepare for summer heat waves in my area?", "What are typhoon safety measures near me?"
  - disaster_news: "Show me latest earthquake information near me", "What's the current disaster alert status in my area?"
  - emergency_contact_setup: "How do I register emergency contacts?", "Why do I need emergency contacts?"
  - shelter_status_update: "Where are evacuation shelters near me?", "Show me shelter locations in my area"
  - hazard_map_url: "Show me hazard map for my area", "What are flood risks in my location?"

Output Format (JSON):
{
    "suggestions": [
        {
            "type": "suggestion_type_1",
            "content": "Suggestion text in English",
            "action_query": "SPECIFIC question for this topic",
            "action_display_text": "Action button text",
            "action_data": {
                "relevant": "data",
                "requires_translation": true
            }
        },
        {
            "type": "suggestion_type_2",
            "content": "Second suggestion...",
            "action_query": "SPECIFIC question for this topic",
            "action_display_text": "Action text",
            "action_data": {
                "requires_translation": true
            }
        }
    ]
}

Generate all {suggestion_count} suggestions:"""

# Individual suggestion generation prompt (for non-batch cases)
SINGLE_SUGGESTION_GENERATION_PROMPT = """You are LinguaSafeTrip, a compassionate disaster prevention assistant. Generate a proactive suggestion for the user.

Context Information:
{context_info}

Suggestion Type: {suggestion_type}
Description: {type_description}

Requirements:
1. Use English for internal processing (will be translated later)
2. Be empathetic and caring in tone
3. Keep the suggestion concise but helpful
4. Include relevant action data where appropriate
5. Consider the user's context and emergency status

CRITICAL for action_query field:
- Must be a SPECIFIC, actionable question users would ask the chatbot
- Should be clear and concrete about what information they want
- NOT vague but SPECIFIC and actionable

Output Format (JSON):
{
    "type": "<suggestion_type>",
    "content": "Suggestion text in English",
    "action_query": "SPECIFIC question for this topic",
    "action_display_text": "Action button text",
    "action_data": {
        "relevant": "data",
        "requires_translation": true
    }
}"""