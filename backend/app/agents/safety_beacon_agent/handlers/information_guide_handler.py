import logging
import uuid
import json
import re
import asyncio
from typing import Dict, Any, List, Optional, cast
from functools import lru_cache

from app.schemas.agent import AgentState, SuggestionCard, SuggestionCardActionButton
from app.schemas.guide import GuideContent # GuideContentをインポート
from app.schemas.search_results import SearchResultItem # SearchResultItemをインポート
from app.tools.guide_tools import UnifiedGuideSearchTool # 新しいUnifiedGuideSearchToolをインポート
from app.tools.web_search_tools import get_web_search_tool # Get appropriate web search tool

# このパッケージ内のモジュール
from ..core.llm_singleton import ainvoke_llm # 統一的なLLM呼び出し
from app.prompts.prompts import SYSTEM_PROMPT_TEXT, INFORMATION_GUIDE_RESPONSE_PROMPT_TEMPLATE, SUGGESTION_CARD_GENERATION_PROMPT_TEMPLATE # 新しいプロンプトをインポート
from langchain_core.messages import SystemMessage, HumanMessage # LangChainメッセージ型をインポート


logger = logging.getLogger(__name__)

# Import TTL cache
from app.utils.ttl_cache import TTLCache
from app.agents.safety_beacon_agent.handlers.complete_response_handlers import CompleteResponseGenerator

# Translation cache with TTL (24 hours, max 5000 entries)
_translation_cache = TTLCache(
    name="translation_cache",
    default_ttl_seconds=86400,  # 24 hours
    max_size=5000,
    cleanup_interval_seconds=3600  # cleanup every hour
)

# フィーチャーフラグ: バッチ処理の有効/無効
USE_BATCH_PROCESSING = True

async def _get_cached_japanese_query(query: str, search_type: str) -> str:
    """
    Get Japanese translation of query with caching to reduce translation overhead
    """
    # More accurate Japanese detection (exclude Chinese-only characters)
    # Check for hiragana or katakana which are unique to Japanese
    is_japanese = bool(re.search(r'[ぁ-んァ-ヶー]', query))
    
    if is_japanese:
        return query
    
    # Check cache first
    cache_key = TTLCache.make_key(query, search_type)
    cached_result = _translation_cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"🔄 Using cached Japanese translation for {search_type}: '{query}' -> '{cached_result}'")
        return cached_result
    
    # Translate and cache
    try:
        translation_prompt = f"""Translate the following query to natural Japanese for {search_type}:

Query: "{query}"

IMPORTANT: Return ONLY the Japanese translation, no explanations or options.

Japanese translation:"""
        translation_response = await ainvoke_llm(translation_prompt, task_type="translation", temperature=0.3, max_tokens=100)
        # Extract just the Japanese text if LLM returns explanations
        japanese_query = translation_response.strip()
        # Clean up common patterns where LLM might return extra text
        if "**" in japanese_query:
            # Extract text between ** markers
            match = re.search(r'\*\*([^*]+)\*\*', japanese_query)
            if match:
                japanese_query = match.group(1)
        # If response contains multiple lines, take the first Japanese line
        lines = japanese_query.split('\n')
        for line in lines:
            if any(char in line for char in 'あいうえおかきくけこがぎぐげごさしすせそざじずぜぞたちつてとだぢづでどなにぬねのはひふへほばびぶべぼぱぴぷぺぽまみむめもやゆよらりるれろわをん'):
                japanese_query = line.strip()
                break
        
        # Cache the result with TTL
        _translation_cache.set(cache_key, japanese_query)
        return japanese_query
    except Exception as e:
        logger.warning(f"{search_type} query translation failed: {e}, using original query")
        return query

def generate_emotional_support_response(emotional_context: Dict[str, Any], user_language: str, query_type: str) -> str:
    """
    情報ガイドハンドラー用の感情的サポート応答生成
    
    NOTE: This function uses predefined templates instead of LLM.
    TODO: Replace with LLM-based generation following CLAUDE.md principles.
    
    Args:
        emotional_context: extract_emotional_context()の結果
        user_language: ユーザーの言語
        query_type: クエリタイプ ("general", "disaster", etc.)
    
    Returns:
        共感的で支援的な応答テキスト
    """
    logger.info(f"🫂 Information Guide - Generating emotional support response for {emotional_context['emotional_state']}")
    
    emotional_state = emotional_context.get('emotional_state', 'anxious')
    intensity = emotional_context.get('intensity', 1)
    support_level = emotional_context.get('support_level', 'moderate')
    
    # 言語別の共感的開始フレーズ
    empathy_starters = {
        'ja': {
            'anxious': 'お気持ちとてもよくわかります。',
            'scared': 'お気持ちお察しします。',
            'worried': 'ご心配なお気持ち、よくわかります。',
            'stressed': 'お疲れさまです。大変な状況ですね。'
        },
        'en': {
            'anxious': 'I completely understand how you\'re feeling.',
            'scared': 'I can sense your fear, and that\'s completely natural.',
            'worried': 'Your worries are completely understandable.',
            'stressed': 'I can see you\'re going through a tough time.'
        }
    }
    
    # 言語別の安心感を与える中間部分
    reassurance_middle = {
        'ja': {
            'disaster': '災害について心配になるのは、とても自然なことです。あなたは一人ではありません。',
            'general': '不安に感じることは自然なことです。一緒に考えていきましょう。'
        },
        'en': {
            'disaster': 'It\'s completely natural to worry about disasters. You\'re not alone in feeling this way.',
            'general': 'It\'s natural to feel anxious. Let\'s work through this together.'
        }
    }
    
    # 言語別の励ましの終了部分
    encouragement_endings = {
        'ja': {
            'light': '私がサポートしますので、一緒に考えていきましょう。',
            'moderate': '一緒に準備していきましょう。きっと大丈夫です。',
            'strong': '私が全力でサポートします。いつでもお声かけください。',
            'crisis': '今すぐサポートが必要ですね。私がお手伝いします。安心してください。'
        },
        'en': {
            'light': 'I\'m here to support you. Let\'s work through this together.',
            'moderate': 'We\'ll prepare together step by step. You\'ve got this.',
            'strong': 'I\'m here to fully support you. Please reach out anytime.',
            'crisis': 'You need support right now, and I\'m here to help. You\'re safe.'
        }
    }
    
    # 実用的なアドバイス部分
    practical_advice = {
        'ja': {
            'disaster': '不安な時こそ、できることから一つずつ始めていきましょう：\\n\\n• 今の安全を確認する\\n• 必要な情報を整理する\\n• 具体的な準備を少しずつ進める',
            'general': '心配事があるときは以下のことを試してみてください：\\n\\n• 深呼吸をして落ち着く\\n• 具体的な問題を整理する\\n• 一歩ずつ解決策を考える'
        },
        'en': {
            'disaster': 'When we\'re anxious, taking small steps can help:\\n\\n• Check your current safety\\n• Gather reliable information\\n• Make preparations step by step',
            'general': 'When you\'re worried, try these steps:\\n\\n• Take deep breaths to calm down\\n• Organize your specific concerns\\n• Think through solutions step by step'
        }
    }
    
    # 言語とサポートレベルに応じて応答を構築
    lang_key = user_language if user_language in empathy_starters else 'en'
    advice_key = query_type if query_type in reassurance_middle[lang_key] else 'general'
    
    # 共感的開始
    starter = empathy_starters[lang_key].get(emotional_state, empathy_starters[lang_key]['anxious'])
    
    # 安心感を与える中間部
    middle = reassurance_middle[lang_key][advice_key]
    
    # 実用的アドバイス
    advice = practical_advice[lang_key][advice_key]
    
    # 励ましの終了
    ending = encouragement_endings[lang_key][support_level]
    
    # 応答を組み立て
    response = f"{starter}\\n\\n{middle}\\n\\n{advice}\\n\\n{ending}"
    
    # Information Guide - Generated emotional support response
    
    return response

async def _invoke_llm_for_task_specific_processing(
    task_prompt_template: str, # タスク特有のプロンプトテンプレート
    user_language: str,
    data_to_process: Dict[str, Any],
    user_input: str = ""
) -> Dict[str, Any]:
    """
    特定の情報処理タスク（ガイド要約、Web検索結果の整形など）のためにLLMを呼び出す。
    SYSTEM_PROMPT_TEXTの関連指示と、処理対象データに基づいて応答を生成する。
    """

    # プロンプトの組み立て
    # SYSTEM_PROMPT_TEXTはLLMの全体的な振る舞いを定義するため、常に含める
    # task_prompt_templateは、具体的なタスク指示とデータを含む
    # HttpUrl型を文字列に変換するヘルパー関数
    def convert_httpurl_to_str(obj):
        if isinstance(obj, list):
            return [convert_httpurl_to_str(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_httpurl_to_str(v) for k, v in obj.items()}
        # Pydantic HttpUrl型かどうかをより確実に判定
        elif obj.__class__.__name__ == 'HttpUrl' and hasattr(obj, 'scheme'):
            return str(obj)
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        # その他の型はそのまま（必要に応じて追加の型変換を実装）
        try:
            # 予期しない型の場合、文字列変換を試みる
            return str(obj)
        except Exception:
            return obj # 変換できなければそのまま返す

    processed_data = convert_httpurl_to_str(data_to_process)

    full_prompt_content = task_prompt_template.format(
        user_language=user_language,
        user_input=user_input,
        data_to_process=json.dumps(processed_data, ensure_ascii=False, indent=2)
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT_TEXT.format(user_language=user_language)), # SYSTEM_PROMPT_TEXTもuser_languageをフォーマット
        HumanMessage(content=full_prompt_content)
    ]

    raw_llm_output = await ainvoke_llm(messages, task_type="information_guide", max_tokens=8000)

    response_text_for_user = raw_llm_output
    suggestion_card_data = None

    try:
        # LLMが {"responseText": "...", "card": {...}} のようなJSON/dictを返すと期待
        if isinstance(raw_llm_output, dict):
            parsed_llm_json = raw_llm_output
        else:
            # マークダウンコードブロックの除去
            json_text = raw_llm_output.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:].rstrip('```').strip()
            elif json_text.startswith('```'):
                json_text = json_text[3:].rstrip('```').strip()
            
            # JSONパース試行
            try:
                parsed_llm_json = json.loads(json_text)
            except json.JSONDecodeError as e:
                # より堅牢なJSON修正を試行
                fixed_json = json_text
                
                # 改行文字をスペースに置換（文字列内の改行は保持）
                import re
                # 文字列外の改行のみ置換
                parts = re.split(r'("(?:[^"\\]|\\.)*")', fixed_json)
                for i in range(0, len(parts), 2):  # 偶数インデックスは文字列外
                    parts[i] = parts[i].replace('\n', ' ').replace('\t', ' ')
                fixed_json = ''.join(parts)
                
                # 末尾カンマの除去
                fixed_json = re.sub(r',\s*}', '}', fixed_json)
                fixed_json = re.sub(r',\s*]', ']', fixed_json)
                
                # エスケープされていない引用符の修正
                fixed_json = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"([^":,}\]]*?)(?<!\\)"', r'"\1\2"', fixed_json)
                
                # 不完全なJSONの場合、終了を補完
                open_braces = fixed_json.count('{') - fixed_json.count('}')
                if open_braces > 0:
                    fixed_json += '}' * open_braces
                open_brackets = fixed_json.count('[') - fixed_json.count(']')
                if open_brackets > 0:
                    fixed_json += ']' * open_brackets
                
                try:
                    parsed_llm_json = json.loads(fixed_json)
                except json.JSONDecodeError:
                    # 最後の手段：JSONの一部を抽出（改善されたパターン）
                    # エスケープされた引用符を考慮した正規表現
                    json_match = re.search(r'"responseText"\s*:\s*"((?:[^"\\]|\\.)*)"', fixed_json, re.DOTALL)
                    if json_match:
                        response_text_for_user = json_match.group(1)
                        # エスケープシーケンスをデコード
                        response_text_for_user = response_text_for_user.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                        logger.warning(f"Extracted responseText from malformed JSON: {response_text_for_user[:100]}...")
                        return {
                            "processed_text_for_user": response_text_for_user,
                            "suggestion_card_data": None
                        }
                    else:
                        raise e

        if isinstance(parsed_llm_json, dict):
            # プロンプトの期待形式に合わせて修正
            response_text_for_user = parsed_llm_json.get("responseText",
                                                       parsed_llm_json.get("processed_text_for_user", raw_llm_output))
            suggestion_card_data = parsed_llm_json.get("card",
                                                     parsed_llm_json.get("suggestion_card_data"))
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"LLM output parsing failed after cleanup attempts: {e}. Using raw output as text.")
        # フォールバック: 生のLLM出力を使用
        # ただし、guide_contentが含まれている場合は、それを直接フォーマット
        if isinstance(data_to_process, dict) and "guide_content" in data_to_process:
            guide_content = data_to_process["guide_content"]
            if guide_content and isinstance(guide_content, list) and len(guide_content) > 0:
                # ガイドコンテンツから直接応答を構築（複数の結果を統合）
                all_parts = []
                for idx, content in enumerate(guide_content[:3]):  # 最大3件まで処理
                    if isinstance(content, dict):
                        title = content.get("title", "")
                        description = content.get("description", "")
                        content_text = content.get("content", "")
                        
                        # 各コンテンツの応答テキストを構築
                        response_parts = []
                        if title:
                            response_parts.append(f"**{title}**")
                        if description:
                            response_parts.append(description)
                        if content_text:
                            # モバイル用に短縮（重要部分のみ抽出）
                            if len(content_text) > 200:
                                content_text = content_text[:200] + "..."
                            response_parts.append(content_text)
                        
                        if response_parts:
                            all_parts.append("\n\n".join(response_parts))
                
                if all_parts:
                    response_text_for_user = "\n\n---\n\n".join(all_parts)
                    logger.info(f"Fallback: Constructed response from {len(all_parts)} guide contents")

    return {
        "processed_text_for_user": response_text_for_user,
        "suggestion_card_data": suggestion_card_data
    }


def _get_default_guide_data(guide_type: str) -> Dict[str, Any]:
    """Return default guide data when mock files don't exist"""
    default_guides = {
        "emergency_kit": {
            "en": {
                "content": "Essential Emergency Kit Items:\n• Water (1 gallon per person per day for 3 days)\n• Non-perishable food (3-day supply)\n• Battery-powered or hand crank radio\n• Flashlight and extra batteries\n• First aid kit\n• Whistle for signaling\n• Face masks\n• Medications\n• Important documents\n• Cash and credit cards"
            },
            "ja": {
                "content": "防災グッズの基本リスト：\n• 水（1人1日3リットル、3日分）\n• 非常食（3日分）\n• 携帯ラジオ（電池式または手回し式）\n• 懐中電灯と予備電池\n• 救急セット\n• ホイッスル\n• マスク\n• 常備薬\n• 重要書類\n• 現金とクレジットカード"
            }
        },
        "typhoon_preparation": {
            "en": {
                "content": "Typhoon Preparation:\n• Secure outdoor items\n• Stock up on water and food\n• Charge all devices\n• Fill bathtub with water\n• Know evacuation routes\n• Have emergency contacts ready"
            },
            "ja": {
                "content": "台風対策：\n• 屋外の物を固定・収納\n• 水と食料の備蓄\n• 全ての機器を充電\n• 浴槽に水を貯める\n• 避難経路の確認\n• 緊急連絡先の準備"
            }
        },
        "earthquake_preparation": {
            "en": {
                "content": "Earthquake Preparation:\n• Secure furniture to walls\n• Know Drop, Cover, Hold On\n• Identify safe spots in each room\n• Practice evacuation drills\n• Keep shoes by bedside\n• Store emergency supplies"
            },
            "ja": {
                "content": "地震対策：\n• 家具の固定\n• DROP, COVER, HOLD ONを覚える\n• 各部屋の安全な場所を確認\n• 避難訓練の実施\n• 枕元に靴を準備\n• 防災用品の備蓄"
            }
        }
    }
    
    # Return requested guide or emergency_kit as default
    return default_guides.get(guide_type, default_guides["emergency_kit"])


async def _get_mock_preparation_guide(query: str, language: str) -> str:
    """
    Get mock preparation guide for debug/test mode using LLM-based selection
    """
    import json
    import os
    
    # Use LLM to determine which mock guide is most relevant
    prompt = f"""Analyze this disaster preparation query and determine the most relevant guide type.

Query: "{query}"

Available guide types:
- emergency_kit: General emergency supplies and disaster kit
- typhoon_preparation: Typhoon/hurricane specific preparation
- earthquake_preparation: Earthquake specific preparation

Return ONLY the guide type ID that best matches the query."""
    
    try:
        guide_type = await ainvoke_llm(prompt, task_type="analysis", temperature=0.3, max_tokens=50)
        guide_type = guide_type.strip().lower()
        
        # Mock data files don't exist - return default guide content
        guide_data = _get_default_guide_data(guide_type)
            
        # Return content in requested language
        lang_data = guide_data.get(language, guide_data.get('en', {}))
        return lang_data.get('content', 'No preparation guide available.')
        
    except Exception as e:
        logger.error(f"Error loading mock preparation guide: {e}")
        # Fallback content
        if language == "ja":
            return "防災準備ガイドの読み込みに失敗しました。"
        else:
            return "Failed to load preparation guide."

async def _extract_disaster_type_from_query(query: str) -> str:
    """
    Extract disaster type from user query using LLM
    
    Args:
        query: User input query
        
    Returns:
        Disaster type (typhoon, earthquake, tsunami, flood, etc.) or 'general'
    """
    try:
        prompt = f"""Analyze the following query and identify the disaster type being asked about.

Query: "{query}"

Return ONLY one of these disaster types:
- typhoon
- earthquake
- tsunami
- flood
- wildfire
- volcanic_eruption
- heavy_rain
- general (if no specific disaster type is mentioned)

Disaster type:"""
        
        response = await ainvoke_llm(prompt, task_type="classification", temperature=0.3)
        disaster_type = response.strip().lower()
        
        # Validate response
        valid_types = {'typhoon', 'earthquake', 'tsunami', 'flood', 'wildfire', 'volcanic_eruption', 'heavy_rain', 'general'}
        if disaster_type not in valid_types:
            logger.warning(f"Invalid disaster type extracted: {disaster_type}, defaulting to 'general'")
            return 'general'
            
        return disaster_type
        
    except Exception as e:
        logger.error(f"Failed to extract disaster type: {e}")
        return 'general'


async def _generate_context_aware_fallback(disaster_type: str, user_language: str) -> str:
    """
    Generate context-aware fallback response based on disaster type
    
    Args:
        disaster_type: Type of disaster (typhoon, earthquake, etc.)
        user_language: User's language code
        
    Returns:
        Context-appropriate safety information in English (will be translated by response_generator)
    """
    
    # Define disaster-specific safety information
    disaster_info = {
        'typhoon': {
            'title': 'Typhoon Preparation',
            'content': """Here are essential typhoon preparation steps:

**Before the Typhoon:**
• Secure outdoor items that could become projectiles
• Stock up on water, food, and emergency supplies
• Charge all devices and prepare battery backups
• Board up windows or use storm shutters
• Fill bathtubs and containers with water

**During the Typhoon:**
• Stay indoors away from windows
• Monitor official weather updates
• Be ready to move to higher floors if flooding occurs
• Never go outside during the eye of the storm

**Emergency Kit Essentials:**
• Water (3 days supply)
• Non-perishable food
• Flashlights and batteries
• First aid kit
• Important documents in waterproof container"""
        },
        'earthquake': {
            'title': 'Earthquake Safety',
            'content': """Here are essential earthquake safety actions:

**During Earthquakes:**
• Drop, Cover, and Hold On
• Stay away from windows and heavy objects
• If outdoors, move to open space away from buildings
• If driving, stop safely and stay in vehicle

**After Earthquakes:**
• Check for injuries and damage
• Be prepared for aftershocks
• Listen to official information
• Evacuate if building is damaged"""
        },
        'tsunami': {
            'title': 'Tsunami Safety',
            'content': """Here are essential tsunami safety actions:

**During Tsunami Warnings:**
• Move immediately to high ground or inland
• Never wait to see the wave
• Stay away from the coast
• Follow marked evacuation routes

**Important Rules:**
• A small tsunami at one point can be large elsewhere
• Tsunamis can continue for hours
• Never return until officials say it's safe"""
        },
        'flood': {
            'title': 'Flood Safety',
            'content': """Here are essential flood safety actions:

**Before Flooding:**
• Monitor weather alerts
• Prepare to evacuate quickly
• Move valuables to higher floors
• Turn off utilities if instructed

**During Flooding:**
• Never walk or drive through flood waters
• Move to higher ground immediately
• Avoid contact with floodwater
• Stay informed through official channels"""
        },
        'wildfire': {
            'title': 'Wildfire Safety',
            'content': """Here are essential wildfire safety actions:

**If Evacuation is Ordered:**
• Leave immediately
• Close all windows and doors
• Turn off gas and propane
• Take emergency supplies and documents

**Evacuation Preparation:**
• Keep car fueled and facing out
• Have multiple evacuation routes
• Stay informed about fire conditions"""
        },
        'volcanic_eruption': {
            'title': 'Volcanic Eruption Safety',
            'content': """Here are essential volcanic eruption safety actions:

**During Eruption:**
• Follow evacuation orders immediately
• Protect yourself from ash fall
• Stay indoors with windows and doors closed
• Wear masks or breathe through cloth

**Important Precautions:**
• Avoid low-lying areas
• Stay away from lava flows
• Be aware of mudflows in valleys"""
        },
        'heavy_rain': {
            'title': 'Heavy Rain Safety',
            'content': """Here are essential heavy rain safety actions:

**During Heavy Rain:**
• Avoid flooded areas and underpasses
• Stay away from rivers and streams
• Be alert for landslide risks
• Monitor weather updates

**Safety Measures:**
• Never drive through flooded roads
• Move to higher ground if needed
• Prepare for power outages
• Keep emergency supplies ready"""
        },
        'general': {
            'title': 'General Emergency Preparedness',
            'content': """Here are general emergency preparedness guidelines:

**Emergency Kit Essentials:**
• Water (1 gallon per person per day)
• Non-perishable food (3-day supply)
• Battery-powered radio
• Flashlight and extra batteries
• First aid kit
• Whistle for signaling
• Local maps

**Important Actions:**
• Know your evacuation routes
• Have a family communication plan
• Keep important documents safe
• Stay informed through official channels"""
        }
    }
    
    # Get appropriate disaster information
    info = disaster_info.get(disaster_type, disaster_info['general'])
    
    # Format the response
    response = f"I couldn't find specific guides in our database, but here's important safety information:\n\n**{info['title']}**\n{info['content']}\n\nFor the most current information, please check official local emergency management websites and follow guidance from authorities."
    
    return response


async def information_guide_node(state: AgentState) -> Dict[str, Any]: # LangGraphノード
    """
    情報・ガイド提供ノード。
    - 内部防災ガイドの提供 (IG-001, IG-003)
    - Web検索による情報補足 (IG-002, IG-003)
    - 非災害関連の一般的な質問への限定的対応 (IG-004)
    
    バッチ処理版：1回のLLM呼び出しで完全な応答を生成
    """
    from langchain_core.messages import AIMessage

    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "ja")
    current_task_type = state.get("current_task_type", "unknown_intent")
    is_disaster_mode = state.get("is_disaster_mode", False)
    
    # enhance_qualityからのフィードバック取得・活用
    improvement_feedback = state.get('improvement_feedback', '')
    if improvement_feedback:
        logger.info(f"🔄 Processing with improvement feedback: {improvement_feedback}")
    else:
        logger.info("🆕 Initial processing (no improvement feedback)")
    
    # primary_intentからcurrent_task_typeへのマッピング修正
    primary_intent = state.get("primary_intent", "")
    if hasattr(primary_intent, 'value'):
        primary_intent = primary_intent.value
    elif isinstance(primary_intent, str) and primary_intent.startswith("IntentCategory."):
        primary_intent = primary_intent.replace("IntentCategory.", "").lower()
    
    # disaster_preparationの場合は適切なタスクタイプを設定
    if primary_intent in ["disaster_preparation", "disaster_information", "preparation_guide"] or current_task_type == "unknown_intent":
        if primary_intent == "disaster_preparation":
            current_task_type = "disaster_preparation"
        elif primary_intent == "preparation_guide":
            current_task_type = "disaster_preparation"
        elif primary_intent == "disaster_information":
            current_task_type = "guide_request"
        elif "準備" in user_input or "対策" in user_input or "備え" in user_input or "preparation" in user_input.lower():
            current_task_type = "disaster_preparation"
        else:
            current_task_type = "guide_request"
    
    logger.info(f"Task type mapping: primary_intent='{primary_intent}' -> current_task_type='{current_task_type}'")
    
    # 感情的コンテキストの抽出を並列化のため後で実行
    emotional_context_task = None
    if current_task_type not in ["general_question_non_disaster", "chitchat"]:
        # 災害関連の質問の場合のみ感情分析を実行
        from app.services.emotional_detector_llm import detect_emotional_state_llm
        emotional_context_task = asyncio.create_task(detect_emotional_state_llm(user_input, user_language))

    node_response_text_parts: List[str] = []
    node_generated_cards: List[Dict[str, Any]] = []

    # ツールインスタンスの取得（シングルトン）
    try:
        from app.tools.guide_tools import get_guide_search_tool
        guide_search_tool = get_guide_search_tool()
    except Exception as e:
        logger.warning(f"Failed to get guide search tool: {e}")
        guide_search_tool = None
    web_search_tool = get_web_search_tool()
    
    if not web_search_tool:
        logger.warning("Web search tool not available. Some functionality may be limited.")

    logger.info(f"Information guide node activated. Task: {current_task_type}, Disaster mode: {is_disaster_mode}, Batch processing: {USE_BATCH_PROCESSING}")
    
    # バッチ処理版を使用する場合
    if USE_BATCH_PROCESSING:
        return await _information_guide_node_batch(state, current_task_type, user_input, user_language, is_disaster_mode)
    
    # 従来版の処理（フォールバック）

    # --- IG-004: 非災害関連の話題への対応 (平常時のみ) ---
    if not is_disaster_mode and current_task_type in ["chitchat", "general_question_non_disaster"]:
        logger.info(f"Handling non-disaster topic (IG-004): type='{current_task_type}', query='{user_input}'")

        data_for_llm: Dict[str, Any] = {"original_query": user_input}

        if current_task_type == "general_question_non_disaster":
            try:
                # Check if test mode is enabled
                from app.config import app_settings
                if app_settings.test_mode and app_settings.environment != "production":
                    logger.info("Test mode: Web search disabled for non-disaster general questions")
                    data_for_llm["search_error"] = "Web search is disabled in test mode"
                elif not web_search_tool:
                    logger.warning("Web search tool not available for general question")
                    data_for_llm["search_error"] = "Web search not available"
                else:
                    # Web検索用に日本語クエリを準備（キャッシュ付き翻訳）
                    japanese_web_query = await _get_cached_japanese_query(user_input, "web_search")

                    # For non-disaster related questions, get web search with content summary
                    search_results_raw = await web_search_tool.ainvoke(input={
                        "query": japanese_web_query,
                        "num_results": 1, # 1 result is sufficient
                        "summarize_content": True, # Request content summary
                        "target_language": "ja"  # Process in Japanese
                })
                # SearchResultItemのリストとして返されることを期待
                if search_results_raw:
                    # Pydanticモデルのリストを辞書のリストに変換
                    data_for_llm["web_results"] = [item for item in search_results_raw]
                    logger.info(f"Web search for non-disaster query '{user_input}' successful with summarization.")
                else:
                    logger.info(f"No web search results for non-disaster query '{user_input}'.")
            except Exception as e:
                logger.error(f"Error during web search for non-disaster query '{user_input}': {e}", exc_info=True)
                data_for_llm["web_search_error"] = "An error occurred during web search."

        # Process with LLM in user's language for normal responses
        llm_processed_output = await _invoke_llm_for_task_specific_processing(
            task_prompt_template=INFORMATION_GUIDE_RESPONSE_PROMPT_TEMPLATE,
            user_language=user_language,  # Use app-specified language
            data_to_process=data_for_llm,
            user_input=user_input
        )
        if llm_processed_output.get("processed_text_for_user"):
            node_response_text_parts.append(llm_processed_output["processed_text_for_user"])
        if llm_processed_output.get("suggestion_card_data"):
            node_generated_cards.append(llm_processed_output["suggestion_card_data"])

    # --- IG-001, IG-003: 内部防災ガイドコンテンツ提供 ---
    elif current_task_type in ["guide_contents_inquiry", "guide_request", "disaster_related", "disaster_guide_request", "disaster_preparation"]:
        # 意図分類で抽出されたガイドトピックがあればそれを使用、なければユーザー入力全体をクエリに
        guide_query = state.get("intermediate_results", {}).get("extracted_entities", {}).get("guide_topic", user_input)
        logger.info(f"Handling guide content inquiry (IG-001): Query='{guide_query}'")

        try:
            # RAG検索用に日本語クエリを準備（キャッシュ付き翻訳）
            japanese_query = await _get_cached_japanese_query(guide_query, "rag_search")

            # GuideSearchToolを日本語クエリで呼び出し
            if guide_search_tool:
                guide_tool_results_raw = await guide_search_tool.search_guides(query=japanese_query, max_results=3) # 関連性の高い3件を取得
            else:
                logger.warning("Guide search tool not available, using empty results")
                guide_tool_results_raw = []

            if guide_tool_results_raw:
                # GuideContentのリストとして返されることを期待
                # Pydanticモデルのリストを辞書のリストに変換
                data_for_llm = {"guide_content": [item for item in guide_tool_results_raw], "original_query": user_input}

                # ガイド検索結果をカード形式で表示
                for idx, guide in enumerate(guide_tool_results_raw[:3]):  # 最大3件
                    # ガイドカードの作成
                    guide_card = {
                        "card_type": "guide_info",
                        "card_id": f"guide_{guide.get('id', idx)}",
                        "title": guide.get("title", ""),
                        "content": guide.get("content", guide.get("summary", ""))[:300] + "...",  # 最初の300文字
                        "source": guide.get("source", "内閣府防災情報"),
                        "keywords": guide.get("keywords", []),
                        "action_query": f"{guide.get('title', '')}についてもっと詳しく教えて",
                        "priority": "medium"
                    }
                    node_generated_cards.append(guide_card)
                    logger.info(f"📚 Generated guide card {idx}: {guide_card['title']}")

                llm_processed_output = await _invoke_llm_for_task_specific_processing(
                    task_prompt_template=INFORMATION_GUIDE_RESPONSE_PROMPT_TEMPLATE,
                    user_language=user_language,  # Use app-specified language
                    data_to_process=data_for_llm,
                    user_input=user_input
                )
                if llm_processed_output.get("processed_text_for_user"):
                    node_response_text_parts.append(llm_processed_output["processed_text_for_user"])
                if llm_processed_output.get("suggestion_card_data"):
                    node_generated_cards.append(llm_processed_output["suggestion_card_data"])
            else:
                logger.warning(f"Guide for query '{guide_query}' not found or tool error. Trying fallback.")
                
                # Fallback handling
                from app.config import app_settings
                
                # In test mode, block web search but still try to generate context-aware fallback
                if app_settings.test_mode and app_settings.environment != "production" and web_search_tool and current_task_type in ["disaster_preparation", "guide_request"]:
                    logger.info("Test mode: Web search is disabled. Using context-aware fallback.")
                    # Extract disaster type and generate fallback
                    disaster_type = await _extract_disaster_type_from_query(user_input)
                    fallback_response = await _generate_context_aware_fallback(disaster_type, user_language)
                    node_response_text_parts.append(fallback_response)
                elif not app_settings.test_mode and web_search_tool and current_task_type in ["disaster_preparation", "guide_request"]:
                    try:
                        # Prepare Japanese query for web search
                        japanese_web_query = await _get_cached_japanese_query(user_input, "web_search")
                        
                        # Use LLM to enhance search query with relevant Japanese keywords
                        enhancement_prompt = f"""Enhance this Japanese search query for disaster preparation content.

Original query: "{japanese_web_query}"

Add relevant Japanese search keywords to find comprehensive preparation information.
Return ONLY the enhanced Japanese query, no explanations."""
                        
                        try:
                            enhanced_query = await ainvoke_llm(enhancement_prompt, task_type="translation", temperature=0.3, max_tokens=100)
                            japanese_web_query = enhanced_query.strip()
                        except Exception as e:
                            logger.warning(f"Query enhancement failed, using original: {e}")
                        
                        logger.info(f"Fallback web search with query: {japanese_web_query}")
                        
                        # Perform web search
                        search_results_raw = await web_search_tool.ainvoke(input={
                            "query": japanese_web_query,
                            "search_type": "preparation",
                            "max_results": 3,
                            "summarize_content": False
                        })
                        
                        if search_results_raw:
                            data_for_llm = {"web_results": [item for item in search_results_raw], "original_query": user_input}
                            
                            llm_processed_output = await _invoke_llm_for_task_specific_processing(
                                task_prompt_template=INFORMATION_GUIDE_RESPONSE_PROMPT_TEMPLATE,
                                user_language=user_language,
                                data_to_process=data_for_llm,
                                user_input=user_input
                            )
                            if llm_processed_output.get("processed_text_for_user"):
                                node_response_text_parts.append(llm_processed_output["processed_text_for_user"])
                            if llm_processed_output.get("suggestion_card_data"):
                                node_generated_cards.append(llm_processed_output["suggestion_card_data"])
                        else:
                            # No results from web search either
                            fallback_response = await _generate_context_aware_fallback("preparation", user_language)
                            node_response_text_parts.append(fallback_response)
                    except Exception as web_e:
                        logger.error(f"Web search fallback failed: {web_e}")
                        fallback_response = await _generate_context_aware_fallback("preparation", user_language)
                        node_response_text_parts.append(fallback_response)
                else:
                    # Extract disaster type from the query to provide context-aware fallback
                    disaster_type = await _extract_disaster_type_from_query(user_input)
                    
                    # Generate context-aware fallback response
                    fallback_response = await _generate_context_aware_fallback(disaster_type, user_language)
                    
                    node_response_text_parts.append(fallback_response)
        except Exception as e:
            logger.error(f"Error fetching or processing guide for '{guide_query}': {e}", exc_info=True)
            # Error in English (translation handled by response_generator)
            node_response_text_parts.append("An error occurred while retrieving guide information.")

    # --- IG-002, IG-003: Web検索による情報補足 (防災関連) ---
    elif current_task_type == "disaster_info_web_search":
        search_query = state.get("intermediate_results", {}).get("web_search_query", user_input)
        logger.info(f"Handling web search inquiry (IG-002): Query='{search_query}'")
        try:
            # Check if test mode is enabled
            from app.config import app_settings
            if app_settings.test_mode and app_settings.environment != "production":
                logger.info("Test mode: Web search is disabled for disaster info search")
                # Generate context-aware fallback instead
                disaster_type = await _extract_disaster_type_from_query(search_query)
                fallback_response = await _generate_context_aware_fallback(disaster_type, user_language)
                node_response_text_parts.append(fallback_response)
            elif not web_search_tool:
                logger.warning("Web search tool not available for disaster info search")
                # Error in English (translation handled by response_generator)
                node_response_text_parts.append("Web search service is not available. Please try again later.")
            else:
                # Web検索用に日本語クエリを準備（キャッシュ付き翻訳）
                japanese_search_query = await _get_cached_japanese_query(search_query, "disaster_web_search")

                # Call web search tool, summary handled by LLM so summarize_content=False
                search_results_raw = await web_search_tool.ainvoke(input={
                    "query": japanese_search_query,
                    "num_results": 3, # Get multiple results
                    "summarize_content": False, # Summary handled by LLM
                    "target_language": "ja"  # Process in Japanese
                })
                
                if search_results_raw:
                    # SearchResultItemのリストとして返されることを期待
                    data_for_llm = {"web_results": [item for item in search_results_raw], "original_query": user_input}

                    llm_processed_output = await _invoke_llm_for_task_specific_processing(
                        task_prompt_template=INFORMATION_GUIDE_RESPONSE_PROMPT_TEMPLATE,
                        user_language=user_language,  # Use app-specified language
                        data_to_process=data_for_llm,
                        user_input=user_input
                    )
                    if llm_processed_output.get("processed_text_for_user"):
                        node_response_text_parts.append(llm_processed_output["processed_text_for_user"])
                    if llm_processed_output.get("suggestion_card_data"):
                        node_generated_cards.append(llm_processed_output["suggestion_card_data"])
                else:
                    # Web検索結果が空の場合、LLMを呼び出さずにフォールバックメッセージを設定
                    logger.info(f"No web search results for query '{search_query}'. Using fallback message.")
                    # Fallback in English (translation handled by response_generator)
                    node_response_text_parts.append(f"No web information found for '{search_query}'.")
        except Exception as e:
            logger.error(f"Error during web search for '{search_query}': {e}", exc_info=True)
            # Error in English (translation handled by response_generator)
            node_response_text_parts.append("An error occurred during web search.")
    else:
        # どの処理にも当てはまらなかった場合 (タスクタイプが不明、またはこのノードの担当外)
        if not node_response_text_parts:
            logger.warning(f"Information guide node reached end without specific action for task: {current_task_type}. User input: {user_input}")
            # Fallback in English (translation handled by response_generator)
            node_response_text_parts.append("I couldn't understand your question properly. Could you please ask in different words?")

    # 感情的コンテキストの取得と感情的サポート応答の生成
    if emotional_context_task:
        try:
            emotional_context = await emotional_context_task
            state['emotional_context'] = emotional_context
            
            # 感情的サポートが必要な場合はフラグを設定（ただし具体的な情報要求の場合は抑制）
            # Check if this is a specific information request that should not prioritize emotional support
            is_specific_info_request = (
                current_task_type in ["disaster_preparation", "guide_contents_inquiry", "guide_request"] and
                emotional_context.get('intensity', 0) < 3  # Only override for low-medium emotional intensity
            )
            
            if emotional_context['should_prioritize'] and not is_specific_info_request:
                state['requires_emotional_support'] = True
                state['emotional_priority'] = 'high'
                # Information Guide - Emotional support priority enabled
            elif is_specific_info_request:
                logger.info(f"📚 Information Guide - Prioritizing information delivery over emotional support for {current_task_type}")
                
                # 感情的サポート応答を生成（ただし、具体的な情報要求の場合は抑制）
                # disaster_preparationタスクの場合は具体的な情報を優先
                if emotional_context.get('emotional_state') != 'neutral' and current_task_type not in ["disaster_preparation", "guide_contents_inquiry"]:
                    logger.info(f"🫂 Information Guide - Generating emotional support response")
                    
                    # 災害関連の場合は "disaster" を、そうでなければ "general" を指定
                    query_type = "disaster" if current_task_type in ["disaster_related", "guide_request", "disaster_guide_request"] else "general"
                    
                    emotional_response = await _generate_emotional_support_response_for_guide(
                        emotional_context, user_language, query_type
                    )
                    
                    # 感情的サポート応答を優先し、既存の応答は後ろに追加
                    if emotional_response:
                        node_response_text_parts.insert(0, emotional_response)
                        # Information Guide - Emotional support response prepended
        except Exception as e:
            logger.error(f"Failed to get emotional context: {e}")
            # Continue without emotional support

    final_response_main_text = "\n".join(filter(None, node_response_text_parts))

    # メッセージ生成 (BaseMessage型で統一)
    response_message = AIMessage(
        content=final_response_main_text,
        additional_kwargs={
            "cards": node_generated_cards,
            "task_type": current_task_type
        }
    )

    updated_intermediate_results = {
        **(state.get("intermediate_results") or {}),
        "information_guide_output_main_text_raw": final_response_main_text,
    }

    current_cards_queue = state.get("cards_to_display_queue", [])
    if not isinstance(current_cards_queue, list): current_cards_queue = []
    updated_cards_queue = current_cards_queue + node_generated_cards

    logger.info(f"Information guide node finished. Main text (brief): '{final_response_main_text[:50]}...', Cards to add: {len(node_generated_cards)}")

    # Ensure we return a dict with required fields
    updates = {
        "messages": [response_message],
        "intermediate_results": updated_intermediate_results,
        "cards_to_display_queue": updated_cards_queue,
        "current_task_type": ["task_complete_information_guide"],
        "secondary_intents": []
    }
    return {
        **updates,
        "messages": updates.get("messages", []),
        "chat_history": state.messages if hasattr(state, 'messages') else [],
        "last_response": final_response_main_text,
        "final_response_text": final_response_main_text,  # 追加: final_response_textが欠落していた
        "intermediate_results": {
            **getattr(state, 'intermediate_results', {}),
            **updates.get("intermediate_results", {})
        }
    }


async def _generate_emotional_support_response_for_guide(
    emotional_context: Dict[str, Any], 
    user_language: str, 
    query_type: str
) -> str:
    """
    Generate emotional support response using LLM for information guide handler
    """
    emotional_state = emotional_context.get('emotional_state', 'anxious')
    intensity = emotional_context.get('intensity', 1)
    support_level = emotional_context.get('support_level', 'moderate')
    
    prompt = f"""You are LinguaSafeTrip, a compassionate disaster prevention assistant.
    
User's emotional state: {emotional_state} (intensity: {intensity}/3)
Support level needed: {support_level}
Query type: {query_type}
Target language: {user_language}

Generate a warm, empathetic response that:
1. Acknowledges their emotional state
2. Provides reassurance and support
3. Offers practical steps they can take
4. Makes them feel heard and supported

The response should be natural and conversational, not formulaic.
Focus on emotional support while being helpful with their {query_type} query.

Generate the response in English (it will be translated by response_generator)."""
    
    try:
        response = await ainvoke_llm(prompt, task_type="emotional_support", temperature=0.7)
        return response.strip()
    except Exception as e:
        logger.error(f"Failed to generate emotional support response: {e}")
        # Fallback to the template-based approach
        return generate_emotional_support_response(emotional_context, user_language, query_type)


async def _information_guide_node_batch(
    state: AgentState, 
    current_task_type: str, 
    user_input: str, 
    user_language: str, 
    is_disaster_mode: bool
) -> Dict[str, Any]:
    """
    バッチ処理版の情報ガイドノード
    ガイド検索、Web検索、応答生成、カード生成、品質チェックを1回のLLM呼び出しで処理
    """
    try:
        intent = state.get("primary_intent", "information_guide")
        
        # 1. データ収集（並列実行）
        search_tasks = []
        guide_results = []
        web_results = []
        
        # ガイド検索
        try:
            from app.tools.guide_tools import get_guide_search_tool
            guide_tool = get_guide_search_tool()
            if guide_tool:
                japanese_query = await _get_cached_japanese_query(user_input, "guide_search")
                search_tasks.append(("guide", guide_tool.search_guides(japanese_query, max_results=3)))
        except Exception as e:
            logger.warning(f"Guide search setup failed: {e}")
        
        # Web検索
        try:
            web_tool = get_web_search_tool()
            if web_tool:
                web_japanese_query = await _get_cached_japanese_query(user_input, "web_search")
                search_tasks.append(("web", web_tool.ainvoke({
                    "query": web_japanese_query,
                    "num_results": 3,
                    "summarize_content": True,
                    "target_language": "ja"
                })))
        except Exception as e:
            logger.warning(f"Web search setup failed: {e}")
        
        # 並列実行
        if search_tasks:
            results = await asyncio.gather(*[task[1] for task in search_tasks], return_exceptions=True)
            for i, (task_type, result) in enumerate(zip([task[0] for task in search_tasks], results)):
                if isinstance(result, Exception):
                    logger.warning(f"{task_type} search failed: {result}")
                else:
                    if task_type == "guide":
                        guide_results = result if result else []
                    elif task_type == "web":
                        web_results = result if result else []
        
        # 2. 完全応答生成（1回のLLM呼び出し）
        response_data = await CompleteResponseGenerator.generate_complete_response(
            user_input=user_input,
            intent=intent,
            user_language=user_language,
            context_data={
                "emotional_context": state.get("emotional_context", {}),
                "location_info": state.get("location_info", {}),
                "is_emergency_mode": is_disaster_mode,
                "task_type": current_task_type
            },
            handler_type="guide",
            search_results=web_results,
            guide_content=guide_results
        )
        
        # 3. メッセージ構築
        from langchain_core.messages import AIMessage
        message = AIMessage(
            content=response_data["main_response"],
            additional_kwargs={
                "cards": response_data["suggestion_cards"],
                "follow_up_questions": response_data["follow_up_questions"],
                "priority": response_data["priority_level"],
                "handler_type": "guide"
            }
        )
        
        # 4. 結果を返す
        result = {
            "messages": [message],
            "final_response_text": response_data["main_response"],
            "quality_self_check": response_data["quality_self_check"],
            "handler_completed": True,
            "last_response": response_data["main_response"],
            "chat_history": state.get("messages", []),
            "intermediate_results": {
                **state.get("intermediate_results", {}),
                "batch_processing_used": True,
                "guide_search_results": len(guide_results),
                "web_search_results": len(web_results)
            },
            "cards_to_display_queue": response_data["suggestion_cards"]  # カードをちゃんと返す
        }
        
        # Batch guide processing completed
        return result
        
    except Exception as e:
        logger.error(f"Batch guide processing failed: {e}")
        # フォールバック: バッチ処理を無効にして従来処理を実行
        logger.info("Falling back to traditional processing")
        global USE_BATCH_PROCESSING
        original_batch_setting = USE_BATCH_PROCESSING
        USE_BATCH_PROCESSING = False
        try:
            return await information_guide_node(state)
        finally:
            USE_BATCH_PROCESSING = original_batch_setting
