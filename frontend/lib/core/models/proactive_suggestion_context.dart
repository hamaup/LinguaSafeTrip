import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:frontend/core/models/location_model.dart';

part 'proactive_suggestion_context.freezed.dart';
part 'proactive_suggestion_context.g.dart';

@freezed
class ProactiveSuggestionContext with _$ProactiveSuggestionContext {
  const factory ProactiveSuggestionContext({
    required String deviceId,
    required String language,
    LocationModel? currentLocation,
    List<String>? currentAreaCodes,
    String? currentSituation,
    int? limit,
    String? lastSuggestionTimestamp,
    Map<String, dynamic>? latestAlertSummary,
    List<Map<String, dynamic>>? suggestionHistorySummary,
  }) = _ProactiveSuggestionContext;

  factory ProactiveSuggestionContext.fromJson(Map<String, dynamic> json) =>
      _$ProactiveSuggestionContextFromJson(json);
}
