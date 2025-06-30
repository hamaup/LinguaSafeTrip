import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:go_router/go_router.dart';
import 'package:frontend/core/models/user_settings_model.dart';
import 'package:frontend/core/models/emergency_contact_model.dart';
import 'package:frontend/core/services/local_storage_service.dart';
import 'package:frontend/core/providers/service_providers.dart';
import 'package:frontend/core/providers/locale_provider.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:frontend/features/onboarding/providers/onboarding_provider.dart' as onboarding;
import 'package:frontend/core/services/suggestion_history_manager.dart';
import 'package:frontend/core/services/api_service.dart';
import 'package:frontend/core/services/timeline_storage_service.dart';

part 'settings_provider.freezed.dart';

@freezed
class SettingsState with _$SettingsState {
  const factory SettingsState({
    required UserSettingsModel? currentUserSettings,
    required List<EmergencyContactModel> currentEmergencyContacts,
    @Default(false) bool isLoading,
    @Default({}) Map<String, bool> notificationSettings,
  }) = _SettingsState;
}

class SettingsNotifier extends Notifier<SettingsState> {
  late final LocalStorageService _localStorage;

  @override
  SettingsState build() {
    _localStorage = ref.read(localStorageServiceProvider);
    // debugPrint('[SettingsNotifier] build() called');
    
    // 初期化をPostFrameCallbackで実行
    WidgetsBinding.instance.addPostFrameCallback((_) {
      loadInitialSettings();
    });
    
    return const SettingsState(
      currentUserSettings: null,
      currentEmergencyContacts: [],
      isLoading: true,  // 初期状態でローディング中に設定
    );
  }

  Future<void> loadInitialSettings() async {
    // debugPrint('[SettingsNotifier] === loadInitialSettings START ===');
    // debugPrint('[SettingsNotifier] loadInitialSettings() called');
    state = state.copyWith(isLoading: true);
    try {
    // debugPrint('[SettingsNotifier] Starting to load initial settings...');
    // debugPrint('[SettingsNotifier] Current state before loading: isLoading=${state.isLoading}, currentUserSettings=${state.currentUserSettings?.toJson()}');

      // 1. ユーザー設定と緊急連絡先を並列で取得
      final results = await Future.wait([
        _localStorage.loadUserSettings(),
        _localStorage.getEmergencyContacts(),
      ]);

      var settings = results[0] as UserSettingsModel?;
      var contacts = results[1] as List<EmergencyContactModel>;
    // debugPrint('[SettingsNotifier] *** LOADED DATA FROM STORAGE ***');
    // debugPrint('[SettingsNotifier] Retrieved settings: ${settings?.toJson()}');
    // debugPrint('[SettingsNotifier] Language code from storage: ${settings?.languageCode}');
    // debugPrint('[SettingsNotifier] Retrieved ${contacts.length} contacts');
    // debugPrint('[SettingsNotifier] *** END LOADED DATA FROM STORAGE ***');

      // 2. 設定がnullの場合、デフォルト設定を作成
      if (settings == null) {
    // debugPrint('[SettingsNotifier] Creating default settings...');
        // デバイスのロケールに基づいてデフォルト言語を決定
        final deviceLocale = WidgetsBinding.instance.platformDispatcher.locale;
        String defaultLanguage = 'en'; // デフォルトは英語
        if (deviceLocale.languageCode == 'ja') {
          defaultLanguage = 'ja';
        } else if (deviceLocale.languageCode == 'zh') {
          defaultLanguage = 'zh';
        }
        
        settings = UserSettingsModel(
          nickname: 'User',
          languageCode: defaultLanguage,
          emergencyContacts: contacts,
        );
        await _localStorage.saveUserSettings(settings);
        // DeviceStatusProviderのキャッシュを無効化
        if (ref.exists(deviceStatusProvider)) {
          ref.read(deviceStatusProvider.notifier).invalidateSettingsCache();
        }
      }
      // 3. 設定と連絡先の整合性チェック
      else if (settings.emergencyContacts.isEmpty && contacts.isNotEmpty) {
    // debugPrint('[SettingsNotifier] Syncing emergency contacts to settings...');
        settings = settings.copyWith(emergencyContacts: contacts);
        await _localStorage.saveUserSettings(settings);
        // DeviceStatusProviderのキャッシュを無効化
        if (ref.exists(deviceStatusProvider)) {
          ref.read(deviceStatusProvider.notifier).invalidateSettingsCache();
        }
      }

      // 4. 状態を更新 (1回のみ)
    // debugPrint('[SettingsNotifier] *** UPDATING STATE ***');
    // debugPrint('[SettingsNotifier] About to update state with:');
    // debugPrint('[SettingsNotifier]   - settings: ${settings.toJson()}');
    // debugPrint('[SettingsNotifier]   - languageCode: ${settings.languageCode}');
    // debugPrint('[SettingsNotifier]   - contacts: ${contacts.length} items');
    // debugPrint('[SettingsNotifier]   - isLoading: false');
      
      state = state.copyWith(
        currentUserSettings: settings,
        currentEmergencyContacts: contacts,
        isLoading: false,
      );
      
    // debugPrint('[SettingsNotifier] State updated. New state:');
    // debugPrint('[SettingsNotifier]   - isLoading: ${state.isLoading}');
    // debugPrint('[SettingsNotifier]   - currentUserSettings: ${state.currentUserSettings?.toJson()}');
    // debugPrint('[SettingsNotifier]   - languageCode: ${state.currentUserSettings?.languageCode}');
      
      // 5. ロケールプロバイダーも更新
      if (settings.languageCode.isNotEmpty) {
    // debugPrint('[SettingsNotifier] *** UPDATING LOCALE PROVIDER ***');
    // debugPrint('[SettingsNotifier] Setting locale to: ${settings.languageCode}');
        ref.read(localeProvider.notifier).setLocale(settings.languageCode);
    // debugPrint('[SettingsNotifier] *** LOCALE PROVIDER UPDATED ***');
      }
      
    // debugPrint('[SettingsNotifier] Successfully loaded all initial settings');
    // debugPrint('[SettingsNotifier] === loadInitialSettings END (SUCCESS) ===');
    } catch (e, stack) {
    // debugPrint('[SettingsNotifier] === loadInitialSettings ERROR ===');
    // debugPrint('[SettingsNotifier] Critical error loading settings: $e');
    // debugPrint('[SettingsNotifier] Stack trace: $stack');
    // debugPrint('[SettingsNotifier] === loadInitialSettings END (ERROR) ===');
      state = state.copyWith(isLoading: false);
      // エラー時は_isInitializedをtrueにしない（リトライ可能にする）
      rethrow;
    }
  }

  Future<void> resetApp(BuildContext context) async {
    // debugPrint('[SettingsNotifier] Starting app reset...');
    state = state.copyWith(isLoading: true);
    try {
      // 1. 全ユーザーデータを完全削除（タイムライン等含む）
    // debugPrint('[SettingsNotifier] Clearing all user data...');
      await _localStorage.clearAllUserData();

      // 2. 全プロバイダーの状態を完全リセット
      try {
    // debugPrint('[SettingsNotifier] Invalidating all providers...');
        
        // 重要: 個別のプロバイダーを無効化して完全リセット
        if (ref.exists(timelineProvider)) {
          ref.invalidate(timelineProvider);
        }
        if (ref.exists(deviceStatusProvider)) {
          ref.invalidate(deviceStatusProvider);
        }
        if (ref.exists(onboarding.onboardingProvider)) {
          ref.invalidate(onboarding.onboardingProvider);
        }
        if (ref.exists(localeProvider)) {
          ref.invalidate(localeProvider);
        }
        
    // debugPrint('[SettingsNotifier] All providers invalidated');
      } catch (e) {
    // debugPrint('[SettingsNotifier] Error resetting providers: $e');
      }

      // 3. 現在の設定プロバイダーの状態を初期値にリセット
      state = const SettingsState(
        currentUserSettings: null,
        currentEmergencyContacts: [],
        isLoading: false,
      );

      // 4. ロケールも初期状態にリセット（デバイスのデフォルト言語に戻す）
      final deviceLocale = WidgetsBinding.instance.platformDispatcher.locale;
      String defaultLanguage = 'en';
      if (deviceLocale.languageCode == 'ja') {
        defaultLanguage = 'ja';
      } else if (deviceLocale.languageCode == 'zh') {
        defaultLanguage = 'zh';
      }
    // debugPrint('[SettingsNotifier] Resetting locale to: $defaultLanguage');
      ref.read(localeProvider.notifier).setLocale(defaultLanguage);

      // 5. オンボーディング画面に遷移（再起動の代替）
    // debugPrint('[SettingsNotifier] Navigating to welcome screen...');
      if (context.mounted) {
        // ignore: use_build_context_synchronously
        context.go('/onboarding/welcome');
      }
      
    // debugPrint('[SettingsNotifier] App reset completed successfully');
    } catch (e) {
    // debugPrint('[SettingsNotifier] Error during app reset: $e');
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  /// デバッグ用完全リセット（Firebaseデータ削除含む）
  Future<void> completeDebugReset(BuildContext context) async {
    // debugPrint('[SettingsNotifier] Starting complete debug reset...');
    state = state.copyWith(isLoading: true);
    
    try {
      // 1. デバイスIDを取得
      final deviceStatusNotifier = ref.read(deviceStatusProvider.notifier);
      final deviceId = await deviceStatusNotifier.getDeviceId();
      
    // debugPrint('[SettingsNotifier] 📱 Device ID for reset: $deviceId');
      
      // 2. バックエンドのFirebaseデータを完全削除
    // debugPrint('[SettingsNotifier] 🗑️ Deleting Firebase data...');
      final apiService = ApiService();
      
      final backendResponse = await apiService.completeAppReset(deviceId);
    // debugPrint('[SettingsNotifier] ✅ Firebase data deleted: ${backendResponse['message']}');
    // debugPrint('[SettingsNotifier] 📊 Reset operations: ${backendResponse['reset_operations']}');
      
      // 3. フロントエンドのローカルデータを完全削除
    // debugPrint('[SettingsNotifier] 🗑️ Clearing local storage...');
      await _localStorage.clearAllUserData();
      
      // 4. 提案履歴管理もクリア
    // debugPrint('[SettingsNotifier] 🗑️ Clearing suggestion history...');
      try {
        await SuggestionHistoryManager.clearHistory();
    // debugPrint('[SettingsNotifier] ✅ Suggestion history cleared');
      } catch (e) {
    // debugPrint('[SettingsNotifier] ⚠️ Failed to clear suggestion history: $e');
      }
      
      // 5. タイムライン履歴を完全にクリア（ローカルストレージ + プロバイダー状態）
    // debugPrint('[SettingsNotifier] 🗑️ Clearing timeline history...');
      try {
        // TimelineProviderの専用メソッドを使用
        if (ref.exists(timelineProvider)) {
          ref.read(timelineProvider.notifier).clearAllTimelineItems();
    // debugPrint('[SettingsNotifier] ✅ Timeline cleared using clearAllTimelineItems method');
        }
        
    // debugPrint('[SettingsNotifier] ✅ Timeline history completely cleared');
      } catch (e) {
    // debugPrint('[SettingsNotifier] ⚠️ Failed to clear timeline history: $e');
      }

      // 6. 災害モード・緊急モードをリセット
    // debugPrint('[SettingsNotifier] 🔄 Resetting emergency mode...');
      try {
        // ローカルストレージの緊急モードもクリア
        await _localStorage.saveEmergencyMode('normal');
    // debugPrint('[SettingsNotifier] 💾 Local emergency mode reset to normal');
        
        // デバイス状態プロバイダーの緊急モードも平常時にリセット
        if (ref.exists(deviceStatusProvider)) {
          ref.read(deviceStatusProvider.notifier).setEmergencyModeForDebug(false);
    // debugPrint('[SettingsNotifier] ✅ Device status emergency mode reset to normal');
        }
        
        await apiService.forceEmergencyModeReset(deviceId);
    // debugPrint('[SettingsNotifier] ✅ Backend emergency mode reset');
      } catch (e) {
    // debugPrint('[SettingsNotifier] ⚠️ Failed to reset emergency mode: $e');
      }

      // 6. チャット履歴もクリア（デバイス状態プロバイダー）
    // debugPrint('[SettingsNotifier] 🗑️ Clearing chat session state...');
      try {
        if (ref.exists(deviceStatusProvider)) {
          // チャットセッションを終了してクリア
          ref.read(deviceStatusProvider.notifier).endChatSession();
    // debugPrint('[SettingsNotifier] ✅ Chat session state cleared');
        }
      } catch (e) {
    // debugPrint('[SettingsNotifier] ⚠️ Failed to clear chat session: $e');
      }

      // 7. 全プロバイダーの状態を完全リセット
      try {
    // debugPrint('[SettingsNotifier] 🔄 Invalidating providers (preserving timeline)...');
        
        // 重要: 個別のプロバイダーを無効化して完全リセット
        // タイムラインプロバイダーは保持（チャット履歴を維持）
        if (ref.exists(deviceStatusProvider)) {
          ref.invalidate(deviceStatusProvider);
        }
        if (ref.exists(onboarding.onboardingProvider)) {
          ref.invalidate(onboarding.onboardingProvider);
        }
        if (ref.exists(localeProvider)) {
          ref.invalidate(localeProvider);
        }
        
    // debugPrint('[SettingsNotifier] ✅ All providers invalidated');
      } catch (e) {
    // debugPrint('[SettingsNotifier] ⚠️ Error resetting providers: $e');
      }

      // 8. 現在の設定プロバイダーの状態を初期値にリセット
      state = const SettingsState(
        currentUserSettings: null,
        currentEmergencyContacts: [],
        isLoading: false,
      );

      // 9. ロケールも初期状態にリセット（デバイスのデフォルト言語に戻す）
      final deviceLocale = WidgetsBinding.instance.platformDispatcher.locale;
      String defaultLanguage = 'en';
      if (deviceLocale.languageCode == 'ja') {
        defaultLanguage = 'ja';
      } else if (deviceLocale.languageCode == 'zh') {
        defaultLanguage = 'zh';
      }
    // debugPrint('[SettingsNotifier] 🌐 Resetting locale to: $defaultLanguage');
      ref.read(localeProvider.notifier).setLocale(defaultLanguage);

      // 10. オンボーディング画面に遷移（再起動の代替）
    // debugPrint('[SettingsNotifier] 🔄 Navigating to welcome screen...');
      if (context.mounted) {
        // ignore: use_build_context_synchronously
        context.go('/onboarding/welcome');
      }
      
    // debugPrint('[SettingsNotifier] === COMPLETE DEBUG RESET SUCCESSFUL ===');
    } catch (e) {
    // debugPrint('[SettingsNotifier] === COMPLETE DEBUG RESET FAILED ===');
    // debugPrint('[SettingsNotifier] ❌ Error during complete debug reset: $e');
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> updateEmergencyContact(EmergencyContactModel updatedContact) async {
    state = state.copyWith(isLoading: true);
    try {
      final updatedContacts = state.currentEmergencyContacts.map((contact) =>
        contact.id == updatedContact.id ? updatedContact : contact
      ).toList();

      await _localStorage.saveEmergencyContacts(updatedContacts);
      // DeviceStatusProviderの連絡先キャッシュを無効化
      if (ref.exists(deviceStatusProvider)) {
        ref.read(deviceStatusProvider.notifier).invalidateContactsCountCache();
      }

      final currentSettings = state.currentUserSettings;
      if (currentSettings != null) {
        final updatedSettings = currentSettings.copyWith(
          emergencyContacts: updatedContacts
        );
        await _localStorage.saveUserSettings(updatedSettings);
        state = state.copyWith(
          currentUserSettings: updatedSettings,
          currentEmergencyContacts: updatedContacts,
          isLoading: false
        );
      } else {
        state = state.copyWith(
          currentEmergencyContacts: updatedContacts,
          isLoading: false
        );
      }
    } catch (e) {
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> deleteEmergencyContact(String contactId) async {
    state = state.copyWith(isLoading: true);
    try {
      final updatedContacts = state.currentEmergencyContacts
        .where((contact) => contact.id != contactId)
        .toList();

      await _localStorage.saveEmergencyContacts(updatedContacts);
      // DeviceStatusProviderの連絡先キャッシュを無効化
      if (ref.exists(deviceStatusProvider)) {
        ref.read(deviceStatusProvider.notifier).invalidateContactsCountCache();
      }

      final currentSettings = state.currentUserSettings;
      if (currentSettings != null) {
        final updatedSettings = currentSettings.copyWith(
          emergencyContacts: updatedContacts
        );
        await _localStorage.saveUserSettings(updatedSettings);
        state = state.copyWith(
          currentUserSettings: updatedSettings,
          currentEmergencyContacts: updatedContacts,
          isLoading: false
        );
      } else {
        state = state.copyWith(
          currentEmergencyContacts: updatedContacts,
          isLoading: false
        );
      }
    } catch (e) {
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> addEmergencyContact(String name, String phoneNumber) async {
    state = state.copyWith(isLoading: true);
    try {
      final newContact = EmergencyContactModel(
        id: const Uuid().v4(),
        name: name,
        phoneNumber: phoneNumber,
      );

      final updatedContacts = [...state.currentEmergencyContacts, newContact];
      await _localStorage.saveEmergencyContacts(updatedContacts);
      // DeviceStatusProviderの連絡先キャッシュを無効化
      if (ref.exists(deviceStatusProvider)) {
        ref.read(deviceStatusProvider.notifier).invalidateContactsCountCache();
      }

      // ユーザー設定も更新
      final currentSettings = state.currentUserSettings;
      if (currentSettings != null) {
        final updatedSettings = currentSettings.copyWith(
          emergencyContacts: updatedContacts
        );
        await _localStorage.saveUserSettings(updatedSettings);
        state = state.copyWith(
          currentUserSettings: updatedSettings,
          currentEmergencyContacts: updatedContacts,
          isLoading: false
        );
      } else {
        state = state.copyWith(
          currentEmergencyContacts: updatedContacts,
          isLoading: false
        );
      }
    } catch (e) {
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }


  Future<void> updateLanguage(BuildContext context, String newLanguageCode) async {
    // debugPrint('[SettingsNotifier] === updateLanguage START ===');
    // debugPrint('[SettingsNotifier] Updating language from ${state.currentUserSettings?.languageCode} to $newLanguageCode');
    
    state = state.copyWith(isLoading: true);
    try {
      final currentSettings = state.currentUserSettings;
      if (currentSettings == null) {
    // debugPrint('[SettingsNotifier] Error: User settings not loaded');
        throw Exception('User settings not loaded');
      }

      final updatedSettings = currentSettings.copyWith(
        languageCode: newLanguageCode,
      );
      
    // debugPrint('[SettingsNotifier] Saving updated settings: ${updatedSettings.toJson()}');
      await _localStorage.saveUserSettings(updatedSettings);
    // debugPrint('[SettingsNotifier] Settings saved to storage');

      state = state.copyWith(
        currentUserSettings: updatedSettings,
        isLoading: false,
      );
      
    // debugPrint('[SettingsNotifier] State updated with new language: ${state.currentUserSettings?.languageCode}');

      // ロケールプロバイダーを更新
    // debugPrint('[SettingsNotifier] Updating locale provider');
      ref.read(localeProvider.notifier).setLocale(newLanguageCode);
      
      // タイムラインプロバイダーを強制リフレッシュして新しい言語でデータを取得
    // debugPrint('[SettingsNotifier] Forcing timeline refresh for language change');
      try {
        if (ref.exists(timelineProvider)) {
          await ref.read(timelineProvider.notifier).forceRefreshForLanguageChange();
    // debugPrint('[SettingsNotifier] Timeline refresh completed');
        }
      } catch (e) {
    // debugPrint('[SettingsNotifier] Timeline refresh failed: $e');
        // Don't rethrow - language update was successful, timeline refresh is secondary
      }
      
    // debugPrint('[SettingsNotifier] === updateLanguage END (SUCCESS) ===');
    } catch (e) {
    // debugPrint('[SettingsNotifier] === updateLanguage END (ERROR) ===');
    // debugPrint('[SettingsNotifier] Error updating language: $e');
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> updateNotificationSettings(Map<String, bool> newSettings) async {
    state = state.copyWith(
      notificationSettings: newSettings,
    );
    // TODO: 必要に応じてバックエンドに同期する処理を追加
  }

  Future<void> updateSettings(UserSettingsModel updatedSettings) async {
    // debugPrint('[SettingsNotifier] === updateSettings START ===');
    // debugPrint('[SettingsNotifier] Updating settings: ${updatedSettings.toJson()}');
    
    state = state.copyWith(isLoading: true);
    try {
      await _localStorage.saveUserSettings(updatedSettings);
    // debugPrint('[SettingsNotifier] Settings saved to storage');

      state = state.copyWith(
        currentUserSettings: updatedSettings,
        isLoading: false,
      );
      
    // debugPrint('[SettingsNotifier] State updated with new settings');
    // debugPrint('[SettingsNotifier] === updateSettings END (SUCCESS) ===');
    } catch (e) {
    // debugPrint('[SettingsNotifier] === updateSettings END (ERROR) ===');
    // debugPrint('[SettingsNotifier] Error updating settings: $e');
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> updateHeartbeatIntervals({
    required int normalMinutes,
    required int emergencyMinutes,
  }) async {
    state = state.copyWith(isLoading: true);
    try {
      final currentSettings = state.currentUserSettings;
      if (currentSettings == null) {
        throw Exception('User settings not loaded');
      }

      final updatedSettings = currentSettings.copyWith(
        heartbeatIntervalNormalMinutes: normalMinutes,
        heartbeatIntervalEmergencyMinutes: emergencyMinutes,
      );
      
      await _localStorage.saveUserSettings(updatedSettings);

      state = state.copyWith(
        currentUserSettings: updatedSettings,
        isLoading: false,
      );
      
      // DeviceStatusProviderにハートビート間隔変更を通知
      try {
        if (ref.exists(deviceStatusProvider)) {
          ref.read(deviceStatusProvider.notifier).onHeartbeatSettingsChanged();
        }
      } catch (e) {
    // debugPrint('[SettingsNotifier] Error notifying device status provider: $e');
      }
      
    // debugPrint('[SettingsNotifier] Heartbeat intervals updated: normal=${normalMinutes}min, emergency=${emergencyMinutes}min');
    } catch (e) {
    // debugPrint('[SettingsNotifier] Error updating heartbeat intervals: $e');
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }
}

final settingsProvider = NotifierProvider<SettingsNotifier, SettingsState>(
  SettingsNotifier.new,
);
