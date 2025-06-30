import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:geolocator/geolocator.dart' as geo;
import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/core/providers/service_providers.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';
import 'package:frontend/features/main_timeline/widgets/suggestion_timeline_item.dart' as widgets;
import 'package:frontend/features/chat/widgets/chat_timeline_item.dart' as chat_widgets;
import 'package:frontend/l10n/app_localizations.dart';
import 'package:tuple/tuple.dart';

/// ストリーミング提案リストウィジェット
/// Server-Sent Events (SSE) を使用して段階的に提案を表示
class StreamingSuggestionsList extends ConsumerStatefulWidget {
  const StreamingSuggestionsList({super.key});

  @override
  ConsumerState<StreamingSuggestionsList> createState() => _StreamingSuggestionsListState();
}

class _StreamingSuggestionsListState extends ConsumerState<StreamingSuggestionsList> {
  final List<TimelineItemModel> _streamedSuggestions = [];
  final List<TimelineItemModel> _chatItems = []; // 質問・回答用
  StreamSubscription? _streamSubscription;
  bool _isStreaming = false;
  bool _hasError = false;
  String? _errorMessage;
  String? _lastMode; // 前回のモードを追跡
  bool _isChatLoading = false; // チャット送信中
  bool _isPausedForChat = false; // チャット中はストリーミング一時停止
  bool? _lastChatActiveState; // 前回のチャット状態を追跡
  bool _isSSEStarting = false; // SSE開始中フラグ（重複防止）
  DateTime? _lastStreamAttempt; // 前回のストリーム試行時刻
  int _reconnectAttempts = 0; // 再接続試行回数
  static const int _maxReconnectAttempts = 3; // 最大再接続試行回数
  static const Duration _reconnectDelay = Duration(seconds: 2); // 再接続遅延
  
  // 緊急連絡先ダイアログ用コントローラー
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  

  @override
  void initState() {
    super.initState();
    // ハートビート同期に統合 - 自動ストリーミングは無効化
    // startStreamingFromHeartbeat()はハートビート処理で明示的に呼び出される
  }

  @override
  void dispose() {
    _streamSubscription?.cancel();
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  /// ConnectivityResultを文字列に変換
  String _connectivityResultToString(ConnectivityResult result) {
    switch (result) {
      case ConnectivityResult.wifi:
        return 'wifi';
      case ConnectivityResult.mobile:
        return 'mobile';
      case ConnectivityResult.ethernet:
        return 'ethernet';
      case ConnectivityResult.none:
        return 'none';
      default:
        return 'unknown';
    }
  }

  /// ハートビート統合SSE接続を開始
  Future<void> startStreamingFromHeartbeat() async {
      // debugPrint('[StreamingSuggestionsList] 🎯 startStreamingFromHeartbeat called');
    if (_isStreaming || _isSSEStarting) {
      // debugPrint('[StreamingSuggestionsList] ⚠️ Already streaming or starting, skipping');
      return;
    }
    
    // SSE開始フラグを立てる（重複防止）
    _isSSEStarting = true;
    
    // レート制限：前回の試行から1秒以内は無視
    final now = DateTime.now();
    if (_lastStreamAttempt != null && 
        now.difference(_lastStreamAttempt!) < const Duration(seconds: 1)) {
      _isSSEStarting = false;
      return;
    }
    _lastStreamAttempt = now;
    
    // 古いサブスクリプションをクリーンアップ
    if (_streamSubscription != null) {
      await _streamSubscription!.cancel();
      _streamSubscription = null;
      // 最小限の待機でパフォーマンス向上
      await Future.delayed(const Duration(milliseconds: 50));
    }

    try {
      // debugPrint('[StreamingSuggestionsList] 🚀 Starting SSE connection...');
      
      if (!ref.exists(deviceStatusProvider) || !ref.exists(settingsProvider)) {
      // debugPrint('[StreamingSuggestionsList] ❌ Required providers not initialized, aborting SSE');
        _isSSEStarting = false;
        return;
      }
      
      final deviceStatus = ref.read(deviceStatusProvider);
      final settings = ref.read(settingsProvider);
      
      // 設定プロバイダーが初期化されていない場合はLocalStorageから直接読み込み
      if (settings.currentUserSettings == null) {
      // debugPrint('[StreamingSuggestionsList] ⚠️ Settings provider not initialized, loading from localStorage');
        try {
          final localStorage = ref.read(localStorageServiceProvider);
          final directSettings = await localStorage.loadUserSettings();
          if (directSettings == null) {
      // debugPrint('[StreamingSuggestionsList] ❌ No user settings found in localStorage, aborting SSE');
            _isSSEStarting = false;
            return;
          }
        } catch (e) {
      // debugPrint('[StreamingSuggestionsList] ❌ Failed to load settings from localStorage: $e');
          _isSSEStarting = false;
          return;
        }
      }

      if (!ref.exists(deviceStatusProvider)) {
      // debugPrint('[StreamingSuggestionsList] ❌ Device status provider not available');
        _isSSEStarting = false;
        return;
      }
      final deviceId = await ref.read(deviceStatusProvider.notifier).getDeviceId();
      
      // 言語コードを取得（ハートビートと同じロジックを使用）
      String language = 'ja'; // デフォルト
      try {
        // まずLocalStorageから直接取得（最も確実）
        final localStorage = ref.read(localStorageServiceProvider);
        final directSettings = await localStorage.loadUserSettings();
        if (directSettings != null && directSettings.languageCode.isNotEmpty) {
          language = directSettings.languageCode;
      // debugPrint('[StreamingSuggestionsList] Language from localStorage: $language');
        } else if (settings.currentUserSettings != null && settings.currentUserSettings!.languageCode.isNotEmpty) {
          // LocalStorageが空の場合のみSettingsProviderを確認
          language = settings.currentUserSettings!.languageCode;
      // debugPrint('[StreamingSuggestionsList] Language from settings provider: $language');
        }
      } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Language retrieval failed, using default: $e');
      }
      
      final currentMode = deviceStatus.currentMode;

      // 位置情報許可状態を即座に確認（SSE接続開始直前）
      final locationPermission = await geo.Geolocator.checkPermission();
      final isLocationGrantedNow = locationPermission == geo.LocationPermission.always || 
                                   locationPermission == geo.LocationPermission.whileInUse;
      final isGpsEnabledNow = await geo.Geolocator.isLocationServiceEnabled();

      // debugPrint('[StreamingSuggestionsList] 📱 Device info: mode=$currentMode, lang=$language, contacts=${settings.currentEmergencyContacts.length}');
      
      if (!ref.exists(apiServiceProvider)) {
      // debugPrint('[StreamingSuggestionsList] ❌ API service not initialized');
        _isSSEStarting = false;
        return;
      }
      final apiService = ref.read(apiServiceProvider);
      final suggestionStream = apiService.streamSuggestions(
        deviceId: deviceId,
        languageCode: language,
        currentMode: currentMode,
        currentLocation: ref.read(deviceStatusProvider).currentLocation,
        batteryLevel: deviceStatus.batteryLevel,
        isBatteryCharging: deviceStatus.isBatteryCharging,
        connectivityStatus: _connectivityResultToString(deviceStatus.connectivityStatus),
        isLocationPermissionGranted: isLocationGrantedNow,
        isGpsEnabled: isGpsEnabledNow,
        isNotificationPermissionGranted: true, // TODO: 実際の通知許可状態を取得
        emergencyContactsCount: settings.currentEmergencyContacts.length,
      );
      
      // debugPrint('[StreamingSuggestionsList] 📡 SSE stream created');

      setState(() {
        _isStreaming = true;
        _hasError = false;
        _errorMessage = null;
        _isSSEStarting = false; // SSE開始完了
      });
      
      // 接続成功時は再接続カウンターをリセット
      _reconnectAttempts = 0;

      _streamSubscription = suggestionStream.listen(
        (data) {
          _handleStreamData(data);
        },
        onError: (error) {
      // debugPrint('[StreamingSuggestionsList] Stream error: $error');
          setState(() {
            _hasError = true;
            _errorMessage = error.toString();
            _isStreaming = false;
            _isSSEStarting = false;
          });
          
          // 自動再接続ロジック（最大3回まで）
          if (_reconnectAttempts < _maxReconnectAttempts) {
            _reconnectAttempts++;
      // debugPrint('[StreamingSuggestionsList] Attempting reconnect ${_reconnectAttempts}/$_maxReconnectAttempts');
            Future.delayed(_reconnectDelay, () {
              if (mounted && !_isStreaming && !_isPausedForChat) {
                startStreamingFromHeartbeat();
              }
            });
          }
        },
        onDone: () {
      // debugPrint('[StreamingSuggestionsList] Stream completed');
          setState(() {
            _isStreaming = false;
          });
          // 成功時は再接続カウンターをリセット
          _reconnectAttempts = 0;
          // TimelineProviderのSSEトリガー状態をリセット
          if (ref.exists(timelineProvider)) {
            ref.read(timelineProvider.notifier).stopStreaming();
          }
        },
      );

    } catch (e) {
      setState(() {
        _hasError = true;
        _errorMessage = e.toString();
        _isStreaming = false;
        _isSSEStarting = false;
      });
    }
  }

  /// ストリーミングを停止
  void stopStreaming() {
    if (_streamSubscription != null) {
      _streamSubscription!.cancel();
      _streamSubscription = null;
    }
    if (mounted) {
      setState(() {
        _isStreaming = false;
      });
    }
  }

  /// ストリームデータを処理（最適化版）
  void _handleStreamData(Map<String, dynamic> data) {
    try {
      // 早期終了条件を最適化
      if (_isPausedForChat || _isChatLoading || !_isStreaming) {
        return;
      }

      // 高速な型チェック
      final dataType = data['type'] as String?;
      if (dataType == null) return;

      // 軽量メッセージの早期処理（ほとんどのケース）
      switch (dataType) {
        case 'no_suggestions':
        case 'complete':
        case 'heartbeat':
          return;
        case 'stream_complete':
          stopStreaming();
          return;
        case 'heartbeat_response':
          // Timeline Provider で処理済み
          return;
      }

      // 重要なメッセージのみ詳細処理
      if (dataType == 'suggestions_push') {
        _processSuggestionsPush(data);
      } else {
        _processSingleSuggestion(data);
      }
    } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Error parsing stream data: $e');
    }
  }

  /// 複数提案を処理（バッチ処理で最適化）
  void _processSuggestionsPush(Map<String, dynamic> data) {
    final suggestionData = data['data'] as List<dynamic>? ?? [];
    if (suggestionData.isEmpty) return;

    final parsedSuggestions = <TimelineItemModel>[];
    
    // バッチでパース処理
    for (final suggestion in suggestionData) {
      if (suggestion is Map<String, dynamic>) {
        final parsed = _parseStreamedSuggestion({'data': suggestion});
        if (parsed != null) {
          parsedSuggestions.add(parsed);
        }
      }
    }

    // 重複チェックを一括実行
    final uniqueSuggestions = parsedSuggestions
        .where((suggestion) => !_isDuplicateWithMainTimeline(suggestion))
        .toList();

    // TimelineProviderに一括追加
    if (ref.exists(timelineProvider)) {
      for (final suggestion in uniqueSuggestions) {
        ref.read(timelineProvider.notifier).addStreamingSuggestion(suggestion);
      }
    }
  }

  /// 単一提案を処理
  void _processSingleSuggestion(Map<String, dynamic> data) {
    final suggestion = _parseStreamedSuggestion(data);
    if (suggestion != null && !_isDuplicateWithMainTimeline(suggestion)) {
      if (ref.exists(timelineProvider)) {
        ref.read(timelineProvider.notifier).addStreamingSuggestion(suggestion);
      }
    }
  }

  /// SSE開始判定（ハートビート同期済み - 自動開始無効）
  bool _shouldStartSSEStreaming() {
    // ハートビート同期に統合されたため、自動開始は無効
    return false;
  }

  /// 最後のハートビート提案時刻を取得
  DateTime? _getLastHeartbeatSuggestionTime(timelineState) {
    try {
      // メインタイムライン（ハートビートAPI経由）の最新提案時刻を取得
      final mainTimelineSuggestions = timelineState.timelineItems
          .where((item) => item.type == TimelineItemType.suggestion)
          .toList();
      
      if (mainTimelineSuggestions.isEmpty) return null;
      
      // 最新の提案時刻を取得
      mainTimelineSuggestions.sort((a, b) => b.timestamp.compareTo(a.timestamp));
      final latestSuggestion = mainTimelineSuggestions.first;
      
      return latestSuggestion.timestamp;
      
    } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Error getting last heartbeat suggestion time: $e');
      return null;
    }
  }

  /// メインタイムラインとの重複チェック
  bool _isDuplicateWithMainTimeline(TimelineItemModel suggestion) {
    try {
      // TimelineProviderから現在のメインタイムライン提案を取得
      if (!ref.exists(timelineProvider)) {
        return false; // プロバイダーが存在しない場合は重複なしとして処理
      }
      final timelineState = ref.read(timelineProvider);
      final mainTimelineSuggestions = timelineState.timelineItems
          .where((item) => item.type == TimelineItemType.suggestion)
          .toList();
      
      // 同じタイプの提案が既に存在するかチェック
      final suggestionType = suggestion.when(
        alert: (_, __, ___, ____, _____) => null,
        suggestion: (_, type, __, ___, ____, _____, ______) => type,
        chat: (_, __, ___, ____, _____) => null,
        chatWithAction: (_, __, ___, ____, _____, ______, _______) => null,
      );
      
      if (suggestionType == null) return false;
      
      // 直近30分以内の同じタイプの提案をチェック
      final thirtyMinutesAgo = DateTime.now().subtract(const Duration(minutes: 30));
      final recentDuplicates = mainTimelineSuggestions.where((item) {
        final itemType = item.when(
          alert: (_, __, ___, ____, _____) => null,
          suggestion: (_, type, __, ___, ____, _____, ______) => type,
          chat: (_, __, ___, ____, _____) => null,
          chatWithAction: (_, __, ___, ____, _____, ______, _______) => null,
        );
        return itemType == suggestionType && item.timestamp.isAfter(thirtyMinutesAgo);
      }).toList();
      
      return recentDuplicates.isNotEmpty;
    } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Error checking duplicates: $e');
      return false; // エラー時は重複なしとして処理続行
    }
  }

  /// ストリームデータを TimelineItemModel に変換
  TimelineItemModel? _parseStreamedSuggestion(Map<String, dynamic> data) {
    try {
      // データ構造に応じて解析
      final suggestionData = data['data'] ?? data;
      
      if (suggestionData['type'] == null) {
      // debugPrint('[StreamingSuggestionsList] Missing type in suggestion data');
        return null;
      }

      final type = suggestionData['type'] as String;
      final id = '${type}_${DateTime.now().millisecondsSinceEpoch}';

      switch (type) {
        case 'welcome_message':
        case 'contact_registration_prompt':
        case 'contact_registration_reminder':
        case 'guide_recommendation':
        case 'app_feature_introduction':
        case 'hazard_map_prompt':
        case 'emergency_contact_setup':
        case 'hazard_map_url':
        case 'low_battery_warning':
        case 'emergency_alert':
        case 'disaster_update':
        case 'disaster_news':
        case 'quiz_reminder':
        case 'safety_confirmation_sms_proposal':
        case 'immediate_safety_action':
        case 'evacuation_prompt':
        case 'official_info_check_prompt':
        case 'seasonal_warning':
        case 'emergency':
        case 'emergency_disaster_news':
        case 'emergency_guidance':
        case 'disaster_info':
        case 'evacuation_instruction':
        case 'location_based_info':
        case 'seasonal_alert':
        case 'app_feature_recommendation':
        case 'shelter_status_update':
        case 'shelter_info':
        case 'location_permission_reminder':
        case 'gps_permission_check':
        case 'notification_permission_reminder':
          return TimelineItemModel.suggestion(
            id: id,
            suggestionType: type,
            content: suggestionData['content'] ?? '',
            actionData: suggestionData['action_data'],
            actionQuery: suggestionData['action_query'],
            actionDisplayText: suggestionData['action_display_text'],
            timestamp: DateTime.parse(
              suggestionData['created_at'] ?? DateTime.now().toIso8601String(),
            ),
          );
        default:
      // debugPrint('[StreamingSuggestionsList] Unknown suggestion type: $type');
          return null;
      }
    } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Failed to parse suggestion: $e');
      return null;
    }
  }

  /// ストリーミングをリセット
  void resetStreaming() {
    stopStreaming();
    setState(() {
      _streamedSuggestions.clear();
      _chatItems.clear();
      _hasError = false;
      _errorMessage = null;
    });
  }


  /// アクションクエリを送信
  Future<void> _sendActionQuery(String actionQuery, String displayText) async {
    if (actionQuery.isEmpty) return;

    // ストリーミングを完全に停止
    stopStreaming();

    setState(() {
      _isChatLoading = true;
      _isPausedForChat = true; // ストリーミングを一時停止
    });

    // 新しい質問をする時は古いチャット履歴をクリア
    setState(() {
      _chatItems.clear(); // 古いチャット履歴をクリア
    });

    // ユーザーの質問をチャットアイテムに追加
    final userMessageId = DateTime.now().millisecondsSinceEpoch.toString();
    final userMessage = TimelineItemModel.chat(
      id: userMessageId,
      timestamp: DateTime.now(),
      messageText: displayText,
      senderNickname: 'You',
      isOwnMessage: true,
    );

    setState(() {
      _chatItems.add(userMessage);
    });

    try {
      if (!ref.exists(deviceStatusProvider) || !ref.exists(settingsProvider)) {
        throw Exception('Required providers not initialized');
      }
      
      final deviceId = await ref.read(deviceStatusProvider.notifier).getDeviceId();
      final settings = ref.read(settingsProvider);
      
      if (settings.currentUserSettings == null) {
        throw Exception('Settings not loaded');
      }

      final language = settings.currentUserSettings!.languageCode;
      final currentLocation = ref.exists(deviceStatusProvider) 
          ? ref.read(deviceStatusProvider).currentLocation
          : null;
      
      // チャット履歴を構築（SSE内のチャットのみ）
      final chatHistory = _chatItems
          .where((item) => item.type == TimelineItemType.chat)
          .take(10)
          .map((item) => item.when(
                alert: (_, __, ___, ____, _____) => null,
                suggestion: (_, __, ___, ____, _____, ______, _______) => null,
                chat: (_, __, messageText, senderNickname, isOwnMessage) => 
                    Tuple2(isOwnMessage ? 'human' : 'assistant', messageText),
                chatWithAction: (_, __, messageText, senderNickname, isOwnMessage, requiresAction, actionData) => 
                    Tuple2(isOwnMessage ? 'human' : 'assistant', messageText),
              ))
          .where((tuple) => tuple != null)
          .cast<Tuple2<String, String>>()
          .toList()
          .reversed
          .toList();

      if (!ref.exists(apiServiceProvider)) {
        throw Exception('API service not initialized');
      }
      final apiService = ref.read(apiServiceProvider);
      final apiResponse = await apiService.sendChatMessage(
        message: actionQuery,
        deviceId: deviceId,
        sessionId: DateTime.now().millisecondsSinceEpoch.toString(),
        language: language,
        chatHistory: chatHistory,
        currentLocation: currentLocation,
      );

      // エージェントの回答を追加（型安全なアクセス）
      final responseText = apiResponse.responseText;
      if (responseText.isNotEmpty) {
        final agentMessageId = DateTime.now().millisecondsSinceEpoch.toString();
        final agentMessage = TimelineItemModel.chat(
          id: agentMessageId,
          timestamp: DateTime.now(),
          messageText: responseText,
          senderNickname: 'SafeBeee',
          isOwnMessage: false,
        );

        setState(() {
          _chatItems.add(agentMessage);
        });

        // ハートビート同期に統合されたため、ストリーミング再開は無効
        Future.delayed(const Duration(seconds: 2), () {
          setState(() {
            _isPausedForChat = false;
          });
        });
      }

    } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Failed to send action query: $e');
      // エラー時はユーザーメッセージを削除
      setState(() {
        _chatItems.removeWhere((item) => item.id == userMessageId);
      });
    } finally {
      setState(() {
        _isChatLoading = false;
        _isPausedForChat = false; // エラー時もストリーミング再開
      });
    }
  }

  /// 緊急連絡先追加ダイアログを表示
  Future<void> _showAddContactDialog(String suggestionId, String suggestionType) async {
    if (!context.mounted) {
      return;
    }
    
    try {
      final result = await showDialog<bool>(
        context: context,
        barrierDismissible: true,
        builder: (dialogContext) {
          return AlertDialog(
            title: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.add_circle, color: Colors.blue),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    AppLocalizations.of(context)?.addEmergencyContact ?? '緊急連絡先を追加',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: _nameController,
                  decoration: InputDecoration(
                    labelText: AppLocalizations.of(context)?.name ?? '名前',
                    prefixIcon: const Icon(Icons.person),
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _phoneController,
                  decoration: InputDecoration(
                    labelText: AppLocalizations.of(context)?.phoneNumber ?? '電話番号',
                    prefixIcon: const Icon(Icons.phone),
                    border: const OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.phone,
                ),
              ],
            ),
            actions: [
              TextButton.icon(
                onPressed: () {
                  _nameController.clear();
                  _phoneController.clear();
                  Navigator.pop(dialogContext);
                },
                icon: const Icon(Icons.close),
                label: Text(AppLocalizations.of(dialogContext)?.cancel ?? 'キャンセル'),
              ),
              ElevatedButton.icon(
                onPressed: () => _saveEmergencyContact(dialogContext, suggestionId, suggestionType),
                icon: const Icon(Icons.save),
                label: Text(AppLocalizations.of(dialogContext)?.save ?? '保存'),
              ),
            ],
          );
        },
      );
      
      // ダイアログが閉じたらカードを削除（保存・キャンセル問わず）
      setState(() {
        _streamedSuggestions.removeWhere((suggestion) => suggestion.id == suggestionId);
      });
    } catch (e) {
      // debugPrint('[StreamingSuggestionsList] Error showing contact dialog: $e');
    }
  }

  /// 緊急連絡先を保存
  Future<void> _saveEmergencyContact(BuildContext context, String suggestionId, String suggestionType) async {
    final name = _nameController.text.trim();
    final phoneNumber = _phoneController.text.trim();

    if (name.isEmpty || phoneNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context)?.pleaseEnterNameAndPhone ?? '名前と電話番号を入力してください'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    try {
      // SettingsProviderを使って緊急連絡先を追加
      if (!ref.exists(settingsProvider)) {
        throw Exception('Settings provider not initialized');
      }
      await ref.read(settingsProvider.notifier).addEmergencyContact(name, phoneNumber);

      // カードの削除は呼び出し元で処理されるため、ここでは削除しない

      _nameController.clear();
      _phoneController.clear();
      
      if (context.mounted && Navigator.canPop(context)) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)?.emergencyContactAdded ?? '緊急連絡先を追加しました'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('保存中にエラーが発生しました: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // モード変更を監視
    final deviceStatus = ref.watch(deviceStatusProvider);
    final currentMode = deviceStatus.currentMode;
    final isChatActive = deviceStatus.isChatActive;
    
    // TimelineProviderのストリーミング状態を監視
    final timelineState = ref.watch(timelineProvider);
    final shouldStartSSE = timelineState.isStreaming;

    // チャット状態変更の監視（状態変化時のみ実行）
    if (_lastChatActiveState != isChatActive) {
      _lastChatActiveState = isChatActive;
      
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && isChatActive && _isStreaming) {
          stopStreaming();
        }
      });
    }
    
    // TimelineProviderからのSSE開始トリガーを監視（重複防止のため状態を記録）
    if (shouldStartSSE && !_isStreaming && !isChatActive && !_isPausedForChat && !_isSSEStarting) {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (mounted) {
          await startStreamingFromHeartbeat();
        }
      });
    }

    if (_lastMode != null && _lastMode != currentMode) {
      // モードが変更された場合、前のモードの提案をクリア
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          // ストリーミングを完全停止
          stopStreaming();
          // 提案をクリア
          setState(() {
            _streamedSuggestions.clear();
            _chatItems.clear(); // チャットも一緒にクリア
            _hasError = false;
            _errorMessage = null;
            _isPausedForChat = false; // 一時停止状態もリセット
          });
        }
      });
    }
    _lastMode = currentMode;
    
    // SSE接続の管理のみ行い、UIは表示しない
    // 提案はTimelineProviderに追加されるため、メインタイムラインで表示される
    return const SizedBox.shrink();
  }
}

/// アニメーション付き提案カード
class AnimatedSuggestionCard extends StatefulWidget {
  final TimelineItemModel suggestion;
  final Function(String suggestionId)? onRemove;

  const AnimatedSuggestionCard({
    super.key,
    required this.suggestion,
    this.onRemove,
  });

  @override
  State<AnimatedSuggestionCard> createState() => _AnimatedSuggestionCardState();
}

class _AnimatedSuggestionCardState extends State<AnimatedSuggestionCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeIn,
    ));
    
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.5),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOut,
    ));

    // アニメーションを開始
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: widgets.SuggestionTimelineItem(
          model: widget.suggestion,
          onRemoveFromStreaming: widget.onRemove,
        ),
      ),
    );
  }
}