import 'package:freezed_annotation/freezed_annotation.dart';

part 'chat_message.freezed.dart';
part 'chat_message.g.dart';

enum MessageSender {
  user,
  ai,
  system,
}

@freezed
class ChatMessage with _$ChatMessage {
  const factory ChatMessage({
    required String id,
    required String content,
    required MessageSender sender,
    required DateTime timestamp,
    String? sessionId,
    Map<String, dynamic>? metadata,
    List<SuggestionCard>? cards,
    bool? isError,
  }) = _ChatMessage;

  factory ChatMessage.fromJson(Map<String, dynamic> json) => _$ChatMessageFromJson(json);
}

@freezed
class SuggestionCard with _$SuggestionCard {
  const factory SuggestionCard({
    required String id,
    required String type,
    required String title,
    String? description,
    Map<String, dynamic>? data,
    List<CardAction>? actions,
  }) = _SuggestionCard;

  factory SuggestionCard.fromJson(Map<String, dynamic> json) => _$SuggestionCardFromJson(json);
}

@freezed
class CardAction with _$CardAction {
  const factory CardAction({
    required String id,
    required String label,
    required String type,
    Map<String, dynamic>? data,
  }) = _CardAction;

  factory CardAction.fromJson(Map<String, dynamic> json) => _$CardActionFromJson(json);
}