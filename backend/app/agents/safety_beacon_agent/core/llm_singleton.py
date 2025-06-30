"""
LLM Singleton Manager
LLMインスタンスの重複作成を防ぎ、パフォーマンスを最適化する
Thread-safe implementation with proper locking
"""
import logging
import os
import asyncio
from typing import Optional, Union, List, Dict, Any
from threading import Lock
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from app.config import app_settings

logger = logging.getLogger(__name__)

# === 統合: LLM呼び出しカウンター (from llm_clients.py) ===
_llm_call_counter = 0
_llm_client_cache = {}
_counter_lock = Lock()
_cache_lock = Lock()

def get_llm_call_count() -> int:
    """現在のLLM呼び出し回数を取得"""
    with _counter_lock:
        return _llm_call_counter

def reset_llm_call_count():
    """LLM呼び出し回数をリセット"""
    global _llm_call_counter
    with _counter_lock:
        _llm_call_counter = 0

def clear_llm_cache():
    """LLMクライアントキャッシュをクリア（テスト用）"""
    global _llm_client_cache
    with _cache_lock:
        _llm_client_cache.clear()
        logger.info("LLM client cache cleared")

def log_llm_prompt(prompt_text: str, call_type: str = "LLM", model_name: str = "unknown"):
    """LLMプロンプトをログに出力し、呼び出し回数をカウント"""
    global _llm_call_counter
    with _counter_lock:
        _llm_call_counter += 1

def log_llm_response(response_text: str, call_type: str = "LLM"):
    """LLM応答をログに出力"""
    if os.getenv('DEBUG_LLM_LOGS', 'false').lower() == 'true':
        pass

# === 統合: get_llm_client関数 (from llm_clients.py) ===
def get_llm_client(
    provider: str = "gemini",
    model_name: Optional[str] = None,
    streaming: bool = False,
    task_type: Optional[str] = None
) -> BaseChatModel:
    """Initialize and return a cached LLM client based on task type"""
    if not model_name and task_type:
        lightweight_model = app_settings.models.lightweight_model
        complex_model = app_settings.models.complex_model
        
        task_model_mapping = {
            "analysis": lightweight_model,
            "translation": lightweight_model,
            "intent_classification": lightweight_model,
            "entity_extraction": lightweight_model,
            "pronoun_resolution": lightweight_model,
            "keyword_extraction": lightweight_model,
            "response_generation": complex_model,
            "emotional_support": complex_model,
            "disaster_analysis": complex_model,
            "guide_summarization": complex_model,
            "web_search_synthesis": complex_model,
            "evacuation_advice": complex_model
        }
        
        model = task_model_mapping.get(task_type, app_settings.models.primary_model)
    else:
        model = model_name or app_settings.models.primary_model

    if provider.lower() != "gemini":
        raise ValueError(f"Unsupported LLM provider: {provider}")

    cache_key = f"{provider}:{model}:{streaming}"
    
    with _cache_lock:
        if cache_key not in _llm_client_cache:
            llm = ChatVertexAI(
                model=model,
                temperature=0.7,
                max_retries=3,
                max_output_tokens=4096,
                streaming=streaming,
                location=app_settings.gcp_location
            )
            _llm_client_cache[cache_key] = llm
            logger.info(f"Created new LLM client: {cache_key}")
        
        return _llm_client_cache[cache_key]


class LLMManager:
    """
    Singleton pattern for LLM instance management
    グラフ全体で単一のLLMインスタンスを共有
    """
    _instance: Optional['LLMManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        with self._lock:
            if getattr(self, '_initialized', False):
                return
            
            self._llm: Optional[BaseChatModel] = None
            self._graph_llm: Optional[BaseChatModel] = None  # グラフ作成時に渡されるLLM
            self._task_type = None  # タスクタイプを保持
            self._instance_lock = Lock()  # インスタンス固有のロック
            self._initialized = True
            logger.info("LLMManager initialized")
    
    def get_llm(self, prefer_graph_llm: bool = True, task_type: Optional[str] = None, model_name: Optional[str] = None) -> BaseChatModel:
        """
        Get LLM instance (Thread-safe)
        
        Args:
            prefer_graph_llm: If True and graph LLM is set, return it. Otherwise create new.
            task_type: Task type for model selection
            model_name: Specific model name override
        
        Returns:
            LLM instance
        """
        # グラフ作成時に渡されたLLMを優先的に使用
        if prefer_graph_llm and self._graph_llm is not None:
            return self._graph_llm
        
        with self._instance_lock:
            # タスクタイプが変わった場合は新しいインスタンスを作成
            if task_type and task_type != self._task_type:
                self._llm = get_llm_client(task_type=task_type, model_name=model_name)
                self._task_type = task_type
                logger.info(f"Created new LLM instance for task: {task_type}")
            elif self._llm is None:
                self._llm = get_llm_client(task_type=task_type, model_name=model_name)
                self._task_type = task_type
                logger.info("Created new LLM instance")
            
            return self._llm
    
    def set_graph_llm(self, llm: BaseChatModel):
        """
        Set LLM instance from graph builder (Thread-safe)
        グラフビルダーから渡されたLLMを設定
        """
        with self._instance_lock:
            self._graph_llm = llm
            logger.info("Graph LLM instance set")
    
    def reset(self):
        """Reset LLM instances (mainly for testing) (Thread-safe)"""
        with self._instance_lock:
            self._llm = None
            self._graph_llm = None
            self._task_type = None
            logger.info("LLM instances reset")


# グローバルインスタンス
llm_manager = LLMManager()


def get_shared_llm(task_type: Optional[str] = None, model_name: Optional[str] = None) -> BaseChatModel:
    """
    Get shared LLM instance
    全てのハンドラーからこの関数を呼び出す
    """
    return llm_manager.get_llm(task_type=task_type, model_name=model_name)


def set_graph_llm(llm: BaseChatModel):
    """
    Set graph LLM instance
    グラフビルダーから呼び出す
    """
    llm_manager.set_graph_llm(llm)

# === 統合: LLMユーティリティ関数 (from llm_utils.py) ===
async def ainvoke_llm(
    prompt: Union[str, List[BaseMessage]], 
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """統一的なLLM非同期呼び出し関数"""
    llm = get_llm_client(model_name=model_name, task_type=task_type)
    
    if temperature is not None:
        llm.temperature = temperature
    if max_tokens is not None:
        llm.max_output_tokens = max_tokens
    
    if isinstance(prompt, str):
        messages = [HumanMessage(content=prompt)]
    else:
        messages = prompt
    
    log_llm_prompt(
        prompt_text=str(messages),
        call_type=task_type or "general",
        model_name=model_name or "default"
    )
    
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            log_llm_response(response_text, call_type=task_type or "general")
            return response_text
            
        except Exception as e:
            error_str = str(e)
            is_retryable = any(x in error_str.lower() for x in [
                "connection reset", "503", "unavailable", "timeout", "network"
            ])
            
            if attempt < max_retries - 1 and is_retryable:
                logger.warning(f"LLM attempt {attempt + 1} failed (retryable): {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"LLM invocation failed after {attempt + 1} attempts: {e}", exc_info=True)
                return _get_fallback_response(task_type, prompt)
    
    return _get_fallback_response(task_type, prompt)

def invoke_llm(
    prompt: Union[str, List[BaseMessage]], 
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """統一的なLLM同期呼び出し関数"""
    try:
        llm = get_llm_client(model_name=model_name, task_type=task_type)
        
        if temperature is not None:
            llm.temperature = temperature
        if max_tokens is not None:
            llm.max_output_tokens = max_tokens
        
        if isinstance(prompt, str):
            messages = [HumanMessage(content=prompt)]
        else:
            messages = prompt
        
        log_llm_prompt(
            prompt_text=str(messages),
            call_type=task_type or "general",
            model_name=model_name or "default"
        )
        
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        log_llm_response(response_text, call_type=task_type or "general")
        
        return response_text
        
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}", exc_info=True)
        raise

def _get_fallback_response(task_type: Optional[str], prompt: Union[str, List]) -> str:
    """タスクタイプに応じたフォールバック応答を提供"""
    logger.warning(f"Using fallback response for task_type: {task_type}")
    
    # LLMベースの自然言語分類を使用（キーワードマッチング廃止）
    # フォールバック時は汎用的な災害対応メッセージを提供
    disaster_type = _classify_disaster_type_fallback(str(prompt) if prompt else "")
    
    if disaster_type == "tsunami":
        if task_type == "intent_classification":
            return '{"primary_intent": "evacuation_support", "confidence": 0.95, "is_disaster_related": true, "emotional_tone": "urgent", "required_action": "immediate_evacuation"}'
        elif task_type == "response_generation":
            return "TSUNAMI WARNING! Evacuate to high ground immediately! Move to at least 10 meters elevation or 3rd floor of a sturdy building. Do not wait. Follow official evacuation routes. Call 119 if you need assistance."
    elif disaster_type == "earthquake":
        if task_type == "response_generation":
            return "EARTHQUAKE! Drop, Cover, and Hold On! Get under a sturdy desk or table. Stay away from windows. After shaking stops, check for injuries and evacuate if building is damaged. Call 119 for emergencies."
    elif disaster_type == "flood":
        if task_type == "response_generation":
            return "FLOOD WARNING! Move to higher ground immediately. Avoid walking in moving water. If trapped in building, go to highest floor. Call 119 if you need rescue. Do not drive through flooded areas."
    
    safety_fallbacks = {
        "disaster_context_analysis": '{"disaster_type": "general", "urgency_level": "moderate", "safety_priority": "general_safety", "reasoning": "LLM service unavailable - using safe defaults"}',
        "shelter_safety_evaluation": '{"safe_shelters": [], "reasoning": "LLM evaluation unavailable - manual verification recommended"}',
        "immediate_safety_action": "Take immediate safety precautions. Move to a safe location and stay alert for emergency instructions. In Japan, call 119 for emergency assistance.",
        "evacuation_context_analysis": '{"disaster_type": "general", "urgency_level": "high", "safety_priority": "immediate_evacuation", "reasoning": "Service unavailable - evacuate to safe location immediately"}',
        "intent_classification": '{"primary_intent": "unknown", "confidence": 0.3, "is_disaster_related": false, "emotional_tone": "neutral", "required_action": "none"}',
        "response_generation": "I'm experiencing technical difficulties. For emergencies: Japan 119, US 911. For disasters: Evacuate to safe locations, follow official guidance.",
        "translation": "[Translation service unavailable]",
        "emergency_response": "EMERGENCY: Contact local emergency services immediately! Japan: 119, US: 911. Evacuate if in danger."
    }
    
    if task_type in safety_fallbacks:
        return safety_fallbacks[task_type]
    
    return "I cannot process your request due to technical issues. For emergencies, call 119 (Japan) or 911 (US)."

async def _classify_disaster_type_simple(prompt: str) -> str:
    """真のLLMベースの災害タイプ分類"""
    try:
        from app.prompts.disaster_prompts import DISASTER_TYPE_CLASSIFICATION_PROMPT
        
        classification_prompt = DISASTER_TYPE_CLASSIFICATION_PROMPT.format(prompt_text=prompt[:200])
        
        result = await ainvoke_llm(classification_prompt, task_type="disaster_type_classification", temperature=0.1, max_tokens=10)
        disaster_type = result.strip().lower()
        
        # 有効なタイプかチェック
        if disaster_type in ["tsunami", "earthquake", "flood"]:
            return disaster_type
        else:
            return "general"
    except:
        # エラー時は一般的な災害として処理
        return "general"

def _classify_disaster_type_fallback(prompt: str) -> str:
    """フォールバック用の災害タイプ分類（LLMが使用不可の場合のみ）"""
    # フォールバック時のみの緊急用分類
    # 本来はLLMベース自然言語分類を使用
    prompt_lower = prompt.lower()
    
    # 最小限の災害タイプ判定（緊急時のフォールバック）
    if any(term in prompt_lower for term in ["tsunami", "津波"]):
        return "tsunami"
    elif any(term in prompt_lower for term in ["earthquake", "地震"]):
        return "earthquake"
    elif any(term in prompt_lower for term in ["flood", "洪水"]):
        return "flood"
    else:
        return "general"