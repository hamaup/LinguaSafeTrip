import 'package:freezed_annotation/freezed_annotation.dart';

part 'heartbeat_response_model.freezed.dart';
part 'heartbeat_response_model.g.dart';

/// デバイスモード
enum DeviceMode {
  @JsonValue('normal')
  normal,
  @JsonValue('emergency')
  emergency,
}

/// 災害アラート
@freezed
class DisasterAlert with _$DisasterAlert {
  const factory DisasterAlert({
    @JsonKey(name: 'alert_id') required String alertId,
    required String type,
    required String severity,
    required String title,
    @JsonKey(name: 'issued_at') required DateTime issuedAt,
  }) = _DisasterAlert;

  factory DisasterAlert.fromJson(Map<String, dynamic> json) =>
      _$DisasterAlertFromJson(json);
}

/// 最寄りの避難所
@freezed
class NearestShelter with _$NearestShelter {
  const factory NearestShelter({
    @JsonKey(name: 'shelter_id') required String shelterId,
    required String name,
    @JsonKey(name: 'distance_km') required double distanceKm,
    required String status,
  }) = _NearestShelter;

  factory NearestShelter.fromJson(Map<String, dynamic> json) =>
      _$NearestShelterFromJson(json);
}

/// 災害ステータス
@freezed
class DisasterStatus with _$DisasterStatus {
  const factory DisasterStatus({
    required DeviceMode mode,
    @JsonKey(name: 'mode_reason') String? modeReason,
    @JsonKey(name: 'active_alerts') @Default([]) List<DisasterAlert> activeAlerts,
    @JsonKey(name: 'nearest_shelter') NearestShelter? nearestShelter,
  }) = _DisasterStatus;

  const DisasterStatus._();

  factory DisasterStatus.fromJson(Map<String, dynamic> json) =>
      _$DisasterStatusFromJson(json);

  /// 緊急モードかどうかを判定
  bool get isEmergencyMode => mode == DeviceMode.emergency;

  /// アクティブなアラートがあるかを判定
  bool get hasActiveAlerts => activeAlerts.isNotEmpty;
}

/// プロアクティブ提案（ハートビート用）
@freezed
class HeartbeatSuggestion with _$HeartbeatSuggestion {
  const factory HeartbeatSuggestion({
    required String type,
    required String content,
    required String priority,
    @JsonKey(name: 'action_query') String? actionQuery,
    @JsonKey(name: 'action_data') Map<String, dynamic>? actionData,
    @JsonKey(name: 'expires_at') DateTime? expiresAt,
  }) = _HeartbeatSuggestion;

  factory HeartbeatSuggestion.fromJson(Map<String, dynamic> json) =>
      _$HeartbeatSuggestionFromJson(json);
}

/// 同期設定
@freezed
class SyncConfig with _$SyncConfig {
  const factory SyncConfig({
    @JsonKey(name: 'min_sync_interval') @Default(30) int minSyncInterval,
    @JsonKey(name: 'force_refresh') @Default(false) bool forceRefresh,
  }) = _SyncConfig;

  factory SyncConfig.fromJson(Map<String, dynamic> json) =>
      _$SyncConfigFromJson(json);
}

/// ハートビートレスポンス
@freezed
class HeartbeatResponse with _$HeartbeatResponse {
  const factory HeartbeatResponse({
    @JsonKey(name: 'sync_id') required String syncId,
    @JsonKey(name: 'server_timestamp') required DateTime serverTimestamp,
    @JsonKey(name: 'disaster_status') required DisasterStatus disasterStatus,
    @JsonKey(name: 'proactive_suggestions') @Default([]) List<HeartbeatSuggestion> proactiveSuggestions,
    @JsonKey(name: 'sync_config') required SyncConfig syncConfig,
  }) = _HeartbeatResponse;

  const HeartbeatResponse._();

  factory HeartbeatResponse.fromJson(Map<String, dynamic> json) =>
      _$HeartbeatResponseFromJson(json);

  /// 緊急モードかどうかを判定（便利メソッド）
  bool get isEmergencyMode => disasterStatus.isEmergencyMode;

  /// 提案があるかを判定
  bool get hasSuggestions => proactiveSuggestions.isNotEmpty;
}