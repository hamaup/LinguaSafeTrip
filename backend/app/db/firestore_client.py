# backend/app/db/firestore_client.py (Emulator connection enforced)
from google.cloud import firestore
from google.cloud.firestore import Client as FirestoreClient, AsyncClient as AsyncFirestoreClient
from google.auth.credentials import AnonymousCredentials # For emulator
from typing import Optional
import os
import logging
import asyncio

logger = logging.getLogger(__name__)
db_client_instance: FirestoreClient | None = None
async_db_client_instance: AsyncFirestoreClient | None = None

def get_db() -> FirestoreClient:
    """同期用Firestoreクライアントを取得"""
    global db_client_instance
    if db_client_instance is None:
        _initialize_firestore()
    return db_client_instance

async def get_async_db() -> AsyncFirestoreClient:
    """非同期用Firestoreクライアントを取得"""
    global async_db_client_instance
    if async_db_client_instance is None:
        await _initialize_async_firestore()
    return async_db_client_instance

def get_db_sync() -> FirestoreClient:
    """同期用Firestoreクライアントを取得 (get_dbのエイリアス - 明確な命名)"""
    return get_db()

async def close_async_db(client: AsyncFirestoreClient) -> None:
    """非同期Firestoreクライアントをクローズ"""
    try:
        # AsyncClient 自身を閉じる（同期メソッドなので await 不要）
        client.close()

        # 内部の gRPC チャンネルをクローズ（属性名は環境で異なることがあるので両方チェック）
        transport = client._firestore_api.transport
        channel = getattr(transport, 'grpc_channel', None) or getattr(transport, '_grpc_channel', None)
        if channel:
            await channel.close()
    except Exception as e:
        logger.warning(f"Failed to close async Firestore client: {e}")
    finally:
        # キャッシュをクリアして、次回の get_async_db() で新しいインスタンスを作成する
        global async_db_client_instance
        async_db_client_instance = None

def _initialize_firestore() -> None:
    """同期Firestoreクライアントを初期化"""
    global db_client_instance
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    if not gcp_project_id:
        raise RuntimeError("GCP_PROJECT_ID is not set in environment variables")

    try:
        firestore_emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
        if firestore_emulator_host:
            logger.info(f"Using Firestore emulator at {firestore_emulator_host}")
            credentials = AnonymousCredentials()
            db_client_instance = firestore.Client(
                project=gcp_project_id,
                credentials=credentials
            )
        else:
            logger.info("Initializing production Firestore client")
            db_client_instance = firestore.Client(project=gcp_project_id)
        logger.info("Firestore client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}", exc_info=True)
        raise

async def _initialize_async_firestore() -> None:
    """非同期Firestoreクライアントを初期化"""
    global async_db_client_instance
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    if not gcp_project_id:
        raise RuntimeError("GCP_PROJECT_ID is not set in environment variables")

    try:
        firestore_emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
        if firestore_emulator_host:
            logger.info(f"Using Firestore emulator (async) at {firestore_emulator_host}")
            credentials = AnonymousCredentials()
            async_db_client_instance = AsyncFirestoreClient(
                project=gcp_project_id,
                credentials=credentials
            )
        else:
            logger.info("Initializing production Firestore async client")
            async_db_client_instance = AsyncFirestoreClient(project=gcp_project_id)
        logger.info("Async Firestore client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize async Firestore client: {e}", exc_info=True)
        raise
