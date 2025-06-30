# v1 API endpoints package initialization
# 循環インポートを避けるため遅延インポート
from fastapi import APIRouter

router = APIRouter()

def include_routers():
    from .endpoints import agent_suggestions
    from .endpoints import devices
    from .endpoints import debug
    from .endpoints import chat
    from .endpoints import audio_chat
    # from .endpoints import network  # Removed - network recovery notification not needed
    from .endpoints import heartbeat
    # from .endpoints import hazard  # Removed - integrated into location tools
    # from .endpoints import unified_disaster_management  # Removed - deleted file
    # from .endpoints import disaster_chat_api  # Removed - integrated into chat.py
    # from .endpoints import proactive_suggestions  # Removed - integrated into agent_suggestions
    from .endpoints import onboarding
    from .endpoints import vector_search_settings  # ベクトル検索設定API
    # from .endpoints import pdf_rag  # Removed - PDF upload functionality not needed

    router.include_router(agent_suggestions.router)
    router.include_router(devices.router)
    router.include_router(debug.router, prefix="/debug")
    router.include_router(vector_search_settings.router)
    router.include_router(chat.router)
    router.include_router(audio_chat.router)  # Add audio chat endpoints
    # router.include_router(network.router)  # Removed - network recovery notification not needed
    router.include_router(heartbeat.router)
    # router.include_router(hazard.router)  # Removed - integrated into location tools
    # router.include_router(unified_disaster_management.router, prefix="/disaster-management")  # Removed - deleted file
    # router.include_router(disaster_chat_api.router)  # Removed - integrated into chat.py
    # router.include_router(proactive_suggestions.router)  # Removed - integrated into agent_suggestions
    router.include_router(onboarding.router)
    # router.include_router(pdf_rag.router, prefix="/pdf-rag")  # Removed - PDF upload functionality not needed
