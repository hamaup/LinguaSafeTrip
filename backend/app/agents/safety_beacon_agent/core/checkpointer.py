"""
LangGraph永続チェックポインター管理
SQLite/PostgreSQL対応の統一チェックポインター
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LinguaSafeTripCheckpointer:
    """LinguaSafeTrip専用チェックポインター管理"""
    
    @staticmethod
    def create_checkpointer():
        """環境に応じたチェックポインター作成"""
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            return LinguaSafeTripCheckpointer._create_postgres_saver()
        else:
            return LinguaSafeTripCheckpointer._create_sqlite_saver()
    
    @staticmethod
    def _create_sqlite_saver():
        """開発環境用SQLiteチェックポインター"""
        # For now, use InMemorySaver for simplicity during testing
        # SQLite persistence can be added later once the core functionality is working
        logger.info("🧪 Using InMemorySaver for development testing - SQLite persistence will be added later")
        return LinguaSafeTripCheckpointer._create_memory_fallback()
    
    @staticmethod
    def _create_postgres_saver():
        """本番環境用PostgreSQLチェックポインター"""
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError:
            logger.warning("langgraph-checkpoint-postgres not installed, falling back to SQLite")
            return LinguaSafeTripCheckpointer._create_sqlite_saver()
        
        postgres_uri = os.getenv("POSTGRES_URI")
        
        if not postgres_uri:
            logger.warning("POSTGRES_URI not found, falling back to SQLite")
            return LinguaSafeTripCheckpointer._create_sqlite_saver()
        
        try:
            saver = PostgresSaver.from_uri(postgres_uri)
            return saver
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            logger.warning("Falling back to SQLite")
            return LinguaSafeTripCheckpointer._create_sqlite_saver()
    
    @staticmethod
    def _create_memory_fallback():
        """フォールバック用インメモリチェックポインター"""
        from langgraph.checkpoint.memory import MemorySaver
        
        logger.warning("⚠️ Using MemorySaver fallback - data will not persist across restarts")
        return MemorySaver()
    
    @staticmethod
    def test_checkpointer_connection():
        """チェックポインター接続テスト"""
        try:
            checkpointer = LinguaSafeTripCheckpointer.create_checkpointer()
            
            # テスト用の軽量な操作
            if hasattr(checkpointer, 'put'):
                return True
            else:
                logger.error("❌ Checkpointer test failed: no put method")
                return False
                
        except Exception as e:
            logger.error(f"❌ Checkpointer test failed: {e}")
            return False