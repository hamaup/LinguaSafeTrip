# backend/app/agents/safety_beacon_agent/proactive_suggester.py
"""
Cleaned and minimized proactive suggester - contains only actively used functions
All modular functionality has been moved to suggestion_generators/
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timezone

# Core schemas
from app.schemas.agent.suggestions import ProactiveSuggestionContext

# Import the new modular implementation
from app.agents.safety_beacon_agent.suggestion_generators.unified_generator import generate_single_suggestion_by_type

logger = logging.getLogger(__name__)

def _check_recent_shelter_search(context: ProactiveSuggestionContext) -> bool:
    """
    Check if shelter search was performed recently based on conversation history
    
    Args:
        context: The proactive suggestion context
        
    Returns:
        bool: True if shelter search was performed recently
    """
    try:
        # Check conversation history for shelter-related keywords
        conversation_history = getattr(context, 'conversation_history', [])
        if not conversation_history:
            return False
            
        # Check last 3 messages for shelter-related content
        recent_messages = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
        
        shelter_keywords = [
            'shelter', '避難所', 'evacuation', '避難', 
            'nearby_shelter', 'shelter_info', 'evacuation_support',
            '近くの避難所', '避難場所'
        ]
        
        for msg in recent_messages:
            if isinstance(msg, dict):
                content = msg.get('content', '').lower()
                # Check for shelter keywords in message
                if any(keyword in content for keyword in shelter_keywords):
                    return True
                # Check for shelter tool usage
                if 'tool' in msg and 'shelter' in str(msg.get('tool', '')).lower():
                    return True
                    
        # Also check if last intent was evacuation-related
        last_intent = getattr(context, 'last_classified_intent', '')
        if last_intent and 'evacuation' in last_intent.lower():
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Error checking recent shelter search: {e}")
        return False

async def invoke_proactive_agent_streaming(
    context: ProactiveSuggestionContext
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    プロアクティブ提案を並列生成し、完了次第ストリーミング出力
    
    Args:
        context: プロアクティブ提案のコンテキスト
        
    Yields:
        Dict: 完成した提案データ
    """
    # 並列タスクリスト
    tasks = []
    
    # 1. 緊急モード判定 - シンプルに統一
    is_emergency = context.is_emergency_mode or context.current_situation == "alert_active"
    
    # Emergency mode check
    # 緊急連絡先が未登録の場合は最優先
    emergency_contacts_count = getattr(context.user_app_usage_summary, 'local_contact_count', 0)
    has_emergency_contacts = emergency_contacts_count > 0
    
    # Check if shelter search was recently performed
    recent_shelter_search = _check_recent_shelter_search(context)
    
    if is_emergency:
        # 緊急時の提案タイプ
        if has_emergency_contacts:
            suggestion_types = [
                "disaster_news",  # 最新の災害情報を最優先
                "safety_confirmation_sms_proposal",  # 安否確認SMS送信提案
            ]
            if not recent_shelter_search:
                suggestion_types.append("shelter_status_update")
        else:
            # 緊急連絡先未登録時は最優先
            suggestion_types = [
                "emergency_contact_setup",  # 最優先
                "disaster_news",
            ]
            if not recent_shelter_search:
                suggestion_types.append("shelter_status_update")
    else:
        # 平常時の提案タイプ
        logger.info("🕐 Normal mode: Generating normal suggestions")
        if has_emergency_contacts:
            suggestion_types = [
                "seasonal_warning",  # 平常時は季節警告を最優先
                "welcome_message",  # 平常時はウェルカム表示
                "disaster_preparedness",  # 平常時は防災準備情報
                "hazard_map_url",  # ハザードマップ情報
            ]
            if not recent_shelter_search:
                suggestion_types.insert(3, "shelter_status_update")  # 4番目に挿入
        else:
            # 緊急連絡先未登録時
            suggestion_types = [
                "welcome_message",
                "seasonal_warning",
                "disaster_preparedness",
                "emergency_contact_setup",  # 優先度を下げる
                "hazard_map_url",
            ]
            if not recent_shelter_search:
                suggestion_types.insert(4, "shelter_status_update")  # 5番目に挿入
    
    # 提案タイプログ
    logger.info(f"📋 Proactive suggestions: {suggestion_types}")
    
    # 2. 並列で提案を生成
    async def generate_suggestion(suggestion_type: str):
        try:
            suggestion = await generate_single_suggestion_by_type(
                suggestion_type, context, context.language_code
            )
            if suggestion:
                return suggestion
            else:
                logger.warning(f"⚠️ {suggestion_type} generation returned None")
                return None
        except Exception as e:
            logger.error(f"❌ Error generating {suggestion_type}: {e}")
            return None
    
    # 並列実行して結果を収集
    tasks = [generate_suggestion(st) for st in suggestion_types]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 優先度順序を保持してストリーミング
    valid_suggestions = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Error generating {suggestion_types[i]}: {result}")
        elif result:
            valid_suggestions += 1
            yield result
    
    # エラーフォールバック：提案が1つも生成されなかった場合
    if valid_suggestions == 0:
        logger.warning("⚠️ No suggestions generated, providing fallback")
        # 基本的な防災準備提案をフォールバックとして提供
        fallback = {
            "type": "disaster_preparedness",
            "content": "Stay prepared for emergencies. Check your emergency supplies and review evacuation routes.",
            "action_query": "",
            "action_data": {"requires_translation": True, "is_fallback": True}
        }
        yield fallback

async def invoke_proactive_agent(
    context: ProactiveSuggestionContext
) -> List[Dict[str, Any]]:
    """
    プロアクティブ提案エージェントを起動（レガシー互換性）
    
    Args:
        context: プロアクティブ提案のコンテキスト
        
    Returns:
        List[Dict]: 生成された提案のリスト
    """
    try:
        logger.info(f"🔄 Legacy invoke_proactive_agent called for device {context.device_id}")
        
        suggestions = []
        async for suggestion in invoke_proactive_agent_streaming(context):
            if suggestion:
                suggestions.append(suggestion)
        
        # 緊急時は正しい順序で並べ直し
        is_emergency = context.is_emergency_mode or context.current_situation == "alert_active"
        
        if is_emergency and suggestions:
            logger.info("🔄 Reordering suggestions for emergency mode")
            emergency_order = [
                "disaster_news",
                "shelter_status_update", 
                "emergency_contact_setup",
                # "seasonal_warning",  # 季節警告は緊急時不要
                # SMS提案は削除
            ]
            
            # タイプ別に分類
            suggestions_by_type = {s.get('type'): s for s in suggestions if isinstance(s, dict) and 'type' in s}
            
            # 緊急時の順序で並べ直し
            ordered_suggestions = []
            for suggestion_type in emergency_order:
                if suggestion_type in suggestions_by_type:
                    ordered_suggestions.append(suggestions_by_type[suggestion_type])
            
            # 順序にない提案があれば最後に追加
            for suggestion in suggestions:
                if isinstance(suggestion, dict) and suggestion.get('type') not in emergency_order:
                    ordered_suggestions.append(suggestion)
            
            suggestions = ordered_suggestions
            logger.info(f"📋 Reordered {len(suggestions)} emergency suggestions")
        
        logger.info(f"📋 Generated {len(suggestions)} suggestions for device {context.device_id}")
        return suggestions
        
    except Exception as e:
        logger.error(f"❌ Error in invoke_proactive_agent: {e}")
        return []