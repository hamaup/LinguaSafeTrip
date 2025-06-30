import logging
import json
import firebase_admin
from firebase_admin import messaging, credentials, exceptions
from typing import List, Dict, Optional, Tuple # 型ヒントを明示的にインポート
import os

logger = logging.getLogger(__name__)

# Firebase Admin SDK initialization
def initialize_firebase():
    """Firebase Admin SDKを初期化"""
    if not firebase_admin._apps:
        try:
            # 環境変数から認証情報を読み込み
            firebase_config_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
            if firebase_config_path:
                cred = credentials.Certificate(firebase_config_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with service account key")
            else:
                # デフォルト認証を試行
                firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized with default credentials")
        except Exception as e:
            logger.warning(f"Firebase Admin SDK initialization failed: {e}")

# 初期化を実行
initialize_firebase()

def _delete_invalid_fcm_token(token: str):
    """Delete invalid FCM token from Firestore (sync version)"""
    try:
        from app.db.firestore_client import get_db_sync
        
        # Use sync Firestore client
        db = get_db_sync()
        
        # Query for the token in device_fcm_tokens collection
        docs = db.collection("device_fcm_tokens").where("token", "==", token).stream()
        
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
            
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} invalid FCM token(s): {token[:10]}...")
        else:
            logger.warning(f"FCM token not found in Firestore: {token[:10]}...")
            
    except Exception as e:
        logger.error(f"Failed to delete invalid FCM token: {e}")
        # Don't fail the main flow if deletion fails

def send_fcm_notification(registration_token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
    """
    単一のデバイストークンにFCM通知を送信する。

    Args:
        registration_token: 送信先のデバイストークン。
        title: 通知のタイトル。
        body: 通知の本文。
        data: 通知に含めるカスタムデータペイロード (オプション)。

    Returns:
        送信に成功した場合は True、失敗した場合は False。
    """
    if not registration_token:
        logger.warning("Registration token is empty. Skipping FCM send.")
        return False

    # Android設定（OS通知のための優先度とチャンネル設定）
    android_config = messaging.AndroidConfig(
        priority="high",  # OS通知表示のために高優先度を設定
        notification=messaging.AndroidNotification(
            channel_id="default_channel",  # 通知チャンネルID
            sound="default",
            default_vibrate_timings=True,
            default_light_settings=True,
            # notification_priority=messaging.AndroidNotificationPriority.HIGH  # Commented out for compatibility
        )
    )
    
    # iOS設定（優先度とサウンド設定）
    apns_config = messaging.APNSConfig(
        headers={
            "apns-priority": "10"  # iOS最高優先度
        },
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                alert=messaging.ApsAlert(
                    title=title,
                    body=body
                ),
                sound="default",
                badge=1,
                content_available=True
            )
        )
    )
    
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=registration_token,
        data=data if data else None,
        android=android_config,
        apns=apns_config
    )
    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent FCM message to token {registration_token[:10]}... Response: {response}")
        return True
    except messaging.UnregisteredError as e:
        logger.warning(f"Token {registration_token[:10]}... seems unregistered: {e}")
        # Delete unregistered token from Firestore
        _delete_invalid_fcm_token(registration_token)
        return False
    except Exception as firebase_error:
        if "UnregisteredError" in str(type(firebase_error)):
            logger.warning(f"Token {registration_token[:10]}... seems unregistered: {firebase_error}")
            return False
        logger.error(f"Firebase error sending FCM to token {registration_token[:10]}... Error: {firebase_error}", exc_info=True)
        return False

def send_disaster_alert_notification(
    tokens: List[str],
    event_id: str,
    alert_level: str,
    disaster_type: str,
    headline: str,
    title_loc_key: str,
    body_loc_key: str,
    title_loc_args: List[str] = None,
    body_loc_args: List[str] = None
) -> Tuple[int, int]:
    """
    災害アラート通知を送信する（詳細設計書v3.0「4.X.2 災害時OSレベル通知用FCMメッセージ」仕様準拠）

    Args:
        tokens: 送信先FCMトークンリスト
        event_id: 災害イベントID
        alert_level: 警戒レベル (emergency/warning/info)
        disaster_type: 災害種別 (earthquake/tsunami/flood etc.)
        headline: 災害ヘッドライン
        title_loc_key: タイトルローカライズキー
        body_loc_key: 本文ローカライズキー
        title_loc_args: タイトル引数
        body_loc_args: 本文引数

    Returns:
        (成功数, 失敗数) のタプル
    """
    if not tokens:
        logger.warning("Empty token list provided. Skipping FCM send.")
        return (0, 0)
    # データペイロード構築
    data = {
        "type": "disaster_alert",
        "event_id": event_id,
        "alert_level": alert_level,
        "disaster_type": disaster_type,
        "headline": headline,
        "deeplink_action": f"/disaster_session?event_id={event_id}"
    }

    # プラットフォーム固有設定
    android_config = messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            channel_id="disaster_alerts_channel",
            sound="default"
        )
    )

    apns_config = messaging.APNSConfig(
        headers={"apns-priority": "10"},
        payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title=title_loc_key,
                        body=body_loc_key,
                        title_loc_key=title_loc_key,
                        loc_key=body_loc_key,
                        title_loc_args=title_loc_args,
                        loc_args=body_loc_args
                    ),
                    sound="default"
                ),
                headers={
                    "apns-push-type": "alert",
                    "apns-priority": "10",
                    "apns-expiration": "0",
                    "apns-collapse-id": f"disaster_alert_{event_id}"
                }
        )
    )

    # 通知メッセージ構築 (ローカライズされた通知はAPNS/Android設定で個別に指定)
    notification = messaging.Notification(
        title="",  # 空文字列 (実際の表示はプラットフォーム設定で上書き)
        body=""     # 空文字列 (実際の表示はプラットフォーム設定で上書き)
    )

    # マルチキャストメッセージ作成
    message = messaging.MulticastMessage(
        notification=notification,
        data=data,
        tokens=tokens,
        android=android_config,
        apns=apns_config
    )

    try:
        response = messaging.send_each_for_multicast(message)
        logger.info(f"Sent disaster alert to {len(tokens)} devices. Success: {response.success_count}, Failure: {response.failure_count}")
        return (response.success_count, response.failure_count)
    except Exception as e:
        if "FirebaseError" in str(type(e)):
            logger.error(f"FirebaseError sending disaster alert: {e}", exc_info=True)
        else:
            logger.error(f"Unexpected error sending disaster alert: {e}", exc_info=True)
        return (0, len(tokens))


def send_fcm_multicast_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    device_languages_map: Optional[Dict[str, str]] = None,
    notification_template_map: Optional[Dict[str, Dict[str, str]]] = None
) -> Tuple[int, int]:
    """
    複数のデバイストークンにFCM通知を一括送信する (Multicast)。
    各ユーザーの言語設定に基づいて通知内容をローカライズすることを試みる。

    Args:
        tokens: 送信先のデバイストークンのリスト。
        title: 通知のタイトル (デフォルトまたは主要言語)。
        body: 通知の本文 (デフォルトまたは主要言語)。
        data: 通知に含めるカスタムデータペイロード (オプション)。
        device_languages_map: 各トークンに対応する言語コードのマップ (オプション)。
        notification_template_map: 特定の通知タイプのための多言語メッセージテンプレート (オプション)。

    Returns:
        (成功数, 失敗数) のタプル。
    """
    if not tokens:
        logger.warning("Registration token list is empty. Skipping FCM multicast send.")
        return (0, 0)

    # Android設定（OS通知のための優先度とチャンネル設定）
    android_config = messaging.AndroidConfig(
        priority="high",  # OS通知表示のために高優先度を設定
        notification=messaging.AndroidNotification(
            channel_id="default_channel",  # 通知チャンネルID
            sound="default",
            default_vibrate_timings=True,
            default_light_settings=True,
            # notification_priority=messaging.AndroidNotificationPriority.HIGH  # Commented out for compatibility
        )
    )
    
    # iOS設定（優先度とサウンド設定）
    apns_config = messaging.APNSConfig(
        headers={
            "apns-priority": "10"  # iOS最高優先度
        },
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                alert=messaging.ApsAlert(
                    title=title,
                    body=body
                ),
                sound="default",
                badge=1,
                content_available=True
            )
        )
    )

    # デフォルトの通知を作成
    notification = messaging.Notification(
        title=title,
        body=body,
    )

    # MulticastMessageを作成
    multicast_message = messaging.MulticastMessage(
        notification=notification,
        tokens=tokens,
        data=data if data else None,
        android=android_config,
        apns=apns_config
    )

    try:
        # 送信前の詳細ログ
        if data:
            if 'disaster_proposals' in data:
                pass
        
        # send_each_for_multicastを使用
        response = messaging.send_each_for_multicast(multicast_message)
        logger.info(f"FCM send_each_for_multicast executed. Success: {response.success_count}, Failure: {response.failure_count}")
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    token = tokens[idx]
                    logger.warning(f"Failed to send to token {token[:10]}... Error: {resp.exception}")
                    if "UnregisteredError" in str(type(resp.exception)):
                        logger.warning(f"Token {token[:10]}... is unregistered. Consider removing it from the database.")
                    elif "SenderIdMismatchError" in str(type(resp.exception)):
                        logger.error(f"Sender ID mismatch for token {token[:10]}...")

        return (response.success_count, response.failure_count)

    except Exception as e:
        if "FirebaseError" in str(type(e)):
            logger.error(f"FirebaseError during FCM send_each_for_multicast: {e}", exc_info=True)
        else:
            logger.error(f"An unexpected error occurred sending FCM multicast: {e}", exc_info=True)
        return (0, len(tokens))

# send_fcm_multicast_notification の古い実装 (send_each_for_multicast を使っていたもの) は削除またはコメントアウト
# def send_fcm_multicast_notification_old(
#     registration_tokens: list[str],
#     title: str,
#     body: str,
#     data: dict | None = None,
#     device_languages: dict[str, str] | None = None # token -> language map
# ) -> tuple[int, int]:
#     """
#     複数のデバイストークンにFCM通知を一括送信する (Multicast)。
#     (旧実装：send_each_for_multicastを使用)
#     """
#     if not registration_tokens:
#         logger.warning("Registration token list is empty. Skipping FCM multicast send.")
#         return (0, 0)

#     notification = messaging.Notification(
#         title=title,
#         body=body,
#     )

#     multicast_message = messaging.MulticastMessage(
#         notification=notification,
#         tokens=registration_tokens,
#         data=data if data else None,
#     )

#     try:
#         response = messaging.send_each_for_multicast(multicast_message)
#         logger.info(f"FCM send_each_for_multicast executed. Success: {response.success_count}, Failure: {response.failure_count}")

#         if response.failure_count > 0:
#             failed_tokens = []
#             for idx, resp in enumerate(response.responses):
#                 if not resp.success:
#                     token = registration_tokens[idx]
#                     failed_tokens.append(token)
#                     logger.warning(f"Failed to send to token {token[:10]}... Error: {resp.exception}")
#                     if isinstance(resp.exception, exceptions.UnregisteredError):
#                          logger.warning(f"Token {token[:10]}... is unregistered. Consider removing it from the database.")
#                     elif isinstance(resp.exception, exceptions.SenderIdMismatchError):
#                          logger.error(f"Sender ID mismatch for token {token[:10]}...")

#         return (response.success_count, response.failure_count)

#     except exceptions.FirebaseError as e:
#         logger.error(f"FirebaseError during FCM send_each_for_multicast: {e}", exc_info=True)
#         return (0, len(registration_tokens))
#     except Exception as e:
#         logger.error(f"An unexpected error occurred sending FCM multicast: {e}", exc_info=True)
#         return (0, len(registration_tokens))
