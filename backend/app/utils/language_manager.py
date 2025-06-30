"""
統一言語管理システム
全てのハンドラーでLLM言語処理を最適化
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class LanguageManager:
    """統一言語処理とキャッシュ管理"""
    
    def __init__(self):
        self.language_cache: Dict[str, Tuple[str, datetime]] = {}
        self.cache_duration = timedelta(minutes=30)  # 30分間キャッシュ
        
        # 言語別の基本応答テンプレート
        self.response_templates = {
            "ja": {
                "greeting": "こんにちは！防災アシスタントのLinguaSafeTripです。",
                "disaster_help": "災害に関するお手伝いをさせていただきます。",
                "shelter_search": "避難所情報を検索しています...",
                "evacuation_guide": "避難に関するガイダンスをお伝えします。"
            },
            "en": {
                "greeting": "Hello! I'm LinguaSafeTrip, your disaster prevention assistant.",
                "disaster_help": "I'll help you with disaster-related information.",
                "shelter_search": "Searching for shelter information...",
                "evacuation_guide": "I'll provide evacuation guidance."
            },
            "zh_CN": {
                "greeting": "你好！我是LinguaSafeTrip，你的防灾助手。",
                "disaster_help": "我将为您提供灾害相关的帮助。",
                "shelter_search": "正在搜索避难所信息...",
                "evacuation_guide": "我将为您提供避难指导。"
            },
            "zh_TW": {
                "greeting": "您好！我是LinguaSafeTrip，您的防災助手。",
                "disaster_help": "我將為您提供災害相關的幫助。",
                "shelter_search": "正在搜尋避難所資訊...",
                "evacuation_guide": "我將為您提供避難指導。"
            },
            "it": {
                "greeting": "Ciao! Sono LinguaSafeTrip, il tuo assistente per la prevenzione dei disastri.",
                "disaster_help": "Ti aiuterò con informazioni relative ai disastri.",
                "shelter_search": "Sto cercando informazioni sui rifugi...",
                "evacuation_guide": "Ti fornirò una guida per l'evacuazione."
            },
            "ko": {
                "greeting": "안녕하세요! 저는 재난 예방 도우미 LinguaSafeTrip입니다.",
                "disaster_help": "재난 관련 정보를 도와드리겠습니다.",
                "shelter_search": "대피소 정보를 검색하고 있습니다...",
                "evacuation_guide": "대피 안내를 제공하겠습니다."
            },
            "es": {
                "greeting": "¡Hola! Soy LinguaSafeTrip, tu asistente de prevención de desastres.",
                "disaster_help": "Te ayudaré con información relacionada con desastres.",
                "shelter_search": "Buscando información sobre refugios...",
                "evacuation_guide": "Te proporcionaré orientación para la evacuación."
            },
            "fr": {
                "greeting": "Bonjour! Je suis LinguaSafeTrip, votre assistant de prévention des catastrophes.",
                "disaster_help": "Je vous aiderai avec des informations sur les catastrophes.",
                "shelter_search": "Recherche d'informations sur les abris...",
                "evacuation_guide": "Je vous fournirai des conseils d'évacuation."
            },
            "de": {
                "greeting": "Hallo! Ich bin LinguaSafeTrip, Ihr Assistent für Katastrophenvorsorge.",
                "disaster_help": "Ich helfe Ihnen mit katastrophenbezogenen Informationen.",
                "shelter_search": "Suche nach Informationen über Notunterkünfte...",
                "evacuation_guide": "Ich werde Ihnen Evakuierungshinweise geben."
            },
            "pt": {
                "greeting": "Olá! Sou LinguaSafeTrip, seu assistente de prevenção de desastres.",
                "disaster_help": "Vou ajudá-lo com informações relacionadas a desastres.",
                "shelter_search": "Procurando informações sobre abrigos...",
                "evacuation_guide": "Fornecerei orientações de evacuação."
            },
            "ru": {
                "greeting": "Здравствуйте! Я LinguaSafeTrip, ваш помощник по предотвращению стихийных бедствий.",
                "disaster_help": "Я помогу вам с информацией о стихийных бедствиях.",
                "shelter_search": "Поиск информации об убежищах...",
                "evacuation_guide": "Я предоставлю инструкции по эвакуации."
            },
            "ar": {
                "greeting": "مرحباً! أنا LinguaSafeTrip، مساعدك في الوقاية من الكوارث.",
                "disaster_help": "سأساعدك بالمعلومات المتعلقة بالكوارث.",
                "shelter_search": "جاري البحث عن معلومات الملاجئ...",
                "evacuation_guide": "سأقدم لك إرشادات الإخلاء."
            },
            "hi": {
                "greeting": "नमस्ते! मैं LinguaSafeTrip हूँ, आपका आपदा रोकथाम सहायक।",
                "disaster_help": "मैं आपदा संबंधित जानकारी में आपकी मदद करूंगा।",
                "shelter_search": "आश्रय स्थल की जानकारी खोज रहा हूँ...",
                "evacuation_guide": "मैं आपको निकासी मार्गदर्शन प्रदान करूंगा।"
            },
            "th": {
                "greeting": "สวัสดีค่ะ! ฉันคือ LinguaSafeTrip ผู้ช่วยป้องกันภัยพิบัติของคุณ",
                "disaster_help": "ฉันจะช่วยคุณเกี่ยวกับข้อมูลที่เกี่ยวข้องกับภัยพิบัติ",
                "shelter_search": "กำลังค้นหาข้อมูลศูนย์พักพิง...",
                "evacuation_guide": "ฉันจะให้คำแนะนำการอพยพ"
            },
            "vi": {
                "greeting": "Xin chào! Tôi là LinguaSafeTrip, trợ lý phòng chống thiên tai của bạn.",
                "disaster_help": "Tôi sẽ giúp bạn với thông tin liên quan đến thiên tai.",
                "shelter_search": "Đang tìm kiếm thông tin về nơi trú ẩn...",
                "evacuation_guide": "Tôi sẽ cung cấp hướng dẫn sơ tán."
            }
        }
    
    async def detect_and_cache_language(self, user_input: str, user_id: str = "default", llm_client=None) -> str:
        """
        言語検出とキャッシュ管理
        アプリの言語設定を使用（LLM検出は使用しない）
        """
        # Note: This method is kept for compatibility but now returns default language
        # Actual language should be passed from app settings
        return "ja"  # デフォルト
    
    
    async def _llm_language_detection(self, user_input: str, llm_client) -> str:
        """LLMによる自然言語検出（互換性のため保持、実際には使用されない）"""
        detection_prompt = f"""Identify the language of this text. For Chinese, distinguish between Simplified (zh_CN) and Traditional (zh_TW). Respond with ONLY the appropriate ISO language code.

Text: "{user_input}"

Examples:
- ja = Japanese
- en = English  
- zh_CN = Chinese Simplified
- zh_TW = Chinese Traditional
- ko = Korean
- es = Spanish
- fr = French
- de = German
- it = Italian
- pt = Portuguese
- ru = Russian
- ar = Arabic
- hi = Hindi
- th = Thai
- vi = Vietnamese

Respond with the language code:"""

        response = await llm_client.ainvoke([HumanMessage(content=detection_prompt)])
        detected = response.content.strip().lower() if hasattr(response, 'content') else "ja"
        
        return detected if detected else "ja"
    
    def should_translate(self, detected_language: str, target_language: str) -> bool:
        """翻訳が必要かどうかの判定"""
        return detected_language != target_language
    
    def get_localized_prompt(self, language: str, prompt_type: str, **kwargs) -> str:
        """多言語対応プロンプト生成"""
        templates = {
            "disaster_analysis": {
                "ja": """災害関連の質問を分析し、以下の情報をJSON形式で返してください：
- intent_category: {categories}
- confidence: 確信度 (0.0-1.0)
- urgency_level: 緊急度 (1-5)
- needs_location: 位置情報が必要か (true/false)

ユーザー質問: "{user_input}"

JSON:""",
                
                "en": """Analyze this disaster-related question and return information in JSON format:
- intent_category: {categories}
- confidence: confidence level (0.0-1.0)
- urgency_level: urgency level (1-5)
- needs_location: requires location info (true/false)

User question: "{user_input}"

JSON:""",
                
                "zh_CN": """分析这个灾害相关问题，以JSON格式返回信息：
- intent_category: {categories}
- confidence: 置信度 (0.0-1.0)
- urgency_level: 紧急程度 (1-5)
- needs_location: 是否需要位置信息 (true/false)

用户问题: "{user_input}"

JSON:""",
                
                "zh_TW": """分析這個災害相關問題，以JSON格式返回資訊：
- intent_category: {categories}
- confidence: 置信度 (0.0-1.0)
- urgency_level: 緊急程度 (1-5)
- needs_location: 是否需要位置資訊 (true/false)

用戶問題: "{user_input}"

JSON:"""
            },
            
            "response_generation": {
                "ja": """以下の情報を基に、日本語で自然な応答を生成してください：

コンテキスト: {context}
ユーザー質問: {user_input}
検索結果: {search_results}

親しみやすく、分かりやすい日本語で応答してください。""",
                
                "en": """Generate a natural English response based on the following information:

Context: {context}
User question: {user_input}
Search results: {search_results}

Please respond in friendly, clear English.""",
                
                "zh_CN": """基于以下信息生成自然的中文回复：

上下文: {context}
用户问题: {user_input}
搜索结果: {search_results}

请用友好、清晰的中文回复。""",
                
                "zh_TW": """基於以下資訊生成自然的中文回覆：

上下文: {context}
用戶問題: {user_input}
搜尋結果: {search_results}

請用友好、清晰的中文回覆。""",
                
                "it": """Genera una risposta naturale in italiano basata sulle seguenti informazioni:

Contesto: {context}
Domanda dell'utente: {user_input}
Risultati di ricerca: {search_results}

Rispondi in italiano amichevole e chiaro.""",
                
                "ko": """다음 정보를 기반으로 자연스러운 한국어 응답을 생성하세요:

문맥: {context}
사용자 질문: {user_input}
검색 결과: {search_results}

친근하고 명확한 한국어로 응답해주세요.""",
                
                "es": """Genera una respuesta natural en español basada en la siguiente información:

Contexto: {context}
Pregunta del usuario: {user_input}
Resultados de búsqueda: {search_results}

Por favor responde en español amistoso y claro.""",
                
                "fr": """Générez une réponse naturelle en français basée sur les informations suivantes:

Contexte: {context}
Question de l'utilisateur: {user_input}
Résultats de recherche: {search_results}

Veuillez répondre en français amical et clair.""",
                
                "de": """Erstellen Sie eine natürliche deutsche Antwort basierend auf den folgenden Informationen:

Kontext: {context}
Benutzerfrage: {user_input}
Suchergebnisse: {search_results}

Bitte antworten Sie in freundlichem, klarem Deutsch.""",
                
                "pt": """Gere uma resposta natural em português baseada nas seguintes informações:

Contexto: {context}
Pergunta do usuário: {user_input}
Resultados da pesquisa: {search_results}

Por favor, responda em português amigável e claro.""",
                
                "ru": """Создайте естественный ответ на русском языке на основе следующей информации:

Контекст: {context}
Вопрос пользователя: {user_input}
Результаты поиска: {search_results}

Пожалуйста, отвечайте на дружелюбном и понятном русском языке.""",
                
                "ar": """قم بإنشاء رد طبيعي باللغة العربية بناءً على المعلومات التالية:

السياق: {context}
سؤال المستخدم: {user_input}
نتائج البحث: {search_results}

يرجى الرد باللغة العربية الودية والواضحة.""",
                
                "hi": """निम्नलिखित जानकारी के आधार पर एक स्वाभाविक हिंदी प्रतिक्रिया उत्पन्न करें:

संदर्भ: {context}
उपयोगकर्ता प्रश्न: {user_input}
खोज परिणाम: {search_results}

कृपया मैत्रीपूर्ण, स्पष्ट हिंदी में उत्तर दें।""",
                
                "th": """สร้างคำตอบภาษาไทยที่เป็นธรรมชาติจากข้อมูลต่อไปนี้:

บริบท: {context}
คำถามของผู้ใช้: {user_input}
ผลการค้นหา: {search_results}

กรุณาตอบด้วยภาษาไทยที่เป็นมิตรและชัดเจน""",
                
                "vi": """Tạo câu trả lời tự nhiên bằng tiếng Việt dựa trên thông tin sau:

Ngữ cảnh: {context}
Câu hỏi của người dùng: {user_input}
Kết quả tìm kiếm: {search_results}

Vui lòng trả lời bằng tiếng Việt thân thiện và rõ ràng."""
            }
        }
        
        if prompt_type in templates and language in templates[prompt_type]:
            return templates[prompt_type][language].format(**kwargs)
        
        # フォールバック：日本語
        return templates.get(prompt_type, {}).get("ja", "").format(**kwargs)
    
    def get_response_template(self, language: str, template_type: str) -> str:
        """応答テンプレート取得"""
        return self.response_templates.get(language, {}).get(template_type, 
               self.response_templates["ja"].get(template_type, ""))
    
    def clear_cache(self, user_id: str = None):
        """キャッシュクリア"""
        if user_id:
            # 特定ユーザーのキャッシュのみクリア
            keys_to_remove = [k for k in self.language_cache.keys() if k.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del self.language_cache[key]
        else:
            # 全キャッシュクリア
            self.language_cache.clear()
        
        logger.info(f"Language cache cleared for user: {user_id or 'all'}")

# グローバルインスタンス
language_manager = LanguageManager()