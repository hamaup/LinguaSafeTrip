import 'package:freezed_annotation/freezed_annotation.dart';

part 'device_response_model.freezed.dart';
part 'device_response_model.g.dart';

/// デバイス能力
@freezed
class DeviceCapabilities with _$DeviceCapabilities {
  const factory DeviceCapabilities({
    @JsonKey(name: 'has_gps') @Default(true) bool hasGps,
    @JsonKey(name: 'gps_enabled') @Default(false) bool gpsEnabled,
    @JsonKey(name: 'has_sms') @Default(true) bool hasSms,
    @JsonKey(name: 'sms_enabled') @Default(false) bool smsEnabled,
    @JsonKey(name: 'has_push_notification') @Default(true) bool hasPushNotification,
    @JsonKey(name: 'push_notification_enabled') @Default(false) bool pushNotificationEnabled,
    @JsonKey(name: 'has_camera') @Default(true) bool hasCamera,
    @JsonKey(name: 'camera_enabled') @Default(false) bool cameraEnabled,
  }) = _DeviceCapabilities;

  factory DeviceCapabilities.fromJson(Map<String, dynamic> json) =>
      _$DeviceCapabilitiesFromJson(json);
}

/// デバイス位置情報
@freezed
class DeviceLocation with _$DeviceLocation {
  const factory DeviceLocation({
    double? latitude,
    double? longitude,
    double? accuracy,
    double? altitude,
    double? speed,
    double? heading,
    DateTime? timestamp,
  }) = _DeviceLocation;

  factory DeviceLocation.fromJson(Map<String, dynamic> json) =>
      _$DeviceLocationFromJson(json);
}

/// デバイスステータス
@freezed
class DeviceStatus with _$DeviceStatus {
  const factory DeviceStatus({
    @JsonKey(name: 'battery_level') int? batteryLevel,
    @JsonKey(name: 'is_charging') bool? isCharging,
    @JsonKey(name: 'is_power_saving_mode') bool? isPowerSavingMode,
    @JsonKey(name: 'network_type') String? networkType,
    @JsonKey(name: 'signal_strength') int? signalStrength,
    @JsonKey(name: 'is_airplane_mode') bool? isAirplaneMode,
    DeviceLocation? location,
    @JsonKey(name: 'emergency_detected') bool? emergencyDetected,
    @JsonKey(name: 'last_updated') required DateTime lastUpdated,
  }) = _DeviceStatus;

  factory DeviceStatus.fromJson(Map<String, dynamic> json) =>
      _$DeviceStatusFromJson(json);
}

/// デバイス登録リクエスト
@freezed
class DeviceCreateRequest with _$DeviceCreateRequest {
  const factory DeviceCreateRequest({
    @JsonKey(name: 'device_id') required String deviceId,
    required String platform,
    @JsonKey(name: 'fcm_token') String? fcmToken,
    @JsonKey(name: 'app_version') String? appVersion,
    @JsonKey(name: 'os_version') String? osVersion,
    String? model,
    @Default('ja') String language,
    @Default('Asia/Tokyo') String timezone,
    DeviceCapabilities? capabilities,
    DeviceStatus? status,
  }) = _DeviceCreateRequest;

  factory DeviceCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$DeviceCreateRequestFromJson(json);
}

/// デバイスレスポンス
@freezed
class DeviceResponse with _$DeviceResponse {
  const factory DeviceResponse({
    @JsonKey(name: 'device_id') required String deviceId,
    required String platform,
    @JsonKey(name: 'fcm_token') String? fcmToken,
    @JsonKey(name: 'app_version') String? appVersion,
    @JsonKey(name: 'os_version') String? osVersion,
    String? model,
    String? language,
    String? timezone,
    required DeviceCapabilities capabilities,
    required DeviceStatus status,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
    @JsonKey(name: 'is_active') @Default(true) bool isActive,
  }) = _DeviceResponse;

  factory DeviceResponse.fromJson(Map<String, dynamic> json) =>
      _$DeviceResponseFromJson(json);
}