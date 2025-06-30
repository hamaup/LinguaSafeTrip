import 'package:freezed_annotation/freezed_annotation.dart';

part 'timeline_item_model.freezed.dart';
part 'timeline_item_model.g.dart';

enum TimelineItemType {
  alert,
  chat,
  suggestion,
}

@freezed
class TimelineItemModel with _$TimelineItemModel {
  const factory TimelineItemModel.alert({
    required String id,
    required DateTime timestamp,
    required String severity,
    required String title,
    required String message,
  }) = AlertTimelineItem;

  const factory TimelineItemModel.chat({
    required String id,
    required DateTime timestamp,
    required String messageText,
    required String senderNickname,
    required bool isOwnMessage,
  }) = ChatTimelineItem;
  
  const factory TimelineItemModel.chatWithAction({
    required String id,
    required DateTime timestamp,
    required String messageText,
    required String senderNickname,
    required bool isOwnMessage,
    required String requiresAction,
    required Map<String, dynamic> actionData,
  }) = ChatWithActionTimelineItem;

  const factory TimelineItemModel.suggestion({
    required String id,
    required String suggestionType,
    required DateTime timestamp,
    required String content,
    required Map<String, dynamic>? actionData,
    String? actionQuery,
    String? actionDisplayText,
  }) = SuggestionTimelineItem;

  factory TimelineItemModel.fromJson(Map<String, dynamic> json) =>
      _$TimelineItemModelFromJson(json);
}

// Extension to provide compatibility
extension TimelineItemModelExtension on TimelineItemModel {
  TimelineItemType get type => when(
    alert: (_,__,___,____,_____) => TimelineItemType.alert,
    chat: (_,__,___,____,_____) => TimelineItemType.chat,
    chatWithAction: (_,__,___,____,_____,______,_______) => TimelineItemType.chat,
    suggestion: (_,__,___,____,_____,______,_______) => TimelineItemType.suggestion,
  );
}