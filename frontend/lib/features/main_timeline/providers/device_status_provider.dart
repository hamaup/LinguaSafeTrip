import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:geolocator/geolocator.dart' as geo;
import 'dart:async';
import 'dart:io' show Platform;
import 'package:battery_plus/battery_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:frontend/core/models/location_model.dart';
import 'package:frontend/core/models/heartbeat_response_model.dart';
import 'package:frontend/core/models/user_settings_model.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/core/providers/service_providers.dart';
import 'package:frontend/core/utils/device_id_util.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:frontend/core/services/local_storage_service.dart';

part 'device_status_provider.freezed.dart';
part 'device_status_provider.g.dart';

@freezed
class DeviceStatusState with _$DeviceStatusState {
  const factory DeviceStatusState({
    @Default(ConnectivityResult.none) ConnectivityResult connectivityStatus,
    @Default(false) bool isGpsEnabled,
    @Default(100) int batteryLevel,
    @Default(false) bool isBatteryCharging,
    LocationModel? currentLocation,
    @Default(false) bool isLocationPermissionGranted,
    String? locationError,
    @Default('normal') String currentMode,
    @Default(false) bool isChatActive,
  }) = _DeviceStatusState;
}

@riverpod
class DeviceStatus extends _$DeviceStatus {
  Timer? _periodicDataTimer;
  DateTime? _lastSyncTimestamp;
  String _currentMode = 'normal';
  bool _isChatActive = false;
  late final LocalStorageService _localStorage;
  int _heartbeatCount = 0;
  
  // 位置情報キャッシュ
  LocationModel? _cachedLocation;
  DateTime? _lastLocationUpdate;
  static const Duration _locationCacheTimeout = Duration(seconds: 60); // キャッシュ時間を60秒に延長
  bool _isGettingLocation = false; // 位置情報取得中フラグ
  
  // 設定キャッシュ - 削除予定
  
  // 権限状態キャッシュ - 削除予定
  
  LocationModel? _lastKnownLocation; // 前回取得成功した位置情報（フォールバック用）
  bool _isPermissionCheckInProgress = false; // 権限チェック中の排他制御フラグ

  @override
  DeviceStatusState build() {
    // LocalStorageServiceを取得
    _localStorage = ref.read(localStorageServiceProvider);
    
    // プロバイダーが破棄される時にタイマーをクリーンアップ
    ref.onDispose(() {
      _stopPeriodicDataTransmission();
    });
    
    return DeviceStatusState(
      currentMode: _currentMode,
      isChatActive: _isChatActive,
    );
  }

  Future<void> initialize() async {
    // 保存された緊急モードを読み込む
    _currentMode = await _localStorage.loadEmergencyMode();
    
    // 初期化時のみUIに反映（その後の更新は setEmergencyMode で行う）
    if (state.currentMode != _currentMode) {
      state = state.copyWith(currentMode: _currentMode);
    }
    
    // Suggestion history management removed - backend controls timing
    
    final connectivity = Connectivity();
    final battery = Battery();

    // 初期状態取得
    _updateConnectivity((await connectivity.checkConnectivity()).first);
    _updateGpsStatus(await geo.Geolocator.isLocationServiceEnabled());
    _updateBatteryStatus(
      await battery.batteryLevel,
      await battery.batteryState,
    );

    // Check initial location permission status
    await _checkLocationPermissionStatus(caller: 'initialize');
    
    // Set up periodic location permission check
    _setupLocationPermissionMonitoring();

    // Location tracking removed from initialization - only obtained during heartbeat

    // 状態変化監視
    connectivity.onConnectivityChanged.listen((results) {
      _updateConnectivity(results.first);
    });
    
    // For battery_plus 6.0.1 - use polling
    Timer.periodic(const Duration(seconds: 30), (_) async {
      _updateBatteryLevel(await battery.batteryLevel);
      _updateBatteryCharging(
        (await battery.batteryState) == BatteryState.charging
      );
    });

    // デバイスデータの定期送信開始（初回送信も含まれる）
    _startPeriodicDataTransmission();
  }

  void _updateConnectivity(ConnectivityResult result) {
    final previousStatus = state.connectivityStatus;
    state = state.copyWith(connectivityStatus: result);
    
    // ネットワーク復旧を検知（オフライン→オンライン）
    if (previousStatus == ConnectivityResult.none && 
        result != ConnectivityResult.none) {
      _handleNetworkRecovery();
    }
  }
  
  Future<void> _handleNetworkRecovery() async {
    try {
      // Network recovery handled automatically by next heartbeat
    } catch (e) {
      if (kDebugMode) {
        // debugPrint('[DeviceStatus] Failed to handle network recovery: $e');
      }
    }
  }

  void _updateGpsStatus(bool enabled) {
    state = state.copyWith(isGpsEnabled: enabled);
  }

  void _updateBatteryStatus(int level, BatteryState batteryState) {
    _updateBatteryLevel(level);
    _updateBatteryCharging(batteryState == BatteryState.charging);
  }

  void _updateBatteryLevel(int level) {
    if (state.batteryLevel != level) {
      state = state.copyWith(batteryLevel: level);
    }
  }

  void _updateBatteryCharging(bool charging) {
    if (state.isBatteryCharging != charging) {
      state = state.copyWith(isBatteryCharging: charging);
    }
  }

  Future<String> getDeviceId() async {
    // DeviceIdUtilを使用して統一されたデバイスIDを取得
    final deviceId = DeviceIdUtil.currentDeviceId;
    if (deviceId != null && deviceId.isNotEmpty) {
      return deviceId;
    }
    
    // 初期化されていない場合は初期化
    return await DeviceIdUtil.initializeAndGetDeviceId();
  }

  Future<LocationModel?> getCurrentLocation() async {
    if (kDebugMode) {
      debugPrint('[DeviceStatus] getCurrentLocation called, kIsWeb: $kIsWeb, _isGettingLocation: $_isGettingLocation');
    }
    
    // 既に位置情報取得中なら早期リターン
    if (_isGettingLocation) {
      if (kDebugMode) {
        debugPrint('[DeviceStatus] Already getting location, skipping...');
      }
      return _cachedLocation;
    }
    
    
    try {
      _isGettingLocation = true;
      
      // Check if location services are enabled
      bool serviceEnabled = await geo.Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        // Web版ではエラー時のstate更新を抑制（無限ループ防止）
        if (!kIsWeb) {
          state = state.copyWith(
            locationError: '位置情報サービスが無効です。設定で有効にしてください。',
            currentLocation: null,
          );
        }
        if (kDebugMode) {
        // debugPrint('[DeviceStatus] Location services are disabled');
        }
        _isGettingLocation = false;
        return null;
      }

      // Check location permission via unified method (this updates state)
      await _checkLocationPermissionStatus(caller: 'getCurrentLocation');
      
      // Use the permission status from state (already updated by _checkLocationPermissionStatus)
      if (!state.isLocationPermissionGranted) {
        final permission = await geo.Geolocator.checkPermission();
        if (permission == geo.LocationPermission.deniedForever) {
          // Web版ではエラー時のstate更新を抑制（無限ループ防止）
          if (!kIsWeb) {
            state = state.copyWith(
              locationError: '位置情報の許可が永続的に拒否されています。設定アプリから許可してください。',
              currentLocation: null,
            );
          }
          if (kDebugMode) {
        // debugPrint('[DeviceStatus] Location permission permanently denied');
          }
        } else {
          // Web版ではエラー時のstate更新を抑制（無限ループ防止）
          if (!kIsWeb) {
            state = state.copyWith(
              locationError: '位置情報の許可が必要です。',
              currentLocation: null,
            );
          }
          if (kDebugMode) {
        // debugPrint('[DeviceStatus] Location permission not granted');
          }
        }
        _isGettingLocation = false;
        return null;
      }
      
      // キャッシュチェック - 60秒以内なら再利用
      if (_cachedLocation != null && _lastLocationUpdate != null) {
        final cacheAge = DateTime.now().difference(_lastLocationUpdate!);
        if (cacheAge < _locationCacheTimeout) {
          if (kDebugMode) {
            // debugPrint('[DeviceStatus] 📍 Using cached location (age: ${cacheAge.inSeconds}s)');
          }
          return _cachedLocation!;
        }
      }
      
      if (kDebugMode) {
        debugPrint('[DeviceStatus] Getting current position...');
      }
      
      // 最後に取得した位置情報をクイックチェック
      try {
        final lastKnown = await geo.Geolocator.getLastKnownPosition();
        if (lastKnown != null) {
          final age = DateTime.now().difference(lastKnown.timestamp);
          // 1分以内なら使用（大幅に緩和）
          if (age < const Duration(minutes: 1)) {
            final cachedLocationModel = LocationModel(
              latitude: lastKnown.latitude,
              longitude: lastKnown.longitude,
              accuracy: lastKnown.accuracy,
            );
            _cachedLocation = cachedLocationModel;
            _lastLocationUpdate = DateTime.now();
            if (kDebugMode) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Using last known position (age: ${age.inSeconds}s)');
            }
            return cachedLocationModel;
          }
        }
      } catch (e) {
        if (kDebugMode) {
        // debugPrint('[DeviceStatus] Error getting last known position: $e');
        }
      }
      
      // Force refresh by using forceLocationUpdate
      
      try {
        
        // エミュレータ検出
        final isEmulator = await _isRunningOnEmulator();
        if (kDebugMode) {
          debugPrint('[DeviceStatus] Running on emulator: $isEmulator');
        }
        
        geo.Position? position;
        
        // まず最後の既知の位置を試す（1分以内のものなら使用）
        try {
          geo.Position? lastKnown = await geo.Geolocator.getLastKnownPosition();
          if (lastKnown != null) {
            final age = DateTime.now().difference(lastKnown.timestamp);
            if (age < const Duration(minutes: 1)) {
              if (kDebugMode) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Using recent last known position (age: ${age.inSeconds}s)');
              }
              position = lastKnown;
            } else {
              if (kDebugMode) {
        // debugPrint('[DeviceStatus] Last known position too old (age: ${age.inSeconds}s), fetching fresh...');
              }
            }
          }
        } catch (e) {
          if (kDebugMode) {
        // debugPrint('[DeviceStatus] Error getting last known position: $e');
          }
        }
        
        // 新しい位置情報を取得（必要な場合）
        if (position == null) {
          int retryCount = 0;
          final maxRetries = kIsWeb ? 1 : 2; // Web版はリトライ1回のみ
          
          while (position == null && retryCount < maxRetries) {
            try {
              if (kDebugMode) {
                debugPrint('[DeviceStatus] Getting current position (attempt ${retryCount + 1}/$maxRetries)...');
              }
              
              // Web版はより長いタイムアウトと最低精度で設定
              final timeoutSeconds = kIsWeb ? 30 : (isEmulator ? 12 : 7);
              final timeLimitSeconds = kIsWeb ? 25 : (isEmulator ? 10 : 5);
              
              if (kDebugMode && kIsWeb) {
                print('[DeviceStatus] 🌐 Web版位置情報取得開始 (タイムアウト: ${timeoutSeconds}秒)');
              }
              
              position = await geo.Geolocator.getCurrentPosition(
                desiredAccuracy: kIsWeb ? geo.LocationAccuracy.lowest : (isEmulator ? geo.LocationAccuracy.lowest : geo.LocationAccuracy.medium),
                timeLimit: Duration(seconds: timeLimitSeconds),
                forceAndroidLocationManager: isEmulator && !kIsWeb,
              ).timeout(
                Duration(seconds: timeoutSeconds),
                onTimeout: () {
                  if (kDebugMode) {
                    debugPrint('[DeviceStatus] ⚠️ Location timeout on ${kIsWeb ? "Web" : "Mobile"} (attempt ${retryCount + 1})');
                  }
                  throw TimeoutException('Location timeout', Duration(seconds: timeoutSeconds));
                },
              );
              
              if (kDebugMode) {
        // if (kDebugMode) debugPrint('[DeviceStatus] ✅ Position obtained successfully');
              }
            } catch (e) {
              retryCount++;
              if (retryCount >= maxRetries) {
                if (kDebugMode) {
        // if (kDebugMode) debugPrint('[DeviceStatus] ❌ All retry attempts failed');
                }
                rethrow;
              }
              if (kDebugMode) {
                debugPrint('[DeviceStatus] Retry $retryCount/$maxRetries after error: $e');
              }
              await Future.delayed(const Duration(seconds: 2)); // 少し待ってからリトライ
            }
          }
        }
        
        // position は null にならないため、このチェックは削除
        
        // getCurrentPosition completed successfully

      // // FOR TESTING ONLY - Override Mountain View coordinates with Tokyo coordinates
      // if (kDebugMode && position.latitude == 37.4217937 && position.longitude == -122.083922) {
      //   debugPrint('[DeviceStatus] 🚨 Detected Mountain View coordinates in debug mode - overriding with Tokyo coordinates');
      //   position = geo.Position(
      //     latitude: 35.6812362,   // Tokyo Station
      //     longitude: 139.7671248, // Tokyo Station
      //     timestamp: position.timestamp,
      //     accuracy: position.accuracy,
      //     altitude: position.altitude,
      //     altitudeAccuracy: position.altitudeAccuracy,
      //     heading: position.heading,
      //     headingAccuracy: position.headingAccuracy,
      //     speed: position.speed,
      //     speedAccuracy: position.speedAccuracy,
      //     isMocked: true,
      //   );
      //   debugPrint('[DeviceStatus] ✅ Location overridden to Tokyo Station for testing');
      // }

      // Position data obtained successfully
      if (position == null) {
        if (kDebugMode) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Position is null after all attempts');
        }
        throw Exception('Failed to get position');
      }
      
      final location = LocationModel(
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
        altitude: position.altitude,
      );

      // 最後の位置情報を保存（フォールバック用）
      _lastKnownLocation = location;
      
      // 位置情報のキャッシュ更新
      _cachedLocation = location;
      _lastLocationUpdate = DateTime.now();
      
      // 状態更新: 位置情報を状態に反映（無限ループを防ぐため条件付き）
      if (state.currentLocation == null || 
          state.currentLocation!.latitude != location.latitude ||
          state.currentLocation!.longitude != location.longitude) {
        state = state.copyWith(
          currentLocation: location,
          locationError: null,
        );
      }

      if (kDebugMode) {
        // if (kDebugMode) debugPrint('[DeviceStatus] ✅ Location updated and cached');
      }
      _isGettingLocation = false;
      return location;
      } catch (innerError) {
        _isGettingLocation = false;
        rethrow;
      }
    } catch (e) {
      if (kDebugMode) debugPrint('[DeviceStatus] Error getting location: $e');
      
      // エラー時の詳細ログ
      if (kDebugMode) debugPrint('[DeviceStatus] ❌ Location acquisition failed: ${e.runtimeType}');
      if (kDebugMode) debugPrint('[DeviceStatus] Error details: $e');
      
      // タイムアウト時の処理（キャッシュは使用しない）
      if (e is TimeoutException) {
        // if (kDebugMode) debugPrint('[DeviceStatus] ⏱️ Location timeout occurred');
      }
      
      // Web版でタイムアウトした場合の処理
      if (kIsWeb && e is TimeoutException) {
        if (kDebugMode) {
          print('[DeviceStatus] 🌐 Web版: 位置情報取得タイムアウト - 位置情報なしで続行');
        }
        // 位置情報なしで続行（フォールバック位置は使用しない）
      }
      
      // フォールバック：前回取得成功した位置情報があれば使用
      if (_lastKnownLocation != null) {
        state = state.copyWith(
          currentLocation: _lastKnownLocation!,
          locationError: '最新の位置情報を取得できません（前回の位置を使用中）',
        );
        return _lastKnownLocation!;
      }
      
      
      // Web版ではエラー時のstate更新を抑制（無限ループ防止）
      if (!kIsWeb) {
        state = state.copyWith(
          locationError: _generateUserFriendlyLocationError(e),
          currentLocation: null,
        );
      } else {
        // Web版ではエラー状態をログのみで記録
        if (kDebugMode) {
          print('[DeviceStatus] 🌐 Web版: 位置情報取得失敗 - 位置情報なしでアプリ続行');
        }
      }
      return null;
    } finally {
      _isGettingLocation = false;
    }
  }

  Future<void> startLocationTracking() async {
    // Clear any cached last known position first
    try {
      await geo.Geolocator.getLastKnownPosition();
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error checking last known position: $e');
    }
    
    // Initialize location permission and get initial location
    await getCurrentLocation();

    // Listen to location service status changes
    geo.Geolocator.getServiceStatusStream().listen((geo.ServiceStatus status) {
      final isEnabled = status == geo.ServiceStatus.enabled;
      _updateGpsStatus(isEnabled);
      
      if (!isEnabled) {
        state = state.copyWith(
          currentLocation: null,
          locationError: 'Location services disabled',
        );
      }
    });
  }

  /// User explicitly requests location permission
  Future<bool> requestLocationPermission() async {
        // if (kDebugMode) debugPrint('[DeviceStatus] User requested location permission');
    
    try {
      // Web版の場合は直接Geolocator.requestPermission()を使用
      if (kIsWeb) {
        try {
          final permission = await geo.Geolocator.requestPermission();
          final isGranted = permission == geo.LocationPermission.always || 
                           permission == geo.LocationPermission.whileInUse;
          
          // 状態を更新
          state = state.copyWith(
            isLocationPermissionGranted: isGranted,
            isGpsEnabled: true, // Web版では常にtrue
            locationError: isGranted ? null : 'ブラウザで位置情報の許可が拒否されました',
          );
          
          // 権限が取得できた場合は即座に位置情報を取得
          if (isGranted) {
            if (kDebugMode) {
              print('[DeviceStatus] 📍 Web permission granted - getting location automatically');
            }
            try {
              final location = await getCurrentLocation();
              if (location != null) {
                state = state.copyWith(
                  currentLocation: location,
                  locationError: null,
                );
                if (kDebugMode) {
                  print('[DeviceStatus] 📍 Web location obtained: ${location.latitude}, ${location.longitude}');
                }
              }
            } catch (e) {
              if (kDebugMode) {
                print('[DeviceStatus] 📍 Failed to get location after permission: $e');
              }
            }
          }
          
          return isGranted;
        } catch (e) {
          if (kDebugMode) {
            print('[DeviceStatus] Web permission request error: $e');
          }
          state = state.copyWith(
            locationError: 'ブラウザで位置情報の許可エラーが発生しました',
          );
          return false;
        }
      }
      
      // モバイル版の処理（従来通り）
      // まず現在の状態を詳細確認
      final currentPermission = await geo.Geolocator.checkPermission();
        // if (kDebugMode) debugPrint('[DeviceStatus] Current permission before request: $currentPermission');
      
      // 永続的に拒否されている場合は設定画面へ誘導
      if (currentPermission == geo.LocationPermission.deniedForever) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Permission permanently denied, opening app settings');
        await openApplicationSettings();
        
        // 設定画面から戻ってきた後の状態確認
        await Future.delayed(const Duration(seconds: 1));
        await _checkLocationPermissionStatus(caller: 'requestLocationPermission_afterSettings');
        return state.isLocationPermissionGranted;
      }
      
      // サービス有効状態も確認
      final serviceEnabled = await geo.Geolocator.isLocationServiceEnabled();
        // if (kDebugMode) debugPrint('[DeviceStatus] Location service enabled: $serviceEnabled');
      
      if (!serviceEnabled) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Location service is disabled, opening location settings');
        final opened = await geo.Geolocator.openLocationSettings();
        // if (kDebugMode) debugPrint('[DeviceStatus] Location settings opened: $opened');
        
        // 設定画面が開かれた後、再度サービス状態を確認
        await Future.delayed(const Duration(seconds: 2));
        final newServiceStatus = await geo.Geolocator.isLocationServiceEnabled();
        // if (kDebugMode) debugPrint('[DeviceStatus] Location service status after settings: $newServiceStatus');
        
        if (!newServiceStatus) {
          state = state.copyWith(
            locationError: '位置情報サービスを有効にしてください',
          );
          return false;
        }
      }
      
      // 許可をリクエスト
      final permission = await geo.Geolocator.requestPermission();
      final isGranted = permission == geo.LocationPermission.always || 
                       permission == geo.LocationPermission.whileInUse;
      
        // if (kDebugMode) debugPrint('[DeviceStatus] Location permission request result: $permission (granted: $isGranted)');
      
      // 状態を更新（統一された権限チェックメソッドを使用）
      await _checkLocationPermissionStatus(caller: 'requestLocationPermission');
      
      // 追加で状態確認（念のため）
      final finalIsGranted = state.isLocationPermissionGranted;
        // if (kDebugMode) debugPrint('[DeviceStatus] Final permission state after request: $finalIsGranted');
      
      if (isGranted) {
        // Location tracking removed - no immediate location fetch on permission grant
        // Location will be obtained only during heartbeat transmission
        
        // 権限取得成功後、再度状態を確認して最新の状態をUIに反映
        await Future.delayed(const Duration(milliseconds: 500));
        await _checkLocationPermissionStatus(caller: 'requestLocationPermission_postSuccess');
      }
      
      // 最終的な状態を再取得
      final finalState = state.isLocationPermissionGranted;
        // if (kDebugMode) debugPrint('[DeviceStatus] Returning final permission state: $finalState');
      return finalState;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error requesting location permission: $e');
      state = state.copyWith(
        locationError: '権限リクエストでエラーが発生しました',
      );
      return false;
    }
  }
  
  /// 位置情報設定画面を開く
  Future<void> openLocationSettings() async {
    try {
      await geo.Geolocator.openLocationSettings();
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error opening location settings: $e');
    }
  }
  
  /// アプリ設定画面を開く（権限設定用）
  Future<void> openApplicationSettings() async {
    try {
      await openAppSettings(); // From permission_handler package
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error opening app settings: $e');
    }
  }

  /// ハートビートの定期送信を開始
  void _startPeriodicDataTransmission() {
    // 既存のタイマーをキャンセル
    _periodicDataTimer?.cancel();
    
    // ユーザー設定のハートビート間隔を使用（分単位から秒単位に変換）
    // 設定が初期化されていない場合はデフォルト値を使用
    UserSettingsModel? userSettings;
    try {
      final settingsState = ref.read(settingsProvider);
      userSettings = settingsState.currentUserSettings;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Settings not initialized for heartbeat, using defaults: $e');
    }
    int intervalSeconds = _currentMode == 'emergency' 
        ? (userSettings?.heartbeatIntervalEmergencyMinutes ?? 15) * 60
        : (userSettings?.heartbeatIntervalNormalMinutes ?? 60) * 60;
    
    // 既存のタイマーが残っていないことを確認
    if (_periodicDataTimer != null && _periodicDataTimer!.isActive) {
        // if (kDebugMode) debugPrint('[DeviceStatus] ⚠️ WARNING: Previous timer still active! Cancelling...');
      _periodicDataTimer!.cancel();
    }
    
    _periodicDataTimer = Timer.periodic(
      Duration(seconds: intervalSeconds),
      (timer) {
        _sendPeriodicDeviceData();
      },
    );
    
    // 初回ハートビート送信
    _sendInitialHeartbeat();
  }

  /// 初回ハートビート送信
  Future<void> _sendInitialHeartbeat() async {
    if (kDebugMode) {
      print('[DeviceStatus] 📍 === INITIAL HEARTBEAT DEBUG START ===');
      print('[DeviceStatus] 📍 Initial heartbeat triggered at: ${DateTime.now()}');
      print('[DeviceStatus] 📍 Current permission status: ${state.isLocationPermissionGranted ? "GRANTED" : "NOT GRANTED"}');
      print('[DeviceStatus] 📍 GPS enabled: ${state.isGpsEnabled}');
      print('[DeviceStatus] 📍 Current location: ${state.currentLocation?.latitude ?? "null"}, ${state.currentLocation?.longitude ?? "null"}');
      print('[DeviceStatus] 📍 Cached location: ${_cachedLocation?.latitude ?? "null"}, ${_cachedLocation?.longitude ?? "null"}');
      print('[DeviceStatus] 📍 Last known location: ${_lastKnownLocation?.latitude ?? "null"}, ${_lastKnownLocation?.longitude ?? "null"}');
    }
    
    // SettingsProviderの初期化を待つ（最大1秒）
    int attempts = 0;
    while (attempts < 10) {
      if (ref.exists(settingsProvider)) {
        final settings = ref.read(settingsProvider);
        if (!settings.isLoading && settings.currentUserSettings != null) {
          break;
        }
      }
      await Future.delayed(const Duration(milliseconds: 100));
      attempts++;
    }
    
    if (kDebugMode) {
      print('[DeviceStatus] 📍 Settings initialized after $attempts attempts');
      print('[DeviceStatus] 📍 Sending first heartbeat now...');
    }
    
    // 即座に送信
    await _sendPeriodicDeviceData();
    
    if (kDebugMode) {
      print('[DeviceStatus] 📍 === INITIAL HEARTBEAT DEBUG END ===');
    }
  }

  /// デバイスデータの定期送信を停止
  void _stopPeriodicDataTransmission() {
    if (_periodicDataTimer != null) {
      _periodicDataTimer?.cancel();
      _periodicDataTimer = null;
    }
  }

  /// ハートビートをバックエンドに送信
  Future<void> _sendPeriodicDeviceData() async {
    try {
      
      final deviceId = await getDeviceId();
      
      final apiService = ref.read(apiServiceProvider);
      
      // 最新の位置情報を取得（エラーの場合はnull）
      LocationModel? currentLocation;
      
      // 位置情報取得（初回でも試みる）
      // 初回ハートビートかつ権限がない場合は、非同期で権限確認を開始
      if (_heartbeatCount == 0 && !state.isLocationPermissionGranted) {
        if (kDebugMode) {
          print('[DeviceStatus] 📍 First heartbeat - location permission NOT granted');
          print('[DeviceStatus] 📍 Starting background permission check...');
        }
        // 非同期で権限確認（ハートビートをブロックしない）
        _checkLocationPermissionStatus(caller: 'first_heartbeat').then((_) {
          if (state.isLocationPermissionGranted) {
            // 権限が取得できたら位置情報を更新
            getCurrentLocation();
          }
        });
        // 初回は前回の位置情報またはnullを使用
        currentLocation = _lastKnownLocation;
        
        // 緊急モードの場合は位置情報取得を強制実行
        if (_currentMode == 'emergency' && currentLocation == null) {
          if (kDebugMode) {
            print('[DeviceStatus] 🚨 Emergency mode: forcing location acquisition on first heartbeat');
          }
          try {
            currentLocation = await getCurrentLocation();
            if (kDebugMode && currentLocation != null) {
              print('[DeviceStatus] 🚨 Emergency location obtained: ${currentLocation.latitude}, ${currentLocation.longitude}');
            }
          } catch (e) {
            if (kDebugMode) {
              print('[DeviceStatus] 🚨 Emergency location acquisition failed: $e');
            }
          }
        }
      } else {
        try {
          // キャッシュがあればそれを使用（初回ハートビートの高速化）
          if (_cachedLocation != null && _lastLocationUpdate != null) {
            final cacheAge = DateTime.now().difference(_lastLocationUpdate!);
            if (cacheAge < _locationCacheTimeout) {
              currentLocation = _cachedLocation;
        // if (kDebugMode) debugPrint('[DeviceStatus] Using cached location for heartbeat');
            } else {
              currentLocation = await getCurrentLocation();
            }
          } else {
            currentLocation = await getCurrentLocation();
          }
        } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Location not available for heartbeat: $e');
          // 位置情報が取得できなくてもハートビートは送信する
        }
      }
      
      // 言語コードを取得（LocalStorageから直接読み込み - チャットと同じロジック）
      String languageCode = 'ja'; // デフォルト
      try {
        final directSettings = await _localStorage.loadUserSettings();
        if (directSettings != null && directSettings.languageCode.isNotEmpty) {
          languageCode = directSettings.languageCode;
        } else {
          // フォールバック：SettingsProviderを確認
          if (ref.exists(settingsProvider)) {
            final settingsState = ref.read(settingsProvider);
            if (!settingsState.isLoading && settingsState.currentUserSettings != null) {
              languageCode = settingsState.currentUserSettings!.languageCode;
            }
          }
        }
      } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Language retrieval failed: $e');
      }
      
        // if (kDebugMode) debugPrint('[DeviceStatus] Using language for heartbeat: $languageCode');
      
      // 緊急連絡先数を取得
      final emergencyContactsCount = await _getEmergencyContactsCount();
      
      // 権限状態を取得（キャッシュ化で最適化）
      final permissions = await _getCachedPermissions();
      final isLocationGrantedNow = permissions['location']!;
      final isGpsEnabledNow = permissions['gps']!;
      final isNotificationPermissionGranted = permissions['notification']!;
      
      // デバッグ：ハートビート送信時の位置情報
      if (kDebugMode) {
        print('[DeviceStatus] 📍 === HEARTBEAT LOCATION DEBUG ===');
        print('[DeviceStatus] 📍 Heartbeat #${_heartbeatCount} at: ${DateTime.now()}');
        print('[DeviceStatus] 📍 Current mode: $_currentMode');
        print('[DeviceStatus] 📍 Location permission: $isLocationGrantedNow');
        print('[DeviceStatus] 📍 GPS enabled: $isGpsEnabledNow');
        if (currentLocation != null) {
          print('[DeviceStatus] ✅ Sending location:');
          print('[DeviceStatus]   - Latitude: ${currentLocation.latitude}');
          print('[DeviceStatus]   - Longitude: ${currentLocation.longitude}');
          print('[DeviceStatus]   - Accuracy: ${currentLocation.accuracy}m');
        } else {
          print('[DeviceStatus] ❌ No location data to send');
        }
        print('[DeviceStatus] 📍 === HEARTBEAT LOCATION DEBUG END ===');
      }
      
      final response = await apiService.sendHeartbeat(
        deviceId: deviceId,
        batteryLevel: state.batteryLevel,
        isBatteryCharging: state.isBatteryCharging,
        connectivityStatus: state.connectivityStatus.name,
        currentLocation: currentLocation,
        currentMode: _currentMode,
        languageCode: languageCode,
        lastSyncTimestamp: _lastSyncTimestamp,
        emergencyContactsCount: emergencyContactsCount,
        isLocationPermissionGranted: isLocationGrantedNow,
        isGpsEnabled: isGpsEnabledNow,
        isNotificationPermissionGranted: isNotificationPermissionGranted,
      );
      
      // レスポンスを処理（型安全なHeartbeatResponseを使用）
      await _processHeartbeatResponse(response);
      
      // 最新の権限状態で状態を更新（整合性確保）
      if (state.isLocationPermissionGranted != isLocationGrantedNow || state.isGpsEnabled != isGpsEnabledNow) {
        state = state.copyWith(
          isLocationPermissionGranted: isLocationGrantedNow,
          isGpsEnabled: isGpsEnabledNow,
        );
      }
      
      // ハートビート成功後にSSE接続をトリガー
      await triggerHeartbeatSSE();
      
      // ハートビートカウントを増やす
      _heartbeatCount++;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] ❌ Failed to send heartbeat: $e');
    }
  }

  /// ハートビートレスポンスを処理
  Future<void> _processHeartbeatResponse(HeartbeatResponse response) async {
    try {
      _lastSyncTimestamp = DateTime.now();
      
      // disaster_status を処理（型安全なアクセス）
      await _processDisasterStatus(response.disasterStatus);
      
      // proactive_suggestions を処理
      if (response.proactiveSuggestions.isNotEmpty) {
        await _processProactiveSuggestions(response.proactiveSuggestions);
      }
      
      // sync_config を処理
      _processSyncConfig(response.syncConfig);
    } catch (e, stackTrace) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Failed to process heartbeat response: $e');
        // if (kDebugMode) debugPrint('[DeviceStatus] Stack trace: $stackTrace');
    }
  }

  /// 災害状態を処理（型安全なDisasterStatusを使用）
  Future<void> _processDisasterStatus(DisasterStatus disasterStatus) async {
    final mode = disasterStatus.mode.name;
    
    // モード変更の検出
    if (mode != _currentMode) {
      final previousMode = _currentMode;
      
      _currentMode = mode;
      
      // 緊急モードをローカルストレージに保存
      await _localStorage.saveEmergencyMode(_currentMode);
      
      // Riverpodの状態を更新してUIに通知（変更がある場合のみ）
      if (state.currentMode != _currentMode) {
        state = state.copyWith(currentMode: _currentMode);
      }
      
      // モード変更時はハートビート間隔を即座に調整
      _adjustHeartbeatIntervalForMode();
      
      if (mode == 'emergency' && previousMode != 'emergency') {
        if (ref.exists(timelineProvider)) {
          ref.read(timelineProvider.notifier).clearNormalModeSuggestions();
        }
      } else if (mode == 'normal' && previousMode == 'emergency') {
        if (ref.exists(timelineProvider)) {
          ref.read(timelineProvider.notifier).clearEmergencyModeSuggestions();
        }
      }
    }
  }
  

  /// プロアクティブ提案を処理（型安全なHeartbeatSuggestionを使用）
  Future<void> _processProactiveSuggestions(List<HeartbeatSuggestion> suggestions) async {
    // チャット中の場合は提案を抑制
    if (_isChatActive) {
      return;
    }
    
    if (suggestions.isEmpty) {
      return;
    }
    
    try {
      if (!ref.exists(timelineProvider)) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Timeline provider not initialized, skipping suggestions');
        return;
      }
      final timelineNotifier = ref.read(timelineProvider.notifier);
      
      // ハートビートAPIから受信した提案をTimelineItemModelに変換
      final newTimelineItems = <TimelineItemModel>[];
      
      for (final suggestion in suggestions) {
        final type = suggestion.type;
        final content = suggestion.content;
        final priority = suggestion.priority;
        final actionQuery = suggestion.actionQuery;
        final actionDisplayText = null; // HeartbeatSuggestionにはaction_display_textフィールドがない
        final expiresAt = suggestion.expiresAt?.toIso8601String();
        final backendActionData = suggestion.actionData;
        
        if (type.isNotEmpty && content.isNotEmpty) {
          final timelineItem = TimelineItemModel.suggestion(
            id: '${type}_${DateTime.now().millisecondsSinceEpoch}',
            suggestionType: type,
            content: content,
            actionData: {
              'priority': priority,
              if (expiresAt != null) 'expires_at': expiresAt,
              if (actionQuery != null) 'action_query': actionQuery,
              // バックエンドからのaction_dataをマージ
              if (backendActionData != null) ...backendActionData,
            },
            actionQuery: actionQuery,
            actionDisplayText: actionDisplayText,
            timestamp: DateTime.now(),
          );
          
          newTimelineItems.add(timelineItem);
        }
      }
      
      // タイムラインに新しい提案を追加
      if (newTimelineItems.isNotEmpty) {
        timelineNotifier.addProactiveSuggestions(newTimelineItems);
      }
      
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Failed to process proactive suggestions: $e');
    }
  }

  /// 同期設定を処理（型安全なSyncConfigを使用）
  void _processSyncConfig(SyncConfig syncConfig) {
    final minSyncInterval = syncConfig.minSyncInterval;
    final forceRefresh = syncConfig.forceRefresh;
    
    // テストモードの場合はサーバー指定間隔を無視
    if (!AppConfig.testMode && minSyncInterval > 0) {
      final currentInterval = _getCurrentExpectedInterval();
      if (minSyncInterval != currentInterval) {
        _updateSyncInterval(minSyncInterval);
      }
    }
    
    if (forceRefresh) {
      if (ref.exists(timelineProvider)) {
        ref.read(timelineProvider.notifier).refreshTimeline();
      }
    }
  }

  /// 現在のモードに期待される間隔を取得
  int _getCurrentExpectedInterval() {
    // ユーザー設定のハートビート間隔を使用（エラー時はデフォルト値）
    UserSettingsModel? userSettings;
    try {
      if (ref.exists(settingsProvider)) {
        final settingsState = ref.read(settingsProvider);
        userSettings = settingsState.currentUserSettings;
      }
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Settings not available for interval: $e');
    }
    return _currentMode == 'emergency' 
        ? (userSettings?.heartbeatIntervalEmergencyMinutes ?? 15) * 60
        : (userSettings?.heartbeatIntervalNormalMinutes ?? 60) * 60;
  }

  /// モードに応じてハートビート間隔を調整
  void _adjustHeartbeatIntervalForMode() {
    final currentInterval = _getCurrentExpectedInterval();
    _updateSyncInterval(currentInterval);
  }

  /// 同期間隔を動的に更新
  void _updateSyncInterval(int seconds) {
    if (_periodicDataTimer != null) {
      _periodicDataTimer?.cancel();
    }
    
        // if (kDebugMode) debugPrint('[DeviceStatus] Heartbeat interval updated to ${seconds}s');
    
    _periodicDataTimer = Timer.periodic(
      Duration(seconds: seconds),
      (timer) {
        _sendPeriodicDeviceData();
      },
    );
  }

  /// ハートビート設定変更時に呼び出されるメソッド
  void onHeartbeatSettingsChanged() {
        // if (kDebugMode) debugPrint('[DeviceStatus] Heartbeat settings changed, adjusting interval');
    _adjustHeartbeatIntervalForMode();
  }

  /// 緊急連絡先数を取得
  Future<int> _getEmergencyContactsCount() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final contactsStringList = prefs.getStringList('app_emergency_contacts_v2');
      return (contactsStringList == null || contactsStringList.isEmpty) ? 0 : contactsStringList.length;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error getting emergency contacts count: $e');
      return 0;
    }
  }
  
  /// 緊急連絡先キャッシュを無効化（連絡先変更時に呼び出し）
  void invalidateContactsCountCache() {
    // Cache removed
  }

  /// 通知権限の状態を確認
  Future<bool> _checkNotificationPermission() async {
    try {
      // permission_handlerパッケージを使用して通知権限を確認
      final status = await Permission.notification.status;
      return status.isGranted;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error checking notification permission: $e');
      return false;
    }
  }

  /// 言語変更時などに即座にハートビートを送信
  Future<void> sendImmediateHeartbeat() async {
    await _sendPeriodicDeviceData();
  }

  /// チャット開始時にプロアクティブ提案を抑制
  void startChatSession() {
    _isChatActive = true;
    state = state.copyWith(isChatActive: true);
  }

  /// チャット終了時にプロアクティブ提案を再開
  void endChatSession() {
    _isChatActive = false;
    state = state.copyWith(isChatActive: false);
    
    // チャット終了後も定期的なハートビートは継続
    // （即座の送信は行わない）
    if (kDebugMode) {
      print('[DeviceStatus] Chat ended - Heartbeat continues at regular intervals');
    }
  }

  /// チャット中かどうかを確認
  bool get isChatActive => _isChatActive;
  
  /// 現在の位置情報を取得（キャッシュから）
  LocationModel? get currentLocation => _cachedLocation;

  /// 現在のモードを取得（デバッグ用）
  String get currentMode => _currentMode;

  /// 提案への操作を記録（履歴管理は無効化済み）
  void acknowledgeSuggestionType(String suggestionType) {
    // Frontend history management disabled - backend controls timing
  }

  /// ハートビート統合SSE接続をトリガー
  Future<void> triggerHeartbeatSSE() async {
    try {
      if (ref.exists(timelineProvider)) {
        ref.read(timelineProvider.notifier).triggerSSEConnection();
      } else {
        // if (kDebugMode) debugPrint('[DeviceStatusProvider] Timeline provider not initialized, skipping SSE trigger');
      }
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatusProvider] Failed to trigger heartbeat SSE: $e');
    }
  }


  /// デバッグ用：緊急モードを手動設定
  void setEmergencyModeForDebug(bool isEmergency) {
    final previousMode = _currentMode;
    _currentMode = isEmergency ? 'emergency' : 'normal';
    
    // 緊急モードをローカルストレージに保存
    _localStorage.saveEmergencyMode(_currentMode).catchError((e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Failed to save emergency mode: $e');
    });
    
    // Riverpodの状態を更新してUIに通知（変更がある場合のみ）
    if (state.currentMode != _currentMode) {
      state = state.copyWith(currentMode: _currentMode);
    }
    
    // ハートビート間隔を即座に調整
    _adjustHeartbeatIntervalForMode();
    
    // モード変更時の提案クリア処理
    if (isEmergency && previousMode != 'emergency') {
      if (ref.exists(timelineProvider)) {
        ref.read(timelineProvider.notifier).clearNormalModeSuggestions();
      }
    } else if (!isEmergency && previousMode == 'emergency') {
      if (ref.exists(timelineProvider)) {
        ref.read(timelineProvider.notifier).clearEmergencyModeSuggestions();
      }
    }
    
    // 即座にハートビートを送信して状態を同期
    Future.microtask(() => _sendPeriodicDeviceData());
  }

  /// アプリ再起動通知（履歴管理は無効化済み）
  Future<void> resetSuggestionHistoryForAppRestart() async {
    // Backend manages all suggestion timing independently
  }

  /// 位置情報許可状態をチェック（排他制御付き）
  Future<void> _checkLocationPermissionStatus({String? caller}) async {
    // 排他制御：既に権限チェック中の場合はスキップ
    if (_isPermissionCheckInProgress) {
      return;
    }
    
    _isPermissionCheckInProgress = true;
    
    try {
      // Web版ではハートビートと同じ方法で権限チェック
      if (kIsWeb) {
        try {
          // Web版：実際の権限状態をチェック（ハートビートと同じロジック）
          final locationPermission = await geo.Geolocator.checkPermission();
          final isLocationGranted = locationPermission == geo.LocationPermission.always || 
                                   locationPermission == geo.LocationPermission.whileInUse;
          
          // GPS有効状態をチェック（Web版では常にtrue）
          final isGpsEnabled = await geo.Geolocator.isLocationServiceEnabled();
          
          if (kDebugMode) {
            print('[DeviceStatus] Web権限チェック結果: $locationPermission -> granted=$isLocationGranted');
          }
          
          // 状態更新
          if (state.isLocationPermissionGranted != isLocationGranted || state.isGpsEnabled != isGpsEnabled) {
            state = state.copyWith(
              isLocationPermissionGranted: isLocationGranted,
              isGpsEnabled: isGpsEnabled,
              locationError: isLocationGranted ? null : 'ブラウザで位置情報の許可が必要です',
            );
          }
          
          // Web版で権限が取得できた場合、即座に位置情報を取得
          if (isLocationGranted && caller == 'first_heartbeat') {
            if (kDebugMode) {
              print('[DeviceStatus] 📍 Web permission granted - attempting location acquisition');
            }
            // 非同期で位置情報取得を開始（ハートビートをブロックしない）
            getCurrentLocation().then((location) {
              if (location != null) {
                // 位置情報取得成功時はstateを更新
                state = state.copyWith(
                  currentLocation: location,
                  locationError: null,
                );
                if (kDebugMode) {
                  print('[DeviceStatus] 📍 Web location acquired automatically: ${location.latitude}, ${location.longitude}');
                }
              }
            }).catchError((e) {
              if (kDebugMode) {
                print('[DeviceStatus] 📍 Web location acquisition failed: $e');
              }
            });
          }
          
          return;
        } catch (e) {
          if (kDebugMode) {
            print('[DeviceStatus] Web location permission check failed: $e');
          }
          // Web版でエラーが発生した場合は状態を更新しない（無限ループ防止）
          return;
        }
      }
      
      // モバイル版の処理（従来通り）
      final locationPermission = await geo.Geolocator.checkPermission();
      final isLocationGranted = locationPermission == geo.LocationPermission.always || 
                               locationPermission == geo.LocationPermission.whileInUse;
      
      // GPS有効状態も同時にチェック
      final isGpsEnabled = await geo.Geolocator.isLocationServiceEnabled();
      
      // 状態更新（いずれかが変更された場合のみ）
      if (state.isLocationPermissionGranted != isLocationGranted || state.isGpsEnabled != isGpsEnabled) {
        state = state.copyWith(
          isLocationPermissionGranted: isLocationGranted,
          isGpsEnabled: isGpsEnabled,
        );
      }
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Failed to check location permission: $e');
    } finally {
      _isPermissionCheckInProgress = false;
    }
  }


  /// 位置情報許可状態の監視を設定
  void _setupLocationPermissionMonitoring() {
    // 15分ごとに位置情報許可状態をチェック
    Timer.periodic(const Duration(minutes: 15), (timer) async {
      await _checkLocationPermissionStatus(caller: 'periodicMonitoring');
    });
  }

  /// 手動で位置情報許可状態を再チェック（設定画面から戻った時など）
  Future<void> refreshLocationPermissionStatus() async {
    await _checkLocationPermissionStatus(caller: 'manualRefresh');
  }
  
  /// 設定キャッシュを無効化（設定変更時に呼び出し）
  void invalidateSettingsCache() {
    // Cache removed
  }
  
  /// 権限状態を取得
  Future<Map<String, bool>> _getCachedPermissions() async {
    try {
      final locationPermission = await geo.Geolocator.checkPermission();
      final isLocationGranted = locationPermission == geo.LocationPermission.always || 
                               locationPermission == geo.LocationPermission.whileInUse;
      final isGpsEnabled = await geo.Geolocator.isLocationServiceEnabled();
      final isNotificationGranted = await _checkNotificationPermission();
      
      return {
        'location': isLocationGranted,
        'gps': isGpsEnabled,
        'notification': isNotificationGranted,
      };
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error getting permissions: $e');
      return {
        'location': false,
        'gps': false,
        'notification': true,
      };
    }
  }
  
  /// 権限キャッシュを無効化（設定画面から戻った時など）
  void invalidatePermissionCache() {
    // Cache removed
  }

  /// GPS取得エラーをユーザーフレンドリーなメッセージに変換
  String _generateUserFriendlyLocationError(dynamic error) {
    final errorString = error.toString().toLowerCase();
    
    if (errorString.contains('timeout') || errorString.contains('time limit')) {
      return 'GPS信号の取得に時間がかかっています。\n• 屋外または窓の近くに移動してください\n• 機内モードがオフになっているか確認してください';
    } else if (errorString.contains('permission') || errorString.contains('denied')) {
      return '位置情報の許可が必要です。\n• 設定アプリ > プライバシー > 位置情報サービス\n• SafeBeeeをオンにしてください';
    } else if (errorString.contains('location service') || errorString.contains('disabled')) {
      return '位置情報サービスが無効です。\n• 設定アプリ > プライバシー > 位置情報サービス\n• 位置情報サービスをオンにしてください';
    } else if (errorString.contains('network') || errorString.contains('connection')) {
      return 'ネットワーク接続を確認してください。\n• Wi-Fiまたはモバイルデータが有効か確認\n• 機内モードがオフになっているか確認';
    } else if (errorString.contains('unavailable') || errorString.contains('not available')) {
      return 'お使いのデバイスで位置情報が利用できません。\n• デバイスの再起動をお試しください\n• 位置情報設定をリセットしてください';
    } else {
      return 'GPS取得に失敗しました。\n• しばらく待ってから再度お試しください\n• 問題が続く場合はアプリを再起動してください';
    }
  }

  /// 手動で位置情報を設定（手動入力機能：将来実装用）
  void setManualLocation(double latitude, double longitude) {
    final manualLocation = LocationModel(
      latitude: latitude,
      longitude: longitude,
      accuracy: 1000.0, // 手動入力のため精度は低く設定
      altitude: null,
    );
    
    _lastKnownLocation = manualLocation;
    state = state.copyWith(
      currentLocation: manualLocation,
      locationError: null,
    );
  }
  
  /// 緊急連絡先数を確認（デバッグ用）
  Future<int> debugGetEmergencyContactsCount() async {
    return await _getEmergencyContactsCount();
  }

  /// 緊急モードを手動で設定（緊急アラート受信時用）
  void setEmergencyMode(bool isEmergency) async {
    final newMode = isEmergency ? 'emergency' : 'normal';
    
    if (newMode != _currentMode) {
      _currentMode = newMode;
      
      // ローカルストレージに保存
      await _localStorage.saveEmergencyMode(_currentMode);
      
      // Riverpod状態を更新（変更がある場合のみ）
      if (state.currentMode != _currentMode) {
        state = state.copyWith(currentMode: _currentMode);
      }
      
      // 緊急モードに移行した場合は位置情報を即座取得
      if (isEmergency) {
        if (kDebugMode) {
          print('[DeviceStatus] 🚨 Entering emergency mode - acquiring location immediately');
        }
        try {
          final emergencyLocation = await getCurrentLocation();
          if (emergencyLocation != null && kDebugMode) {
            print('[DeviceStatus] 🚨 Emergency location acquired: ${emergencyLocation.latitude}, ${emergencyLocation.longitude}');
          }
        } catch (e) {
          if (kDebugMode) {
            print('[DeviceStatus] 🚨 Emergency location acquisition failed: $e');
          }
        }
      }
      
      // ハートビート間隔を即座に調整
      _adjustHeartbeatIntervalForMode();
      
      // 即座にハートビートを送信して緊急モードをバックエンドに通知
      await sendImmediateHeartbeat();
      
      // debugPrint('[DeviceStatus] Emergency mode set to: $_currentMode');
    }
  }

  /// Force refresh location (for testing)
  Future<LocationModel?> forceRefreshLocation() async {
        // if (kDebugMode) debugPrint('[DeviceStatus] === FORCE REFRESH LOCATION ===');
        // if (kDebugMode) debugPrint('[DeviceStatus] Clearing cached position and fetching fresh location...');
    
    // Clear the last known location to force fresh fetch
    _lastKnownLocation = null;
    
    // Force getCurrentPosition with appropriate settings
    try {
      final isEmulator = await _isRunningOnEmulator();
        // if (kDebugMode) debugPrint('[DeviceStatus] Getting fresh position (emulator: $isEmulator)...');
      
      final position = await geo.Geolocator.getCurrentPosition(
        desiredAccuracy: isEmulator ? geo.LocationAccuracy.lowest : geo.LocationAccuracy.medium,
        timeLimit: Duration(seconds: isEmulator ? 30 : 15),
        forceAndroidLocationManager: isEmulator,
      );
      
        // if (kDebugMode) debugPrint('[DeviceStatus] Fresh position obtained: lat=${position.latitude}, lng=${position.longitude}');
        // if (kDebugMode) debugPrint('[DeviceStatus] Position timestamp: ${position.timestamp}');
        // if (kDebugMode) debugPrint('[DeviceStatus] Is Mocked: ${position.isMocked}');
      
      final location = LocationModel(
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
        altitude: position.altitude,
      );
      
      // Update last known location
      _lastKnownLocation = location;
      
      // 位置情報のstate更新は不要（キャッシュのみで管理）
      // UIに表示しないため、無限ループの原因となるstate更新を削除
      
      return location;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Force refresh failed: $e');
      state = state.copyWith(
        locationError: '位置情報の更新に失敗しました',
        currentLocation: null,
      );
      return null;
    }
  }
  
  /// エミュレータで実行されているかを検出
  Future<bool> _isRunningOnEmulator() async {
    try {
      // Platform情報からエミュレータを検出
      if (kIsWeb) return false;
      
      // Androidエミュレータの検出
      if (Platform.isAndroid) {
        // Androidエミュレータの一般的な特徴
        final deviceInfo = DeviceInfoPlugin();
        final androidInfo = await deviceInfo.androidInfo;
        
        // エミュレータの一般的な特徴をチェック
        final isEmulator = !androidInfo.isPhysicalDevice || 
                          androidInfo.brand.contains('generic') ||
                          androidInfo.model.contains('sdk') ||
                          androidInfo.model.contains('emulator') ||
                          androidInfo.fingerprint.contains('generic') ||
                          androidInfo.hardware.contains('ranchu') ||
                          androidInfo.product.contains('sdk');
        
        if (isEmulator) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Detected Android emulator: ${androidInfo.model}');
        }
        return isEmulator;
      }
      
      // iOSシミュレータの検出
      if (Platform.isIOS) {
        final deviceInfo = DeviceInfoPlugin();
        final iosInfo = await deviceInfo.iosInfo;
        
        // iOSシミュレータの検出
        final isSimulator = !iosInfo.isPhysicalDevice;
        
        if (isSimulator) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Detected iOS simulator');
        }
        return isSimulator;
      }
      
      return false;
    } catch (e) {
        // if (kDebugMode) debugPrint('[DeviceStatus] Error detecting emulator: $e');
      // エラー時は安全のためエミュレータとして扱う
      return true;
    }
  }

}
