import 'package:freezed_annotation/freezed_annotation.dart';

part 'proactive_suggestion_response_model.freezed.dart';
part 'proactive_suggestion_response_model.g.dart';

/// プロアクティブ提案アイテム（完全版）
@freezed
class SuggestionItem with _$SuggestionItem {
  const factory SuggestionItem({
    required String type,
    required String content,
    @JsonKey(name: 'action_data') Map<String, dynamic>? actionData,
    @JsonKey(name: 'suggestion_id') required String suggestionId,
    @JsonKey(name: 'action_query') String? actionQuery,
    @JsonKey(name: 'action_display_text') String? actionDisplayText,
    @JsonKey(name: 'created_at') DateTime? createdAt,
  }) = _SuggestionItem;

  factory SuggestionItem.fromJson(Map<String, dynamic> json) =>
      _$SuggestionItemFromJson(json);
}

/// プロアクティブ提案APIレスポンス
@freezed
class ProactiveSuggestionResponse with _$ProactiveSuggestionResponse {
  const factory ProactiveSuggestionResponse({
    required List<SuggestionItem> suggestions,
    @JsonKey(name: 'has_more_items') @Default(false) bool hasMoreItems,
    @JsonKey(name: 'is_disaster_related') bool? isDisasterRelated,
    @JsonKey(name: 'disaster_severity') String? disasterSeverity,
    @JsonKey(name: 'disaster_event_ids') List<String>? disasterEventIds,
    @JsonKey(name: 'next_check_after') DateTime? nextCheckAfter,
  }) = _ProactiveSuggestionResponse;

  const ProactiveSuggestionResponse._();

  factory ProactiveSuggestionResponse.fromJson(Map<String, dynamic> json) =>
      _$ProactiveSuggestionResponseFromJson(json);

  /// 災害関連の提案かどうかを判定
  bool get isDisasterRelatedSuggestions => isDisasterRelated ?? false;

  /// 高優先度の災害かどうかを判定
  bool get isHighPriorityDisaster => 
      disasterSeverity != null && 
      ['critical', 'high'].contains(disasterSeverity?.toLowerCase());
}