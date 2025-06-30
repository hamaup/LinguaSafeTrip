"""
完全応答生成ハンドラー
各ハンドラーで応答生成、カード生成、品質チェックを1回のLLM呼び出しで処理
"""
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import AIMessage
from app.schemas.agent_state import AgentState
from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
# from app.config.timeout_settings import get_llm_timeout  # Not needed for ainvoke_llm

logger = logging.getLogger(__name__)

class CompleteResponseGenerator:
    """完全応答生成クラス"""
    
    @staticmethod
    async def generate_complete_response(
        user_input: str,
        intent: str,
        user_language: str,
        context_data: Dict[str, Any],
        handler_type: str,
        search_results: List[Dict[str, Any]] = None,
        guide_content: List[Dict[str, Any]] = None,
        improvement_feedback: str = "",
        state: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        完全応答生成
        
        統合タスク:
        1. メイン応答生成
        2. サジェスションカード生成（0-3個）
        3. フォローアップ質問生成
        4. 品質自己評価
        5. 緊急度判定
        
        Args:
            user_input: ユーザー入力
            intent: 分類された意図
            user_language: ユーザー言語
            context_data: コンテキストデータ
            handler_type: ハンドラータイプ（disaster/evacuation/guide/safety）
            search_results: 検索結果（オプション）
            guide_content: ガイドコンテンツ（オプション）
            
        Returns:
            完全な応答データ
        """
        
        try:
            # 自動フィードバック取得（明示的に渡されていない場合）
            if not improvement_feedback and state:
                improvement_feedback = state.get('improvement_feedback', '')
                if improvement_feedback:
                    logger.info(f"🔄 Auto-detected improvement feedback: {improvement_feedback}")
            
            # コンテキストデータを整理
            formatted_context = CompleteResponseGenerator._format_context_data(context_data)
            formatted_search = CompleteResponseGenerator._format_search_results(search_results)
            formatted_guides = CompleteResponseGenerator._format_guide_content(guide_content)
            
            # ハンドラー特化プロンプトを構築
            prompt = CompleteResponseGenerator._build_complete_response_prompt(
                user_input=user_input,
                intent=intent,
                user_language=user_language,
                handler_type=handler_type,
                context_data=formatted_context,
                search_results=formatted_search,
                guide_content=formatted_guides,
                improvement_feedback=improvement_feedback
            )
            
            # LLM呼び出し（1回で全て処理）
            response = await ainvoke_llm(
                prompt,
                task_type=f"complete_response_{handler_type}",
                temperature=0.7,
                max_tokens=4096
            )
            
            logger.debug(f"Raw LLM response length for {handler_type}: {len(response)} chars")
            
            # 応答を解析
            result = CompleteResponseGenerator._parse_complete_response(response)
            
            # 後処理
            result = CompleteResponseGenerator._post_process_response(result, intent, handler_type)
            
            response_length = len(result.get('main_response', ''))
            logger.info(f"✅ Complete response generated for {handler_type}: {response_length} chars")
            
            if response_length < 300:
                logger.warning(f"Short response detected for {handler_type}: {result.get('main_response', '')[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Complete response generation failed for {handler_type}: {e}")
            return await CompleteResponseGenerator._create_fallback_response(user_input, intent, user_language)
    
    @staticmethod
    def _format_context_data(context: Dict[str, Any]) -> str:
        """コンテキストデータを整形"""
        if not context:
            return "No additional context available"
        
        formatted_items = []
        
        # GPS required check
        if context.get("gps_required"):
            formatted_items.append("GPS REQUIRED: User needs to enable location services to find nearby shelters")
            formatted_items.append("Action Needed: Prompt user to turn on GPS/location settings")
            if context.get("custom_message"):
                formatted_items.append(f"Message: {context['custom_message']}")
        
        # Location information
        location = context.get("location_info", {})
        if location and isinstance(location, dict):
            lat = location.get("latitude")
            lon = location.get("longitude")
            if lat and lon:
                formatted_items.append(f"User Location: {lat}, {lon}")
                if location.get("address"):
                    formatted_items.append(f"Address: {location['address']}")
        
        # Shelter context
        shelter_ctx = context.get("shelter_context", {})
        if shelter_ctx:
            shelters_found = shelter_ctx.get("shelters_found", 0)
            if shelters_found > 0:
                formatted_items.append(f"Shelters Found: {shelters_found}")
                nearest = shelter_ctx.get("nearest_shelter")
                if nearest:
                    name = nearest.get("name", "Unknown")
                    dist = nearest.get("distance_km", "Unknown")
                    formatted_items.append(f"Nearest Shelter: {name} ({dist}km)")
        
        # 感情コンテキスト
        emotional_state = context.get("emotional_context", {})
        if emotional_state:
            formatted_items.append(f"Emotional state: {emotional_state.get('state', 'neutral')} (intensity: {emotional_state.get('intensity', 1)})")
        
        # 緊急モード
        if context.get("is_emergency_mode"):
            formatted_items.append("Emergency mode: Active")
        
        # 位置情報
        location = context.get("location_info", {})
        if location:
            location_parts = []
            if isinstance(location, dict):
                if location.get("latitude") and location.get("longitude"):
                    location_parts.append(f"Coordinates: {location['latitude']}, {location['longitude']}")
                if location.get("city"):
                    location_parts.append(location["city"])
                if location.get("prefecture"):
                    location_parts.append(location["prefecture"])
            if location_parts:
                formatted_items.append(f"Location: {', '.join(location_parts)}")
            else:
                formatted_items.append(f"Location: {str(location)}")
        
        # 災害コンテキスト
        disaster_context = context.get("disaster_context", {})
        if disaster_context:
            formatted_items.append(f"Disaster context: {json.dumps(disaster_context, ensure_ascii=False)}")
        
        # シェルターコンテキスト
        shelter_context = context.get("shelter_context", {})
        if shelter_context:
            shelters_found = shelter_context.get("shelters_found", 0)
            nearest = shelter_context.get("nearest_shelter")
            if nearest:
                formatted_items.append(f"Shelters found: {shelters_found}, Nearest: {nearest.get('name', 'Unknown')} ({nearest.get('distance_km', 'N/A')}km)")
            else:
                formatted_items.append(f"Shelters found: {shelters_found}")
        
        return "\n".join(formatted_items) if formatted_items else "Standard context"
    
    @staticmethod
    def _format_search_results(results: List[Dict[str, Any]]) -> str:
        """検索結果を整形 - 番号付けせずに自然な形式で提供"""
        if not results:
            return "No search results available"
        
        # 避難所データの場合
        shelter_results = []
        other_results = []
        
        for result in results[:5]:  # Show up to 5 results
            if "name" in result and "latitude" in result:
                # This is shelter data
                name = result.get("name", "Unknown Shelter")
                distance = result.get("distance_km", "Unknown")
                address = result.get("address", "")
                
                shelter_info = f"• {name}"
                if address:
                    shelter_info += f" - Address: {address}"
                    
                shelter_results.append(shelter_info)
            else:
                # Regular search result format
                title = result.get("title", "No title")
                snippet = result.get("snippet", result.get("content", ""))[:200]
                url = result.get("url", "")
                
                result_text = f"• {title}: {snippet}"
                if url:
                    # URLからドメイン名を抽出して短縮表示
                    from urllib.parse import urlparse
                    try:
                        domain = urlparse(url).netloc
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        result_text += f"\n  [{domain}]"
                    except:
                        result_text += "\n  [source]"
                    
                other_results.append(result_text)
        
        # 結果を自然な形式で結合
        formatted_output = []
        if shelter_results:
            formatted_output.append("Available evacuation shelters:")
            formatted_output.extend(shelter_results)
        if other_results:
            if shelter_results:
                formatted_output.append("Additional information:")
            formatted_output.extend(other_results)
        
        return "\n\n".join(formatted_output)
    
    @staticmethod
    def _format_guide_content(guides: List[Dict[str, Any]]) -> str:
        """ガイドコンテンツを整形 - 番号付けせずに自然な形式で提供"""
        if not guides:
            return "No guide content available"
        
        formatted_guides = []
        for guide in guides[:2]:
            title = guide.get("title", "No title")
            content = guide.get("content", "")[:300]
            source = guide.get("source", "")
            
            guide_text = f"• Guide: {title}\n  Content: {content}"
            if source:
                # URLからドメイン名を抽出して短縮表示
                from urllib.parse import urlparse
                try:
                    domain = urlparse(source).netloc
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    guide_text += f"\n  [{domain}]"
                except:
                    guide_text += "\n  [source]"
                
            formatted_guides.append(guide_text)
        
        return "\n\n".join(formatted_guides)
    
    @staticmethod
    def _build_complete_response_prompt(
        user_input: str,
        intent: str,
        user_language: str,
        handler_type: str,
        context_data: str,
        search_results: str,
        guide_content: str,
        improvement_feedback: str = ""
    ) -> str:
        """完全応答プロンプトを構築"""
        
        # ハンドラー特化の指示
        handler_instructions = {
            "disaster": "Focus on current disaster information, safety status, and immediate actions needed.",
            "evacuation": "Prioritize evacuation routes, shelter information, and urgent safety measures. If shelter data is available in search results, provide specific shelter names, distances, and directions.",
            "guide": "Provide practical step-by-step guidance and preparation information.",
            "safety": "Help with safety confirmation messages and emergency communication."
        }
        
        handler_instruction = handler_instructions.get(handler_type, "Provide helpful assistance.")
        
        # カード生成ガイドライン
        card_guidelines = {
            "disaster": ["Latest Updates", "Safety Checklist", "Emergency Contacts"],
            "evacuation": ["Find Shelters", "Evacuation Routes", "What to Bring"],
            "guide": ["Preparation Steps", "Emergency Kit", "Safety Tips"],
            "safety": ["Send Update", "Check Family", "Emergency Info"]
        }
        
        suggested_cards = card_guidelines.get(handler_type, ["Learn More", "Get Help", "Stay Safe"])
        
        # 改善フィードバックがある場合の指示を追加
        feedback_instruction = ""
        if improvement_feedback:
            feedback_instruction = f"""
**IMPROVEMENT FEEDBACK TO ADDRESS:**
{improvement_feedback}

IMPORTANT: Address the above feedback in your response generation. Make sure to incorporate the suggestions and improve upon any identified issues.

"""
        
        return f"""You are LinguaSafeTrip, a disaster prevention assistant. Generate a COMPLETE response package in ONE output.

{feedback_instruction}

**Request Information:**
User Input: "{user_input}"
Intent: {intent}
Handler Type: {handler_type}
Target Language: {user_language}

**Context Information:**
{context_data}

**Available Data:**
Search Results (shelters, news, or other relevant data):
{search_results}
NOTE: For evacuation requests, search results contain nearby shelter locations with names, distances, and coordinates. USE THIS DATA in your response!

Guide Content:
{guide_content}

**DATA REFERENCE RULES:**
- Use the actual information from the data above
- Sources are shown as [domain.com] - use these exact references
- Do NOT invent sources or create your own citations
- Do NOT use numbered references like "search result 1"
- If no source is shown, don't add one

**GENERATE ALL COMPONENTS SIMULTANEOUSLY:**

1. **Main Response** (in {user_language}):
   - {handler_instruction}
   - Address the user's {intent} request directly and completely
   - Include relevant information from available data
   - For evacuation: ALWAYS mention specific shelters if available in search results
   - Be specific and actionable (mention shelter names and distances)
   - CRITICAL: Prioritize essential information:
     * In emergencies: Lead with immediate actions needed
     * Safety instructions must be clear and direct
     * Most important information first, details second
     * Avoid unnecessary elaboration during critical situations
   - For non-emergency queries: Provide thorough educational content
   - Use natural, conversational tone with clear structure
   - Show empathy if emotional context suggests distress
   - Use numbered or bulleted lists when appropriate

2. **Suggestion Cards** (0-3 cards in {user_language}):
   - Create actionable cards that help user continue their journey
   - **CRITICAL**: Each card MUST have a "card_type" field. Available types:
     - "evacuation_info" for shelter/evacuation related cards
     - "preparedness_tip" for general safety tips and checklists
     - "action" for specific action choices or requests
     - "disaster_info" for disaster updates and alerts
   - Suggested types for {handler_type}: {', '.join(suggested_cards)}
   - Required fields for each card:
     * card_type: MUST be one of the types above
     * title: Short title (20 chars max)
     * content: Brief description (40 chars max)
     * action_query: Specific question/action when tapped
   - Make action_query specific and useful
   - Only create cards that add genuine value

3. **Follow-up Questions** (0-2 questions in {user_language}):
   - Natural questions to clarify needs or offer additional help
   - Should be specific to the {intent} context
   - Avoid generic questions

4. **Quality Self-Assessment**:
   - Evaluate if response fully addresses the user's request
   - Check if information is accurate and helpful
   - Determine if any revision is needed
   - Consider completeness and safety

5. **Priority Assessment**:
   - Determine urgency level based on intent and context
   - Consider emotional state and emergency indicators

**IMPORTANT GUIDELINES:**
- Always respond in {user_language} unless specifically asked to translate
- If emotional distress is detected, prioritize reassurance
- For emergency situations, emphasize immediate safety
- If no data is available, provide reasonable general guidance
- CRITICAL: Response strategy based on context:
  * EMERGENCY SITUATIONS: Be concise, clear, and action-focused
    - Lead with the most critical action needed NOW
    - Use simple, direct language
    - Numbered steps for immediate actions
    - Save detailed explanations for later
  * NON-EMERGENCY QUERIES: Provide comprehensive educational content
    - Detailed explanations and background information
    - Multiple examples and scenarios
    - Complete coverage of the topic
    - Proactive tips and recommendations
- Match response depth to urgency - life safety always comes first
- Include relevant information appropriately prioritized
- Ensure all action_query values are specific and actionable

**Return ONLY this JSON structure:**
{{
    "main_response": "Complete response text in {user_language}",
    "suggestion_cards": [
        {{
            "card_type": "evacuation_info|preparedness_tip|action|disaster_info",
            "title": "Card title (20 chars max)",
            "content": "Card description (40 chars max)",
            "action_query": "Specific action when tapped"
        }}
    ],
    "follow_up_questions": ["Question 1 in {user_language}", "Question 2 in {user_language}"],
    "quality_self_check": {{
        "is_complete": true/false,
        "is_accurate": true/false,
        "has_hallucinations": false,
        "needs_revision": false,
        "confidence": 0.0-1.0,
        "revision_reason": "reason if needs_revision is true, else null",
        "hallucination_check": "List any fake references like 'search result X' or placeholders found"
    }},
    "priority_level": "low/normal/high/critical",
    "estimated_satisfaction": 0.0-1.0,
    "processing_notes": "Any important processing observations"
}}"""
    
    @staticmethod
    def _parse_complete_response(response: str) -> Dict[str, Any]:
        """完全応答を解析"""
        try:
            # マークダウンコードブロックを除去
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            
            # JSONをパース
            result = json.loads(json_text.strip())
            
            # 必須フィールドの検証
            required_fields = ['main_response', 'suggestion_cards', 'follow_up_questions', 'quality_self_check']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing required field: {field}")
                    result[field] = CompleteResponseGenerator._get_default_response_value(field)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse complete response JSON: {e}")
            return CompleteResponseGenerator._extract_response_fallback(response)
    
    @staticmethod
    def _extract_response_fallback(response: str) -> Dict[str, Any]:
        """フォールバック: 応答から基本情報を抽出"""
        import re
        
        # メイン応答を抽出
        main_response_match = re.search(r'"main_response":\s*"([^"]+)"', response, re.DOTALL)
        main_response = main_response_match.group(1) if main_response_match else response[:200]
        
        return {
            "main_response": main_response,
            "suggestion_cards": [],
            "follow_up_questions": [],
            "quality_self_check": {
                "is_complete": False,
                "is_accurate": False,
                "needs_revision": True,
                "confidence": 0.3,
                "revision_reason": "JSON parsing failed"
            },
            "priority_level": "normal",
            "estimated_satisfaction": 0.3,
            "processing_notes": "Fallback parsing used due to JSON error"
        }
    
    @staticmethod
    def _get_default_response_value(field: str) -> Any:
        """応答のデフォルト値を取得"""
        defaults = {
            "main_response": "I apologize, but I'm having trouble generating a complete response. Please try again.",
            "suggestion_cards": [],
            "follow_up_questions": [],
            "quality_self_check": {
                "is_complete": False,
                "is_accurate": False,
                "needs_revision": True,
                "confidence": 0.3,
                "revision_reason": "Default value used"
            },
            "priority_level": "normal",
            "estimated_satisfaction": 0.3,
            "processing_notes": "Default value used"
        }
        return defaults.get(field)
    
    @staticmethod
    def _post_process_response(result: Dict[str, Any], intent: str, handler_type: str) -> Dict[str, Any]:
        """応答の後処理"""
        import re
        
        # メイン応答から幻覚的な参照を削除
        main_response = result.get("main_response", "")
        
        # 幻覚パターンを検出・削除
        hallucination_patterns = [
            r'\(search result \d+\)',  # (search result 1)
            r'search result \d+',      # search result 1
            r'検索結果\d+',             # 検索結果4
            r'Search Result \d+',      # Search Result 1
            r'result #\d+',            # result #3
            r'\(result \d+\)',         # (result 1)
            r'（検索結果\d+）',         # （検索結果4）
            r'（search result \d+）',  # （search result 1）
        ]
        
        # 削除されたパターンを記録
        removed_hallucinations = []
        for pattern in hallucination_patterns:
            matches = re.findall(pattern, main_response, flags=re.IGNORECASE)
            if matches:
                removed_hallucinations.extend(matches)
                main_response = re.sub(pattern, '', main_response, flags=re.IGNORECASE)
        
        # プレースホルダーパターンを検出・削除
        placeholder_patterns = [
            r'\[.*?\]',                # [location name], [distance]
            r'【.*?】',                 # 【場所名】
        ]
        
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, main_response)
            if matches:
                removed_hallucinations.extend(matches)
                main_response = re.sub(pattern, '', main_response)
        
        # 基本的なクリーンアップのみ
        main_response = main_response.strip()
        
        result["main_response"] = main_response
        
        # 幻覚が検出された場合は品質チェックを更新
        if removed_hallucinations:
            logger.warning(f"Removed hallucinated references: {removed_hallucinations}")
            quality_check = result.get("quality_self_check", {})
            quality_check["has_hallucinations"] = True
            quality_check["confidence"] = min(0.5, quality_check.get("confidence", 0.7))
            quality_check["hallucination_check"] = f"Removed: {', '.join(removed_hallucinations)}"
            result["quality_self_check"] = quality_check
        
        # 緊急意図の場合は優先度を上げる
        if intent in ["evacuation_support", "safety_confirmation"] or "emergency" in intent.lower():
            result["priority_level"] = "critical"
        
        # カード数の制限とcard_type検証
        cards = result.get("suggestion_cards", [])
        validated_cards = []
        
        for card in cards[:3]:  # 最大3枚に制限
            if isinstance(card, dict):
                # card_typeが欠落している場合、デフォルト値を設定
                if not card.get("card_type"):
                    # ハンドラータイプとカードの内容から適切なcard_typeを推測
                    if handler_type == "evacuation" and "shelter" in card.get("title", "").lower():
                        card["card_type"] = "evacuation_info"
                    elif handler_type == "disaster":
                        card["card_type"] = "disaster_info"
                    elif "checklist" in card.get("title", "").lower() or "preparedness" in card.get("title", "").lower():
                        card["card_type"] = "preparedness_tip"
                    else:
                        card["card_type"] = "action"
                    
                    logger.warning(f"Added missing card_type: {card['card_type']} to card: {card.get('title', 'Unknown')}")
                
                validated_cards.append(card)
        
        result["suggestion_cards"] = validated_cards
        
        # フォローアップ質問の制限
        questions = result.get("follow_up_questions", [])
        if len(questions) > 2:
            result["follow_up_questions"] = questions[:2]
        
        # 品質チェックの調整
        quality_check = result.get("quality_self_check", {})
        if quality_check.get("confidence", 0) < 0.6 and handler_type in ["evacuation", "safety"]:
            # 緊急ハンドラーでは基準を緩和
            quality_check["confidence"] = max(0.6, quality_check.get("confidence", 0))
            quality_check["needs_revision"] = False
        
        return result
    
    @staticmethod
    async def _create_fallback_response(user_input: str, intent: str, user_language: str) -> Dict[str, Any]:
        """フォールバック応答を作成"""
        # 英語でフォールバックメッセージを生成
        fallback_message = "I apologize, but I encountered an issue generating a response. Please try again."
        
        # フォールバック・エラーも翻訳（新フロー）
        if user_language != "en":
            try:
                from app.tools.translation_tool import translation_tool
                logger.info(f"🌐 Fallback translation: EN → {user_language}")
                fallback_message = await translation_tool.translate(
                    text=fallback_message,
                    target_language=user_language,
                    source_language="en"
                )
                logger.info(f"🌐 Fallback translation completed: '{fallback_message[:50]}...'")
            except Exception as e:
                logger.error(f"❌ Fallback translation failed: {e}, using English")
                # 翻訳失敗時は英語のまま
        
        return {
            "main_response": fallback_message,
            "suggestion_cards": [],
            "follow_up_questions": [],
            "quality_self_check": {
                "is_complete": False,
                "is_accurate": False,
                "needs_revision": True,
                "confidence": 0.2,
                "revision_reason": "Response generation failed"
            },
            "priority_level": "normal",
            "estimated_satisfaction": 0.2,
            "processing_notes": "Fallback response due to generation failure"
        }


# 各ハンドラーでの使用例
async def complete_disaster_processor(state: AgentState) -> Dict[str, Any]:
    """災害情報ハンドラー - 完全応答版"""
    try:
        user_input = state.get("user_input", "")
        intent = state.get("primary_intent", "disaster_information")
        user_language = state.get("user_language", "ja")
        
        # 災害データ取得（必要に応じて）
        disaster_data = await get_disaster_data(state)
        
        # 完全応答生成
        response_data = await CompleteResponseGenerator.generate_complete_response(
            user_input=user_input,
            intent=intent,
            user_language=user_language,
            context_data={
                "emotional_context": state.get("emotional_context", {}),
                "location_info": state.get("location_info", {}),
                "is_emergency_mode": state.get("is_emergency_mode", False),
                "disaster_context": disaster_data
            },
            handler_type="disaster",
            search_results=disaster_data.get("search_results", [])
        )
        
        # メッセージ構築
        message = AIMessage(
            content=response_data["main_response"],
            additional_kwargs={
                "cards": response_data["suggestion_cards"],
                "follow_up_questions": response_data["follow_up_questions"],
                "priority": response_data["priority_level"],
                "handler_type": "disaster"
            }
        )
        
        return {
            "messages": [message],
            "final_response_text": response_data["main_response"],
            "quality_self_check": response_data["quality_self_check"],
            "handler_completed": True
        }
        
    except Exception as e:
        logger.error(f"Complete disaster processor failed: {e}")
        return {"error": str(e)}


async def complete_evacuation_processor(state: AgentState) -> Dict[str, Any]:
    """避難支援ハンドラー - 完全応答版"""
    try:
        user_input = state.get("user_input", "")
        intent = state.get("primary_intent", "evacuation_support")
        user_language = state.get("user_language", "ja")
        
        # 避難所データ取得
        shelter_data = await get_shelter_data(state)
        
        # 位置情報を取得（user_locationフィールドを確認）
        location_info = state.get("location_info") or state.get("user_location", {})
        
        # 完全応答生成
        response_data = await CompleteResponseGenerator.generate_complete_response(
            user_input=user_input,
            intent=intent,
            user_language=user_language,
            context_data={
                "emotional_context": state.get("emotional_context", {}),
                "location_info": location_info,
                "is_emergency_mode": state.get("is_emergency_mode", False),
                "shelter_context": {
                    "shelters_found": len(shelter_data.get("nearby_shelters", [])),
                    "nearest_shelter": shelter_data.get("nearby_shelters", [None])[0] if shelter_data.get("nearby_shelters") else None,
                    "all_shelters": shelter_data.get("nearby_shelters", [])
                }
            },
            handler_type="evacuation",
            search_results=shelter_data.get("nearby_shelters", [])
        )
        
        # 緊急度が高い場合の特別処理
        if response_data["priority_level"] == "critical":
            logger.warning("Critical evacuation request detected")
        
        # メッセージ構築
        message = AIMessage(
            content=response_data["main_response"],
            additional_kwargs={
                "cards": response_data["suggestion_cards"],
                "follow_up_questions": response_data["follow_up_questions"],
                "priority": response_data["priority_level"],
                "handler_type": "evacuation",
                "is_emergency": response_data["priority_level"] == "critical"
            }
        )
        
        return {
            "messages": [message],
            "final_response_text": response_data["main_response"],
            "quality_self_check": response_data["quality_self_check"],
            "handler_completed": True,
            "is_emergency_response": response_data["priority_level"] == "critical"
        }
        
    except Exception as e:
        logger.error(f"Complete evacuation processor failed: {e}")
        return {"error": str(e)}


# ヘルパー関数（例）
async def get_disaster_data(state: AgentState) -> Dict[str, Any]:
    """災害データを取得"""
    # 実際の災害データ取得ロジック
    return {
        "current_alerts": [],
        "search_results": [],
        "severity": "normal"
    }

async def get_shelter_data(state: AgentState) -> Dict[str, Any]:
    """避難所データを取得"""
    # Get shelter data from state if available
    shelter_context = state.get("shelter_context", {})
    nearby_shelters = shelter_context.get("nearby_shelters", [])
    
    # If no shelter context, check for search results
    if not nearby_shelters:
        search_results = state.get("search_results", [])
        if search_results and isinstance(search_results[0], dict) and "name" in search_results[0]:
            nearby_shelters = search_results
    
    return {
        "nearby_shelters": nearby_shelters,
        "capacity_info": shelter_context.get("capacity_info", {}),
        "routes": shelter_context.get("routes", [])
    }