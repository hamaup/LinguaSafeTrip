"""
タイムアウト設定の統一管理
各種API、HTTP通信、検索処理のタイムアウト値を一元管理
"""
from typing import Dict
from enum import Enum


class TimeoutType(str, Enum):
    """タイムアウトタイプ"""
    HTTP_REQUEST = "http_request"     # HTTP リクエスト
    API_CALL = "api_call"             # API 呼び出し
    DATABASE = "database"             # データベース操作
    SEARCH = "search"                 # 検索処理
    LLM_INVOKE = "llm_invoke"         # LLM 呼び出し
    EMERGENCY = "emergency"           # 緊急時処理


class TimeoutConfig:
    """タイムアウト設定（秒）"""
    
    # HTTP関連タイムアウト
    HTTP_DEFAULT = 30.0              # 通常のHTTPリクエスト
    HTTP_EXTENDED = 120.0            # 長時間のHTTPリクエスト
    
    # API呼び出しタイムアウト
    API_QUICK = 10.0                 # 高速API呼び出し
    API_DEFAULT = 30.0               # 通常のAPI呼び出し
    API_EXTENDED = 60.0              # 長時間のAPI呼び出し
    
    # 検索処理タイムアウト
    SEARCH_QUICK = 5.0               # 高速検索
    SEARCH_DEFAULT = 15.0            # 通常検索
    SEARCH_EXTENDED = 30.0           # 拡張検索
    
    # LLM関連タイムアウト
    LLM_QUICK = 10.0                 # 高速LLM処理
    LLM_DEFAULT = 30.0               # 通常LLM処理
    LLM_EXTENDED = 60.0              # 長時間LLM処理
    
    # データベースタイムアウト
    DB_QUICK = 5.0                   # 高速クエリ
    DB_DEFAULT = 15.0                # 通常クエリ
    DB_EXTENDED = 30.0               # 長時間クエリ
    
    # 緊急時処理タイムアウト
    EMERGENCY_CRITICAL = 5.0         # 緊急時クリティカル
    EMERGENCY_DEFAULT = 10.0         # 緊急時通常
    
    @classmethod
    def get_timeout(cls, timeout_type: TimeoutType, operation: str = "default") -> float:
        """
        タイムアウト種別と操作に応じたタイムアウト値を取得
        
        Args:
            timeout_type: タイムアウトタイプ
            operation: 操作種別 ("quick", "default", "extended")
            
        Returns:
            float: タイムアウト値（秒）
        """
        if timeout_type == TimeoutType.HTTP_REQUEST:
            if operation == "extended":
                return cls.HTTP_EXTENDED
            else:
                return cls.HTTP_DEFAULT
                
        elif timeout_type == TimeoutType.API_CALL:
            if operation == "quick":
                return cls.API_QUICK
            elif operation == "extended":
                return cls.API_EXTENDED
            else:
                return cls.API_DEFAULT
                
        elif timeout_type == TimeoutType.SEARCH:
            if operation == "quick":
                return cls.SEARCH_QUICK
            elif operation == "extended":
                return cls.SEARCH_EXTENDED
            else:
                return cls.SEARCH_DEFAULT
                
        elif timeout_type == TimeoutType.LLM_INVOKE:
            if operation == "quick":
                return cls.LLM_QUICK
            elif operation == "extended":
                return cls.LLM_EXTENDED
            else:
                return cls.LLM_DEFAULT
                
        elif timeout_type == TimeoutType.DATABASE:
            if operation == "quick":
                return cls.DB_QUICK
            elif operation == "extended":
                return cls.DB_EXTENDED
            else:
                return cls.DB_DEFAULT
                
        elif timeout_type == TimeoutType.EMERGENCY:
            if operation == "critical":
                return cls.EMERGENCY_CRITICAL
            else:
                return cls.EMERGENCY_DEFAULT
                
        else:
            return cls.HTTP_DEFAULT  # フォールバック
    
    @classmethod
    def get_all_timeouts(cls) -> Dict[str, float]:
        """全てのタイムアウト設定を辞書で取得"""
        return {
            "http_default": cls.HTTP_DEFAULT,
            "http_extended": cls.HTTP_EXTENDED,
            "api_quick": cls.API_QUICK,
            "api_default": cls.API_DEFAULT,
            "api_extended": cls.API_EXTENDED,
            "search_quick": cls.SEARCH_QUICK,
            "search_default": cls.SEARCH_DEFAULT,
            "search_extended": cls.SEARCH_EXTENDED,
            "llm_quick": cls.LLM_QUICK,
            "llm_default": cls.LLM_DEFAULT,
            "llm_extended": cls.LLM_EXTENDED,
            "db_quick": cls.DB_QUICK,
            "db_default": cls.DB_DEFAULT,
            "db_extended": cls.DB_EXTENDED,
            "emergency_critical": cls.EMERGENCY_CRITICAL,
            "emergency_default": cls.EMERGENCY_DEFAULT,
        }