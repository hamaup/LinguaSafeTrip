# backend/app/api/v1/endpoints/push.py
# 【send_all を使う代替案コード - 再掲】

import os
import base64
import json
import logging
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

# Firestore
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

# --- Firebase / Firestore 初期化 ---
db = None
try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.Client()
    logger.info("Firebase Admin SDK and Firestore client initialized successfully.")
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        logger.info(f"Firestore client targeting emulator: {os.getenv('FIRESTORE_EMULATOR_HOST')}")
except Exception as e:
     logger.error(f"Failed during SDK/DB initialization: {e}", exc_info=True)

# --- Pub/Sub Push リクエストモデル ---
class PubSubMessage(BaseModel): data: str; messageId: str; publishTime: str; attributes: Optional[Dict[str, str]] = None
class PubSubPushRequest(BaseModel): message: PubSubMessage; subscription: str

# --- Helper Functions ---
def _generate_notification_content(alert_info: Dict[str, Any], user_language: str) -> Dict[str, str]:
    # (変更なし)
    alert_type = alert_info.get("type", "Unknown")
    original_title = alert_info.get("title", "New Alert Information")
    link = alert_info.get("link", "")
    if user_language == "zh":
        if alert_type == "earthquake": title = f"地震警报: {original_title}"
        elif alert_type == "tsunami": title = f"海啸警报: {original_title}"
        else: title = f"新的警报: {original_title}"
        body = "请检查应用程序了解详情。"
        if link: body += f" 链接: {link}"
    else: # デフォルト英語
        if alert_type == "earthquake": title = f"Earthquake Alert: {original_title}"
        elif alert_type == "tsunami": title = f"Tsunami Alert: {original_title}"
        else: title = f"New Alert: {original_title}"
        body = "Please check the app for details."
        if link: body += f" Link: {link}"
    MAX_TITLE_LENGTH = 100; MAX_BODY_LENGTH = 200
    title = title[:MAX_TITLE_LENGTH] + ('...' if len(title) > MAX_TITLE_LENGTH else '')
    body = body[:MAX_BODY_LENGTH] + ('...' if len(body) > MAX_BODY_LENGTH else '')
    return {"title": title, "body": body}

def _get_tokens_from_firestore(alert_type: str) -> List[Dict[str, str]]:
    # (変更なし)
    if db is None: logger.error("DB client unavailable."); return []
    query = (db.collection("users").where(filter=FieldFilter("subscriptions", "array_contains", alert_type)).where(filter=FieldFilter("fcm_token", ">", "")))
    docs = query.stream()
    subscribers = []
    for doc in docs:
        user = doc.to_dict(); token = user.get("fcm_token"); language = user.get("language", "en")
        if token and isinstance(token, str) and token.strip(): subscribers.append({"token": token, "language": language})
    return subscribers

# --- ★★★ send_all を使うヘルパー関数 ★★★ ---
async def _delete_invalid_token(token: str):
    """Delete invalid FCM token from Firestore"""
    try:
        db = firestore.Client()
        # Query for the token in device_fcm_tokens collection
        docs = db.collection("device_fcm_tokens").where("token", "==", token).stream()
        
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
            
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} invalid token(s): {token[:10]}...")
        else:
            logger.warning(f"Token not found in Firestore: {token[:10]}...")
            
    except Exception as e:
        logger.error(f"Failed to delete invalid token: {e}")


def _send_fcm_via_send_all(messages: List[messaging.Message]) -> tuple[int, int]:
    """【send_all用】FCM send_all を実行し、結果を返す (同期)"""
    if not messages:
        logger.info("[SendAll Test] No messages to send.")
        return 0, 0
    try:
        # ★ messaging.send_all を使用 (Messageオブジェクトのリストを渡す)
        response: messaging.BatchResponse = messaging.send_all(messages)
        success_count = response.success_count
        failure_count = response.failure_count
        logger.info(f"[SendAll Test] Result: success={success_count}, failure={failure_count}")
        # 個々のエラーも確認できる
        if failure_count > 0:
            logger.error("[SendAll Test] Some messages failed:")
            for idx, send_resp in enumerate(response.responses):
                if not send_resp.success:
                     failed_token = messages[idx].token if idx < len(messages) and messages[idx].token else "unknown_token"
                     logger.error(f"  Failed for token {failed_token[:10]}...: {send_resp.exception}")
                     # 例外の型やメッセージで無効トークンか判断できる場合がある
                     if isinstance(send_resp.exception, messaging.UnregisteredError):
                         logger.warning(f"    Token {failed_token[:10]}... seems unregistered.")
                         # Delete invalid token from Firestore
                         # Run async function in thread since we're in sync context
                         import asyncio
                         asyncio.create_task(_delete_invalid_token(failed_token))
                     elif isinstance(send_resp.exception, messaging.InvalidArgumentError):
                         logger.error(f"    Token {failed_token[:10]}... is invalid.")
                         # Delete invalid token from Firestore
                         # Run async function in thread since we're in sync context
                         import asyncio
                         asyncio.create_task(_delete_invalid_token(failed_token))
        return success_count, failure_count
    except Exception as e:
        # send_all でのエラー (404等が発生するか確認)
        logger.error(f"[SendAll Test] Error sending FCM via send_all: {e}", exc_info=True)
        raise e # ★ エラーを再 raise
# --- ★★★ ここまで ★★★ ---

# --- FastAPI ルーター定義 ---
router = APIRouter()

@router.post(
    "/pubsub-push-handler",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Pub/Sub push 受信 → FCM send_all 送信" # Summary 変更
)
async def handle_pubsub_push(payload: PubSubPushRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="DB client not initialized")

    # 1) メッセージのデコード
    try:
        decoded = base64.b64decode(payload.message.data)
        message_str = decoded.decode("utf-8")
        alert_info = json.loads(message_str)
        alert_type = alert_info.get("type")
        if not alert_type:
            raise ValueError("Alert type missing")
        logger.info(f"Decoded Alert Info (ID): {alert_info.get('id')}")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid message data format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding message: {e}")

    # 2) Firestore から購読者トークンを取得
    try:
        def _get_tokens(alert_type: str) -> List[str]:
            docs = db.collection("users").where(filter=FieldFilter("subscriptions", "array_contains", alert_type)).stream()
            return [doc.to_dict().get("fcm_token") for doc in docs if doc.to_dict().get("fcm_token")]
        tokens: List[str] = await run_in_threadpool(_get_tokens, alert_type)
        logger.info(f"Collected {len(tokens)} tokens: {tokens}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying subscribers: {e}")

    # 3) FCM 一括送信: send_each_for_multicast を使用します
    if tokens:
        content = _generate_notification_content(alert_info, "en")
        multicast_msg = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title=content["title"],
                body=content["body"]
            ),
            data={
                "id": alert_info.get("id", ""),
                "type": alert_type,
                "link": alert_info.get("link", ""),
            }
        )
        try:
            # send_each_for_multicast uses individual /messages:send under the hood—no /batch endpoint
            batch_response = messaging.send_each_for_multicast(multicast_msg)
            logger.info(f"send_each_for_multicast: success={batch_response.success_count}, failure={batch_response.failure_count}")
            if batch_response.failure_count:
                for idx, resp in enumerate(batch_response.responses):
                    if not resp.success:
                        token = tokens[idx]
                        logger.error(f"Failed token: {token[:10]}..., error: {resp.exception}")
        except Exception as e:
            logger.error(f"Error in send_each_for_multicast: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"FCM send error: {e}")
    else:
        logger.info("No tokens to send; skipping FCM")

    return None