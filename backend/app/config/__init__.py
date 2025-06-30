# backend/app/config/__init__.py
"""
SafetyBee 統一設定管理
すべての設定を一箇所で管理
"""

from .app_settings import app_settings

__all__ = [
    "app_settings"
]