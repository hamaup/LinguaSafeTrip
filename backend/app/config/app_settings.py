# backend/app/config/app_settings.py
"""
SafetyBee 統一設定管理
すべてのアプリケーション設定を一箇所で管理
機密情報は環境変数(.env)から取得、その他の設定はここで定義
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class TokenLimits:
    """トークン制限設定"""
    input_limit: int = 100000
    max_history_tokens: int = 90000
    threshold_for_flash: int = 7000

@dataclass
class ModelConfig:
    """AIモデル設定"""
    # 環境変数から取得、タスクに応じてモデルを使い分け
    # Note: Gemini 2.5 Flash-Lite is only available in global region
    # Gemini 2.5 Flash is GA but only available in US/EU regions (not in asia-northeast1)
    primary_model: str = os.getenv("PRIMARY_MODEL_NAME", "gemini-2.0-flash")
    fallback_model: str = os.getenv("FALLBACK_MODEL_NAME", "gemini-2.0-flash")
    lightweight_model: str = os.getenv("LIGHTWEIGHT_MODEL_NAME", "gemini-2.0-flash")  # 簡単なタスク用
    complex_model: str = os.getenv("COMPLEX_MODEL_NAME", "gemini-2.5-flash")  # 複雑なタスク用（GA版、US/EUのみ）
    flash_lite_model: str = os.getenv("FLASH_LITE_MODEL_NAME", "gemini-2.5-flash")  # Flash-Lite（globalのみ）

@dataclass
class CacheConfig:
    """キャッシュ設定"""
    # TTL設定（分単位）
    ttl_minutes = {
        # Firestore永続キャッシュ
        "warning": 1,           # 1分（リアルタイム性重視）
        "hazard": 1440,         # 24時間（静的データ）
        "elevation": 43200,     # 30日（ほぼ不変）
        "risk_assessment": 5,   # 5分（動的評価）
        "area_code": 0,         # 永続（変更なし）
        "shelter": 43200,       # 30日（1ヶ月）（更新頻度非常に低）

        # インメモリキャッシュ
        "translation": 1440,         # 24時間
        "language_detection": 30,    # 30分
        "llm_client": 0,            # 永続
        "news": 10080,              # 7日

        # 政府API統合キャッシュ
        "gov_api_shelter": 43200,    # 30日（1ヶ月）- 避難所情報
        "gov_api_hazard": 43200,     # 30日（1ヶ月）- ハザードマップ
        "gov_api_elevation": 43200,  # 30日（1ヶ月）- 標高情報
    }

    # メモリキャッシュサイズ設定
    memory_cache_limits = {
        "translation": 1000,         # 翻訳キャッシュ最大エントリ数
        "language_detection": 500,   # 言語検出キャッシュ最大エントリ数
        "llm_client": 50,           # LLMクライアント最大数
        "news": 100,                # ニュースキャッシュ最大エントリ数
    }

    # メモリキャッシュは自動管理（クリーンアップ不要）
    # Firestoreキャッシュは取得時に期限切れ自動削除

@dataclass
class DisasterMonitorConfig:
    """災害監視設定"""
    # テスト環境用（開発時）
    test_intervals = {
        "news_collection": 21600,      # 6時間
        "disaster_monitor": 21600,     # 6時間
        "periodic_data": 21600,        # 6時間
    }

    # 本番環境用（平常時）
    normal_intervals = {
        "news_collection": 3600,    # 1時間
        "disaster_monitor": 1800,   # 30分
        "periodic_data": 1800,      # 30分
    }

    # 緊急時
    emergency_intervals = {
        "news_collection": 900,     # 15分
        "disaster_monitor": 600,    # 10分
        "periodic_data": 600,       # 10分
    }

    # JMAフィードURL
    jma_feed_urls: List[str] = None

    def __post_init__(self):
        if self.jma_feed_urls is None:
            self.jma_feed_urls = [
                "https://www.jma.go.jp/bosai/quake/data/list.json",
                "https://www.jma.go.jp/bosai/tsunami/data/list.json",
                "https://www.jma.go.jp/bosai/warning/data/list.json"
            ]

@dataclass
class CooldownConfig:
    """提案クールダウン設定（秒単位）"""
    # 平常時のみの提案
    welcome_message_normal: int = 3600               # 1時間（デバッグ用に短縮）
    welcome_message_emergency: int = 31536000        # 365日（緊急時は実質無効化）

    quiz_reminder_normal: int = 86400                # 24時間
    quiz_reminder_emergency: int = 86400             # 24時間（緊急時は実質無効）

    seasonal_normal: int = 43200                     # 12時間（平常時のみ表示）
    seasonal_emergency: int = 31536000               # 365日（緊急時は実質無効化）

    # 両モードで使用する提案
    emergency_contact_normal: int = 300            # 5分（デバッグ用に短縮）
    emergency_contact_emergency: int = 300         # 5分（緊急時は短縮）

    low_battery_normal: int = 480                  # 8分
    low_battery_emergency: int = 240               # 4分（緊急時は短縮）

    location_normal: int = 960                     # 16分
    location_emergency: int = 300                  # 5分（緊急時は短縮）

    notification_normal: int = 480                 # 8分
    notification_emergency: int = 300              # 5分（緊急時は短縮）

    # 災害関連（緊急時により頻繁に）
    disaster_news_normal: int = 1800               # 30分（平常時は準備情報）
    disaster_news_emergency: int = 180             # 3分（緊急時は最新情報）

    # 防災準備情報（平常時のみ）
    disaster_preparedness_normal: int = 1800       # 30分（disaster_newsと同じ）
    disaster_preparedness_emergency: int = 86400   # 24時間（緊急時は実質無効）

    shelter_normal: int = 3600                     # 60分
    shelter_emergency: int = 480                   # 5分

    hazard_map_normal: int = 3600                  # 60分
    hazard_map_emergency: int = 600                # 10分

    # 緊急時のみの提案
    immediate_action_normal: int = 86400           # 24時間（平常時は実質無効）
    immediate_action_emergency: int = 300          # 5分（緊急時は頻繁に）

    sms_proposal_normal: int = 31536000             # 365日（平常時は実質無効化）
    sms_proposal_emergency: int = 600               # 10分（緊急時のみ）

    # 後方互換性のため旧形式も残す（非推奨）
    guide: int = 420                               # 削除予定
    quiz: int = 960                                # quiz_reminder用（非推奨）

@dataclass
class WebSearchConfig:
    """Web検索設定"""
    cache_duration_minutes: int = 129600  # 90日（3ヶ月）- テスト時のAPI使用量削減
    emergency_cache_minutes: int = 5      # 緊急時は5分

@dataclass
class GovernmentAPIConfig:
    """政府・自治体API設定"""
    # データ収集間隔（分単位）
    collection_intervals = {
        "shelter_data": 43200,      # 30日（1ヶ月）
        "elevation_data": 43200,    # 30日（1ヶ月）
        "hazard_data": 43200,       # 30日（1ヶ月）
    }

    # 対象地域（全国対応）
    target_regions = [
        # 関東地方
        "tokyo", "kanagawa", "saitama", "chiba", "ibaraki", "tochigi", "gunma",
        # 関西地方
        "osaka", "kyoto", "hyogo", "nara", "wakayama", "shiga",
        # 中部地方
        "aichi", "shizuoka", "gifu", "mie", "nagano", "yamanashi",
        "fukui", "ishikawa", "toyama", "niigata",
        # 九州地方
        "fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima",
        # 東北地方
        "sendai", "fukushima", "yamagata", "iwate", "aomori", "akita",
        # 北海道・沖縄
        "hokkaido", "okinawa",
        # その他主要都市
        "hiroshima", "okayama", "yamaguchi", "tokushima", "kagawa", "ehime", "kochi"
    ]

    # API設定
    tokyo_opendata_base_url: str = "https://service.api.metro.tokyo.lg.jp"
    gsi_elevation_url: str = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
    gsi_hazard_base_url: str = "https://disaportal.gsi.go.jp/hazardmap/api"

    # レート制限（requests per minute）
    rate_limits = {
        "tokyo_opendata": 60,
        "gsi_elevation": 60,
        "gsi_shelter_geojson": 5  # 大容量ファイルのため制限
    }

    # タイムアウト設定（秒）
    timeouts = {
        "tokyo_opendata": 10,
        "gsi_elevation": 5,
        "gsi_hazard": 10,
        "other_municipal": 15
    }

    # 自治体API設定ファイルパス
    municipal_apis_config_path: str = "app/resources/municipal_api_configs.json"

    def __post_init__(self):
        """設定の後処理"""
        # JSONファイルから自治体API設定を読み込み
        import json
        import os

        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "resources", "municipal_api_configs.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.municipal_apis_config = json.load(f)
            else:
                self.municipal_apis_config = {
                    "municipal_apis": {},
                    "gsi_apis": {},
                    "special_apis": {}
                }
        except Exception as e:
            import logging
            logging.warning("Failed to load municipal API config: %s", e)
            self.municipal_apis_config = {
                "municipal_apis": {},
                "gsi_apis": {},
                "special_apis": {}
            }

    def get_municipal_apis(self) -> dict:
        """自治体API設定を取得"""
        return getattr(self, 'municipal_apis_config', {}).get('municipal_apis', {})

    def get_gsi_apis(self) -> dict:
        """国土地理院API設定を取得"""
        return getattr(self, 'municipal_apis_config', {}).get('gsi_apis', {})

    def get_special_apis(self) -> dict:
        """特別API設定を取得"""
        return getattr(self, 'municipal_apis_config', {}).get('special_apis', {})

    def get_enabled_municipal_apis(self) -> dict:
        """有効な自治体API設定のみを取得"""
        municipal_apis = self.get_municipal_apis()
        return {name: config for name, config in municipal_apis.items()
                if config.get('enabled', False)}

    def get_api_config_for_region(self, region: str) -> dict:
        """地域に対応するAPI設定を取得"""
        municipal_apis = self.get_municipal_apis()

        # 直接の地域名で検索
        if region in municipal_apis:
            return municipal_apis[region]

        # 県庁所在地API設定も検索
        prefecture_apis = municipal_apis.get('prefecture_apis', {})
        if region in prefecture_apis:
            return prefecture_apis[region]

        return {}

@dataclass
class ExternalAPIConfig:
    """外部API設定"""
    osm_overpass_url: str = "https://overpass-api.de/api/interpreter"
    gsi_shelter_api_url: str = "https://maps.gsi.go.jp/xyz/hinanjo/geojson/"
    use_shelter_dummy_data: bool = False
    use_mock_disaster_data: bool = False

    # JMA Atom Feed設定
    jma_feed_urls: List[str] = None
    jma_polling_interval_minutes: float = 5.0
    jma_polling_interval_test_minutes: float = 1.0

    def __post_init__(self):
        if self.jma_feed_urls is None:
            self.jma_feed_urls = [
                "http://www.data.jma.go.jp/developer/xml/feed/regular.xml",
                "http://www.data.jma.go.jp/developer/xml/feed/extra.xml",
                "http://www.data.jma.go.jp/developer/xml/feed/eqvol.xml"
            ]

@dataclass
class CORSConfig:
    """CORS設定"""
    origins: List[str] = None

    def __post_init__(self):
        if self.origins is None:
            self.origins = [
                "http://localhost:3000",
                "http://localhost:8000"
            ]

@dataclass
class PubSubConfig:
    """PubSub設定"""
    alert_topic: str = "disaster-alerts"

@dataclass
class EmergencyConfig:
    """緊急時設定"""
    enabled: bool = True
    use_mock_data: bool = False
    alert_check_interval: int = 60  # 秒

@dataclass
class LoggingConfig:
    """ログ設定"""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    debug_llm_logs: bool = os.getenv("DEBUG_LLM_LOGS", "false").lower() == "true"

@dataclass
class TimeoutConfig:
    """タイムアウト設定"""
    # API level timeouts (seconds)
    api_timeout: float = 30.0
    api_extended_timeout: float = 45.0

    # LLM timeouts (seconds)
    llm_timeout: float = 15.0
    llm_fast_timeout: float = 8.0

    # Tool timeouts (seconds)
    web_search_timeout: float = 8.0
    web_search_fallback_timeout: float = 5.0
    guide_search_timeout: float = 5.0
    translation_timeout: float = 5.0

    # LangGraph timeouts (seconds)
    graph_execution_timeout: float = 40.0
    node_execution_timeout: float = 10.0

    # Retry configuration
    max_retries: int = 1
    retry_delay: float = 0.5

@dataclass
class GraphConfig:
    """LangGraphの実行設定"""
    recursion_limit: int = 50
    max_retries: int = 2
    timeout: float = 40.0  # Graph execution timeout in seconds
    checkpoint_namespace: str = "safety_beacon"
    enable_debug: bool = False
    use_unified_graph: bool = True  # 新統合グラフを使用するかどうか

@dataclass
class VectorSearchConfig:
    """ベクトル検索設定"""
    # ベクトル検索バックエンド選択
    # "auto" | "vertex_ai" | "faiss" | "keyword_only"
    backend: str = "auto"

    # 検索品質設定
    # "high" | "standard" | "fast"
    quality: str = "standard"

    # 結果数とスコア閾値
    max_results: int = 5
    score_threshold: float = 0.7

    # フォールバック設定
    enable_offline_fallback: bool = True
    enable_cache: bool = True
    cache_duration_minutes: int = 60

    # Vertex AI Vector Search設定（Matching Engine）
    vertex_matching_engine_index_id: str = os.getenv("VERTEX_MATCHING_ENGINE_INDEX_ID", "")
    vertex_matching_engine_endpoint_id: str = os.getenv("VERTEX_MATCHING_ENGINE_ENDPOINT_ID", "")
    vertex_matching_engine_location: str = os.getenv("VERTEX_MATCHING_ENGINE_LOCATION", "asia-northeast1")

    # デバッグ・開発設定
    debug_search_performance: bool = False

    def get_backend_for_environment(self, environment: str) -> str:
        """環境に応じた推奨バックエンドを取得"""
        if self.backend != "auto":
            return self.backend

        # 自動選択の場合
        if environment == "development":
            return "faiss"  # ローカル開発
        elif environment in ["staging", "production"]:
            return "vertex_ai"  # クラウド環境（staging/production同じ）
        else:
            return "keyword_only"  # フォールバック

    def get_embedding_model_for_backend(self, backend: str) -> str:
        """バックエンドに応じた埋め込みモデルを取得"""
        if backend == "vertex_ai":
            return "text-embedding-004"
        elif backend == "faiss":
            return "sentence-transformers/all-MiniLM-L6-v2"
        else:
            return "none"

@dataclass
class ApplicationConfig:
    """アプリケーション基本設定"""
    # サーバー設定
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # アプリケーション設定
    app_name: str = "LinguaSafeTrip"
    app_version: str = "4.0.0"
    api_version: str = "v1"
    
    # セッション設定
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 1000
    
    # レート制限
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

@dataclass
class DatabaseConfig:
    """データベース設定"""
    # Firestore設定
    max_batch_size: int = 500
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # コレクション名
    device_collection: str = "devices"
    memory_collection: str = "agent_memory"
    cache_collection: str = "cache"
    heartbeat_collection: str = "device_heartbeats"
    suggestion_collection: str = "proactive_suggestions"

@dataclass
class SecurityConfig:
    """セキュリティ設定"""
    # CORS設定
    allowed_origins: List[str] = None
    allowed_methods: List[str] = None
    allowed_headers: List[str] = None
    
    # 認証設定
    auth_enabled: bool = True
    token_expiry_hours: int = 24
    
    # データ暗号化
    encrypt_sensitive_data: bool = True
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "https://safetybee.app",
                "https://linguasafetrip.app"
            ]
        if self.allowed_methods is None:
            self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if self.allowed_headers is None:
            self.allowed_headers = ["*"]

@dataclass
class NotificationConfig:
    """通知設定"""
    # FCM設定
    fcm_enabled: bool = True
    fcm_priority: str = "high"
    fcm_time_to_live: int = 3600  # 1時間
    
    # SMS設定（Twilio等）
    sms_enabled: bool = False
    sms_provider: str = "twilio"
    sms_from_number: str = ""
    
    # Email設定
    email_enabled: bool = False
    email_provider: str = "sendgrid"
    email_from_address: str = "noreply@linguasafetrip.app"

@dataclass
class MonitoringConfig:
    """モニタリング設定"""
    # メトリクス設定
    metrics_enabled: bool = True
    metrics_interval_seconds: int = 60
    
    # ヘルスチェック
    health_check_path: str = "/health"
    readiness_check_path: str = "/ready"
    
    # アラート設定
    alert_enabled: bool = True
    alert_threshold_error_rate: float = 0.1  # 10%
    alert_threshold_response_time: float = 5.0  # 5秒

class AppSettings:
    """アプリケーション設定の統合管理"""

    def __init__(self):
        # 基本環境設定
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        # テストモード設定
        self.use_testing_mode = os.getenv("USE_TESTING_MODE", "true").lower() == "true"

        # 機密情報（環境変数から取得）
        self.gcp_project_id = self._get_required_env("GCP_PROJECT_ID")
        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", self.gcp_project_id)
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")

        # APIキー（機密情報）
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.firebase_service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT")

        # エミュレータ設定
        self.firestore_emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
        self.firebase_auth_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
        
        # 各設定セクション
        self.app = ApplicationConfig()
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.notification = NotificationConfig()
        self.monitoring = MonitoringConfig()
        self.tokens = TokenLimits()
        self.models = ModelConfig()
        self.cache = CacheConfig()
        self.disaster_monitor = DisasterMonitorConfig()
        self.cooldown = CooldownConfig()
        self.web_search = WebSearchConfig()
        self.government_api = GovernmentAPIConfig()
        self.external_apis = ExternalAPIConfig()
        self.cors = CORSConfig()
        self.pubsub = PubSubConfig()
        self.emergency = EmergencyConfig()
        self.logging = LoggingConfig()
        self.timeouts = TimeoutConfig()
        self.graph = GraphConfig()
        self.vector_search = VectorSearchConfig()

        # Firestore設定（後方互換性のため維持）
        self.history_collection_name = self.database.memory_collection

        # 設定の初期化ログ
        self._log_initialization()

    def _get_required_env(self, key: str) -> str:
        """必須環境変数を取得（未設定の場合はエラー）"""
        value = os.getenv(key)
        if not value:
            if self.environment in ["development", "test"]:
                # 開発環境ではデフォルト値を使用
                defaults = {
                    "GCP_PROJECT_ID": "safetybee-development"
                }
                value = defaults.get(key, "")
                if value:
                    logger.warning(f"Using development fallback for {key}: {value}")
                else:
                    raise ValueError(f"Required environment variable {key} is not set")
            else:
                # staging/productionでは厳密なエラー
                raise ValueError(f"Required environment variable {key} is not set in {self.environment}")
        return value

    def _log_initialization(self):
        """初期化ログを出力"""
        logger.info(f"🔧 {self.app.app_name} v{self.app.app_version} 設定が読み込まれました")
        logger.info(f"  - 環境: {self.environment}")
        logger.info(f"  - テストモード: {self.test_mode}")
        logger.info(f"  - GCPプロジェクト: {self.gcp_project_id}")
        logger.info(f"  - プライマリモデル: {self.models.primary_model}")
        logger.info(f"  - API版: {self.app.api_version}")

        # ベクトル検索設定のログ
        vector_backend = self.vector_search.get_backend_for_environment(self.environment)
        embedding_model = self.vector_search.get_embedding_model_for_backend(vector_backend)
        logger.info(f"  - バックエンド: {vector_backend} (設定値: {self.vector_search.backend})")
        logger.info(f"  - 埋め込みモデル: {embedding_model}")
        logger.info(f"  - 品質: {self.vector_search.quality}")
        logger.info(f"  - 最大結果数: {self.vector_search.max_results}")

        if self.test_mode:
            logger.info("🧪 テストモード設定:")
            for service, interval in self.disaster_monitor.test_intervals.items():
                logger.info(f"  - {service}: {interval}秒")

    # テストモード関連メソッド
    def is_test_mode(self) -> bool:
        """TEST_MODEが有効かどうかを判定"""
        return self.test_mode

    def get_test_config(self) -> Dict[str, Any]:
        """テストモード用の統一設定を取得"""
        if not self.test_mode:
            return {}

        return {
            "environment": "test",
            "use_mock_data": True,
            "log_level": "DEBUG",
            "news_collection_interval_seconds": self.disaster_monitor.test_intervals["news_collection"],
            "disaster_monitor_interval_seconds": self.disaster_monitor.test_intervals["disaster_monitor"],
            "periodic_data_interval_seconds": self.disaster_monitor.test_intervals["periodic_data"],
            "use_mock_apis": True,
            "use_mock_disaster_data": self.external_apis.use_mock_disaster_data,
            "use_shelter_dummy_data": self.external_apis.use_shelter_dummy_data,
            "use_mock_emergency_data": self.emergency.use_mock_data,
            "use_firestore_emulator": True,
            "firestore_emulator_host": self.firestore_emulator_host,
            "enable_emergency_testing": True,
            "emergency_mode_enabled": False,
            "skip_external_apis": True,
            "fast_mode": True,
        }

    def get_interval(self, service_name: str, mode: str = "normal") -> int:
        """サービス別の間隔設定を取得

        Args:
            service_name: 'news_collection', 'disaster_monitor', 'periodic_data'
            mode: 'test', 'normal', 'emergency'
        """
        if self.test_mode or mode == "test":
            return self.disaster_monitor.test_intervals.get(service_name, 15)
        elif mode == "emergency":
            return self.disaster_monitor.emergency_intervals.get(service_name, 300)
        else:
            return self.disaster_monitor.normal_intervals.get(service_name, 300)

    def get_cooldown_hours(self, suggestion_type: str, mode: str = "normal") -> float:
        """提案タイプのクールダウン時間を時間単位で取得

        Args:
            suggestion_type: 提案タイプ
            mode: "normal" または "emergency"
        """
        # モード別のキーを構築
        mode_key = f"{suggestion_type}_{mode}"

        # まずモード別設定を探す
        cooldown_seconds = getattr(self.cooldown, mode_key, None)

        # モード別設定がない場合は旧形式を試す（後方互換性）
        if cooldown_seconds is None:
            cooldown_seconds = getattr(self.cooldown, suggestion_type, None)

        # それでもない場合はデフォルト値
        if cooldown_seconds is None:
            cooldown_seconds = 600  # 10分

        return cooldown_seconds / 3600

    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.environment == "production"

    def is_staging(self) -> bool:
        """ステージング環境かどうか"""
        return self.environment == "staging"

    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.environment == "development"

    def is_cloud_environment(self) -> bool:
        """クラウド環境かどうか（staging/production）"""
        return self.environment in ["staging", "production"]

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得（デバッグ用）"""
        return {
            "environment": self.environment,
            "test_mode": self.test_mode,
            "tokens": self.tokens.__dict__,
            "models": self.models.__dict__,
            "disaster_monitor": {
                "test_intervals": self.disaster_monitor.test_intervals,
                "normal_intervals": self.disaster_monitor.normal_intervals,
                "emergency_intervals": self.disaster_monitor.emergency_intervals,
                "jma_feed_urls": self.disaster_monitor.jma_feed_urls
            },
            "cooldown": self.cooldown.__dict__,
            "web_search": self.web_search.__dict__,
            "external_apis": self.external_apis.__dict__,
            "cors": self.cors.__dict__,
            "pubsub": self.pubsub.__dict__,
            "app": self.app.__dict__,
            "database": self.database.__dict__,
            "security": self.security.__dict__,
            "notification": self.notification.__dict__,
            "monitoring": self.monitoring.__dict__,
        }

# グローバル設定インスタンス
app_settings = AppSettings()