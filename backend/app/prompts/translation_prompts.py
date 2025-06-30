"""
Translation prompts for SafetyBee
Translation-related prompt definitions
"""

# Translation prompt template
TRANSLATION_PROMPT_TEMPLATE = """You are a professional translator specializing in disaster prevention and safety content.

Translate the following text from {source_language_name} to {target_language_name}.

Requirements:
- Maintain the original meaning and tone
- Use natural, fluent language in the target language
- For disaster/safety terms, use appropriate official terminology
- Keep formatting and structure intact
- If technical terms are used, preserve their accuracy

Text to translate:
{text_to_translate}

Provide only the translated text without any additional comments or explanations."""

# Language code to full name mapping
LANGUAGE_FULL_NAMES = {
    'en': 'English',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ko': 'Korean',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'tl': 'Filipino',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'pl': 'Polish',
    'tr': 'Turkish',
    'he': 'Hebrew',
    'uk': 'Ukrainian',
    'cs': 'Czech',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'mt': 'Maltese',
    'ga': 'Irish',
    'cy': 'Welsh',
    'is': 'Icelandic'
}

def get_disaster_terms_help(target_language: str) -> str:
    """
    Get disaster-specific terminology help for translation
    
    Args:
        target_language: Target language code
        
    Returns:
        Additional context for disaster term translation
    """
    disaster_terms_help = {
        'ja': """
Common disaster terms in Japanese:
- 地震 (jishin) = earthquake
- 津波 (tsunami) = tsunami  
- 台風 (taifuu) = typhoon
- 避難 (hinan) = evacuation
- 避難所 (hinanjo) = evacuation shelter
- 緊急 (kinkyuu) = emergency
- 災害 (saigai) = disaster
- 防災 (bousai) = disaster prevention
- 警報 (keihou) = warning/alert
- 注意報 (chuuihou) = advisory
""",
        'zh': """
Common disaster terms in Chinese:
- 地震 (dìzhèn) = earthquake
- 海啸 (hǎixiào) = tsunami
- 台风 (táifēng) = typhoon
- 疏散 (shūsàn) = evacuation
- 避难所 (bìnànsuǒ) = evacuation shelter
- 紧急 (jǐnjí) = emergency
- 灾害 (zāihài) = disaster
- 防灾 (fángzāi) = disaster prevention
- 警报 (jǐngbào) = warning/alert
""",
        'ko': """
Common disaster terms in Korean:
- 지진 (jijin) = earthquake
- 쓰나미 (sseunami) = tsunami
- 태풍 (taepung) = typhoon
- 대피 (daepi) = evacuation
- 대피소 (daepiso) = evacuation shelter
- 긴급 (gingeup) = emergency
- 재해 (jaehae) = disaster
- 방재 (bangjae) = disaster prevention
- 경보 (gyeongbo) = warning/alert
"""
    }
    
    return disaster_terms_help.get(target_language, "")