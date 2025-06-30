import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:uuid/uuid.dart';
import '../../../core/navigation/app_router.dart';
import '../../../core/models/emergency_contact_model.dart';
import '../../../core/models/user_settings_model.dart';
import '../../../core/models/device_response_model.dart';
import '../../../core/services/local_storage_service.dart';
import '../../main_timeline/providers/device_status_provider.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/fcm_service.dart';
import '../../../core/utils/device_id_util.dart';
import '../../../core/providers/locale_provider.dart';
import '../../../core/providers/service_providers.dart';
import '../../settings/providers/settings_provider.dart';
import 'onboarding_provider.dart';

// Test environment flag
bool isTestEnvironment = const String.fromEnvironment('E2E_TEST') == 'true';

final onboardingProviderTest = NotifierProvider<OnboardingNotifierTest, OnboardingState>(
  OnboardingNotifierTest.new,
);

class OnboardingNotifierTest extends OnboardingNotifier {
  @override
  Future<void> completeOnboarding(BuildContext context) async {
    try {
      state = state.copyWith(isLoading: true);

      // ニックネームのバリデーション
      if (state.nickname.trim().isEmpty) {
        throw Exception('ニックネームが入力されていません');
      }
      if (state.nickname.trim().length < 2) {
        throw Exception('ニックネームは2文字以上入力してください');
      }

      // 緊急連絡先を保存
      await ref.read(localStorageServiceProvider)
          .saveEmergencyContacts(state.emergencyContacts);

      // ユーザー設定を保存
      final userSettings = UserSettingsModel(
        nickname: state.nickname.trim(),
        languageCode: state.selectedLanguageCode,
        emergencyContacts: state.emergencyContacts,
        heartbeatIntervalNormalMinutes: 6,
        heartbeatIntervalEmergencyMinutes: 6,
      );
      
      await ref.read(localStorageServiceProvider).saveUserSettings(userSettings);

      // オンボーディング完了フラグを設定
      await ref.read(localStorageServiceProvider).setOnboardingComplete(true);

      // テスト環境の場合、FCMトークン取得をスキップ
      String? fcmToken;
      if (!isTestEnvironment) {
        try {
          fcmToken = await ref.read(fcmServiceProvider).getFCMToken();
        } catch (e) {
          if (kDebugMode) {
            print('[OnboardingNotifier] FCM token retrieval failed: $e');
          }
          // FCMトークン取得失敗は続行可能
        }
      } else {
        if (kDebugMode) {
          print('[OnboardingNotifier] Test environment: Skipping FCM token retrieval');
        }
        fcmToken = 'test-fcm-token';
      }

      // デバイス情報を登録
      String? deviceId = DeviceIdUtil.currentDeviceId;
      if (deviceId == null) {
        deviceId = await DeviceIdUtil.initializeAndGetDeviceId();
      }
      
      // DeviceCreateRequestを直接作成
      final deviceCreateRequest = DeviceCreateRequest(
        deviceId: deviceId,
        fcmToken: fcmToken ?? '',
        platform: DeviceIdUtil.getPlatform(),
        language: state.selectedLanguageCode,
        timezone: 'Asia/Tokyo',
      );

      // テスト環境でもAPI呼び出しを試みる（失敗しても続行）
      try {
        final apiService = ref.read(apiServiceProvider);
        await apiService.registerOrUpdateDevice(deviceCreateRequest);
      } catch (e) {
        if (kDebugMode) {
          print('[OnboardingNotifier] Device registration failed: $e');
        }
        // デバイス登録失敗は続行可能
      }

      // ロケールプロバイダーを更新
      ref.read(localeProvider.notifier).setLocale(state.selectedLanguageCode);
      
      // 設定プロバイダーに新しい設定を通知
      try {
        ref.read(settingsProvider.notifier).loadInitialSettings();
      } catch (e) {
        if (kDebugMode) {
          print('[OnboardingNotifier] Settings provider update failed: $e');
        }
      }

      // デバッグログ
      if (kDebugMode) {
        print('[OnboardingNotifier] 📍 === ONBOARDING COMPLETE DEBUG ===');
        print('[OnboardingNotifier] 📍 Onboarding completed at: ${DateTime.now()}');
        print('[OnboardingNotifier] 📍 Device ID: $deviceId');
        print('[OnboardingNotifier] 📍 User settings: nickname=${state.nickname}, language=${state.selectedLanguageCode}');
        print('[OnboardingNotifier] 📍 Emergency contacts: ${state.emergencyContacts.length}');
        print('[OnboardingNotifier] 📍 FCM token: ${fcmToken ?? 'none'}');
        print('[OnboardingNotifier] 📍 === ONBOARDING COMPLETE DEBUG END ===');
      }
      
      // メイン画面へ遷移
      if (context.mounted) {
        context.goNamed(AppRoutes.mainTimeline);
        if (kDebugMode) {
          print('[OnboardingNotifier] Navigation to main timeline initiated');
        }
      }
    } catch (e, stackTrace) {
      if (kDebugMode) {
        print('[OnboardingNotifier] Onboarding error: $e');
        print('[OnboardingNotifier] Stack trace: $stackTrace');
      }
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${e.toString()}')),
        );
      }
    } finally {
      state = state.copyWith(isLoading: false);
    }
  }
}