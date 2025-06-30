// lib/core/utils/device_id_util.dart
import 'dart:io';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import 'package:flutter/foundation.dart'; // kDebugMode用

class DeviceIdUtil {
  static const String _deviceIdKey = 'unique_device_id_v1'; // キー名 (バージョン管理を考慮)
  static String? _cachedDeviceId;

  // プライベートコンストラクタ (インスタンス化を防ぐ)
  DeviceIdUtil._();

  static Future<void> _generateAndSaveDeviceId(SharedPreferences prefs) async {
    const uuid = Uuid();
    _cachedDeviceId = uuid.v4(); // 新しいUUID v4を生成
    await prefs.setString(_deviceIdKey, _cachedDeviceId!); // ローカルストレージに保存
    if (kDebugMode) {
      print('Generated and saved new device ID: $_cachedDeviceId');
    }
  }

  /// アプリ起動時にデバイスIDを初期化（生成または読み込み）し、取得します。
  /// このメソッドは `main()` 関数で一度だけ呼び出すことを想定しています。
  static Future<String> initializeAndGetDeviceId() async {
    // メモリキャッシュに既にIDがあればそれを返す
    if (_cachedDeviceId != null && _cachedDeviceId!.isNotEmpty) {
      if (kDebugMode) {
        print('Returned cached device ID: $_cachedDeviceId');
      }
      return _cachedDeviceId!;
    }

    final SharedPreferences prefs = await SharedPreferences.getInstance();
    
    // 古いキー形式からのマイグレーション
    await _migrateOldDeviceId(prefs);
    
    final String? existingId = prefs.getString(_deviceIdKey);

    if (existingId != null && existingId.isNotEmpty) {
      _cachedDeviceId = existingId;
      if (kDebugMode) {
        print('Loaded existing device ID from storage: $_cachedDeviceId');
      }
    } else {
      // 既存IDがない場合は新規生成・保存
      await _generateAndSaveDeviceId(prefs);
    }
    // ここでは _cachedDeviceId が null でないことが保証される
    return _cachedDeviceId!;
  }

  /// 古いキー形式のデバイスIDを新しいキーに移行
  static Future<void> _migrateOldDeviceId(SharedPreferences prefs) async {
    const String oldKey = 'device_id';
    final String? oldDeviceId = prefs.getString(oldKey);
    final String? newDeviceId = prefs.getString(_deviceIdKey);
    
    // 新しいキーにIDがなく、古いキーにIDがある場合は移行
    if (newDeviceId == null && oldDeviceId != null && oldDeviceId.isNotEmpty) {
      await prefs.setString(_deviceIdKey, oldDeviceId);
      await prefs.remove(oldKey); // 古いキーを削除
      if (kDebugMode) {
        print('Migrated device ID from old key: $oldDeviceId');
      }
    }
  }

  /// 現在キャッシュされているデバイスIDを取得します。
  /// `initializeAndGetDeviceId` が呼び出された後に使用してください。
  static String? get currentDeviceId {
    if (_cachedDeviceId == null || _cachedDeviceId!.isEmpty) {
      if (kDebugMode) {
        print('Warning: currentDeviceId accessed before initialization or ID is empty.');
      }
    }
    return _cachedDeviceId;
  }

  static String getPlatform() {
    if (Platform.isAndroid) return 'android';
    if (Platform.isIOS) return 'ios';
    if (Platform.isWindows) return 'web';
    if (Platform.isMacOS) return 'web';
    if (Platform.isLinux) return 'web';
    return 'web';
  }
}
