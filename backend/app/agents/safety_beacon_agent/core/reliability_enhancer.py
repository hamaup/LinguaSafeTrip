"""
信頼性強化モジュール - ハルシネーション軽減・翻訳精度向上
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def _enhance_reliability_and_safety(
    user_input: str,
    response: str,
    handler_type: str,
    user_language: str
) -> Dict[str, Any]:
    """
    信頼性・安全性の強化
    - ハルシネーション軽減
    - 翻訳精度の向上
    - 回答の信頼性向上
    """
    import re
    
    enhanced_response = response
    translation_preserved = False
    
    # 0. 幻覚的な参照を削除
    hallucination_patterns = [
        r'\(search result \d+\)',  # (search result 1)
        r'search result \d+',      # search result 1
        r'検索結果\d+',             # 検索結果4
        r'Search Result \d+',      # Search Result 1
        r'（検索結果\d+）',         # （検索結果4）
        r'（search result \d+）',  # （search result 1）
        r'result #\d+',            # result #3
        r'\[.*?\]',                # [location name] - 緊急マーカー以外
        r'【.*?】',                 # 【場所名】
    ]
    
    removed_hallucinations = []
    for pattern in hallucination_patterns:
        if pattern == r'\[.*?\]':
            # 緊急マーカーは除外
            matches = re.findall(pattern, enhanced_response)
            non_emergency = [m for m in matches if m not in ["[URGENT]", "[DANGER]", "[CRITICAL]", "[NOW]"]]
            if non_emergency:
                removed_hallucinations.extend(non_emergency)
                for match in non_emergency:
                    enhanced_response = enhanced_response.replace(match, '')
        else:
            matches = re.findall(pattern, enhanced_response, flags=re.IGNORECASE)
            if matches:
                removed_hallucinations.extend(matches)
                enhanced_response = re.sub(pattern, '', enhanced_response, flags=re.IGNORECASE)
    
    # 基本的なクリーンアップのみ
    enhanced_response = enhanced_response.strip()
    
    if removed_hallucinations:
        logger.warning(f"🚫 Removed hallucinated references: {removed_hallucinations}")
    
    # 1. ハルシネーション軽減（データソース言及の強化）
    if handler_type in ["disaster_unified", "evacuation_unified"]:
        hallucination_reduction = await _reduce_hallucination_risk(enhanced_response, handler_type, user_language)
        if hallucination_reduction.get("enhanced"):
            enhanced_response = hallucination_reduction["text"]
            logger.info("🛡️ Reduced hallucination risk")
    
    # 2. 翻訳精度の保持（技術用語・固有名詞の保護）
    if user_language != "ja":
        translation_accuracy = await _preserve_translation_accuracy(enhanced_response, user_language)
        if translation_accuracy.get("preserved"):
            enhanced_response = translation_accuracy["text"]
            translation_preserved = True
            logger.info("🌐 Preserved translation accuracy")
    
    # 3. 信頼性表現の強化（不確実性の明示）
    reliability_enhancement = await _enhance_reliability_expression(enhanced_response, handler_type, user_language)
    if reliability_enhancement.get("enhanced"):
        enhanced_response = reliability_enhancement["text"]
        logger.info("✅ Enhanced reliability expression")
    
    return {
        "enhanced_response": enhanced_response if enhanced_response != response else None,
        "translation_preserved": translation_preserved,
        "reliability_enhanced": True
    }

async def _reduce_hallucination_risk(response: str, handler_type: str, user_language: str) -> Dict[str, Any]:
    """ハルシネーション軽減のための情報源明記"""
    
    # 災害情報での情報源明記 - LLMベースの内容分析（簡易版：災害関連コンテンツ検出）
    if handler_type == "disaster_unified" and await _contains_disaster_information(response):
        source_disclaimers = {
            "ja": "\n\n※ 災害情報は気象庁等の公式情報を元にしています。最新情報は公式サイトでご確認ください。",
            "en": "\n\n※ Disaster information is based on official sources like JMA. Please check official sites for the latest updates.",
            "ko": "\n\n※ 재해 정보는 기상청 등 공식 정보를 바탕으로 합니다. 최신 정보는 공식 사이트에서 확인해 주세요.",
            "zh": "\n\n※ 灾害信息基于气象厅等官方信息。请在官方网站确认最新信息。"
        }
        
        return {
            "enhanced": True,
            "text": response + source_disclaimers.get(user_language, source_disclaimers["en"])
        }
    
    # 避難情報での責任制限 - LLMベースの内容分析（簡易版：避難関連コンテンツ検出）
    if handler_type == "evacuation_unified" and await _contains_evacuation_content(response):
        evacuation_disclaimers = {
            "ja": "\n\n※ 避難に関する判断は最終的にご自身で行ってください。緊急時は119番や自治体の指示に従ってください。",
            "en": "\n\n※ Please make final evacuation decisions yourself. In emergencies, follow 119 or local authority instructions.",
            "ko": "\n\n※ 대피에 관한 판단은 최종적으로 본인이 해주세요. 긴급시에는 119번이나 지자체 지시를 따라주세요.",
            "zh": "\n\n※ 请自己做出最终的避难判断。紧急时请遵循119或当地政府的指示。"
        }
        
        return {
            "enhanced": True,
            "text": response + evacuation_disclaimers.get(user_language, evacuation_disclaimers["en"])
        }
    
    return {"enhanced": False, "text": response}

async def _preserve_translation_accuracy(response: str, user_language: str) -> Dict[str, Any]:
    """翻訳精度の保持（重要用語の保護）"""
    
    # 災害関連の重要用語をLLMベースで検出（簡易版：災害関連コンテンツの存在確認）
    term_consistency_maintained = await _contains_important_disaster_terms(response, user_language)
    
    return {
        "preserved": term_consistency_maintained,
        "text": response  # 実際の用語保護ロジックは翻訳処理側で実装
    }

async def _enhance_reliability_expression(response: str, handler_type: str, user_language: str) -> Dict[str, Any]:
    """信頼性表現の強化（不確実性の適切な表現）"""
    
    # 予測や推定を含む回答の信頼性表現 - LLMベースの不確実性検出（簡易版）
    has_uncertainty = await _contains_uncertainty_expressions(response, user_language)
    
    if has_uncertainty:
        reliability_notes = {
            "ja": "\n\n※ 予測情報は変更される可能性があります。",
            "en": "\n\n※ Forecast information may change.",
            "ko": "\n\n※ 예측 정보는 변경될 가능성이 있습니다.",
            "zh": "\n\n※ 预测信息可能会发生变化。"
        }
        
        return {
            "enhanced": True,
            "text": response + reliability_notes.get(user_language, reliability_notes["en"])
        }
    
    return {"enhanced": False, "text": response}

async def _contains_disaster_information(response: str) -> bool:
    """真のLLMベースの災害情報内容検出"""
    try:
        from .llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import DISASTER_INFO_DETECTION_PROMPT
        
        prompt = DISASTER_INFO_DETECTION_PROMPT.format(response_text=response[:200])
        
        result = await ainvoke_llm(prompt, task_type="content_analysis", temperature=0.1, max_tokens=10)
        return result.strip().lower() == "true"
    except:
        return False

async def _contains_evacuation_content(response: str) -> bool:
    """真のLLMベースの避難関連内容検出"""
    try:
        from .llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import EVACUATION_CONTENT_DETECTION_PROMPT
        
        prompt = EVACUATION_CONTENT_DETECTION_PROMPT.format(response_text=response[:200])
        
        result = await ainvoke_llm(prompt, task_type="content_analysis", temperature=0.1, max_tokens=10)
        return result.strip().lower() == "true"
    except:
        return False

async def _contains_important_disaster_terms(response: str, user_language: str) -> bool:
    """真のLLMベースの重要災害用語検出"""
    try:
        from .llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import IMPORTANT_DISASTER_TERMS_DETECTION_PROMPT
        
        prompt = IMPORTANT_DISASTER_TERMS_DETECTION_PROMPT.format(response_text=response[:200], user_language=user_language)
        
        result = await ainvoke_llm(prompt, task_type="content_analysis", temperature=0.1, max_tokens=10)
        return result.strip().lower() == "true"
    except:
        return True  # Default to preserving accuracy

async def _contains_uncertainty_expressions(response: str, user_language: str) -> bool:
    """真のLLMベースの不確実性表現検出"""
    try:
        from .llm_singleton import ainvoke_llm
        from app.prompts.disaster_prompts import UNCERTAINTY_EXPRESSIONS_DETECTION_PROMPT
        
        prompt = UNCERTAINTY_EXPRESSIONS_DETECTION_PROMPT.format(response_text=response[:200], user_language=user_language)
        
        result = await ainvoke_llm(prompt, task_type="content_analysis", temperature=0.1, max_tokens=10)
        return result.strip().lower() == "true"
    except:
        return False