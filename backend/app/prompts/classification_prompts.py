"""
Classification prompts for natural language-based classification
LLM自然言語分類用のプロンプト定義
"""

# JMA Event Type Classification Prompt
JMA_EVENT_TYPE_CLASSIFICATION_PROMPT = """Classify the following JMA (Japan Meteorological Agency) event into one of these categories:

Event to classify:
Title: {title}
Content: {content}

Classification Categories:
1. EARTHQUAKE - Earthquake information, seismic intensity reports
2. TSUNAMI - Tsunami warnings, advisories, or information
3. WEATHER - Weather warnings, advisories (rain, wind, snow, etc.)
4. VOLCANO - Volcanic activity warnings or information
5. OTHER - Any other type of meteorological information

Instructions:
- Analyze the title and content to determine the primary event type
- Consider Japanese terms like: 地震 (earthquake), 津波 (tsunami), 警報 (warning), 注意報 (advisory), 火山 (volcano)
- Focus on the main hazard being reported
- Respond with only the category name (EARTHQUAKE, TSUNAMI, WEATHER, VOLCANO, or OTHER)

Classification:"""

# Disaster News Classification Prompt
DISASTER_NEWS_CLASSIFICATION_PROMPT = """Determine if this news article is disaster-related.

Article to classify:
Title: {title}
Content: {content}

Disaster-related topics include:
- Natural disasters (earthquakes, tsunamis, typhoons, floods, fires, volcanic eruptions)
- Weather warnings and alerts
- Disaster prevention and preparedness
- Emergency response and evacuation
- Infrastructure damage from natural events
- Evacuation orders and shelter information

Non-disaster topics include:
- General news, politics, sports, entertainment
- Regular weather forecasts (without warnings)
- Economic news (unless disaster-related)
- International news (unless about disasters affecting Japan)

Respond with only "true" if disaster-related, "false" if not disaster-related.

Classification:"""

# Emergency Detection Prompt
EMERGENCY_DETECTION_PROMPT = """Analyze this user input to determine if it indicates an emergency situation requiring immediate assistance.

User Input: {user_input}

Emergency indicators include:
- Immediate danger or life-threatening situations
- Requests for urgent help or rescue
- Reports of ongoing disasters (earthquake, fire, accident)
- Medical emergencies
- Being trapped or unable to escape
- Immediate safety concerns

Non-emergency indicators include:
- General questions about disaster preparation
- Information requests about past events
- Routine safety inquiries
- Academic or educational questions

Consider the urgency and immediacy of the situation described.

Respond with only "true" if this indicates an emergency, "false" if not an emergency.

Emergency Status:"""