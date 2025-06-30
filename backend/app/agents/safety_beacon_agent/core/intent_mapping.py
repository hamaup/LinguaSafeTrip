"""
Unified intent category mapping for SafetyBeacon
統一されたカテゴリマッピングを提供
"""

# 統一されたカテゴリ定義
# off_topic_handlerの出力 → 内部で使用する正規化された名前
INTENT_CATEGORY_MAPPING = {
    # 災害関連
    "disaster_info_query": "disaster_info",
    "disaster_information": "disaster_info",
    "disaster_info": "disaster_info",
    
    "evacuation_support_request": "evacuation_support",
    "evacuation_support": "evacuation_support",
    
    "emergency_help_request": "emergency_help",
    "emergency_help": "emergency_help",
    
    "disaster_preparation_guide": "disaster_preparation",
    "disaster_preparation": "disaster_preparation",
    
    "safety_confirmation_query": "safety_confirmation",
    "safety_confirmation": "safety_confirmation",
    
    "communication_request": "communication",
    "communication": "communication",
    
    # 非災害関連
    "off_topic": "off_topic",
    "greeting": "greeting",
    "small_talk": "small_talk",
    
    # エラー・不明
    "unknown": "off_topic",
    "error": "off_topic",
    "timeout": "off_topic",
    "empty_input": "off_topic"
}

# ノードマッピング
INTENT_TO_NODE_MAPPING = {
    "disaster_info": "disaster_info_node",
    "evacuation_support": "evacuation_support_node",
    "emergency_help": "disaster_info_node",
    "disaster_preparation": "information_guide_node",
    "safety_confirmation": "safety_processor",
    "communication": "disaster_info_node",
    "off_topic": "response_synthesizer",
    "greeting": "response_synthesizer",
    "small_talk": "response_synthesizer"
}

# 災害関連カテゴリのセット
DISASTER_RELATED_CATEGORIES = {
    "disaster_info",
    "evacuation_support",
    "emergency_help",
    "disaster_preparation",
    "safety_confirmation",
    "communication"
}

def normalize_intent(intent: str) -> str:
    """
    意図カテゴリを正規化された形式に変換
    
    Args:
        intent: 元の意図カテゴリ名
        
    Returns:
        正規化された意図カテゴリ名
    """
    if not intent:
        return "off_topic"
    
    # 小文字に変換
    intent_lower = str(intent).lower()
    
    # enum形式の処理 (例: "IntentCategory.disaster_info_query" → "disaster_info_query")
    if "." in intent_lower:
        intent_lower = intent_lower.split(".")[-1]
    
    # マッピングから正規化された名前を取得
    return INTENT_CATEGORY_MAPPING.get(intent_lower, "off_topic")

def get_node_for_intent(intent: str) -> str:
    """
    正規化された意図から次のノードを取得
    
    Args:
        intent: 正規化された意図カテゴリ
        
    Returns:
        次のノード名
    """
    normalized_intent = normalize_intent(intent)
    return INTENT_TO_NODE_MAPPING.get(normalized_intent, "response_synthesizer")

def is_disaster_related(intent: str) -> bool:
    """
    意図が災害関連かどうかを判定
    
    Args:
        intent: 意図カテゴリ名
        
    Returns:
        災害関連の場合True
    """
    normalized_intent = normalize_intent(intent)
    return normalized_intent in DISASTER_RELATED_CATEGORIES