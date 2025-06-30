import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class LocalNotificationService {
  static final LocalNotificationService _instance = LocalNotificationService._internal();
  factory LocalNotificationService() => _instance;
  LocalNotificationService._internal();

  final FlutterLocalNotificationsPlugin _flutterLocalNotificationsPlugin = 
      FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const DarwinInitializationSettings initializationSettingsIOS =
        DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsIOS,
    );

    await _flutterLocalNotificationsPlugin.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // Android 13+ の通知許可をリクエスト
    await _requestPermissions();

    if (kDebugMode) {
      print('[LocalNotificationService] Initialized successfully');
    }
  }

  Future<void> _requestPermissions() async {
    final androidImplementation = _flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    
    if (androidImplementation != null) {
      final granted = await androidImplementation.requestNotificationsPermission();
      if (kDebugMode) {
        print('[LocalNotificationService] Android notification permission granted: $granted');
      }
      
      // 通知チャンネルの作成確認
      await _createNotificationChannels();
    }
    
    final iosImplementation = _flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>();
    
    if (iosImplementation != null) {
      final granted = await iosImplementation.requestPermissions(
        alert: true,
        badge: true,
        sound: true,
      );
      if (kDebugMode) {
        print('[LocalNotificationService] iOS notification permission granted: $granted');
      }
    }
  }

  void _onNotificationTapped(NotificationResponse notificationResponse) {
    if (kDebugMode) {
      print('[LocalNotificationService] Notification tapped: ${notificationResponse.payload}');
    }
    // 通知タップ時の処理をここに実装
  }

  Future<void> showEmergencyNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    final AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'emergency_alerts',
      'Emergency Alerts',
      channelDescription: '緊急災害アラート通知',
      importance: Importance.max,
      priority: Priority.high,
      ticker: '緊急アラート',
      color: const Color(0xFFFF0000),
      enableVibration: true,
      playSound: true,
      // Remove custom sound for now - use default
      styleInformation: BigTextStyleInformation(body),
      category: AndroidNotificationCategory.alarm,
    );

    const DarwinNotificationDetails iOSPlatformChannelSpecifics =
        DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
      // Remove custom sound for now - use default
      interruptionLevel: InterruptionLevel.critical,
    );

    final NotificationDetails platformChannelSpecifics = NotificationDetails(
      android: androidPlatformChannelSpecifics,
      iOS: iOSPlatformChannelSpecifics,
    );

    await _flutterLocalNotificationsPlugin.show(
      DateTime.now().millisecondsSinceEpoch.remainder(100000),
      title,
      body,
      platformChannelSpecifics,
      payload: payload,
    );
  }

  Future<void> showNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'general_notifications',
      'General Notifications',
      channelDescription: '一般通知',
      importance: Importance.defaultImportance,
      priority: Priority.defaultPriority,
      ticker: '通知',
      enableVibration: true,
      playSound: true,
      styleInformation: BigTextStyleInformation(''),
    );

    const DarwinNotificationDetails iOSPlatformChannelSpecifics =
        DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final NotificationDetails platformChannelSpecifics = NotificationDetails(
      android: androidPlatformChannelSpecifics,
      iOS: iOSPlatformChannelSpecifics,
    );

    await _flutterLocalNotificationsPlugin.show(
      DateTime.now().millisecondsSinceEpoch.remainder(100000),
      title,
      body,
      platformChannelSpecifics,
      payload: payload,
    );

    if (kDebugMode) {
      print('[LocalNotificationService] Notification shown: $title');
    }
  }

  Future<void> cancelAllNotifications() async {
    await _flutterLocalNotificationsPlugin.cancelAll();
  }

  /// 通知チャンネルの明示的作成
  Future<void> _createNotificationChannels() async {
    final androidImplementation = _flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    
    if (androidImplementation != null) {
      // 緊急アラートチャンネル
      const emergencyChannel = AndroidNotificationChannel(
        'emergency_alerts',
        'Emergency Alerts',
        description: '緊急災害アラート通知',
        importance: Importance.max,
        playSound: true,
        enableVibration: true,
      );
      
      // 一般通知チャンネル
      const generalChannel = AndroidNotificationChannel(
        'general_notifications',
        'General Notifications',
        description: '一般通知',
        importance: Importance.defaultImportance,
        playSound: true,
        enableVibration: true,
      );
      
      await androidImplementation.createNotificationChannel(emergencyChannel);
      await androidImplementation.createNotificationChannel(generalChannel);
    }
  }

  /// テスト用：シンプルなOSレベル通知を表示
  Future<void> showTestNotification() async {
    try {
      // シンプルな通知設定でテスト
      const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
        'test_channel',
        'Test Notifications',
        channelDescription: 'Test notification channel',
        importance: Importance.high,
        priority: Priority.high,
      );
      
      const NotificationDetails platformChannelSpecifics = NotificationDetails(
        android: androidDetails,
      );
      
      await _flutterLocalNotificationsPlugin.show(
        0,
        'テスト通知',
        'OSレベル通知のテストです',
        platformChannelSpecifics,
      );
      
      // 緊急通知もテスト
      await showEmergencyNotification(
        title: 'テスト緊急アラート',
        body: 'これは緊急アラートのテストです。',
        payload: 'test_alert',
      );
    } catch (e) {
      rethrow;
    }
  }
}