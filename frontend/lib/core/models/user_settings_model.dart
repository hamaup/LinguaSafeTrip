import 'package:uuid/uuid.dart';
import 'package:frontend/core/models/emergency_contact_model.dart';

class UserSettingsModel {
  final String nickname;
  final String languageCode;
  final List<EmergencyContactModel> emergencyContacts;
  final int heartbeatIntervalNormalMinutes;  // 平常時ハートビート間隔（分）
  final int heartbeatIntervalEmergencyMinutes;  // 災害時ハートビート間隔（分）
  final bool isStreamingEnabled;  // ストリーミング機能の有効/無効
  final bool isVoiceInputEnabled;  // 音声入力機能の有効/無効

  UserSettingsModel({
    required this.nickname,
    required this.languageCode,
    required this.emergencyContacts,
    this.heartbeatIntervalNormalMinutes = 6,  // デフォルト: 6分 (360秒)
    this.heartbeatIntervalEmergencyMinutes = 6,  // デフォルト: 6分 (360秒)
    this.isStreamingEnabled = true,   // デフォルト: 有効
    this.isVoiceInputEnabled = false,  // デフォルト: 無効 (一時的)
  });

  UserSettingsModel copyWith({
    String? nickname,
    String? languageCode,
    List<EmergencyContactModel>? emergencyContacts,
    int? heartbeatIntervalNormalMinutes,
    int? heartbeatIntervalEmergencyMinutes,
    bool? isStreamingEnabled,
    bool? isVoiceInputEnabled,
  }) {
    return UserSettingsModel(
      nickname: nickname ?? this.nickname,
      languageCode: languageCode ?? this.languageCode,
      emergencyContacts: emergencyContacts ?? this.emergencyContacts,
      heartbeatIntervalNormalMinutes: heartbeatIntervalNormalMinutes ?? this.heartbeatIntervalNormalMinutes,
      heartbeatIntervalEmergencyMinutes: heartbeatIntervalEmergencyMinutes ?? this.heartbeatIntervalEmergencyMinutes,
      isStreamingEnabled: isStreamingEnabled ?? this.isStreamingEnabled,
      isVoiceInputEnabled: isVoiceInputEnabled ?? this.isVoiceInputEnabled,
    );
  }

  Map<String, dynamic> toJson() => {
    'nickname': nickname,
    'language_code': languageCode,
    'emergency_contacts': emergencyContacts.map((e) => e.toJson()).toList(),
    'heartbeat_interval_normal_minutes': heartbeatIntervalNormalMinutes,
    'heartbeat_interval_emergency_minutes': heartbeatIntervalEmergencyMinutes,
    'is_streaming_enabled': isStreamingEnabled,
    'is_voice_input_enabled': isVoiceInputEnabled,
  };

  factory UserSettingsModel.fromJson(Map<String, dynamic> json) {
    // 後方互換性のため両方のキー名をチェック
    final languageCode = json['language_code'] ?? json['languageCode'];

    // 緊急連絡先のデータ変換処理
    List<EmergencyContactModel> contacts = [];
    final contactsData = json['emergency_contacts'] ?? json['emergencyContacts'];

    if (contactsData is List) {
      contacts = contactsData.map((item) {
        if (item is String) {
          // 旧形式(String)から新形式(EmergencyContactModel)に変換
          return EmergencyContactModel(
            id: const Uuid().v4(),
            name: '連絡先',
            phoneNumber: item,
          );
        } else if (item is Map) {
          // 新形式の場合
          return EmergencyContactModel.fromJson(item.cast<String, dynamic>());
        }
        return EmergencyContactModel(
          id: const Uuid().v4(),
          name: '連絡先',
          phoneNumber: '',
        );
      }).toList();
    }

    return UserSettingsModel(
      nickname: json['nickname'] as String,
      languageCode: languageCode as String,
      emergencyContacts: contacts,
      heartbeatIntervalNormalMinutes: json['heartbeat_interval_normal_minutes'] as int? ?? 6,
      heartbeatIntervalEmergencyMinutes: json['heartbeat_interval_emergency_minutes'] as int? ?? 6,
      isStreamingEnabled: json['is_streaming_enabled'] as bool? ?? true,
      isVoiceInputEnabled: json['is_voice_input_enabled'] as bool? ?? false,
    );
  }
}
