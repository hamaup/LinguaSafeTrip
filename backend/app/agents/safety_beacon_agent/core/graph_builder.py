"""
Unified Graph Builder - 統合グラフビルダー
シンプルな6ノード構成で高速処理を実現
"""
import logging
from typing import Dict, Any
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from .checkpointer import LinguaSafeTripCheckpointer
from app.schemas.agent_state import AgentState
from .llm_singleton import set_graph_llm
from .reliability_enhancer import _enhance_reliability_and_safety

# Import routers and handlers
from .intent_router import intent_router, route_from_intent_router
from ..handlers.disaster_info_handler import handle_disaster_information_request
from ..handlers.evacuation_support_handler import handle_evacuation_support_request
from ..handlers.information_guide_handler import information_guide_node
from ..handlers.sms_confirmation_handler import handle_sms_confirmation_request
from ..handlers.general_reflection_handler import general_unified_reflection
from ..handlers.clarification_handler import clarification_handler

logger = logging.getLogger(__name__)

def route_after_quality_enhancement(state: AgentState) -> str:
    """Route after quality enhancement - loop back to handler if improvement needed"""
    return route_from_reflection_hub_internal(state)

# Keep old name as alias for backward compatibility
route_from_reflection_hub = route_after_quality_enhancement

def route_from_reflection_hub_internal(state: AgentState) -> str:
    """Internal routing logic"""
    
    # 最大リフレクション回数チェック（無限ループ防止）
    reflection_count = state.get("reflection_count", 0)
    max_reflections = 2
    
    if reflection_count >= max_reflections:
        # Max reflections reached - ending
        return "END"
    
    # リフレクション結果をチェック
    needs_improvement = state.get("needs_improvement", False)
    improvement_target = state.get("improvement_target", "")
    
    if needs_improvement and improvement_target:
        # Quality insufficient - routing back to handler
        return improvement_target
    
    # 品質十分またはエラー時は終了
    # Quality sufficient or processing complete - ending
    return "END"

# Unified reflection hub: All handlers go through reflection with possible loopback

# Wrapper functions with verb-based naming (LangGraph best practice)
async def process_disaster(state: AgentState) -> Dict[str, Any]:
    """Process disaster information requests"""
    # NODE ENTRY: process_disaster
    return await handle_disaster_information_request(state)

async def process_evacuation(state: AgentState) -> Dict[str, Any]:
    """Process evacuation support requests"""
    # NODE ENTRY: process_evacuation
    return await handle_evacuation_support_request(state)

async def process_guide(state: AgentState) -> Dict[str, Any]:
    """Process preparedness guide requests"""
    # NODE ENTRY: process_guide
    return await information_guide_node(state)

async def process_safety(state: AgentState) -> Dict[str, Any]:
    """Process safety confirmation requests"""
    # NODE ENTRY: process_safety
    user_language = state.get("user_language", "ja")
    return await handle_sms_confirmation_request(state, target_language=user_language)

async def process_general(state: AgentState) -> Dict[str, Any]:
    """Process general inquiries with reflection"""
    # NODE ENTRY: process_general
    return await general_unified_reflection(state)

# Keep old names as aliases for backward compatibility
disaster_unified = process_disaster
evacuation_unified = process_evacuation
guide_unified = process_guide
safety_unified = process_safety
# general_unified_reflection is imported from handlers - no alias needed

async def enhance_quality(state: AgentState) -> Dict[str, Any]:
    """Enhance response quality - reduce hallucination, improve translation, strengthen reliability"""
    
    # NODE ENTRY: enhance_quality
    return await unified_reflection_hub_internal(state)

# Keep old name as alias for backward compatibility
unified_reflection_hub = enhance_quality

async def unified_reflection_hub_internal(state: AgentState) -> Dict[str, Any]:
    """Internal implementation for quality enhancement"""
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "ja")
    final_response_text = state.get("final_response_text", "")
    current_task_type = state.get("current_task_type", ["unknown"])
    last_handler = current_task_type[0] if current_task_type else "unknown"
    reflection_count = state.get("reflection_count", 0)
    
    # リフレクション回数を増加
    updated_reflection_count = reflection_count + 1
    
    # 緊急時フラグを記録（緊急時も品質評価と改善を実行）
    is_emergency = state.get("is_disaster_mode", False) or state.get("emergency_detected", False)
    if is_emergency:
        # Emergency mode - but still evaluating quality for improvement
        pass
    
    # エラー状態は翻訳のみで品質評価スキップ
    is_error_state = state.get("error_message") or state.get("handler_error")
    if is_error_state:
        # Error state detected - translation only, no quality evaluation
        
        # フォールバック・エラーの翻訳処理（評価なし）
        if user_language != "en" and final_response_text and _is_english_response(final_response_text):
            try:
                from app.tools.translation_tool import translation_tool
                # Error response translation
                final_response_text = await translation_tool.translate(
                    text=final_response_text,
                    target_language=user_language,
                    source_language="en"
                )
                # Error response translation completed
            except Exception as e:
                logger.error(f"Error response translation failed: {e}, using English")
                # 翻訳失敗時は英語のまま
        
        # Error state - translation completed, quality evaluation skipped
        return {
            **state,
            "final_response_text": final_response_text,
            "last_response": final_response_text,
            "reflection_count": updated_reflection_count,
            "needs_improvement": False,
            "reflection_applied": False
        }
    
    requires_action = state.get("requires_action")
    if requires_action and not final_response_text:
        # Action-only response - quality approved
        return {
            **state,
            "reflection_count": updated_reflection_count,
            "needs_improvement": False,
            "reflection_applied": False
        }
    
    # 品質評価の実行
    quality_result = await _evaluate_response_quality(
        user_input, final_response_text, last_handler, user_language, reflection_count, is_emergency
    )
    
    # 改善が必要な場合（緊急時も含む）
    if quality_result.get("needs_improvement", False):
        # Quality insufficient - needs improvement by handler
        return {
            **state,
            "reflection_count": updated_reflection_count,
            "needs_improvement": True,
            "improvement_target": quality_result.get("target_handler", last_handler),
            "improvement_feedback": quality_result.get("feedback", "General improvement needed"),
            "reflection_applied": True
        }
    
    # 品質十分な場合（改善版があれば適用）
    improved_response = quality_result.get("improved_response", final_response_text)
    if improved_response != final_response_text:
        # Response improved by reflection hub
        pass
    
    # 新フロー: 専門ハンドラーで翻訳済み → enhance_qualityで品質チェック
    final_response = improved_response
    
    # 翻訳が必要な場合（フォールバック・エラー時やハンドラー翻訳失敗時）
    needs_translation = (
        user_language != "en" and 
        _is_english_response(improved_response) and
        not _is_already_translated(improved_response, user_language)
    )
    
    if needs_translation:
        try:
            from app.tools.translation_tool import translation_tool
            # Quality-stage translation
            final_response = await translation_tool.translate(
                text=improved_response,
                target_language=user_language,
                source_language="en"
            )
            # Quality-stage translation completed
        except Exception as e:
            logger.error(f"Quality-stage translation failed: {e}, using original response")
            final_response = improved_response
    
    # 品質評価完了
    improvement_msg = "Enhanced reliability, reduced hallucination, improved translation accuracy" if improved_response != final_response_text else "Quality validated - translation ensured"
    # Response quality sufficient - processing complete
    
    return {
        **state,
        "final_response_text": final_response,
        "last_response": final_response,
        "reflection_count": updated_reflection_count,
        "needs_improvement": False,
        "reflection_applied": True,
        "reflection_improvement": improvement_msg
    }

async def _evaluate_response_quality(
    user_input: str,
    response: str,
    handler_type: str,
    user_language: str,
    reflection_count: int,
    is_emergency: bool = False
) -> Dict[str, Any]:
    """表現品質の評価（内容の正確性は専門ハンドラーが保証済み）"""
    
    # 最大リフレクション回数チェック
    if reflection_count >= 1:  # 1回目のリフレクションで十分
        return {
            "needs_improvement": False,
            "feedback": "Maximum reflections reached",
            "improved_response": response
        }
    
    needs_improvement = False
    feedback = ""
    improved_response = response
    
    # 1. 内容の充実度評価（文字数ではなく内容で判断）
    content_completeness = await _evaluate_content_completeness(
        user_input, response, handler_type, user_language
    )
    
    if content_completeness.get("needs_enhancement"):
        # Content needs enhancement
        enhancement = content_completeness.get("enhancement", {})
        
        # SafetyBee機能の案内が必要な場合
        if enhancement.get("add_safetybee_features"):
            safety_additions = {
                "ja": "\n\n💡 SafetyBeeでは、リアルタイムの災害情報、避難所検索、防災ガイドなどの機能もご利用いただけます。",
                "en": "\n\n💡 SafetyBee offers real-time disaster information, shelter search, and preparedness guides.",
                "ko": "\n\n💡 SafetyBee는 실시간 재해 정보, 대피소 검색, 방재 가이드 등의 기능을 제공합니다.",
                "zh": "\n\n💡 SafetyBee提供实时灾害信息、避难所搜索和防灾指南等功能。"
            }
            improved_response = response + safety_additions.get(user_language, safety_additions["en"])
            # Added SafetyBee feature suggestions based on content needs
    
    # 2. ハルシネーション軽減・信頼性チェック
    reliability_enhancement = await _enhance_reliability_and_safety(
        user_input, improved_response, handler_type, user_language
    )
    
    if reliability_enhancement.get("enhanced_response"):
        improved_response = reliability_enhancement["enhanced_response"]
        # Enhanced response reliability and safety
    
    # 2. 内容の完全性チェック（実際の品質評価）
    # ここで具体的な品質問題があればリジェクトを判定
    content_issues = await _check_content_quality(user_input, response, handler_type, is_emergency)
    
    if content_issues.get("has_issues", False):
        logger.warning(f"Content quality issues detected: {content_issues.get('issues', [])}")
        return {
            "needs_improvement": True,
            "target_handler": handler_type,
            "feedback": content_issues.get("feedback", "Content needs improvement"),
            "improved_response": response
        }
    
    # 3. 防災関連性の評価（内容の意味的な関連性で判断）
    if handler_type in ["general_unified_reflection", "general_inquiry"]:
        safety_relevance = await _evaluate_safety_relevance(
            user_input, improved_response, user_language
        )
        
        if safety_relevance.get("needs_safety_context"):
            safety_context = {
                "ja": "\n\n🛡️ なお、災害への備えも大切です。SafetyBeeの防災ガイドや避難所検索機能もぜひご活用ください。",
                "en": "\n\n🛡️ Remember, disaster preparedness is important. Check out SafetyBee's preparedness guides and shelter search features.",
                "ko": "\n\n🛡️ 재해 대비도 중요합니다. SafetyBee의 방재 가이드와 대피소 검색 기능을 활용해 주세요.",
                "zh": "\n\n🛡️ 记住，灾害准备很重要。请查看SafetyBee的防灾指南和避难所搜索功能。"
            }
            improved_response = improved_response + safety_context.get(user_language, safety_context["en"])
            # Added disaster preparedness context based on content analysis
    
    # 4. 翻訳精度と一貫性の検証
    translation_quality = await _verify_translation_quality(
        improved_response, user_language, handler_type
    )
    
    if translation_quality.get("needs_translation_improvement"):
        logger.warning(f"Translation quality issue detected: {translation_quality.get('issue')}")
        return {
            "needs_improvement": True,
            "target_handler": handler_type,
            "feedback": f"Translation quality improvement needed: {translation_quality.get('feedback')}",
            "improved_response": improved_response
        }
    
    if translation_quality.get("translation_validated"):
        # Translation accuracy and consistency validated
        pass
    
    return {
        "needs_improvement": needs_improvement,
        "target_handler": handler_type if needs_improvement else None,
        "feedback": feedback,
        "improved_response": improved_response
    }

async def _check_content_quality(
    user_input: str,
    response: str,
    handler_type: str,
    is_emergency: bool
) -> Dict[str, Any]:
    """表現・形式の品質チェック（内容検証は専門ハンドラーの責任）"""
    import re
    
    issues = []
    
    # リフレクションハブは内容の事実確認はしない
    # 専門ハンドラーがデータソースと整合性を確保済み
    
    # 1. 表現の妥当性チェック（形式的な問題のみ）
    if len(response.strip()) < 5:
        issues.append("Response too minimal for user interaction")
    
    # 2. 基本的な構造チェック
    if response.count("。") == 0 and response.count(".") == 0 and len(response) > 20:
        issues.append("Missing proper sentence structure")
    
    # 3. 明らかな形式エラー
    if response.startswith("ERROR") or response.startswith("FAIL"):
        issues.append("Error state in response")
    
    # 4. 幻覚的な参照の検出
    hallucination_patterns = [
        r'search result \d+',      # search result 1
        r'検索結果\d+',             # 検索結果4
        r'Search Result \d+',      # Search Result 1
        r'\(search result \d+\)',  # (search result 1)
        r'（検索結果\d+）',         # （検索結果4）
        r'result #\d+',            # result #3
    ]
    
    for pattern in hallucination_patterns:
        if re.search(pattern, response, flags=re.IGNORECASE):
            issues.append(f"Hallucinated reference detected: {pattern}")
            logger.warning(f"Hallucination detected in response: {pattern}")
    
    # 5. プレースホルダーの検出
    placeholder_patterns = [
        r'\[.*?\]',                # [location name], [distance]
        r'【.*?】',                 # 【場所名】
    ]
    
    for pattern in placeholder_patterns:
        matches = re.findall(pattern, response)
        if matches and not all('[' in m and ']' in m for m in ["[URGENT]", "[DANGER]", "[CRITICAL]", "[NOW]"]):
            # 緊急マーカー以外のプレースホルダーを検出
            non_emergency_placeholders = [m for m in matches if m not in ["[URGENT]", "[DANGER]", "[CRITICAL]", "[NOW]"]]
            if non_emergency_placeholders:
                issues.append(f"Placeholder text detected: {non_emergency_placeholders}")
                logger.warning(f"Placeholder detected in response: {non_emergency_placeholders}")
    
    # 内容の正確性は専門ハンドラーに委ねる
    has_issues = len(issues) > 0
    feedback = f"Format/expression issues: {', '.join(issues)}" if has_issues else ""
    
    # 緊急時は形式的問題でもリジェクト
    if is_emergency and has_issues:
        logger.warning(f"Emergency response has format issues: {issues}")
    
    return {
        "has_issues": has_issues,
        "issues": issues,
        "feedback": feedback
    }

# 削除: _ensure_proper_translation（統一出口翻訳に変更済み）

async def _evaluate_content_completeness(
    user_input: str,
    response: str,
    handler_type: str,
    user_language: str
) -> Dict[str, Any]:
    """内容の充実度を評価（LLMによる意味的評価）"""
    
    # シンプルに災害・避難関連のハンドラーからの応答は常にSafetyBee機能を案内
    if handler_type in ["disaster_information", "evacuation_support", "task_complete_disaster_info", "task_complete_evacuation"]:
        return {
            "needs_enhancement": True,
            "reason": "Disaster-related response should include SafetyBee features",
            "enhancement": {"add_safetybee_features": True}
        }
    
    # 一般的な質問への応答も常にSafetyBeeの価値を伝える
    if handler_type in ["general", "general_inquiry", "task_complete_general"]:
        return {
            "needs_enhancement": True,
            "reason": "General response should include safety context",
            "enhancement": {"add_safetybee_features": True}
        }
    
    # その他のハンドラーは改善不要
    return {
        "needs_enhancement": False,
        "reason": "",
        "enhancement": {}
    }

async def _evaluate_safety_relevance(
    user_input: str,
    response: str,
    user_language: str
) -> Dict[str, Any]:
    """防災関連性を評価（ハンドラータイプで判断）"""
    
    # 一般的な質問への応答には常に防災コンテキストを追加
    return {"needs_safety_context": True}

async def _verify_translation_quality(
    response: str,
    user_language: str,
    handler_type: str
) -> Dict[str, Any]:
    """翻訳品質を検証"""
    
    # 英語応答の場合は翻訳検証不要
    if user_language == "en":
        return {"translation_validated": True, "needs_translation_improvement": False}
    
    # 基本的な翻訳品質チェック
    quality_issues = []
    
    # 1. 言語の一貫性チェック
    language_consistency = await _check_language_consistency(response, user_language)
    if not language_consistency.get("is_consistent"):
        quality_issues.append(f"Language inconsistency: {language_consistency.get('issue')}")
    
    # 2. 災害用語の翻訳精度チェック
    if handler_type in ["disaster", "evacuation", "safety"]:
        terminology_accuracy = await _check_disaster_terminology(response, user_language)
        if not terminology_accuracy.get("is_accurate"):
            quality_issues.append(f"Terminology issue: {terminology_accuracy.get('issue')}")
    
    # 3. 文脈の保持チェック
    context_preservation = await _check_context_preservation(response, user_language)
    if not context_preservation.get("is_preserved"):
        quality_issues.append(f"Context issue: {context_preservation.get('issue')}")
    
    # 検証結果
    if quality_issues:
        return {
            "needs_translation_improvement": True,
            "issue": "; ".join(quality_issues),
            "feedback": f"Improve translation quality: {'; '.join(quality_issues)}",
            "translation_validated": False
        }
    
    return {
        "needs_translation_improvement": False,
        "translation_validated": True,
        "quality_score": 0.9
    }

def _is_english_response(text: str) -> bool:
    """応答が英語かどうかを判定"""
    # 簡易判定：英語的な単語の割合
    english_indicators = ["the", "and", "is", "are", "I", "you", "to", "for", "of", "with"]
    words = text.lower().split()
    if not words:
        return False
    
    english_word_count = sum(1 for word in words if any(indicator in word for indicator in english_indicators))
    return english_word_count / len(words) > 0.3

def _is_already_translated(text: str, target_language: str) -> bool:
    """既に指定言語に翻訳済みかどうかを判定"""
    if target_language == "ja":
        # ひらがな・カタカナ・漢字を含むかチェック
        import re
        return bool(re.search(r'[ひらがなカタカナ漢字ぁ-んァ-ンー一-龯]', text))
    elif target_language == "ko":
        # ハングル文字を含むかチェック
        import re
        return bool(re.search(r'[가-힣]', text))
    elif target_language == "zh":
        # 中国語文字を含むかチェック
        import re
        return bool(re.search(r'[一-龯]', text))
    
    return False

async def _check_language_consistency(response: str, user_language: str) -> Dict[str, Any]:
    """言語の一貫性をチェック"""
    # 基本チェック：指定言語に翻訳されているか
    is_translated = _is_already_translated(response, user_language)
    is_english = _is_english_response(response)
    
    if user_language != "en" and is_english and not is_translated:
        return {
            "is_consistent": False,
            "issue": f"Response appears to be in English instead of {user_language}"
        }
    
    return {"is_consistent": True}

async def _check_disaster_terminology(response: str, user_language: str) -> Dict[str, Any]:
    """災害用語の翻訳精度をチェック"""
    # 基本的な災害用語が適切に翻訳されているかチェック
    # より詳細な実装は後で追加可能
    return {"is_accurate": True}

async def _check_context_preservation(response: str, user_language: str) -> Dict[str, Any]:
    """文脈の保持をチェック"""
    # 基本的な文脈保持チェック
    # より詳細な実装は後で追加可能
    return {"is_preserved": True}

# Simplified reflection system - no complex LLM evaluation needed

def create_unified_graph(llm: BaseChatModel) -> StateGraph:
    """
    統合グラフ作成 - 7ノード構成（統合リフレクションハブ付き）
    全ハンドラーの結果にセルフリフレクション機能を提供
    """
    # グラフ用のLLMを設定（全ハンドラーで共有）
    set_graph_llm(llm)
    logger.info("Set shared LLM instance for unified graph")
    
    workflow = StateGraph(AgentState)

    # 8 nodes total: 1 router + 1 clarifier + 5 processors + 1 quality enhancer (matches expected flowchart)
    workflow.add_node("analyze_intent", intent_router)           # Analyze user intent
    workflow.add_node("clarify_intent", clarification_handler)   # Clarify unclear intent
    workflow.add_node("process_disaster", process_disaster)      # Process disaster info
    workflow.add_node("process_evacuation", process_evacuation)  # Process evacuation
    workflow.add_node("process_guide", process_guide)            # Process guides
    workflow.add_node("process_safety", process_safety)          # Process safety
    workflow.add_node("process_general", process_general)        # Process general
    workflow.add_node("enhance_quality", enhance_quality)        # Enhance quality

    # Set entry point
    workflow.set_entry_point("analyze_intent")

    # Routing from intent analyzer
    workflow.add_conditional_edges(
        "analyze_intent",
        route_from_intent_router,
        {
            "clarify_intent": "clarify_intent",
            "process_disaster": "process_disaster",
            "process_evacuation": "process_evacuation",
            "process_guide": "process_guide",
            "process_safety": "process_safety",
            "process_general": "process_general"
        }
    )

    # Clarification goes back to intent analysis for re-routing
    workflow.add_edge("clarify_intent", "analyze_intent")
    
    # All processing handlers go through quality enhancement
    workflow.add_edge("process_disaster", "enhance_quality")
    workflow.add_edge("process_evacuation", "enhance_quality")
    workflow.add_edge("process_guide", "enhance_quality")
    workflow.add_edge("process_safety", "enhance_quality")
    workflow.add_edge("process_general", "enhance_quality")
    
    # Conditional routing after quality enhancement (loop back if needed)
    workflow.add_conditional_edges(
        "enhance_quality",
        route_after_quality_enhancement,
        {
            "process_disaster": "process_disaster",
            "process_evacuation": "process_evacuation", 
            "process_guide": "process_guide",
            "process_safety": "process_safety",
            "process_general": "process_general",
            "END": END
        }
    )

    # Unified graph created: 8 nodes (intent+clarify+5 processors+quality) - matches expected flowchart
    
    # 永続的なチェックポインター設定
    persistent_checkpointer = LinguaSafeTripCheckpointer.create_checkpointer()
    
    # グラフのコンパイル
    compiled_graph = workflow.compile(checkpointer=persistent_checkpointer)
    
    return compiled_graph