"""
タイムアウト設定
実際の処理時間を考慮した現実的な値
"""
from enum import Enum

class TimeoutSettings:
    """タイムアウト設定クラス"""
    
    # データ取得系（Firestore/キャッシュ）
    FIRESTORE_READ = 5.0        # Firestore読み取り: 5秒（ネットワーク遅延考慮）
    FIRESTORE_WRITE = 8.0       # Firestore書き込み: 8秒（大きなドキュメント考慮）
    CACHE_READ = 2.0            # キャッシュ読み取り: 2秒
    CACHE_WRITE = 3.0           # キャッシュ書き込み: 3秒
    
    # 外部API呼び出し
    GEOCODING_API = 5.0         # ジオコーディング: 5秒
    ELEVATION_API = 5.0         # 標高API: 5秒
    JMA_API = 10.0              # 気象庁API: 10秒（公的APIは遅い場合がある）
    WEB_SEARCH_API = 8.0        # Web検索API: 8秒
    NEWS_API = 6.0              # ニュースAPI: 6秒
    
    # LLM呼び出し
    LLM_QUICK = 10.0            # 簡単なLLMタスク: 10秒（分類、短い生成）
    LLM_STANDARD = 20.0         # 標準的なLLMタスク: 20秒（応答生成）
    LLM_COMPLEX = 30.0          # 複雑なLLMタスク: 30秒（品質チェック、複数タスク）
    LLM_BATCH = 40.0            # バッチLLMタスク: 40秒（複数処理統合）
    
    # 内部処理
    HISTORY_FETCH = 5.0         # 履歴取得: 5秒（複数ドキュメント）
    LOCATION_PARSE = 3.0        # 位置情報解析: 3秒（ジオコーディング含む）
    DEVICE_DATA_FETCH = 4.0     # デバイスデータ取得: 4秒
    USER_PROFILE_FETCH = 4.0    # ユーザープロファイル取得: 4秒
    
    # 統合処理
    PARALLEL_TASK_GROUP = 15.0  # 並列タスクグループ: 15秒（最も遅いタスク＋余裕）
    AGENT_GRAPH_TOTAL = 60.0    # エージェント全体: 60秒
    
    # ベクトル検索
    VECTOR_SEARCH = 5.0         # ベクトル検索: 5秒
    EMBEDDING_GENERATION = 3.0   # 埋め込み生成: 3秒
    
    # 翻訳
    TRANSLATION_QUICK = 5.0     # 短文翻訳: 5秒
    TRANSLATION_BATCH = 15.0    # バッチ翻訳: 15秒
    
    # その他
    FILE_READ = 2.0             # ファイル読み取り: 2秒
    FILE_WRITE = 3.0            # ファイル書き込み: 3秒
    HTTP_REQUEST_DEFAULT = 10.0  # デフォルトHTTPリクエスト: 10秒


class TimeoutContext(str, Enum):
    """タイムアウトのコンテキスト"""
    CRITICAL = "critical"       # クリティカルパス（ユーザー待機中）
    BACKGROUND = "background"   # バックグラウンド処理
    BATCH = "batch"            # バッチ処理


def get_timeout(operation: str, context: TimeoutContext = TimeoutContext.CRITICAL) -> float:
    """
    操作とコンテキストに基づいてタイムアウト値を取得
    
    Args:
        operation: 操作名（TimeoutSettingsの属性名）
        context: 処理のコンテキスト
        
    Returns:
        タイムアウト値（秒）
    """
    base_timeout = getattr(TimeoutSettings, operation, TimeoutSettings.HTTP_REQUEST_DEFAULT)
    
    # コンテキストに基づいて調整
    if context == TimeoutContext.CRITICAL:
        # クリティカルパスは基本値のまま
        return base_timeout
    elif context == TimeoutContext.BACKGROUND:
        # バックグラウンドは1.5倍の余裕
        return base_timeout * 1.5
    elif context == TimeoutContext.BATCH:
        # バッチ処理は2倍の余裕
        return base_timeout * 2.0
    
    return base_timeout


# 使いやすいヘルパー関数
def get_llm_timeout(task_complexity: str = "standard") -> float:
    """LLMタスクのタイムアウト値を取得"""
    complexity_map = {
        "quick": TimeoutSettings.LLM_QUICK,
        "standard": TimeoutSettings.LLM_STANDARD,
        "complex": TimeoutSettings.LLM_COMPLEX,
        "batch": TimeoutSettings.LLM_BATCH
    }
    return complexity_map.get(task_complexity, TimeoutSettings.LLM_STANDARD)


def get_api_timeout(api_type: str) -> float:
    """外部APIのタイムアウト値を取得"""
    api_map = {
        "geocoding": TimeoutSettings.GEOCODING_API,
        "elevation": TimeoutSettings.ELEVATION_API,
        "jma": TimeoutSettings.JMA_API,
        "web_search": TimeoutSettings.WEB_SEARCH_API,
        "news": TimeoutSettings.NEWS_API
    }
    return api_map.get(api_type, TimeoutSettings.HTTP_REQUEST_DEFAULT)


# デバッグ用：全タイムアウト設定を表示
def print_timeout_settings():
    """全タイムアウト設定を表示"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=== Timeout Settings ===")
    for attr in dir(TimeoutSettings):
        if not attr.startswith("_") and isinstance(getattr(TimeoutSettings, attr), (int, float)):
            logger.info("%s: %ss", attr, getattr(TimeoutSettings, attr))