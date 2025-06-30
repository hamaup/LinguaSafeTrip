import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:geolocator/geolocator.dart' as geo;
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

part 'onboarding_state.dart';

final onboardingProvider = NotifierProvider<OnboardingNotifier, OnboardingState>(
  OnboardingNotifier.new,
);

class OnboardingNotifier extends Notifier<OnboardingState> {
  @override
  OnboardingState build() {
    // デバイスのロケールに基づいてデフォルト言語を決定
    final deviceLocale = WidgetsBinding.instance.platformDispatcher.locale;
    String defaultLanguage = 'en'; // デフォルトは英語
    if (deviceLocale.languageCode == 'ja') {
      defaultLanguage = 'ja';
    } else if (deviceLocale.languageCode == 'zh') {
      defaultLanguage = 'zh';
    }
    
    // 初期化時に現在の権限状態をチェック
    _checkInitialPermissions();
    
    return OnboardingState(
      permissionStatusLocation: PermissionStatus.denied,
      permissionStatusNotification: PermissionStatus.denied,
      nickname: '',
      selectedLanguageCode: defaultLanguage,
      emergencyContacts: [],
      isLoading: false,
    );
  }

  Future<void> _checkInitialPermissions() async {
    try {
      final locationStatus = await Permission.location.status;
      final notificationStatus = await Permission.notification.status;
      
      state = state.copyWith(
        permissionStatusLocation: locationStatus,
        permissionStatusNotification: notificationStatus,
      );
      
      if (kDebugMode) {
        print('[OnboardingNotifier] 初期権限状態: 位置情報=$locationStatus, 通知=$notificationStatus');
      }
    } catch (e) {
      if (kDebugMode) {
        print('[OnboardingNotifier] 初期権限チェックエラー: $e');
      }
    }
  }


  Future<void> requestLocationPermission() async {
    if (state.context != null && !state.context!.mounted) return;

    PermissionStatus? status;
    try {
      // Web版ではpermission_handlerは正常に動作しないため、Geolocatorを使用
      if (kIsWeb) {
        try {
          // Web版：まず現在の権限状態をチェック
          var permission = await geo.Geolocator.checkPermission();
          
          // 権限がない場合のみリクエスト
          if (permission == geo.LocationPermission.denied) {
            permission = await geo.Geolocator.requestPermission();
          }
          
          // 実際に位置情報取得を試して権限確認
          if (permission == geo.LocationPermission.deniedForever) {
            try {
              await geo.Geolocator.getCurrentPosition(
                desiredAccuracy: geo.LocationAccuracy.low,
                timeLimit: const Duration(seconds: 3),
              );
              // 取得成功 = 権限あり
              permission = geo.LocationPermission.whileInUse;
              if (kDebugMode) {
                print('[OnboardingNotifier] Web版: 実際の位置情報取得で権限ありを確認');
              }
            } catch (e) {
              if (kDebugMode) {
                print('[OnboardingNotifier] Web版: 位置情報取得失敗 - 権限なし: $e');
              }
            }
          }
          
          // Geolocatorの結果をPermissionStatusに変換
          switch (permission) {
            case geo.LocationPermission.always:
            case geo.LocationPermission.whileInUse:
              status = PermissionStatus.granted;
              break;
            case geo.LocationPermission.denied:
              status = PermissionStatus.denied;
              break;
            case geo.LocationPermission.deniedForever:
              status = PermissionStatus.permanentlyDenied;
              break;
            case geo.LocationPermission.unableToDetermine:
              status = PermissionStatus.denied;
              break;
          }
          
          if (kDebugMode) {
            print('[OnboardingNotifier] Web版 最終権限状態: $permission -> $status');
          }
        } catch (e) {
          if (kDebugMode) {
            print('[OnboardingNotifier] Web版 権限チェックエラー: $e');
          }
          status = PermissionStatus.denied;
        }
      } else {
        // モバイル版：従来通りのpermission_handlerを使用
        status = await Permission.location.request();
      }
      if (state.context != null && !state.context!.mounted) return;

      state = state.copyWith(permissionStatusLocation: status);
      
      // Web版では状態再チェックはスキップ（既にGeolocatorで確認済み）
      if (!kIsWeb && status == PermissionStatus.denied) {
        // モバイル版のみ：少し待ってから再チェック
        await Future.delayed(const Duration(milliseconds: 500));
        final recheckStatus = await Permission.location.status;
        if (recheckStatus.isGranted) {
          state = state.copyWith(permissionStatusLocation: recheckStatus);
          status = recheckStatus; // statusを更新
          if (kDebugMode) {
            print('[OnboardingNotifier] モバイル版: 権限再チェックで付与を検出');
          }
        }
      }
      
      // デバッグモードの場合は追加ログを出力
      if (kDebugMode) {
        print('[OnboardingNotifier] 位置情報権限リクエスト結果: $status');
      }

      // 権限が許可された場合は即座に位置情報を取得
      if (status.isGranted) {
        if (kDebugMode) {
          print('[OnboardingNotifier] 📍 位置情報権限が許可されました - 位置情報を取得中...');
        }
        try {
          // DeviceStatusProviderに位置情報取得を依頼
          final deviceStatusNotifier = ref.read(deviceStatusProvider.notifier);
          final location = await deviceStatusNotifier.getCurrentLocation();
          if (location != null && kDebugMode) {
            print('[OnboardingNotifier] 📍 位置情報取得成功: ${location.latitude}, ${location.longitude}');
          }
        } catch (e) {
          if (kDebugMode) {
            print('[OnboardingNotifier] 📍 位置情報取得エラー: $e');
          }
        }
      }
      
      // 権限が拒否されてもアプリを続行可能にする
      if (status.isDenied) {
        if (kDebugMode) {
          print('[OnboardingNotifier] 位置情報権限が拒否されましたが続行します');
        }
        // 例外を投げずに警告のみ
      } else if (status.isPermanentlyDenied) {
        if (kDebugMode) {
          print('[OnboardingNotifier] 位置情報権限が永久拒否されましたが続行します');
        }
        // 例外を投げずに警告のみ
      }
    } catch (e) {
      // 権限リクエストエラーでもアプリをクラッシュさせない
      if (kDebugMode) {
        print('[OnboardingNotifier] 位置情報権限エラー（続行可能）: $e');
      }
      
      // 権限を未設定として継続
      state = state.copyWith(permissionStatusLocation: PermissionStatus.denied);
      
      // UI警告は表示するが例外は投げない
      if (state.context != null && state.context!.mounted && status != null) {
        ScaffoldMessenger.of(state.context!).showSnackBar(
          SnackBar(
            content: const Text('位置情報権限の設定をスキップしました'),
            action: status.isPermanentlyDenied
              ? SnackBarAction(
                  label: '設定を開く',
                  onPressed: () => openAppSettings(),
                )
              : null,
          ),
        );
      }
    }
  }

  Future<void> requestNotificationPermission() async {
    PermissionStatus? status;
    try {
      // 実際の権限リクエストを実行（デバッグモードでも）
      status = await Permission.notification.request();
      state = state.copyWith(permissionStatusNotification: status);
      
      // デバッグモードの場合は追加ログを出力
      if (kDebugMode) {
        print('[OnboardingNotifier] 通知権限リクエスト結果: $status');
      }

      // 権限が拒否されてもアプリを続行可能にする
      if (status.isDenied) {
        if (kDebugMode) {
          print('[OnboardingNotifier] 通知権限が拒否されましたが続行します');
        }
        // 例外を投げずに警告のみ
      } else if (status.isPermanentlyDenied) {
        if (kDebugMode) {
          print('[OnboardingNotifier] 通知権限が永久拒否されましたが続行します');
        }
        // 例外を投げずに警告のみ
      }
    } catch (e) {
      // 権限リクエストエラーでもアプリをクラッシュさせない
      if (kDebugMode) {
        print('[OnboardingNotifier] 通知権限エラー（続行可能）: $e');
      }
      
      // 権限を未設定として継続
      state = state.copyWith(permissionStatusNotification: PermissionStatus.denied);
      
      // UI警告は表示するが例外は投げない
      if (state.context != null && state.context!.mounted && status != null) {
        ScaffoldMessenger.of(state.context!).showSnackBar(
          SnackBar(
            content: const Text('通知権限の設定をスキップしました'),
            action: status?.isPermanentlyDenied == true
              ? SnackBarAction(
                  label: '設定を開く',
                  onPressed: () => openAppSettings(),
                )
              : null,
          ),
        );
      }
    }
  }

  void updateNickname(String nickname) {
    state = state.copyWith(nickname: nickname);
  }

  void updateLanguage(String languageCode) {
    state = state.copyWith(selectedLanguageCode: languageCode);
  }


  void addEmergencyContact(String name, String phoneNumber) {
    final newContact = EmergencyContactModel(
      id: const Uuid().v4(),
      name: name,
      phoneNumber: phoneNumber,
    );
    state = state.copyWith(
      emergencyContacts: [...state.emergencyContacts, newContact],
    );
  }

  void updateEmergencyContact(String id, String name, String phoneNumber) {
    final updatedContacts = state.emergencyContacts.map((contact) {
      return contact.id == id
          ? contact.copyWith(name: name, phoneNumber: phoneNumber)
          : contact;
    }).toList();
    state = state.copyWith(emergencyContacts: updatedContacts);
  }

  void deleteEmergencyContact(String id) {
    final filteredContacts = state.emergencyContacts
        .where((contact) => contact.id != id)
        .toList();
    state = state.copyWith(emergencyContacts: filteredContacts);
  }


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
        heartbeatIntervalNormalMinutes: 6,  // デフォルト: 6分 (360秒)
        heartbeatIntervalEmergencyMinutes: 6,  // デフォルト: 6分 (360秒)
      );
      
      await ref.read(localStorageServiceProvider).saveUserSettings(userSettings);

      // オンボーディング完了フラグを設定
      await ref.read(localStorageServiceProvider).setOnboardingComplete(true);

      // デバイス情報を登録
      String? fcmToken;
      try {
        fcmToken = await ref.read(fcmServiceProvider).getFCMToken();
      } catch (e) {
        // Firebase未初期化エラーの場合はnullで続行
        if (kDebugMode) {
          print('[OnboardingNotifier] FCM token retrieval failed: $e');
        }
        fcmToken = null;
      }
      String? deviceId = DeviceIdUtil.currentDeviceId;
      if (deviceId == null) {
        deviceId = await DeviceIdUtil.initializeAndGetDeviceId();
      }
      
      // Web版ではデバイス登録をスキップ
      if (!kIsWeb) {
        // DeviceCreateRequestを直接作成
        final deviceCreateRequest = DeviceCreateRequest(
          deviceId: deviceId,
          fcmToken: fcmToken ?? '',
          platform: DeviceIdUtil.getPlatform(),
          language: state.selectedLanguageCode,
          timezone: 'Asia/Tokyo',
        );
        try {
          final apiService = ref.read(apiServiceProvider);
          await apiService.registerOrUpdateDevice(deviceCreateRequest);
        } catch (e) {
          print('[OnboardingNotifier] Device registration failed: $e');
          // デバイス登録失敗は続行可能
        }
      } else {
        print('[OnboardingNotifier] Skipping device registration for web platform');
      }

      // ロケールプロバイダーを更新
      ref.read(localeProvider.notifier).setLocale(state.selectedLanguageCode);
      
      // 設定プロバイダーに新しい設定を通知
      try {
        ref.read(settingsProvider.notifier).loadInitialSettings();
      } catch (e) {
        // 設定プロバイダーの更新に失敗しても続行
        if (kDebugMode) {
          print('[OnboardingNotifier] Settings provider update failed: $e');
        }
      }

      // デバッグ：オンボーディング完了時点での位置情報状態
      if (kDebugMode) {
        print('[OnboardingNotifier] 📍 === ONBOARDING COMPLETE DEBUG ===');
        print('[OnboardingNotifier] 📍 Onboarding completed at: ${DateTime.now()}');
        print('[OnboardingNotifier] 📍 Device ID: $deviceId');
        print('[OnboardingNotifier] 📍 User settings: nickname=${state.nickname}, language=${state.selectedLanguageCode}');
        print('[OnboardingNotifier] 📍 Emergency contacts: ${state.emergencyContacts.length}');
        print('[OnboardingNotifier] 📍 Note: Location permission will be requested after navigation');
        print('[OnboardingNotifier] 📍 === ONBOARDING COMPLETE DEBUG END ===');
      }
      
      // メイン画面へ遷移
      print('[OnboardingNotifier] Context mounted check: ${context.mounted}');
      if (context.mounted) {
        print('[OnboardingNotifier] Navigating to main timeline...');
        // ignore: use_build_context_synchronously
        context.goNamed(AppRoutes.mainTimeline);
        print('[OnboardingNotifier] Navigation called successfully');
      } else {
        print('[OnboardingNotifier] WARNING: Context not mounted, cannot navigate!');
      }
    } catch (e, stackTrace) {
      // if (kDebugMode) debugPrint('[OnboardingNotifier] Onboarding error: $e');
      
      // NotInitializedErrorの場合は特別処理
      if (e is StateError || e.toString().contains('NotInitialized')) {
        // メイン画面に遷移（エラーを無視）
        if (context.mounted) {
          context.go('/');
        }
        return;
      }
      
      if (context.mounted) {
        // ignore: use_build_context_synchronously
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${e.toString()}')),
        );
      }
    } finally {
      state = state.copyWith(isLoading: false);
    }
  }
}
