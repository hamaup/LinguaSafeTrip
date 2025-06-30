import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/widgets/foreground_notification.dart';
import 'package:frontend/core/services/local_notification_service.dart';

// グローバルなProviderコンテナ（アラート通知用）
ProviderContainer? _globalProviderContainer;

// バックグラウンドメッセージハンドラー（トップレベル関数である必要がある）
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  if (kDebugMode) {
    print('バックグラウンドメッセージを受信: ${message.messageId}');
    print('Title: ${message.notification?.title}');
    print('Body: ${message.notification?.body}');
    print('Data: ${message.data}');
  }
  
  // バックグラウンドでは通知は自動的に表示される
  // アプリが起動した時に処理されるようにデータを保存することも可能
}

class FCMService {
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final LocalNotificationService _localNotificationService = LocalNotificationService();
  static BuildContext? _context;
  
  // ProviderContainerを設定
  static void setProviderContainer(ProviderContainer container) {
    _globalProviderContainer = container;
  }
  
  // BuildContextを設定（フォアグラウンド通知用）
  static void setContext(BuildContext context) {
    _context = context;
  }

  Future<void> initialize() async {
    // ローカル通知サービスを初期化
    await _localNotificationService.initialize();
    
    // バックグラウンドメッセージハンドラーを設定
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // iOS (およびWeb) での通知許可リクエスト
    NotificationSettings settings = await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    if (kDebugMode) {
      print('通知許可状態: ${settings.authorizationStatus}');
    }

    // FCMトークンの取得と表示 (デバッグ用)
    await _printAndCacheFCMToken();

    // フォアグラウンドメッセージ受信リスナー
    FirebaseMessaging.onMessage.listen((RemoteMessage message) async {
      if (kDebugMode) {
        print('フォアグラウンドメッセージを受信: ${message.messageId}');
        print('Title: ${message.notification?.title}');
        print('Body: ${message.notification?.body}');
        print('Data: ${message.data}');
      }
      
      // 災害アラートの統一判定
      if (_isDisasterAlert(message)) {
        _handleDisasterAlert(message);
        // 緊急アラートの場合はOSレベル通知も表示
        await _showOSLevelNotification(message, isEmergency: true);
      } else {
        // 一般通知の場合
        await _showOSLevelNotification(message, isEmergency: false);
      }
      
      // フォアグラウンドでも通知を表示したい場合は、
      // ローカル通知ライブラリを使用して表示する
      _showForegroundNotification(message);
    });

    // 通知タップ時の処理（アプリが終了状態から起動された場合）
    FirebaseMessaging.instance.getInitialMessage().then((RemoteMessage? message) {
      if (message != null) {
        if (kDebugMode) {
          print('アプリ起動時メッセージ: ${message.messageId}');
        }
        _handleNotificationTap(message);
      }
    });

    // 通知タップ時の処理（アプリがバックグラウンドから復帰した場合）
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      if (kDebugMode) {
        print('通知タップでアプリ復帰: ${message.messageId}');
      }
      _handleNotificationTap(message);
    });

    // FCMトークンが更新された際のリスナー設定
    _firebaseMessaging.onTokenRefresh.listen((newToken) {
      if (kDebugMode) {
        print("FCMトークンが更新されました: $newToken");
      }
      // 新しいトークンをサーバーに送信する処理をここに追加
    });
  }

  Future<void> _showOSLevelNotification(RemoteMessage message, {required bool isEmergency}) async {
    final title = message.notification?.title ?? 'SafeBeee通知';
    final body = message.notification?.body ?? '';
    
    if (isEmergency) {
      await _localNotificationService.showEmergencyNotification(
        title: title,
        body: body,
        payload: message.data.toString(),
      );
    } else {
      await _localNotificationService.showNotification(
        title: title,
        body: body,
        payload: message.data.toString(),
      );
    }
    
    if (kDebugMode) {
      print('OSレベル通知表示: $title (Emergency: $isEmergency)');
    }
  }

  void _showForegroundNotification(RemoteMessage message) async {
    // フォアグラウンドでの通知表示
    if (_context != null) {
      final title = message.notification?.title ?? 'SafeBeee通知';
      final body = message.notification?.body ?? '';
      
      // オーバーレイで通知を表示
      ForegroundNotificationOverlay.show(
        context: _context!,
        title: title,
        body: body,
        duration: const Duration(seconds: 6),
        onTap: () {
          // 通知タップ時の処理
          _handleNotificationTap(message);
        },
      );
      
      if (kDebugMode) {
        print('フォアグラウンド通知表示: $title');
      }
    } else {
      if (kDebugMode) {
        print('フォアグラウンド通知表示（コンテキストなし）: ${message.notification?.title}');
      }
    }
  }

  void _handleNotificationTap(RemoteMessage message) {
    // 通知タップ時の処理
    if (kDebugMode) {
      print('通知がタップされました: ${message.data}');
    }
    
    // 災害アラートの統一判定
    if (_isDisasterAlert(message)) {
      _handleDisasterAlert(message);
    }
    
    // データに基づいて適切な画面に遷移
    final data = message.data;
    if (data.containsKey('click_action')) {
      // 画面遷移処理をここに実装
      if (kDebugMode) {
        print('画面遷移: ${data['click_action']}');
      }
    }
  }

  /// 災害アラートかどうかを統一判定
  bool _isDisasterAlert(RemoteMessage message) {
    return message.data.containsKey('disaster_type') || 
           message.data.containsKey('alert_type') ||
           message.data.containsKey('disaster_level');
  }

  void _handleDisasterAlert(RemoteMessage message) {
    if (kDebugMode) {
      print('[FCMService] === HANDLING DISASTER ALERT ===');
      print('[FCMService] Message data: ${message.data}');
    }
    
    if (_globalProviderContainer == null) {
      if (kDebugMode) {
        print('[FCMService] WARNING: Provider container not set, cannot notify timeline');
      }
      return;
    }
    
    try {
      // Import the timeline provider
      final timelineNotifier = _globalProviderContainer!.read(timelineProvider.notifier);
      
      // Pass the complete alert data (data + notification) to timeline provider
      final completeAlertData = Map<String, dynamic>.from(message.data);
      if (message.notification != null) {
        completeAlertData['title'] = message.notification!.title ?? '';
        completeAlertData['body'] = message.notification!.body ?? '';
        if (kDebugMode) {
          print('[FCMService] Added notification data to alert:');
          print('[FCMService]   - title: ${message.notification!.title}');
          print('[FCMService]   - body: ${message.notification!.body}');
        }
      }
      if (kDebugMode) {
        print('[FCMService] Complete alert data: $completeAlertData');
      }
      timelineNotifier.handleDisasterAlert(completeAlertData);
      
      if (kDebugMode) {
        print('[FCMService] Successfully notified timeline provider of disaster alert');
      }
    } catch (e) {
      if (kDebugMode) {
        print('[FCMService] Error notifying timeline provider: $e');
      }
    }
  }


  Future<String?> getFCMToken() async {
    try {
      return await _firebaseMessaging.getToken();
    } catch (e) {
      if (kDebugMode) {
        print("FCMトークン取得エラー: $e");
      }
      return null;
    }
  }

  Future<void> _printAndCacheFCMToken() async {
    String? token = await getFCMToken();
    if (kDebugMode) {
      print("現在のFCMトークン: $token");
    }
  }
}
