# backend/app/agents/safety_beacon_agent/history_manager.py
import logging
import os
import uuid
import datetime
from typing import List, Tuple, Optional
from langchain_google_firestore import FirestoreChatMessageHistory
from app.db.firestore_client import get_db
from app.config import app_settings

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """クライアント側会話履歴管理クラス"""
    MAX_TURNS = 10  # 保持する最大会話ターン数
    MAX_TOKENS = 2000  # LLMプロンプト用の最大トークン数

    @staticmethod
    def add_turn(history: List[Tuple[str, str]], user_msg: str, ai_msg: str) -> List[Tuple[str, str]]:
        """新しい会話ターンを追加し、最大ターン数を超えないように調整"""
        new_history = [*history, ("user", user_msg), ("ai", ai_msg)]
        return new_history[-ChatHistoryManager.MAX_TURNS:]

    @staticmethod
    def format_for_llm(history: List[Tuple[str, str]]) -> str:
        """LLMプロンプト用に会話履歴を整形"""
        return "\n".join(f"{role}: {msg}" for role, msg in history)

    @staticmethod
    def truncate_by_tokens(history: List[Tuple[str, str]], max_tokens: int = MAX_TOKENS) -> List[Tuple[str, str]]:
        """トークン数に基づいて履歴を切り詰め (簡易実装)"""
        # TODO: tiktokenなどを用いた正確なトークンカウントを実装
        return history[-ChatHistoryManager.MAX_TURNS:]

def get_chat_message_history(session_id: str, device_id: str) -> FirestoreChatMessageHistory:
    """Firestoreから会話履歴を取得 (トップレベル関数)

    Args:
        session_id: 会話セッションID
        device_id: ユーザーデバイスID (形式: [a-zA-Z0-9-]{8,64})
    """
    try:
        # セッションID生成ロジックを追加
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:16]}"
            logger.info(f"Generated new session ID: {session_id}")

        if not device_id:
            logger.error("Device ID is required")
            raise ValueError("Device ID cannot be empty")

        firestore_client = get_db()
        collection_name = app_settings.history_collection_name or "chat_histories"

        # Firestoreエミュレータ設定の確認
        if os.getenv("FIRESTORE_EMULATOR_HOST"):
            pass
        
        # デバイスIDベースのドキュメントID（セッションIDは無視して、デバイスごとに1つの履歴）
        document_id = device_id
        logger.info(f"Using document ID: {document_id} for device: {device_id}")

        # メッセージ履歴の初期化
        try:
            history = FirestoreChatMessageHistory(
                collection=collection_name,
                session_id=document_id,  # デバイスIDをドキュメントIDとして使用
                client=firestore_client
            )
            return history
        except Exception as init_error:
            logger.error(f"History initialization failed: {init_error}", exc_info=True)
            # フォールバックせずにエラーを再発生
            raise RuntimeError(f"History initialization failed for device {device_id}") from init_error
    except Exception as e:
        logger.error(f"Chat history setup failed: {str(e)}", exc_info=True)
        logger.warning("Falling back to in-memory chat history due to Firestore connection failure")
        # Firestoreエラーの場合はインメモリ履歴にフォールバック
        from langchain_core.chat_history import InMemoryChatMessageHistory
        return InMemoryChatMessageHistory()
