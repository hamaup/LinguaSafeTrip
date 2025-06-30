"""
LangGraphチェックポイント + Firestore履歴の統合管理
2層メモリアーキテクチャの実装
"""

import uuid
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_firestore import FirestoreChatMessageHistory
from typing import Any as CompiledGraph  # Type alias for compiled graph

from app.db.firestore_client import get_db

logger = logging.getLogger(__name__)

class IntegratedMemoryManager:
    """LangGraphチェックポイント + Firestore履歴の統合管理"""
    
    def __init__(self, graph: CompiledGraph):
        self.graph = graph
    
    def generate_thread_id(self, session_id: Optional[str], device_id: str) -> str:
        """統一スレッドID生成"""
        if session_id:
            return f"{device_id}_{session_id}"
        else:
            # 新規セッション生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            new_session_id = f"session_{timestamp}_{unique_id}"
            return f"{device_id}_{new_session_id}"
    
    def extract_session_id(self, thread_id: str) -> str:
        """スレッドIDからセッションIDを抽出"""
        # "device_123_session_20241214_abc123" -> "session_20241214_abc123"
        parts = thread_id.split("_", 1)
        if len(parts) > 1:
            return parts[1]
        else:
            # フォールバック: 新規セッションID生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            return f"session_{timestamp}_{unique_id}"
    
    async def get_langgraph_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """LangGraphチェックポイントから状態取得"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state_snapshot = self.graph.get_state(config)
            
            if state_snapshot and state_snapshot.values:
                return state_snapshot.values
            
            return None
        except Exception as e:
            logger.error(f"Failed to get LangGraph state for thread {thread_id}: {e}")
            return None
    
    async def get_firestore_history(
        self, 
        session_id: str, 
        device_id: str
    ) -> List[BaseMessage]:
        """Firestore長期履歴取得"""
        try:
            # Firestoreドキュメント: デバイス+セッション複合キー
            document_id = f"{device_id}_{session_id}"
            
            history = FirestoreChatMessageHistory(
                collection="chat_histories",
                session_id=document_id,
                client=get_db()
            )
            
            messages = history.messages
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get Firestore history for {device_id}_{session_id}: {e}")
            return []
    
    async def sync_histories(
        self, 
        thread_id: str, 
        session_id: str, 
        device_id: str
    ) -> List[BaseMessage]:
        """2層メモリの同期と統合"""
        
        # LangGraphからの現在状態
        langgraph_state = await self.get_langgraph_state(thread_id)
        langgraph_history = langgraph_state.get("chat_history", []) if langgraph_state else []
        
        # Firestoreからの長期履歴
        firestore_history = await self.get_firestore_history(session_id, device_id)
        
        # 履歴の統合（重複除去）
        integrated_history = self._merge_histories(langgraph_history, firestore_history)
        
        return integrated_history
    
    def _merge_histories(
        self, 
        langgraph_history: List[BaseMessage], 
        firestore_history: List[BaseMessage]
    ) -> List[BaseMessage]:
        """履歴マージ（重複除去とタイムスタンプソート）"""
        
        all_messages = []
        seen_content = set()
        
        # すべてのメッセージを収集
        for msg in firestore_history + langgraph_history:
            # コンテンツベースの重複チェック
            content_key = f"{type(msg).__name__}:{msg.content}"
            
            if content_key not in seen_content:
                all_messages.append(msg)
                seen_content.add(content_key)
        
        # タイムスタンプでソート（メッセージにタイムスタンプがない場合は順序を維持）
        try:
            all_messages.sort(key=lambda x: getattr(x, 'timestamp', datetime.min))
        except:
            # タイムスタンプソートに失敗した場合は元の順序を維持
            pass
        
        return all_messages
    
    def format_for_response(
        self, 
        messages: List[BaseMessage]
    ) -> List[Tuple[str, str]]:
        """レスポンス形式に変換"""
        formatted = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "human"
            elif isinstance(message, AIMessage):
                role = "assistant"  
            else:
                continue
            
            formatted.append((role, message.content))
        
        return formatted
    
    async def update_firestore_with_new_message(
        self,
        session_id: str,
        device_id: str,
        user_message: str,
        ai_response: str
    ) -> None:
        """新しいメッセージをFirestoreに保存"""
        try:
            document_id = f"{device_id}_{session_id}"
            
            history = FirestoreChatMessageHistory(
                collection="chat_histories",
                session_id=document_id,
                client=get_db()
            )
            
            # 新しいメッセージを追加
            history.add_user_message(user_message)
            history.add_ai_message(ai_response)
            
        except Exception as e:
            logger.error(f"Failed to update Firestore history: {e}")
    
    def get_thread_statistics(self) -> Dict[str, Any]:
        """スレッド統計情報（今後の拡張用）"""
        return {
            "checkpointer_type": type(self.graph.checkpointer).__name__,
            "timestamp": datetime.now().isoformat()
        }