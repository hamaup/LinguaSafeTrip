import logging

# --- アプリケーション内のツールをインポート ---
# パスは実際のプロジェクト構造に合わせてください
from app.tools.alert_tools import DisasterAlertAssessmentTool
from app.tools.notification_tools import trigger_fcm_push, notify_network_restored
from app.tools.contact_tools import EmergencyContactManagementTool
from app.tools.guide_tools import get_guide_search_tool
# SMS tools removed - functionality handled by frontend
from app.tools.web_search_tools import get_web_search_tool
from app.tools.location_tools import LocationBasedDisasterInfoTool, NearbyShelterInfoTool
# 他に必要なツールがあればここに追加

logger = logging.getLogger(__name__)

# --- ツールのリスト ---
# LangChainエージェントに渡すツールのリストを定義します。
# 各ツールは @tool デコレータなどで正しくLangChainツールとして定義されている必要があります。
def get_tools():
    """ツール取得 - キャッシュがあれば使用、なければ初期化"""
    global _tools_cache, _tools_ready
    
    # キャッシュされたツールがあれば即座に返す
    if _tools_ready and _tools_cache:
        return _tools_cache
    
    # キャッシュがない場合は同期初期化（最初のリクエストのみ）
    if not _tools_ready:
        logger.info("⏳ Initializing tools on first request...")
        
    try:
        # Get unified tools
        web_search_tool = get_web_search_tool()
        guide_search_tool = get_guide_search_tool()
        
        initialized_tools = [
            DisasterAlertAssessmentTool(),
            EmergencyContactManagementTool(),
            LocationBasedDisasterInfoTool(),
            NearbyShelterInfoTool()
        ]
        
        # Add web search tool if available
        if web_search_tool:
            initialized_tools.append(web_search_tool)
            
        # Add unified RAG tool if available
        if guide_search_tool:
            initialized_tools.append(guide_search_tool)
        
        # キャッシュに保存
        _tools_cache = initialized_tools
        _tools_ready = True
        
        logger.info(f"✅ Initialized {len(initialized_tools)} tools")
        return initialized_tools
        
    except Exception as e:
        logger.error(f"Tool initialization error: {e}", exc_info=True)
        # フォールバック：基本ツールのみ
        fallback_tools = [
            DisasterAlertAssessmentTool(),
            EmergencyContactManagementTool(),
            LocationBasedDisasterInfoTool(),
            NearbyShelterInfoTool()
        ]
        logger.warning(f"Using fallback tools only: {len(fallback_tools)} tools")
        return fallback_tools

# グローバルツール状態管理
_tools_cache = None
_tools_initialization_lock = False
_tools_ready = False

def is_tools_ready():
    """ツールが初期化済みかチェック"""
    return _tools_ready

def preload_tools():
    """バックグラウンドでツールを事前ロード"""
    global _tools_cache, _tools_initialization_lock, _tools_ready
    
    if _tools_initialization_lock or _tools_ready:
        return
        
    _tools_initialization_lock = True
    logger.info("🔧 Starting background tool preload...")
    
    try:
        _tools_cache = get_tools()
        _tools_ready = True
        logger.info(f"✅ Tools preloaded successfully: {len(_tools_cache)} tools ready")
    except Exception as e:
        logger.error(f"❌ Tool preload failed: {e}")
        _tools_cache = None
    finally:
        _tools_initialization_lock = False

# 互換性のためのグローバル変数（deprecated）
tools = []
