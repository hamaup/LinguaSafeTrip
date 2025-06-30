// lib/core/services/local_storage_service.dart
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/models/user_settings_model.dart';
import 'package:frontend/core/models/emergency_contact_model.dart';

class LocalStorageService {
  static const String _onboardingCompleteKey = 'app_onboarding_complete_v2';
  static const String _userSettingsKey = 'app_user_settings_v2';
  static const String _emergencyContactsKey = 'app_emergency_contacts_v2';
  static const String _deviceIdKey = 'app_device_id_v2';
  static const String _emergencyModeKey = 'app_emergency_mode_v2';

  final Future<SharedPreferences> _prefs;

  LocalStorageService() : _prefs = SharedPreferences.getInstance();

  Future<void> setOnboardingComplete(bool value) async {
    final prefs = await _prefs;
    await prefs.setBool(_onboardingCompleteKey, value);
    if (kDebugMode) {
      print('LocalStorage: Onboarding complete flag set to $value');
    }
  }

  Future<bool> getOnboardingComplete() async {
    final prefs = await _prefs;
    final bool result = prefs.getBool(_onboardingCompleteKey) ?? false;
    if (kDebugMode) {
      print('LocalStorage: Onboarding complete flag is $result');
    }
    return result;
  }

  // 開発用: 全データをクリア
  Future<void> clearAllData() async {
    final prefs = await _prefs;
    await prefs.clear();
    if (kDebugMode) {
      print('LocalStorage: All data cleared');
    }
  }

  Future<void> saveUserSettings(UserSettingsModel settings) async {
    final prefs = await _prefs;
    final String jsonString = jsonEncode(settings.toJson());
    await prefs.setString(_userSettingsKey, jsonString);
    if (kDebugMode) {
      print('LocalStorage: User settings saved: $jsonString');
    }
  }

  Future<UserSettingsModel?> loadUserSettings() async {
    final prefs = await _prefs;
    // debugPrint('--- [LocalStorage loadUserSettings] START ---');
    // debugPrint('[LocalStorage] Loading from key: $_userSettingsKey');

    final String? jsonString = prefs.getString(_userSettingsKey);
    // debugPrint('[LocalStorage] Raw JSON string: ${jsonString ?? "NULL"}');

    if (jsonString == null || jsonString.isEmpty) {
    // debugPrint('[LocalStorage] No settings data found in storage');
    // debugPrint('--- [LocalStorage loadUserSettings] END (NULL) ---');
      return null;
    }

    try {
    // debugPrint('[LocalStorage] Attempting to parse JSON...');
      final jsonMap = jsonDecode(jsonString) as Map<String, dynamic>;
    // debugPrint('[LocalStorage] Decoded JSON map: $jsonMap');

    // debugPrint('[LocalStorage] Creating UserSettingsModel...');
      final settings = UserSettingsModel.fromJson(jsonMap);
    // debugPrint('[LocalStorage] Created settings: ${settings.toJson()}');

    // debugPrint('--- [LocalStorage loadUserSettings] END (SUCCESS) ---');
      return settings;
    } catch (e, stack) {
    // debugPrint('[LocalStorage] ERROR parsing settings: $e');
    // debugPrint('[LocalStorage] Stack trace: $stack');
    // debugPrint('[LocalStorage] Removing corrupted data...');
      await prefs.remove(_userSettingsKey);

    // debugPrint('--- [LocalStorage loadUserSettings] END (ERROR) ---');
      return null;
    }
  }

  Future<void> saveEmergencyContacts(List<EmergencyContactModel> contacts) async {
    final prefs = await _prefs;
    // debugPrint('[LocalStorage] === SAVE EMERGENCY CONTACTS START ===');
    // debugPrint('[LocalStorage] Number of contacts to save: ${contacts.length}');
    
    final List<String> stringList = contacts.map((contact) {
      final json = contact.toJson();
      final encoded = jsonEncode(json);
    // debugPrint('[LocalStorage] Encoding contact: ${contact.name} -> $encoded');
      return encoded;
    }).toList();
    
    // debugPrint('[LocalStorage] Saving to key: $_emergencyContactsKey');
    // debugPrint('[LocalStorage] StringList to save: $stringList');
    
    await prefs.setStringList(_emergencyContactsKey, stringList);
    
    // Verify save was successful
    final savedList = prefs.getStringList(_emergencyContactsKey);
    // debugPrint('[LocalStorage] Verification - saved list: $savedList');
    // debugPrint('[LocalStorage] Verification - saved count: ${savedList?.length ?? 0}');
    
    if (kDebugMode) {
      print('[LocalStorage] Emergency contacts saved: ${contacts.length} contacts.');
    }
    // debugPrint('[LocalStorage] === SAVE EMERGENCY CONTACTS END ===');
  }

  Future<List<EmergencyContactModel>> getEmergencyContacts() async {
    final prefs = await _prefs;
    // debugPrint('[LocalStorage] === GET EMERGENCY CONTACTS START ===');
    // debugPrint('[LocalStorage] Reading from key: $_emergencyContactsKey');
    
    final List<String>? stringList = prefs.getStringList(_emergencyContactsKey);
    // debugPrint('[LocalStorage] Raw stringList: $stringList');
    // debugPrint('[LocalStorage] Is null: ${stringList == null}');
    // debugPrint('[LocalStorage] Count: ${stringList?.length ?? 0}');
    
    if (stringList != null && stringList.isNotEmpty) {
      try {
        final contacts = stringList
            .map((s) {
    // debugPrint('[LocalStorage] Decoding: $s');
              final decoded = EmergencyContactModel.fromJson(jsonDecode(s));
    // debugPrint('[LocalStorage] Decoded to: ${decoded.name} - ${decoded.phoneNumber}');
              return decoded;
            })
            .toList();
        if (kDebugMode) {
          print('[LocalStorage] Emergency contacts loaded: ${contacts.length} contacts.');
        }
    // debugPrint('[LocalStorage] === GET EMERGENCY CONTACTS END (SUCCESS) ===');
        return contacts;
      } catch (e, stackTrace) {
        if (kDebugMode) {
          print('[LocalStorage] Error parsing emergency contacts: $e. Removing invalid data.');
        }
    // debugPrint('[LocalStorage] Error: $e');
    // debugPrint('[LocalStorage] Stack: $stackTrace');
        await prefs.remove(_emergencyContactsKey);
    // debugPrint('[LocalStorage] === GET EMERGENCY CONTACTS END (ERROR) ===');
        return [];
      }
    }
    if (kDebugMode) {
      print('[LocalStorage] No emergency contacts found.');
    }
    // debugPrint('[LocalStorage] === GET EMERGENCY CONTACTS END (EMPTY) ===');
    return [];
  }

  Future<String> getOrCreateDeviceId() async {
    final prefs = await _prefs;
    String? deviceId = prefs.getString(_deviceIdKey);
    if (deviceId == null) {
      deviceId = const Uuid().v4();
      await prefs.setString(_deviceIdKey, deviceId);
      if (kDebugMode) {
        print('LocalStorage: New device ID generated: $deviceId');
      }
    } else if (kDebugMode) {
      print('LocalStorage: Existing device ID loaded: $deviceId');
    }
    return deviceId;
  }

  Future<void> clearUserSettingsAndContacts() async {
    final prefs = await _prefs;
    
    // Clear all user-related data
    await prefs.remove(_onboardingCompleteKey);
    await prefs.remove(_userSettingsKey);
    await prefs.remove(_emergencyContactsKey);
    
    // Note: Device ID is intentionally not cleared to maintain device tracking
    
    // Clear any additional cached data (if any)
    if (kDebugMode) {
      print('LocalStorage: User settings and contacts cleared');
    }
  }
  
  // 完全リセット用：タイムライン等の全データをクリア（デバイスIDは保持）
  Future<void> clearAllUserData() async {
    final prefs = await _prefs;
    
    // 保持すべきキー（デバイスIDなど）を保存
    final String? deviceId = prefs.getString(_deviceIdKey);
    
    // 全データクリア
    await prefs.clear();
    
    // デバイスIDのみ復元
    if (deviceId != null) {
      await prefs.setString(_deviceIdKey, deviceId);
    }
    
    if (kDebugMode) {
      print('LocalStorage: All user data cleared (device ID preserved)');
    }
  }
  
  // 緊急モードの保存
  Future<void> saveEmergencyMode(String mode) async {
    final prefs = await _prefs;
    await prefs.setString(_emergencyModeKey, mode);
    if (kDebugMode) {
      print('LocalStorage: Emergency mode saved: $mode');
    }
  }
  
  // 緊急モードの読み込み
  Future<String> loadEmergencyMode() async {
    final prefs = await _prefs;
    final mode = prefs.getString(_emergencyModeKey) ?? 'normal';
    if (kDebugMode) {
      print('LocalStorage: Emergency mode loaded: $mode');
    }
    return mode;
  }
}
