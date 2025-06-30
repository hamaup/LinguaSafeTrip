"""
災害関連処理の統合最適化
複数のLLM呼び出しを1回にまとめて効率化
"""

import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from .language_manager import language_manager

logger = logging.getLogger(__name__)

class IntegratedDisasterAnalysis(BaseModel):
    """統合災害分析結果"""
    intent_category: str = Field(..., description="災害関連インテント")
    confidence: float = Field(..., description="確信度 0.0-1.0")
    urgency_level: int = Field(..., description="緊急度 1-5")
    needs_location: bool = Field(..., description="位置情報が必要か")
    user_situation: str = Field(..., description="ユーザーの状況分析")
    recommended_action: str = Field(..., description="推奨アクション")
    response_type: str = Field(..., description="応答タイプ")
    search_keywords: List[str] = Field(default=[], description="検索キーワード")

class DisasterProcessingOptimizer:
    """災害関連処理の統合最適化クラス"""
    
    def __init__(self):
        # LLMによる自然な分類のため、カテゴリを柔軟に設定
        self.disaster_domains = [
            "hazard_map_request",     # ハザードマップ要求
            "shelter_search",         # 避難所検索
            "evacuation_guidance",    # 避難指示・ガイダンス
            "earthquake_info",        # 地震情報
            "tsunami_info",           # 津波情報
            "weather_disaster",       # 気象災害（台風、豪雨等）
            "disaster_news",          # 災害ニュース
            "safety_confirmation",    # 安否確認
            "emergency_contact",      # 緊急連絡
            "disaster_preparation",   # 災害準備・備蓄
            "disaster_guide_request", # 防災ガイド要求
            "risk_assessment",        # リスク評価・確認
            "general_disaster_info"   # その他災害関連情報
        ]
    
    async def integrated_disaster_analysis(
        self, 
        user_input: str, 
        user_language: str,
        user_location: Optional[Dict] = None,
        chat_history: List = None,
        llm_client = None
    ) -> Tuple[IntegratedDisasterAnalysis, str]:
        """
        統合災害分析 - 1回のLLM呼び出しで複数の分析を実行
        Returns: (分析結果, 検出言語)
        """
        if not llm_client:
            raise ValueError("LLM client is required")
        
        # 1. アプリの設定言語を使用（言語検出は不要）
        detected_language = user_language  # アプリの指定言語を使用
        
        # 2. 統合分析プロンプト生成
        analysis_prompt = self._build_integrated_analysis_prompt(
            user_input, detected_language, user_location, chat_history
        )
        
        logger.info(f"🔄 Executing integrated disaster analysis for: '{user_input[:50]}...'")
        
        try:
            # 3. 1回のLLM呼び出しで全分析を実行
            response = await llm_client.ainvoke([HumanMessage(content=analysis_prompt)])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # 4. JSON解析
            analysis_result = self._parse_analysis_response(response_text)
            
            return analysis_result, detected_language
            
        except Exception as e:
            logger.error(f"Integrated disaster analysis failed: {e}")
            
            # フォールバック：シンプル分析
            fallback_result = self._create_fallback_analysis(user_input)
            return fallback_result, detected_language
    
    def _build_integrated_analysis_prompt(
        self, 
        user_input: str, 
        language: str,
        user_location: Optional[Dict] = None,
        chat_history: List = None
    ) -> str:
        """統合分析プロンプト構築"""
        
        # 位置情報の文字列化
        location_str = ""
        if user_location:
            location_str = f"緯度: {user_location.get('latitude', 'N/A')}, 経度: {user_location.get('longitude', 'N/A')}"
        
        # 履歴の文字列化
        history_str = ""
        if chat_history and len(chat_history) > 0:
            recent_messages = chat_history[-3:] if len(chat_history) > 3 else chat_history
            history_str = "\\n".join([f"- {msg}" for msg in recent_messages])
        
        # 内部処理は常に英語で実行
        prompt = f"""CRITICAL: Comprehensively analyze this disaster-related question and determine the appropriate response approach.

【User Question】: "{user_input}"
【User Language】: {language}
【Location Info】: {location_str or "None"}
【Recent History】: {history_str or "None"}

IMPORTANT: Look at EACH character and word carefully. Do NOT confuse different disaster types.
津波 = tsunami, 地震 = earthquake, 台風 = typhoon

Understand the user's true intent deeply and analyze:

**Detailed Analysis Points**:
- "What disasters happen in Japan?" "What is earthquake?" → educational_explanation
- "What can LinguaSafeTrip do?" "LinguaSafeTrip features" "main functions" → function_demonstration
- "Am I safe now?" "How is the situation?" "大丈夫？" "安全？" → safety_status_check
- "Show hazard map" "Check risks" → hazard_map_request
- "Find shelters" "Where are nearby shelters?" → shelter_search
- "Latest earthquake info" "Disaster news" "台風情報" "津波情報" → disaster_news
- "What to prepare?" "Emergency kit?" → disaster_preparation
- "How to stay safe?" "Safety guide" → disaster_guide_request
- "Help!" "Emergency!" → emergency_contact
- "台風の最新情報" "台風は来る？" → typhoon disaster_news (NOT earthquake)
- "津波は大丈夫？" "海で安全？" → tsunami disaster_news (NOT evacuation)
- "地震の情報" "地震は大丈夫？" → earthquake disaster_news (NOT typhoon)

**Critical Disambiguation for Coastal/Tsunami Queries**:
- "Is tsunami safe?" "津波は大丈夫？" "Will tsunami come?" "津波来る？" → disaster_news (NOT shelter_search)
- "Near the sea, is tsunami OK?" "海の近くで津波は大丈夫？" "海辺で津波大丈夫？" → disaster_news (safety check)
- "Where to evacuate from tsunami?" "津波からどこに避難？" "津波の避難場所" → shelter_search
- Questions about current safety status → disaster_news first
- Safety confirmation queries ("大丈夫", "安全", "safe") → disaster_news, NOT evacuation_support

**User Situation Detailed Analysis**:
- Beginner: Seeking basic disaster knowledge
- Learner: Wants systematic disaster education
- Preparer: Considering specific preparations/measures
- Worried: Feeling anxiety/fear, seeking reassurance
- Checker: Wants to know current situation/risks
- Emergency: Facing imminent danger

CRITICAL RULES:
1. If the user asks about LinguaSafeTrip (e.g., "LinguaSafeTripは何ができますか", "What can LinguaSafeTrip do", "LinguaSafeTrip features"), you MUST:
   - Set intent_category as "disaster_guide_request"
   - Set response_type as "function_demonstration"
   - Set confidence as 0.95 or higher
2. This is NOT an off-topic question - LinguaSafeTrip function explanation is a core disaster-related query.

Return the following in JSON format:

1. intent_category - Select the most appropriate category:
   {', '.join(self.disaster_domains)}

2. confidence - Confidence level (0.0-1.0)

3. urgency_level - Urgency level (1-5):
   1: Information/learning purpose (disaster basics, app features, etc.)
   2: Preparedness/planning (emergency kit, evacuation plan, etc.)
   3: Specific measures (local risk check, shelter research, etc.)
   4: Imminent situation (alerts active, high anxiety, etc.)
   5: Life-threatening emergency (disaster occurring, dangerous situation, etc.)

4. needs_location - Requires location information (true/false)

5. user_situation - Current user situation/context (within 50 characters)
   Examples: "Beginner wanting to learn about disasters", "Seeking local risk info", "Emergency requiring immediate help"

6. recommended_action - Optimal response action (specific)

7. response_type - Response type:
   - educational_explanation: Educational explanation (disaster knowledge, basics)
   - function_demonstration: Feature explanation/demonstration
   - safety_status_check: Safety status check/current report
   - hazard_map_display: Hazard map/risk information display
   - shelter_search: Shelter search/guidance
   - information_lookup: Disaster information search/news
   - guide_provision: Guide/procedure provision
   - emergency_response: Emergency response/immediate instructions
   - direct_answer: Direct answer

8. search_keywords - Search keywords (array format, max 5)

**Important Judgment Criteria**:
- "How to" "What should I do" "How can I prepare" → educational_explanation
- "What can LinguaSafeTrip do" "Tell me about LinguaSafeTrip" "LinguaSafeTrip features" → function_demonstration
- "Am I safe" "Is it safe now" "Current safety status" → safety_status_check
- "Show map" "Hazard map" "Risk areas" → hazard_map_display
- "Shelter" "Evacuation center" "Where to evacuate" → shelter_search
- "Latest news" "Current disaster" "What happened" → information_lookup
- "How to stay safe" "Safety tips" "Protection methods" → guide_provision

Respond in JSON format only:"""

        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> IntegratedDisasterAnalysis:
        """分析レスポンスの解析"""
        try:
            # JSONブロックを抽出
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # Pydanticモデルに変換
                return IntegratedDisasterAnalysis(**data)
            else:
                logger.warning("No JSON found in analysis response")
                return self._create_fallback_analysis("No valid JSON response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return self._create_fallback_analysis("JSON parsing failed")
    
    def _create_fallback_analysis(self, user_input: str) -> IntegratedDisasterAnalysis:
        """フォールバック分析結果の作成"""
        return IntegratedDisasterAnalysis(
            intent_category="general_disaster",
            confidence=0.5,
            urgency_level=2,
            needs_location=True,
            user_situation="Analysis failed, providing general assistance",
            recommended_action="provide_general_disaster_information",
            response_type="direct_answer",
            search_keywords=["disaster", "safety", "information"]
        )
    
    async def generate_optimized_response(
        self,
        analysis: IntegratedDisasterAnalysis,
        detected_language: str,
        search_results: Optional[Dict] = None,
        guide_content: Optional[str] = None,
        llm_client = None
    ) -> str:
        """最適化された応答生成 - 1回のLLM呼び出しで最終応答を生成"""
        
        if not llm_client:
            return self._create_template_response(analysis, detected_language)
        
        # 応答生成プロンプト構築（response_typeに基づく）
        response_prompt = self._build_response_prompt(analysis, detected_language, search_results, guide_content)
        
        try:
            response = await llm_client.ainvoke([HumanMessage(content=response_prompt)])
            generated_text = response.content if hasattr(response, 'content') else str(response)
            # Optimized response generated successfully
            return generated_text
        except Exception as e:
            logger.error(f"Optimized response generation failed: {e}")
            # キャッシュされたテンプレート応答を使用
            return self._create_template_response(analysis, detected_language)
    
    def _build_response_prompt(
        self,
        analysis: IntegratedDisasterAnalysis,
        language: str,
        search_results: Optional[Dict] = None,
        guide_content: Optional[str] = None
    ) -> str:
        """response_typeに基づいた応答生成プロンプトを構築"""
        
        # 基本情報
        # analysisが辞書の場合とオブジェクトの場合の両方に対応
        if isinstance(analysis, dict):
            intent_category = analysis.get('intent_category', 'unknown')
            response_type = analysis.get('response_type', 'direct_answer')
            user_situation = analysis.get('user_situation', 'Unknown situation')
            urgency_level = analysis.get('urgency_level', 1)
            recommended_action = analysis.get('recommended_action', 'Provide general assistance')
        else:
            intent_category = analysis.intent_category
            response_type = analysis.response_type
            user_situation = analysis.user_situation
            urgency_level = analysis.urgency_level
            recommended_action = analysis.recommended_action
        
        base_context = f"""
Intent: {intent_category}
Response Type: {response_type}
User Situation: {user_situation}
Urgency Level: {urgency_level}
Recommended Action: {recommended_action}
"""
        
        # 追加コンテンツ
        additional_content = ""
        if search_results:
            additional_content += f"\\nSearch Results: {str(search_results)}"
        if guide_content:
            additional_content += f"\\nGuide Content: {guide_content}"
        
        # 言語別の指示を追加
        language_instruction = self._get_language_instruction(language)
        
        # 内部処理は常に英語で実行（応答は最終的にユーザー言語に翻訳される）
        if response_type == "educational_explanation":
            return f"""{base_context}

The user is seeking educational explanation about disasters. Generate response following these guidelines:

**Response Guidelines**:
- Use clear, beginner-friendly language
- Include specific examples and statistics
- Focus on Japan's disaster characteristics
- Provide engaging, educational content
- Guide towards next steps (preparation/countermeasures)

**Required Content**: Disaster basics, Japan's disaster features, statistics, historical cases, etc.

{additional_content}

{language_instruction}

Generate an educational and valuable response in natural, friendly tone:"""
        
        elif response_type == "function_demonstration":
            return f"""{base_context}

The user wants to know about LinguaSafeTrip's functions. Generate response following these guidelines:

**Response Guidelines**:
- Explain LinguaSafeTrip's main features specifically
- Include usage examples and scenarios
- Suggest trying features interactively
- Emphasize feature value and convenience
- Encourage gradual feature discovery

**Main Features**: Disaster information, shelter search, preparation guides, real-time alerts, multilingual support, etc.

{additional_content}

{language_instruction}

Generate an engaging explanation of LinguaSafeTrip's features and encourage actual usage:"""
        
        elif response_type == "safety_status_check":
            return f"""{base_context}

The user wants to check current safety status. Generate response following these guidelines:

**Response Guidelines**:
- Check current disaster information and alert status
- Provide location-specific information if available
- Balance reassurance with continuous caution
- Give specific safety advice
- Explain what to do if situations change

{additional_content}

{language_instruction}

Generate an appropriate safety status assessment with balanced reassurance and caution:"""
        
        else:
            # Default for other response types
            return f"""{base_context}

Generate an appropriate response based on the user's situation and intent.

**Response Guidelines**:
- Understand user's intent and situation
- Provide specific and practical information
- Use appropriate tone and detail level
- Guide towards next helpful actions

{additional_content}

{language_instruction}

Generate a valuable and appropriate response for the user:"""
    
    def _create_template_response(self, analysis: IntegratedDisasterAnalysis, language: str) -> str:
        """テンプレートベース応答作成"""
        # 言語別のテンプレート応答
        templates = {
            "earthquake_info": {
                "ja": "地震の後は以下の行動を心がけてください：\n\n• **安全確認**: 自分と周囲の人の怪我がないか確認\n• **火の始末**: ガスの元栓を閉め、電気のブレーカーを落とす\n• **避難判断**: 建物の損傷状況を確認し、危険な場合は避難\n• **情報収集**: ラジオやスマートフォンで最新情報を確認\n• **連絡**: 家族や知人の安否確認を行う\n\n状況に応じて、適切な行動を取ってください。",
                "en": "After an earthquake, please follow these steps:\n\n• **Safety Check**: Check for injuries to yourself and others\n• **Fire Prevention**: Turn off gas and electricity\n• **Evacuation Decision**: Check building damage and evacuate if dangerous\n• **Information**: Get updates from radio or smartphone\n• **Communication**: Confirm safety of family and friends\n\nTake appropriate action based on your situation.",
                "zh": "地震后请采取以下行动：\n\n• **安全检查**：检查自己和周围人的伤情\n• **防火措施**：关闭煤气和电源\n• **疏散决定**：检查建筑物损坏情况，如有危险请撤离\n• **信息收集**：通过收音机或智能手机获取最新信息\n• **联系**：确认家人和朋友的安全\n\n请根据情况采取适当行动。"
            },
            "tsunami_info": {
                "ja": "津波警報・注意報が発令された場合：\n\n• **即座に高台へ**: 海岸から離れ、高い場所へ避難\n• **車は使わない**: 渋滞を避けるため徒歩で避難\n• **川から離れる**: 津波は川を遡上します\n• **情報収集**: 防災無線やラジオで最新情報を確認\n• **戻らない**: 警報解除まで安全な場所に留まる\n\n命を最優先に行動してください。",
                "en": "When tsunami warnings are issued:\n\n• **Move to High Ground**: Leave coastal areas immediately\n• **Don't Use Cars**: Evacuate on foot to avoid traffic\n• **Stay Away from Rivers**: Tsunamis can travel up rivers\n• **Get Information**: Monitor emergency broadcasts\n• **Don't Return**: Stay safe until warnings are lifted\n\nPrioritize your life above all else.",
                "zh": "海啸警报发布时：\n\n• **立即前往高地**：远离海岸，撤离到高处\n• **不要使用汽车**：步行撤离以避免交通堵塞\n• **远离河流**：海啸会沿河上溯\n• **收集信息**：监听紧急广播\n• **不要返回**：在警报解除前留在安全地点\n\n生命安全最重要。"
            },
            "landslide_info": {
                "ja": "土砂災害に関する重要な情報です：\n\n• **前兆現象に注意**: 小石が落ちる、地鳴り、異常な匂い、湧水の変化\n• **避難のタイミング**: 前兆を感じたら直ちに避難\n• **避難方向**: 崖や急傾斜地から離れ、谷筋を避ける\n• **安全な場所**: 高台や頑丈な建物の2階以上\n• **情報収集**: 土砂災害警戒情報に注意\n\n雨が止んでも土砂災害は発生する可能性があります。十分ご注意ください。",
                "en": "Important information about landslides:\n\n• **Warning signs**: Falling pebbles, ground rumbling, unusual smells, changes in spring water\n• **Evacuation timing**: Evacuate immediately when you notice warning signs\n• **Evacuation direction**: Move away from cliffs and steep slopes, avoid valleys\n• **Safe locations**: Higher ground or upper floors of sturdy buildings\n• **Information**: Monitor landslide warnings\n\nLandslides can occur even after rain stops. Please remain vigilant.",
                "zh": "关于泥石流的重要信息：\n\n• **前兆现象**：小石块掉落、地鸣、异常气味、泉水变化\n• **撤离时机**：发现前兆立即撤离\n• **撤离方向**：远离悬崖和陡坡，避开山谷\n• **安全地点**：高地或坚固建筑的二楼以上\n• **信息收集**：关注泥石流预警信息\n\n即使雨停后也可能发生泥石流。请保持警惕。"
            },
            "general_disaster": {
                "ja": "災害に関する情報をお探しですね。具体的にどのような情報が必要でしょうか？\n\n私がお手伝いできること：\n• 最新の災害情報の提供\n• 避難所の検索\n• 防災準備のアドバイス\n• 緊急時の行動指針\n\n詳しい状況をお教えいただければ、より適切な情報を提供できます。",
                "en": "I understand you're looking for disaster information. What specific information do you need?\n\nI can help with:\n• Latest disaster updates\n• Finding evacuation shelters\n• Disaster preparedness advice\n• Emergency action guidelines\n\nPlease tell me more about your situation for better assistance.",
                "zh": "您正在寻找灾害信息。您需要什么具体信息？\n\n我可以帮助您：\n• 提供最新灾害信息\n• 搜索避难所\n• 防灾准备建议\n• 紧急行动指南\n\n请告诉我更多情况，以便提供更好的帮助。"
            }
        }
        
        # カテゴリに基づいてテンプレートを選択
        # analysisが辞書の場合とオブジェクトの場合の両方に対応
        if isinstance(analysis, dict):
            category_key = analysis.get('intent_category', 'general_disaster')
        else:
            category_key = analysis.intent_category
        if "earthquake" in category_key:
            category_key = "earthquake_info"
        elif "tsunami" in category_key:
            category_key = "tsunami_info"
        elif "landslide" in category_key:
            category_key = "landslide_info"
        
        # テンプレートを取得（見つからない場合は汎用テンプレート）
        category_templates = templates.get(category_key, templates["general_disaster"])
        return category_templates.get(language, category_templates.get("ja", "災害情報をお探しですね。どのような情報が必要でしょうか？"))
    
    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction for response generation"""
        language_names = {
            'ja': 'Japanese',
            'en': 'English',
            'ko': 'Korean',
            'zh': 'Chinese',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian'
        }
        
        target_language = language_names.get(language, 'Japanese')
        
        return f"""
IMPORTANT: Generate the ENTIRE response in {target_language} language.
Do NOT generate in English and expect translation later.
The response MUST be naturally written in {target_language} from the beginning.
"""

# グローバルインスタンス
disaster_optimizer = DisasterProcessingOptimizer()