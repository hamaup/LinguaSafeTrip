import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:tuple/tuple.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/models/chat_message.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/core/models/location_model.dart';
import 'package:frontend/core/services/api_service.dart';
import 'package:frontend/core/providers/service_providers.dart';
import 'package:frontend/core/providers/shelter_provider.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';

part 'chat_provider.freezed.dart';
part 'chat_provider.g.dart';

@freezed
class ChatState with _$ChatState {
  const factory ChatState({
    @Default('') String currentInput,
    @Default(false) bool isLoading,
    @Default('') String loadingStatus,
    @Default(<ChatMessage>[]) List<ChatMessage> messages,
    CancelToken? cancelToken,
    String? errorMessage,
  }) = _ChatState;
}

@Riverpod(keepAlive: true)
class Chat extends _$Chat {
  ApiService get _apiService => ref.read(apiServiceProvider);

  @override
  ChatState build() {
    return const ChatState();
  }

  /// チャット入力を更新
  void updateInput(String input) {
    state = state.copyWith(currentInput: input);
  }

  /// チャットメッセージを送信
  Future<TimelineItemModel?> sendMessage(String messageText) async {
    if (messageText.trim().isEmpty) return null;

    try {
      // デバイス情報を取得
      final deviceStatusState = ref.read(deviceStatusProvider);
      final settingsState = ref.read(settingsProvider);
      final userSettings = settingsState.currentUserSettings;
      
      if (userSettings == null) {
        throw Exception('ユーザー設定が読み込まれていません');
      }

      // メッセージIDを生成
      final userMessageId = 'user_${DateTime.now().millisecondsSinceEpoch}';
      
      // ローディング開始
      state = state.copyWith(
        isLoading: true,
        loadingStatus: 'メッセージを送信中...',
        currentInput: '',
        cancelToken: CancelToken(),
      );

      // ユーザーメッセージを即座にタイムラインに追加
      final userTimelineItem = TimelineItemModel.chat(
        id: userMessageId,
        timestamp: DateTime.now(),
        messageText: messageText,
        senderNickname: userSettings.nickname,
        isOwnMessage: true,
      );
      ref.read(timelineProvider.notifier).addTimelineItem(userTimelineItem);

      final language = userSettings.languageCode;

      // Chat開始をDeviceStatusProviderに通知
      ref.read(deviceStatusProvider.notifier).startChatSession();

      state = state.copyWith(loadingStatus: 'コンテキストを取得中...');

      // セッションIDを生成
      final sessionId = DateTime.now().millisecondsSinceEpoch.toString();

      // デバイスIDを取得
      final deviceId = await ref.read(deviceStatusProvider.notifier).getDeviceId();
      
      // Use cached location instead of fetching new location
      final currentLocation = ref.read(deviceStatusProvider).currentLocation;
      
      
      // チャット履歴の構築（位置情報取得と並列で実行済み）
      final chatHistory = _buildChatHistory();

      // チャットAPIを呼び出し
      final response = await _apiService.sendChatMessage(
        message: messageText,
        deviceId: deviceId,
        sessionId: sessionId,
        language: language,
        chatHistory: chatHistory,
        currentLocation: currentLocation,
        isDisasterMode: deviceStatusState.currentMode == 'emergency',
        cancelToken: state.cancelToken,
      );

      if (kDebugMode) {
        print('[ChatProvider] API Response received: ${response.responseText}');
        print('[ChatProvider] Generated cards: ${response.generatedCardsForFrontend?.length ?? 0}');
      }

      // 応答処理
      final assistantMessageId = 'assistant_${DateTime.now().millisecondsSinceEpoch}';
      
      final userMessage = ChatMessage(
        id: userMessageId,
        content: messageText,
        sender: MessageSender.user,
        timestamp: DateTime.now(),
        sessionId: sessionId,
        metadata: {'senderNickname': userSettings.nickname},
      );

      // 避難所データを抽出
      List<dynamic>? shelterData;
      if (response.generatedCardsForFrontend?.isNotEmpty == true) {
        // 避難所カードをフィルタリング
        final shelterCards = response.generatedCardsForFrontend!.where((card) {
          final cardType = card['card_type'] ?? card['type'] ?? '';
          return cardType == 'evacuation_shelter' || 
                 cardType == 'shelter' || 
                 cardType == 'shelter_info' ||
                 cardType == 'evacuation_info';
        }).toList();
        
        if (shelterCards.isNotEmpty) {
          shelterData = shelterCards;
          if (kDebugMode) {
            print('[ChatProvider] Found ${shelterCards.length} shelter cards for map display');
          }
        }
      }
      
      final assistantMessage = ChatMessage(
        id: assistantMessageId,
        content: response.responseText,
        sender: MessageSender.ai,
        timestamp: DateTime.now(),
        sessionId: sessionId,
        metadata: {
          'senderNickname': 'SafeBeee',
          if (shelterData != null) 'shelters': shelterData,
        },
      );

      // メッセージを追加
      state = state.copyWith(
        messages: [...state.messages, userMessage, assistantMessage],
        isLoading: false,
        loadingStatus: '',
        cancelToken: null,
      );

      // Chat終了をDeviceStatusProviderに通知
      ref.read(deviceStatusProvider.notifier).endChatSession();

      // 生成されたカードがある場合の処理
      if (response.generatedCardsForFrontend?.isNotEmpty == true) {
        await _processGeneratedCards(response.generatedCardsForFrontend!, assistantMessageId);
      }

      // AI応答をタイムラインに追加
      TimelineItemModel assistantTimelineItem;
      
      // requiresActionがある場合は特別なアイテムを作成
      if (response.requiresAction != null && response.actionData != null) {
        if (kDebugMode) {
          print('[ChatProvider] Creating chat with action item: ${response.requiresAction}');
          print('[ChatProvider] Action data present: ${response.actionData != null}');
        }
        assistantTimelineItem = TimelineItemModel.chatWithAction(
          id: assistantMessageId,
          timestamp: DateTime.now(),
          messageText: response.responseText,
          senderNickname: 'SafeBeee',
          isOwnMessage: false,
          requiresAction: response.requiresAction!,
          actionData: response.actionData!,
        );
      } else {
        assistantTimelineItem = TimelineItemModel.chat(
          id: assistantMessageId,
          timestamp: DateTime.now(),
          messageText: response.responseText,
          senderNickname: 'SafeBeee',
          isOwnMessage: false,
        );
      }
      
      if (kDebugMode) {
        print('[ChatProvider] Adding assistant timeline item: ${assistantTimelineItem.id}');
      }
      
      ref.read(timelineProvider.notifier).addTimelineItem(assistantTimelineItem);
      
      // 避難所データがある場合は、TimelineProviderに設定
      if (shelterData != null && shelterData.isNotEmpty) {
        ref.read(timelineProvider.notifier).setShelterDataForChat(assistantMessageId, shelterData);
      }
      
      if (kDebugMode) {
        print('[ChatProvider] Assistant timeline item added successfully');
      }

      // nullを返す（chat_input_fieldでの重複追加を防ぐ）
      return null;

    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        loadingStatus: '',
        errorMessage: e.toString(),
        cancelToken: null,
      );

      // Chat終了をDeviceStatusProviderに通知
      ref.read(deviceStatusProvider.notifier).endChatSession();

      if (kDebugMode) {
        // Error sending message
      }
      rethrow;
    }
  }

  /// アクションクエリを送信
  Future<TimelineItemModel?> sendActionQuery(String actionQuery, String displayText) async {
    try {
      state = state.copyWith(
        isLoading: true,
        loadingStatus: 'アクション実行中...',
        cancelToken: CancelToken(),
      );

      final deviceStatusState = ref.read(deviceStatusProvider);
      final settingsState = ref.read(settingsProvider);
      final userSettings = settingsState.currentUserSettings;
      
      if (userSettings == null) {
        throw Exception('ユーザー設定が読み込まれていません');
      }

      final language = userSettings.languageCode;

      // Chat開始をDeviceStatusProviderに通知
      ref.read(deviceStatusProvider.notifier).startChatSession();

      // デバイスIDを取得
      final deviceId = await ref.read(deviceStatusProvider.notifier).getDeviceId();
      
      // セッションIDを生成
      final sessionId = DateTime.now().millisecondsSinceEpoch.toString();

      // チャット履歴の構築
      final chatHistory = _buildChatHistory();

      // Use cached location instead of fetching new location
      final currentLocation = ref.read(deviceStatusProvider).currentLocation;

      // APIを呼び出し
      final response = await _apiService.sendChatMessage(
        message: actionQuery,
        deviceId: deviceId,
        sessionId: sessionId,
        language: language,
        chatHistory: chatHistory,
        currentLocation: currentLocation,
        isDisasterMode: deviceStatusState.currentMode == 'emergency',
        cancelToken: state.cancelToken,
      );

      // メッセージを追加
      final userMessageId = 'user_${DateTime.now().millisecondsSinceEpoch}';
      final assistantMessageId = 'assistant_${DateTime.now().millisecondsSinceEpoch}';
      
      final userMessage = ChatMessage(
        id: userMessageId,
        content: displayText,
        sender: MessageSender.user,
        timestamp: DateTime.now(),
        sessionId: sessionId,
        metadata: {'senderNickname': userSettings.nickname},
      );

      // 避難所データを処理してメッセージに含める
      List<dynamic>? shelterData;
      if (response.generatedCardsForFrontend?.isNotEmpty == true) {
        // 避難所カードをフィルタリング
        final shelterCards = response.generatedCardsForFrontend!.where((card) {
          final cardType = card['card_type'] ?? card['type'] ?? '';
          return cardType == 'evacuation_shelter' || 
                 cardType == 'shelter' || 
                 cardType == 'shelter_info' ||
                 (card['location'] != null && card['location']['latitude'] != null);
        }).toList();
        
        if (shelterCards.isNotEmpty) {
          shelterData = shelterCards;
          if (kDebugMode) {
            // Found shelter cards for map display
          }
        }
      }

      final assistantMessage = ChatMessage(
        id: assistantMessageId,
        content: response.responseText,
        sender: MessageSender.ai,
        timestamp: DateTime.now(),
        sessionId: sessionId,
        metadata: {
          'senderNickname': 'SafeBeee',
          if (shelterData != null) 'shelters': shelterData,
        },
      );

      state = state.copyWith(
        messages: [...state.messages, userMessage, assistantMessage],
        isLoading: false,
        loadingStatus: '',
        cancelToken: null,
      );

      // Chat終了をDeviceStatusProviderに通知
      ref.read(deviceStatusProvider.notifier).endChatSession();

      // 生成されたカードがある場合の処理（追加処理用）
      if (response.generatedCardsForFrontend?.isNotEmpty == true) {
        await _processGeneratedCards(response.generatedCardsForFrontend!, assistantMessageId);
      }

      // タイムラインアイテムを作成して返す
      return TimelineItemModel.chat(
        id: userMessageId,
        timestamp: DateTime.now(),
        messageText: displayText,
        senderNickname: userSettings.nickname,
        isOwnMessage: true,
      );

    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        loadingStatus: '',
        errorMessage: e.toString(),
        cancelToken: null,
      );

      // Chat終了をDeviceStatusProviderに通知
      ref.read(deviceStatusProvider.notifier).endChatSession();

      if (kDebugMode) {
        // Error sending action query
      }
      rethrow;
    }
  }

  /// 提案からクエリを送信
  Future<TimelineItemModel?> sendSuggestionQuery(TimelineItemModel suggestion) async {
    return suggestion.when(
      alert: (_, __, ___, ____, _____) => null,
      suggestion: (_, __, ___, ____, _____, actionQuery, actionDisplayText) {
        if (actionQuery?.isNotEmpty == true && actionDisplayText?.isNotEmpty == true) {
          return sendActionQuery(actionQuery!, actionDisplayText!);
        }
        return null;
      },
      chat: (_, __, ___, ____, _____) => null,
      chatWithAction: (_, __, ___, ____, _____, ______, _______) => null,
    );
  }

  /// チャットをキャンセル
  void cancelChat() {
    state.cancelToken?.cancel('User cancelled');
    state = state.copyWith(
      isLoading: false,
      loadingStatus: '',
      cancelToken: null,
    );

    // Chat終了をDeviceStatusProviderに通知
    ref.read(deviceStatusProvider.notifier).endChatSession();
  }

  /// メッセージを追加
  void addMessage(ChatMessage message) {
    state = state.copyWith(
      messages: [...state.messages, message],
    );
  }

  /// チャット履歴を構築
  List<Tuple2<String, String>> _buildChatHistory() {
    return state.messages
        .take(10) // 最新10件のメッセージを取得
        .map((message) => Tuple2(
              message.sender == MessageSender.user ? 'human' : 'assistant',
              message.content,
            ))
        .toList()
        .reversed
        .toList();
  }

  /// 生成されたカードを処理
  Future<void> _processGeneratedCards(List<dynamic> generatedCards, String messageId) async {
    try {
      // Shelter Providerを使用して避難所データを処理
      final shelterNotifier = ref.read(shelterProvider.notifier);
      final processedShelters = await shelterNotifier.preprocessShelterData(generatedCards);

      // 避難所データが処理された場合、チャットIDとのマッピングを設定
      if (processedShelters.isNotEmpty) {
        final shelterDataId = 'shelter_${DateTime.now().millisecondsSinceEpoch}';
        shelterNotifier.setChatToShelterMapping(messageId, shelterDataId);
      }
      
      // 避難所カードは個別の提案カードとしては追加しない
      // 代わりに、チャットメッセージのメタデータに含まれる避難所データを使用して
      // ChatTimelineItem内で地図が表示される
    } catch (e) {
      if (kDebugMode) {
        print('[ChatProvider] Error processing generated cards: $e');
      }
    }
  }

  /// エラーをクリア
  void clearError() {
    state = state.copyWith(errorMessage: null);
  }

  /// チャット履歴をクリア
  void clearHistory() {
    state = state.copyWith(
      messages: [],
    );
  }
}