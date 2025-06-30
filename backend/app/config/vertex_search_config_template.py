import os
from typing import Optional

class VertexSearchConfig:
    """Vertex AI Search設定"""
    
    # プロジェクト設定
    PROJECT_ID = os.getenv("VERTEX_SEARCH_PROJECT_ID", "your-project-id")
    LOCATION = "global"  # Vertex AI Searchは現在globalのみサポート
    
    # Data Store設定
    DATA_STORE_ID = os.getenv("VERTEX_SEARCH_DATASTORE_ID", "your-datastore-id")
    
    # App設定
    SEARCH_APP_ID = os.getenv("VERTEX_SEARCH_APP_ID", "your-search-app-id")
    
    # キャッシュ設定
    CACHE_TTL = int(os.getenv("VERTEX_SEARCH_CACHE_TTL", "86400"))  # 24時間
    CACHE_KEY_PREFIX = "vertex_search:"
    
    # クエリ制限（無料枠内に収める）
    DAILY_QUERY_LIMIT = int(os.getenv("VERTEX_SEARCH_DAILY_LIMIT", "300"))  # 月9,000クエリ相当
    MONTHLY_QUERY_LIMIT = int(os.getenv("VERTEX_SEARCH_MONTHLY_LIMIT", "9000"))
    
    # 検索設定
    MAX_RESULTS = int(os.getenv("VERTEX_SEARCH_MAX_RESULTS", "10"))
    ENABLE_GENERATIVE_ANSWERS = os.getenv("VERTEX_SEARCH_ENABLE_GA", "false").lower() == "true"  # PoCでは無効
    
    @classmethod
    def get_serving_config(cls) -> str:
        return f"projects/{cls.PROJECT_ID}/locations/{cls.LOCATION}/collections/default_collection/dataStores/{cls.DATA_STORE_ID}/servingConfigs/default_search"
    
    @classmethod
    def get_parent(cls) -> str:
        return f"projects/{cls.PROJECT_ID}/locations/{cls.LOCATION}/collections/default_collection/dataStores/{cls.DATA_STORE_ID}"