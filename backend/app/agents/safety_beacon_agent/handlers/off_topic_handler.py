"""
Improved Off-Topic Handler with LLM-based natural language processing
- LLM-based language detection instead of keyword-based
- Natural language intent classification
- Context-aware response generation
"""

import logging
import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.schemas.agent import AgentState, DisasterIntentSchema
from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
from langchain_core.language_models.chat_models import BaseChatModel
from app.prompts.intent_prompts import OFF_TOPIC_HANDLER_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

class ImprovedOffTopicHandler:
    """LLMベースの自然言語処理を使用した改善されたオフトピックハンドラー"""

    def __init__(self):
        # 言語制限を撤廃 - 動的言語サポート
        self.supported_languages = [
            {"code": "ja", "name": "Japanese", "native": "日本語"},
            {"code": "en", "name": "English", "native": "English"},
            {"code": "zh", "name": "Chinese", "native": "中文"},
            {"code": "ko", "name": "Korean", "native": "한국어"},
            {"code": "es", "name": "Spanish", "native": "Español"},
            {"code": "fr", "name": "French", "native": "Français"},
            {"code": "de", "name": "German", "native": "Deutsch"},
            {"code": "it", "name": "Italian", "native": "Italiano"},
            {"code": "pt", "name": "Portuguese", "native": "Português"},
            {"code": "ru", "name": "Russian", "native": "Русский"},
            {"code": "ar", "name": "Arabic", "native": "العربية"},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
            {"code": "th", "name": "Thai", "native": "ไทย"},
            {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt"}
        ]


    async def _translate_to_english(self, text: str, source_language: str) -> str:
        """Helper method for parallel translation to English"""
        try:
            from app.tools.translation_tool import translate_text

            translation_result = await translate_text(
                text=text,
                target_language="en",
                source_language=source_language,
                llm_provider="gemini"
            )

            if translation_result and translation_result.translated_text:
                return translation_result.translated_text
            else:
                logger.warning(f"Translation from {source_language} failed, using original text")
                return text

        except Exception as e:
            logger.error(f"Translation error: {e}, using original text")
            return text

    async def _classify_intent_with_llm(self, user_input: str, context: Dict[str, Any]) -> DisasterIntentSchema:
        """LLMを使用して意図分類を自然言語で実行 - 多言語対応"""
        if not user_input.strip():
            from app.schemas.common.enums import IntentCategory
            return DisasterIntentSchema(
                is_disaster_related=False,
                primary_intent=IntentCategory.UNKNOWN,
                confidence=0.9,
                reasoning="Empty or whitespace-only input"
            )

        try:
            # 完全にLLMベースの自然言語分類 - CLAUDE.md準拠
            classification_prompt = OFF_TOPIC_HANDLER_CLASSIFICATION_PROMPT.format(
                user_input=user_input
            )

            # Add timeout for LLM call to prevent hanging
            import asyncio

            response_text = await asyncio.wait_for(
                ainvoke_llm(classification_prompt, task_type="intent_classification", temperature=0.3),
                timeout=60.0  # 60 second timeout
            )

            # JSONを抽出して解析
            json_match = re.search(r'\{[^}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                # 災害関連カテゴリの定義
                disaster_related_categories = {
                    'disaster_information',
                    'evacuation_support',
                    'safety_confirmation',
                    'disaster_preparation',
                    'emergency_help',
                    'information_request'
                }

                primary_intent = data.get('primary_intent', 'unknown')
                is_disaster_related = primary_intent in disaster_related_categories

                from app.schemas.common.enums import IntentCategory

                # Convert string to enum
                try:
                    intent_enum = IntentCategory(primary_intent)
                except ValueError:
                    intent_enum = IntentCategory.UNKNOWN

                result = DisasterIntentSchema(
                    is_disaster_related=is_disaster_related,
                    primary_intent=intent_enum,
                    confidence=float(data.get('confidence', 0.5)),
                    reasoning=data.get('reasoning', 'LLM classification')
                )

                logger.info(f"Intent classified: {result.primary_intent} (confidence: {result.confidence:.2f})")
                return result
            else:
                logger.warning("Could not parse LLM intent classification response")
                from app.schemas.common.enums import IntentCategory
                return DisasterIntentSchema(
                    is_disaster_related=False,
                    primary_intent=IntentCategory.UNKNOWN,
                    confidence=0.3,
                    reasoning="Failed to parse LLM response"
                )

        except asyncio.TimeoutError:
            logger.warning("Intent classification timed out, using fallback")
            from app.schemas.common.enums import IntentCategory
            return DisasterIntentSchema(
                is_disaster_related=False,
                primary_intent=IntentCategory.UNKNOWN,
                confidence=0.2,
                reasoning="Classification timed out"
            )
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            from app.schemas.common.enums import IntentCategory
            return DisasterIntentSchema(
                is_disaster_related=False,
                primary_intent=IntentCategory.UNKNOWN,
                confidence=0.1,
                reasoning=f"Classification error: {str(e)}"
            )

    async def _generate_natural_response(self, user_input: str, language_code: str, intent: DisasterIntentSchema, context: Dict[str, Any]) -> str:
        """検出された言語と意図に基づいて自然な応答を生成"""
        try:
            # 言語情報を取得（動的フォールバック）
            language_info = next((lang for lang in self.supported_languages if lang["code"] == language_code), None)
            if not language_info:
                # サポートリストにない言語の場合は動的に生成
                language_info = {"code": language_code, "name": language_code.title(), "native": language_code.title()}

            # コンテキスト応答の設定
            context_info = ""
            if context.get('is_disaster_mode'):
                context_info = "Note: The system is currently in disaster mode - prioritize safety information."

            response_prompt = f"""You are LinguaSafeTrip, a compassionate and caring disaster prevention assistant.
Your core principle is to respond with genuine empathy, understanding, and care for the user's well-being.
Always make users feel heard, valued, and supported, especially during stressful or uncertain times.

User input: "{user_input}"
Target response language: {language_info["name"]} ({language_info["native"]})
Intent classification: {intent.primary_intent}
Is disaster-related: {intent.is_disaster_related}
Confidence: {intent.confidence:.2f}

{context_info}

Important Instructions:
1. Generate response in English (will be translated by response_generator)
2. Do not mix languages
3. Be natural, friendly, and conversational with genuine warmth
4. Show empathy and understanding in your responses
5. Prioritize the user's emotional well-being alongside practical information

Intent-based Response Guidelines:

For greetings/small talk:
- Respond naturally to greetings and conversation
- Introduce yourself as LinguaSafeTrip
- Offer help with disaster-related topics
- Example: "Hello! I'm LinguaSafeTrip, your disaster prevention assistant. Is there anything related to disasters I can help you with?"

For disaster-related (non-emergency):
- Acknowledge the question
- Provide useful information
- Offer additional resources

For off-topic (weather, cooking, health, finance, entertainment, etc.):
- Do NOT provide the requested content (e.g., weather forecasts, recipes, medical advice, investment tips)
- Politely explain it's outside your expertise
- Clearly state LinguaSafeTrip's specialization (disasters/disaster prevention)
- Guide towards related disaster topics

For finance/investment:
- Example: "I apologize, but I'm a disaster prevention specialist. I cannot provide financial or investment advice. However, I can help with disaster insurance or investing in disaster preparedness."

For inappropriate content:
- Example: "I apologize, but I cannot answer such questions. Is there anything related to disaster prevention I can help you with?"

For general weather:
- Example: "I apologize, but I specialize in disaster prevention. For general weather forecasts, please check your local meteorological agency. However, I can help with severe weather information like typhoons or heavy rain warnings."

Generate a natural, conversational response in English (translation will be handled by response_generator):"""

            # Add timeout for LLM call to prevent hanging
            response_text = await asyncio.wait_for(
                ainvoke_llm(response_prompt, task_type="response_generation", temperature=0.7),
                timeout=60.0  # 60 second timeout for response generation
            )

            logger.info(f"Response generated in {language_code}")
            return response_text.strip()

        except asyncio.TimeoutError:
            logger.warning("Response generation timed out, using quick fallback")
            # タイムアウト時のフォールバック（内部処理は英語）
            return "I'm LinguaSafeTrip. I can help with disaster prevention."
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # エラー時のフォールバック（内部処理は英語）
            return "I apologize for the error. I'm LinguaSafeTrip, and I can help with disaster and safety information."

    def _safe_get_state_value(self, state: Dict[str, Any], key: str, default: Any = None) -> Any:
        """stateから値を安全に取得"""
        if isinstance(state, dict):
            return state.get(key, default)
        return getattr(state, key, default)

    def _safe_get_messages(self, state: Dict[str, Any]) -> List:
        """stateからchat_historyを安全に取得"""
        chat_history = self._safe_get_state_value(state, "chat_history", [])
        return chat_history if isinstance(chat_history, list) else []

    async def handle(self, state: AgentState) -> Dict[str, Any]:
        """改善されたオフトピックハンドラーのメイン処理"""
        try:
            # Trace execution
            from ..core.graph_tracer import get_tracer
            session_id = self._safe_get_state_value(state, 'session_id', 'unknown')
            tracer = get_tracer(session_id)
            tracer.enter_node('improved_off_topic_handler')

            # ユーザー入力を取得
            user_input = self._safe_get_state_value(state, "user_input", "")
            current_input = self._safe_get_state_value(state, "current_user_input", user_input)
            messages = self._safe_get_messages(state)

            # 優先順位: current_user_input > user_input > 最後のメッセージ
            last_message_content = current_input if current_input else user_input
            if not last_message_content and messages:
                last_message = messages[-1]
                if isinstance(last_message, (HumanMessage, AIMessage)):
                    last_message_content = getattr(last_message, 'content', '')
                elif isinstance(last_message, tuple) and len(last_message) >= 2:
                    last_message_content = last_message[1]  # (role, content) tuple

            # Ensure we have a string
            last_message_content = str(last_message_content) if last_message_content else ""

            if not last_message_content or not last_message_content.strip():
                logger.warning("Empty input detected")
                # IMPORTANT: Preserve intermediate_results even for empty input
                existing_intermediate_results = self._safe_get_state_value(state, 'intermediate_results', {})

                # Return to response generator with proper fallback state
                return {
                    "last_askuser_reason": "空の入力を受信",
                    "turn_count": self._safe_get_state_value(state, 'turn_count', 0) + 1,
                    "requires_professional_handling": False,
                    "current_task_type": "invalid_input",
                    "primary_intent": "unknown",
                    "intent_confidence": 0.3,
                    "is_disaster_related": False,
                    "routing_decision": {"next": "response_synthesizer"},
                    "off_topic_response": "I'm sorry, but the input was empty. Is there anything I can help you with?",
                    # CRITICAL: Preserve intermediate_results to avoid fallback errors
                    "intermediate_results": existing_intermediate_results,
                    "user_input": last_message_content or "",
                    "current_user_input": last_message_content or ""
                }

            logger.info(f"🔴 NODE ENTRY: initial_analyzer")
            logger.info(f"🔴 NODE INPUT: user_input='{last_message_content}'")
            logger.info(f"🔴 NODE INPUT: turn_count={self._safe_get_state_value(state, 'turn_count', 0)}")
            logger.info(f"🔴 NODE INPUT: session_id={session_id}")
            logger.info(f"📝 Processing input: '{last_message_content}'")

            # 新しいアーキテクチャ: 意図分類後に英語翻訳
            # ステップ1: LLMで意図分類（多言語のまま処理）
            context = {
                'is_disaster_mode': self._safe_get_state_value(state, 'is_disaster_mode', False),
                'user_location': self._safe_get_state_value(state, 'user_location', {}),
                'external_alerts': self._safe_get_state_value(state, 'external_alerts', [])
            }
            # OPTIMIZATION: Parallelize intent classification and translation
            app_language = self._safe_get_state_value(state, 'user_language', 'ja')

            # Prepare parallel tasks
            tasks = []

            # Task 1: Intent classification (always run)
            intent_task = asyncio.create_task(
                self._classify_intent_with_llm(last_message_content, context)
            )
            tasks.append(("intent", intent_task))

            # Task 2: Translation (only if needed)
            translation_task = None
            if app_language not in ['en', 'ja']:
                logger.info(f"Preparing translation {app_language} -> English")
                translation_task = asyncio.create_task(
                    self._translate_to_english(last_message_content, app_language)
                )
                tasks.append(("translation", translation_task))

            # Execute tasks in parallel
            logger.info(f"Running {len(tasks)} parallel LLM tasks")

            try:
                # Wait for all tasks with timeout
                completed_tasks = await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                    timeout=60.0  # Total timeout for all parallel tasks
                )

                # Extract results
                intent = None
                english_input = last_message_content  # Default

                for i, (task_name, _) in enumerate(tasks):
                    result = completed_tasks[i]
                    if isinstance(result, Exception):
                        logger.error(f"{task_name} task failed: {result}")
                        continue

                    if task_name == "intent":
                        intent = result
                    elif task_name == "translation" and result:
                        english_input = result
                        logger.info(f"Input translated to English")

                # Fallback if intent classification failed
                if not intent:
                    logger.warning("Intent classification failed, using fallback")
                    from app.schemas.common.enums import IntentCategory
                    intent = DisasterIntentSchema(
                        is_disaster_related=False,
                        primary_intent=IntentCategory.UNKNOWN,
                        confidence=0.2,
                        reasoning="Parallel processing failed"
                    )

            except asyncio.TimeoutError:
                logger.warning("Parallel LLM tasks timed out, using fallbacks")
                from app.schemas.common.enums import IntentCategory
                intent = DisasterIntentSchema(
                    is_disaster_related=False,
                    primary_intent=IntentCategory.UNKNOWN,
                    confidence=0.1,
                    reasoning="Parallel tasks timed out"
                )
                english_input = last_message_content
            except Exception as e:
                logger.error(f"Parallel processing error: {e}")
                from app.schemas.common.enums import IntentCategory
                intent = DisasterIntentSchema(
                    is_disaster_related=False,
                    primary_intent=IntentCategory.UNKNOWN,
                    confidence=0.1,
                    reasoning=f"Parallel processing error: {str(e)}"
                )
                english_input = last_message_content

            # ステップ3: 翻訳されたテキストを状態に保存
            # Store both original and English version for different processing stages
            logger.info(f"📝 Original input: {last_message_content}")
            # 災害関連の場合は災害コンテキストを準備してからdisaster_context_managerに移譲
            if intent.is_disaster_related and intent.confidence > 0.7:
                logger.info(f"Disaster-related intent detected: {intent.primary_intent}")

                # 災害コンテキストマネージャーの機能を統合実行
                from ..managers.disaster_context_manager import prepare_disaster_context
                disaster_context = await prepare_disaster_context(state)

                # IMPORTANT: Preserve intermediate_results from input state
                existing_intermediate_results = self._safe_get_state_value(state, 'intermediate_results', {})

                logger.info(f"🔴 NODE EXIT: initial_analyzer -> context_router (disaster intent)")
                logger.info(f"🔴 ROUTING REASON: Disaster-related intent detected: {intent.primary_intent}")
                logger.info(f"🔴 ROUTING DECISION: next=context_router, confidence={intent.confidence}")

                return {
                    "last_askuser_reason": f"災害関連の問い合わせを検出: {intent.primary_intent}",
                    "turn_count": self._safe_get_state_value(state, 'turn_count', 0) + 1,
                    "requires_professional_handling": True,
                    "current_task_type": "disaster_related",
                    "primary_intent": str(intent.primary_intent.value).lower(),
                    "is_disaster_related": True,
                    "intent_confidence": intent.confidence,
                    "detected_language": "en",  # 統一処理
                    "is_disaster_mode": disaster_context.get("is_emergency_mode", False),
                    "disaster_context": disaster_context,
                    "routing_decision": {"next": "router_node", "reason": f"災害関連意図処理完了: {intent.primary_intent}"},
                    # Store both versions for processing pipeline
                    "original_user_input": last_message_content,
                    "english_user_input": english_input,
                    "target_language": app_language,  # For later translation back to user language
                    # CRITICAL: Preserve intermediate_results to avoid fallback errors
                    "intermediate_results": existing_intermediate_results
                }

            # OPTIMIZATION: Skip response generation for disaster-related intents
            # They will be handled by specialized handlers
            logger.info(f"Using app language setting: {app_language}")

            # Only generate response for non-disaster intents to avoid redundant LLM calls
            response_text = ""
            if not (intent.is_disaster_related and intent.confidence > 0.7):
                # 英語で応答を生成（内部処理言語統一）
                response_text = await self._generate_natural_response(
                    english_input, "en", intent, context  # Always process in English internally
                )
            else:
                # For disaster-related intents, set placeholder (will be handled by specialized handlers)
                response_text = "Disaster-related query detected - routing to specialized handler"

            # 状態更新（アプリの設定言語を使用）
            # IMPORTANT: Preserve intermediate_results from input state
            existing_intermediate_results = self._safe_get_state_value(state, 'intermediate_results', {})

            updates = {
                "last_askuser_reason": "自然言語処理による応答生成",
                "turn_count": self._safe_get_state_value(state, 'turn_count', 0) + 1,
                "requires_professional_handling": False,
                "current_task_type": "off_topic",
                "primary_intent": str(intent.primary_intent.value).lower(),
                "secondary_intents": [],
                "intent_confidence": intent.confidence,
                "is_disaster_related": intent.is_disaster_related,
                "detected_language": "en",  # 統一処理言語
                "routing_decision": {
                    "next": "response_synthesizer",
                    "reason": f"オフトピック処理完了: {intent.primary_intent}"
                },
                "off_topic_response": response_text,
                # Store both versions for processing pipeline
                "original_user_input": last_message_content,
                "english_user_input": english_input,
                "target_language": app_language,  # For translation back to user language
                # CRITICAL: Preserve intermediate_results to avoid fallback errors
                "intermediate_results": existing_intermediate_results
            }

            # Trace exit with routing decision
            tracer.exit_node('improved_off_topic_handler', updates)
            if 'routing_decision' in updates:
                next_node = updates['routing_decision'].get('next', 'unknown')
                reason = updates['routing_decision'].get('reason', '')
                tracer.routing_decision('improved_off_topic_handler', next_node, reason)

            return updates

        except Exception as e:
            logger.error(f"Error in improved off_topic_handler: {e}", exc_info=True)

            # Trace error
            from ..core.graph_tracer import get_tracer
            session_id = self._safe_get_state_value(state, 'session_id', 'unknown')
            tracer = get_tracer(session_id)
            tracer.error('improved_off_topic_handler', str(e))

            # Get app language for error response
            app_language = self._safe_get_state_value(state, 'user_language', 'ja')

            # CLAUDE.mdに従い、内部処理は英語で統一
            # エラー応答は英語で生成し、response_generatorで翻訳される
            error_response = "I apologize. I'm LinguaSafeTrip, a disaster prevention assistant. Is there anything related to disasters or safety I can help you with?"

            # IMPORTANT: Preserve intermediate_results even in error case
            existing_intermediate_results = self._safe_get_state_value(state, 'intermediate_results', {})

            return {
                "last_askuser_reason": "エラー発生時のフォールバック応答",
                "turn_count": self._safe_get_state_value(state, 'turn_count', 0) + 1,
                "requires_professional_handling": False,
                "current_task_type": "off_topic",
                "primary_intent": "off_topic",
                "secondary_intents": [],
                "intent_confidence": 0.5,
                "is_disaster_related": False,
                "detected_language": app_language,
                "routing_decision": {"next": "response_synthesizer", "reason": "エラーフォールバック"},
                "off_topic_response": error_response,
                # CRITICAL: Preserve intermediate_results to avoid fallback errors
                "intermediate_results": existing_intermediate_results
            }

def make_linguasafetrip_node(llm: BaseChatModel):
    """改善されたLangGraph用ノードファクトリ関数"""
    handler = ImprovedOffTopicHandler()

    async def improved_linguasafetrip_node(state: AgentState):
        return await handler.handle(state)

    return improved_linguasafetrip_node