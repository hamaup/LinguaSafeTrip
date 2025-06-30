import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:tuple/tuple.dart';

part 'chat_response_model.freezed.dart';
part 'chat_response_model.g.dart';

/// 災害アクションカードモデル
@freezed
class DisasterActionCard with _$DisasterActionCard {
  const factory DisasterActionCard({
    @JsonKey(name: 'card_id') required String cardId,
    required String title,
    @JsonKey(name: 'content_markdown') required String contentMarkdown,
    required List<Map<String, dynamic>> actions,
    required int priority,
    required String type,
    @JsonKey(name: 'icon_url') String? iconUrl,
    @JsonKey(name: 'additional_data') Map<String, dynamic>? additionalData,
  }) = _DisasterActionCard;

  factory DisasterActionCard.fromJson(Map<String, dynamic> json) =>
      _$DisasterActionCardFromJson(json);
}

/// チャットAPIレスポンスモデル
@freezed
class ChatResponse with _$ChatResponse {
  const factory ChatResponse({
    @JsonKey(name: 'sessionId') required String sessionId,
    @JsonKey(name: 'responseText') required String responseText,
    @JsonKey(name: 'updatedChatHistory') required List<List<String>> updatedChatHistory,
    @JsonKey(name: 'currentTaskType') required String currentTaskType,
    @JsonKey(name: 'requiresAction') String? requiresAction,
    @JsonKey(name: 'actionData') Map<String, dynamic>? actionData,
    @JsonKey(name: 'debugInfo') Map<String, dynamic>? debugInfo,
    @JsonKey(name: 'generatedCardsForFrontend') List<Map<String, dynamic>>? generatedCardsForFrontend,
    @JsonKey(name: 'isEmergencyResponse') bool? isEmergencyResponse,
    @JsonKey(name: 'emergencyLevel') int? emergencyLevel,
    @JsonKey(name: 'emergencyActions') List<String>? emergencyActions,
    @JsonKey(name: 'actionCards') List<DisasterActionCard>? actionCards,
  }) = _ChatResponse;

  const ChatResponse._();

  factory ChatResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatResponseFromJson(json);

  /// チャット履歴をTupleリストに変換
  List<Tuple2<String, String>> get chatHistoryAsTuples {
    return updatedChatHistory.map((item) {
      if (item.length >= 2) {
        return Tuple2(item[0], item[1]);
      }
      return const Tuple2('', '');
    }).toList();
  }

  /// 緊急モードかどうかを判定
  bool get isEmergencyMode => isEmergencyResponse ?? false;

  /// アクションが必要かどうかを判定
  bool get hasRequiredAction => requiresAction != null && requiresAction!.isNotEmpty;

  /// アクションカードがあるかどうかを判定
  bool get hasActionCards => actionCards != null && actionCards!.isNotEmpty;
}