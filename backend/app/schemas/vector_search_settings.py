"""
ベクトル検索設定スキーマ
ユーザーが選択可能な検索エンジン設定
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class VectorSearchBackend(str, Enum):
    """ベクトル検索バックエンドタイプ"""
    VERTEX_AI = "vertex_ai"         # 高速検索（クラウド）
    FAISS_LOCAL = "faiss_local"     # オフライン検索（端末内）
    KEYWORD_ONLY = "keyword_only"   # 軽量検索（キーワードのみ）
    AUTO = "auto"                   # 自動選択

class VectorSearchQuality(str, Enum):
    """検索品質設定"""
    HIGH = "high"       # 高精度（遅い）
    STANDARD = "standard"  # 標準（バランス）
    FAST = "fast"       # 高速（軽量）

class VectorSearchSettings(BaseModel):
    """ベクトル検索設定"""
    backend: VectorSearchBackend = VectorSearchBackend.AUTO
    quality: VectorSearchQuality = VectorSearchQuality.STANDARD
    max_results: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_offline_fallback: bool = True
    enable_cache: bool = True
    
    class Config:
        use_enum_values = True

class UserVectorSearchPreferences(BaseModel):
    """ユーザーのベクトル検索設定"""
    user_id: str
    device_id: str
    search_settings: VectorSearchSettings
    last_updated: Optional[str] = None
    
    # パフォーマンス統計（ユーザーにフィードバック表示用）
    performance_stats: Optional[Dict[str, Any]] = Field(default_factory=dict)

class VectorSearchCapabilities(BaseModel):
    """デバイス・環境のベクトル検索能力"""
    supports_vertex_ai: bool = True
    supports_local_faiss: bool = False  # モバイルでは通常False
    supports_keyword_search: bool = True
    network_available: bool = True
    estimated_local_storage_mb: Optional[int] = None
    
    # 推奨設定
    recommended_backend: VectorSearchBackend
    recommended_quality: VectorSearchQuality