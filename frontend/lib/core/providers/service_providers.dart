import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/core/services/api_service.dart';
import 'package:frontend/core/services/local_storage_service.dart';
import 'package:frontend/core/services/fcm_service.dart';

/// 中央集権化されたサービスプロバイダ定義
/// 
/// すべてのサービスプロバイダをここに集約し、
/// アプリ全体で統一されたインスタンスを使用する

/// API Service Provider
/// HTTP通信とバックエンドAPIとの連携を提供
final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

/// Local Storage Service Provider  
/// ローカルストレージ（SharedPreferences）へのアクセスを提供
final localStorageServiceProvider = Provider<LocalStorageService>((ref) {
  return LocalStorageService();
});

/// FCM (Firebase Cloud Messaging) Service Provider
/// プッシュ通知の送受信機能を提供
final fcmServiceProvider = Provider<FCMService>((ref) {
  return FCMService();
});