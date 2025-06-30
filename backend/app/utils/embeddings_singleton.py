"""
SentenceTransformer埋め込みモデルのシングルトン管理
初回ロードのボトルネックを解消
"""
import logging
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)

# グローバルインスタンス
_embeddings_instance: Optional[object] = None
_embeddings_lock = Lock()


def get_embeddings_model():
    """
    埋め込みモデルのシングルトンインスタンスを取得
    初回のみモデルをロード、以降は同じインスタンスを返す
    """
    global _embeddings_instance
    
    if _embeddings_instance is None:
        with _embeddings_lock:
            # ダブルチェックロッキング
            if _embeddings_instance is None:
                logger.info("🚀 Initializing embeddings model (first time only)...")
                
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                except ImportError:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                
                # SentenceTransformerモデルを一度だけロード
                _embeddings_instance = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                
                # Embeddings model initialized successfully
    
    return _embeddings_instance


def preload_embeddings():
    """
    アプリケーション起動時に呼び出して事前ロード
    """
    logger.info("📦 Preloading embeddings model...")
    get_embeddings_model()
    # Embeddings model preloaded