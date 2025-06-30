import 'package:freezed_annotation/freezed_annotation.dart';

part 'alert_model.freezed.dart';
part 'alert_model.g.dart';

enum AlertSeverity {
  info,
  warning,
  danger,
  emergency,
  critical,
}

@freezed
class AlertModel with _$AlertModel {
  const factory AlertModel({
    required String id,
    required DateTime timestamp,
    // TimelineItemType type, // Removed as TimelineItemModel is now a union
    required String title,
    required String message,
    required AlertSeverity severity,
    required String source,
    required String area,
    String? detailsUrl,
  }) = _AlertModel;

  const AlertModel._(); // For custom getters/methods if needed in the future

  factory AlertModel.fromJson(Map<String, dynamic> json) =>
      _$AlertModelFromJson(json);
}
