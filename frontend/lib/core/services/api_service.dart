import 'dart:io'; // HttpClient用
import 'dart:convert'; // jsonDecode, utf8, LineSplitter用
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart'; // kDebugModeのため
import 'package:frontend/core/config/app_config.dart'; // P1-005(改)で作成
import 'package:frontend/core/utils/device_id_util.dart'; // P1-007で作成
import 'package:frontend/core/models/app_exception.dart'; // P1-010で作成
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/core/models/location_model.dart';
import 'package:frontend/core/models/chat_response_model.dart';
import 'package:frontend/core/models/heartbeat_response_model.dart';
import 'package:frontend/core/models/proactive_suggestion_response_model.dart';
import 'package:frontend/core/models/device_response_model.dart';
import 'package:frontend/core/services/local_storage_service.dart';
import 'package:frontend/core/services/suggestion_history_manager.dart';
import 'package:tuple/tuple.dart'; // Tuple2のため

class ApiService {
  late final Dio _dio;

  ApiService() {
    final options = BaseOptions(
      baseUrl: AppConfig.apiBaseUrl, // dart-defineまたは.envから読み込まれたベースURL
      connectTimeout: const Duration(seconds: 10), // 接続タイムアウトを10秒に短縮
      receiveTimeout: const Duration(seconds: 30), // 受信タイムアウトを30秒に短縮
      headers: {
        'Content-Type': 'application/json',
        // Acceptヘッダーなども必要に応じて追加
      },
    );
    _dio = Dio(options);

    if (kDebugMode) {
      // デバッグモード時のみログインターセプターを追加
      _dio.interceptors.add(
        LogInterceptor(
          request: true,
          requestHeader: true,
          requestBody: true,
          responseHeader: true,
          responseBody: true,
          error: true,
          logPrint: (object) {
            if (kDebugMode) print(object.toString());
          },
        ),
      );
    }
  }

  // リクエストオプションに最新のデバイスIDをマージするヘルパー
  Options _mergeWithOptions(Options? options) {
    final deviceId = DeviceIdUtil.currentDeviceId;
    final Map<String, dynamic> headers = Map<String, dynamic>.from(
      options?.headers ?? {},
    );
    if (deviceId != null && deviceId.isNotEmpty) {
      headers['X-Device-ID'] = deviceId;
    }
    return (options ?? Options()).copyWith(headers: headers);
  }

  // 共通のリクエスト処理とエラーハンドリング
  Future<T> _handleRequest<T>(
    Future<Response<dynamic>> Function() requestFunction,
  ) async {
    try {
      final Response<dynamic> response = await requestFunction();
      // ステータスコードが2xxでない場合はエラーとして扱うことも検討 (Dioはデフォルトで2xx以外をエラーとする)
      // if (response.statusCode != null && (response.statusCode! < 200 || response.statusCode! >= 300)) {
      //   throw DioException(requestOptions: response.requestOptions, response: response, message: "Request failed with status ${response.statusCode}");
      // }
      if (response.data == null && T != Null && T != dynamic) {
        // Tがvoidやdynamicでない場合にnullチェック
        throw AppException(
          message: "API response data is null, but expected type $T",
        );
      }
      // レスポンスデータが期待する型Tであることを確認 (必要に応じてさらに厳密な型チェックや変換)
      // ここでは、呼び出し元で適切に型が指定されることを期待する
      return response.data as T;
    } on DioException catch (e) {
      if (kDebugMode) {
        print('ApiService DioError: ${e.type} - ${e.message}');
        if (e.response != null) {
          print(
            'DioError Response: ${e.response?.statusCode} - ${e.response?.data}',
          );
        }
      }
      throw AppException.fromDioError(e); // カスタム例外に変換
    } catch (e, stackTrace) {
      if (kDebugMode) {
        print('ApiService Unexpected Error: $e');
        print('ApiService StackTrace: $stackTrace');
      }
      throw AppException(
        message: 'An unexpected error occurred in ApiService: ${e.toString()}',
        underlyingError: e,
      );
    }
  }

  // GETリクエスト
  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _handleRequest<T>(
      () => _dio.get(
        path,
        queryParameters: queryParameters,
        options: _mergeWithOptions(options),
      ),
    );
  }

  // POSTリクエスト
  Future<T> post<T>(String path, {dynamic data, Options? options, CancelToken? cancelToken}) async {
    return _handleRequest<T>(
      () => _dio.post(path, data: data, options: _mergeWithOptions(options), cancelToken: cancelToken),
    );
  }

  // PUTリクエスト
  Future<T> put<T>(String path, {dynamic data, Options? options}) async {
    return _handleRequest<T>(
      () => _dio.put(path, data: data, options: _mergeWithOptions(options)),
    );
  }

  // PATCHリクエスト
  Future<T> patch<T>(String path, {dynamic data, Options? options}) async {
    return _handleRequest<T>(
      () => _dio.patch(path, data: data, options: _mergeWithOptions(options)),
    );
  }

  /// Health check to warm up the backend
  Future<void> performHealthCheck() async {
    try {
      await get<Map<String, dynamic>>('/health');
      if (kDebugMode) {
        print('Health check successful - backend warmed up');
      }
    } catch (e) {
      // Don't throw - this is just a warm-up call
      if (kDebugMode) {
        print('Health check failed (non-critical): $e');
      }
    }
  }

  // DELETEリクエスト
  Future<T> delete<T>(String path, {dynamic data, Options? options}) async {
    return _handleRequest<T>(
      () => _dio.delete(path, data: data, options: _mergeWithOptions(options)),
    );
  }

  // --- バックエンドAPIエンドポイントに対応するメソッド群 ---

  /// デバイス情報をバックエンドに登録または更新します。
  /// このメソッドはオンボーディング完了時やFCMトークン更新時に呼び出されることを想定しています。
  Future<DeviceResponse> registerOrUpdateDevice(DeviceCreateRequest deviceInfo) async {
    try {
      // バックエンドの仕様に合わせてエンドポイントとHTTPメソッドを決定
      // 例: POST /v1/devices または PUT /v1/devices/{deviceId}
      final response = await post<Map<String, dynamic>>(
        '/devices',
        data: deviceInfo.toJson(),
      );
      
      if (kDebugMode) {
        print('Device registered/updated successfully: ${deviceInfo.deviceId}');
      }
      
      return DeviceResponse.fromJson(response);
    } catch (e) {
      if (kDebugMode) {
        print('Failed to register/update device: $e');
      }
      // エラーを再スローするか、ここでハンドリングするかはアプリの要件による
      rethrow;
    }
  }

  /// タイムラインの初期アイテムを取得します
  Future<List<TimelineItemModel>> getTimelineItems({
    required String deviceId,
    required String language,
    LocationModel? currentLocation,
    List<String>? currentAreaCodes,
    String? currentSituation,
    int? limit,
    String? lastSuggestionTimestamp,
    List<Map<String, dynamic>>? chatHistorySummary,
    bool isEmergencyMode = false,
  }) async {
    try {
      // Validate language parameter
      String finalLanguage = language;
      if (finalLanguage.isEmpty) {
        finalLanguage = 'en';
      }
      if (!['en', 'ja', 'zh', 'zh_CN', 'zh_TW', 'ko', 'es', 'fr', 'de', 'it', 'pt', 'ru'].contains(finalLanguage)) {
        // WARNING: Unsupported language $finalLanguage, defaulting to en');
        finalLanguage = 'en';
      }

      final Map<String, dynamic> requestBody = {
        'device_id': deviceId,
        'language_code': finalLanguage,
        if (currentLocation != null) 'current_location': currentLocation.toJson(),
        if (currentAreaCodes != null && currentAreaCodes.isNotEmpty)
          'current_area_codes': currentAreaCodes,
        if (currentSituation != null) 'current_situation': currentSituation,
        if (limit != null) 'limit': limit,
        if (lastSuggestionTimestamp != null)
          'last_suggestion_timestamp': lastSuggestionTimestamp,
        if (chatHistorySummary != null && chatHistorySummary.isNotEmpty)
          'suggestion_history_summary': chatHistorySummary,
        if (isEmergencyMode) 'is_emergency_mode': true,
        'user_app_usage_summary': await _buildUserAppUsageSummary(),
      };

      final headers = {
        'Accept-Language': finalLanguage,
        'X-Device-ID': deviceId,
      };
      
      // 廃止されたエンドポイントからハートビートエンドポイントに変更
      final response = await post<Map<String, dynamic>>(
        '/sync/heartbeat',
        data: requestBody,
        options: Options(headers: headers),
      );
      
      // ハートビートレスポンスのフィールド名に合わせる
      final suggestions = response['proactive_suggestions'] ?? response['suggestions'] ?? [];
      
      if (suggestions == null) {
        throw AppException(message: "API response missing suggestions");
      }

        final List<dynamic> suggestionsList = suggestions is List ? suggestions : [];
        final items = suggestionsList.map((itemJson) {
          final type = itemJson['type'] as String;

          switch (type) {
            case 'welcome_message':
            case 'contact_registration_prompt':
            case 'contact_registration_reminder':
            case 'guide_recommendation':
            case 'app_feature_introduction':
            case 'hazard_map_prompt':
            case 'emergency_contact_setup':
            case 'low_battery_warning':
            case 'emergency_alert':
            case 'disaster_update':
            case 'disaster_news':  // 平常時・緊急時両方で使用
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
            case 'shelter_info':
              return TimelineItemModel.suggestion(
                id: '${itemJson['type']}_${DateTime.now().millisecondsSinceEpoch}',
                suggestionType: itemJson['type'],
                content: itemJson['content'],
                actionData: itemJson['action_data'],
                actionQuery: itemJson['action_query'],
                actionDisplayText: itemJson['action_display_text'],
                timestamp: DateTime.parse(itemJson['created_at'] ?? DateTime.now().toIso8601String()),
              );
            default:
              // 未知のタイプの場合はスキップして処理を続行
              return null; // nullを返してスキップ
          }
      }).where((item) => item != null).cast<TimelineItemModel>().toList();

      return items;
    } catch (e, stack) {
        // Failed to fetch timeline items: $e');
        // Stack trace: $stack');
      rethrow;
    }
  }

  /// 追加のタイムラインアイテムを取得します
  Future<List<TimelineItemModel>> getMoreTimelineItems(
    String lastItemId,
  ) async {
    // final response = await get<List<dynamic>>('/timeline', queryParameters: {'last_item_id': lastItemId});
    await Future.delayed(const Duration(milliseconds: 500));
    // Dummy: return empty list to simulate no more items
    final List<Map<String, dynamic>> dummyResponse = [];
    return dummyResponse
        .map((itemJson) => TimelineItemModel.fromJson(itemJson))
        .toList();
  }

  /// チャットメッセージを送信します
  Future<ChatResponse> sendChatMessage({
    required String message,
    required String deviceId,
    required String sessionId,
    String? language,
    List<Tuple2<String, String>>? chatHistory,
    LocationModel? currentLocation,
    bool isDisasterMode = false,
    int? emergencyContactsCount,
    CancelToken? cancelToken,
  }) async {
    // Validate and ensure language is set
    String finalLanguage = language ?? 'en';
    if (finalLanguage.isEmpty) {
        // WARNING: Empty language parameter in chat, defaulting to en
      finalLanguage = 'en';
    }
    if (!['en', 'ja', 'zh', 'zh_CN', 'zh_TW', 'ko', 'es', 'fr', 'de', 'it', 'pt', 'ru'].contains(finalLanguage)) {
        // WARNING: Unsupported language defaulting to en
      finalLanguage = 'en';
    }
    
    // Get emergency contacts count if not provided
    int contactsCount = emergencyContactsCount ?? await _getLocalEmergencyContactCount();
    
    // エンドポイントパスを修正: /chat/messages → /chat
    final Map<String, dynamic> requestBody = {
      'device_id': deviceId,
      'session_id': sessionId,
      'user_input': message,
      'user_language': finalLanguage,
      'is_disaster_mode': isDisasterMode,
      'client_context': {
        'emergency_contacts_count': contactsCount,
      },
    };

    // Add location data if available
    if (currentLocation != null) {
      requestBody['user_location'] = currentLocation.toJson();
    }

    // チャット履歴をフォーマット
    if (chatHistory != null && chatHistory.isNotEmpty) {
      requestBody['chat_history'] = chatHistory
          .map((tuple) => [tuple.item1, tuple.item2])
          .toList();
    }

    // デバッグモードまたはテストモードの場合、デバッグ情報を追加
    if (AppConfig.isDebugMode || AppConfig.isTestMode) {
      requestBody['debug'] = true;
    }

        // 🔴 Chat request emergency_contacts_count: $contactsCount');

    final response = await post<Map<String, dynamic>>(
      '/chat', 
      data: requestBody,
      cancelToken: cancelToken,
    );
    return ChatResponse.fromJson(response);
  }

  /// デバッグ用のアラート発報を実行します
  Future<Map<String, dynamic>> triggerDebugAlert({
    required String deviceId,
    String alertType = 'earthquake',
    String severity = 'Emergency',
    String? customTitle,
    String? customDescription,
  }) async {
    try {
      final Map<String, dynamic> requestBody = {
        'device_id': deviceId,
        'alert_type': alertType,
        'severity': severity,
        'title': customTitle ?? '🚨 デバッグ用緊急アラート',
        'description': customDescription ?? 'デバッグ機能から発報されたテストアラートです。',
      };
      
      final response = await post<Map<String, dynamic>>(
        '/debug/trigger-mock-alert',
        data: requestBody,
      );
      
      return response;
    } catch (e) {
        // Failed to trigger debug alert: $e');
      rethrow;
    }
  }

  /// ユーザーアプリ利用状況サマリーを構築
  Future<Map<String, dynamic>> _buildUserAppUsageSummary() async {
    try {
      // ローカルストレージから緊急連絡先数を取得
      int contactCount = await _getLocalEmergencyContactCount();
      
      return {
        'local_contact_count': contactCount,
        'is_new_user': contactCount == 0, // 緊急連絡先が0の場合は新規ユーザーとみなす
        'unread_guide_topics': <String>[],
        'incomplete_settings': contactCount == 0 ? ['emergency_contacts'] : <String>[],
        'last_app_open_days_ago': 0, // 現在のセッションなので0
      };
    } catch (e) {
        // Failed to build user app usage summary: $e');
      return {
        'local_contact_count': 0,
        'is_new_user': true,
        'unread_guide_topics': <String>[],
        'incomplete_settings': ['emergency_contacts'],
        'last_app_open_days_ago': 0,
      };
    }
  }

  /// ローカルの緊急連絡先数を取得
  Future<int> _getLocalEmergencyContactCount() async {
    try {
      final localStorageService = LocalStorageService();
      final emergencyContacts = await localStorageService.getEmergencyContacts();
      final count = emergencyContacts.length;
      
      return count;
    } catch (e) {
        // Failed to get local emergency contact count: $e');
      return 0;
    }
  }


  /// 統合ハートビートAPIを送信
  Future<HeartbeatResponse> sendHeartbeat({
    required String deviceId,
    required int batteryLevel,
    required bool isBatteryCharging,
    required String connectivityStatus,
    LocationModel? currentLocation,
    String currentMode = 'normal',
    String languageCode = 'ja',
    DateTime? lastSyncTimestamp,
    List<String>? acknowledgedSuggestionTypes,
    bool resetSuggestionHistory = false,
    int emergencyContactsCount = 0,
    bool isLocationPermissionGranted = false,
    bool isGpsEnabled = false,
    bool isNotificationPermissionGranted = false,
  }) async {
    final requestStartTime = DateTime.now();
    try {
      
      // 表示済み提案タイプを取得
      final storedSuggestionTypes = await SuggestionHistoryManager.getAcknowledgedSuggestionTypes();
      // パラメータで渡されたタイプと統合（重複を排除）
      final allAcknowledgedTypes = <String>{
        ...storedSuggestionTypes,
        if (acknowledgedSuggestionTypes != null) ...acknowledgedSuggestionTypes,
      }.toList();
      
      
      // 古い履歴をクリーンアップ（パフォーマンス向上）
      await SuggestionHistoryManager.cleanupOldSuggestions();
      
      // Convert connectivity status to network type
      String networkType = 'unknown';
      switch (connectivityStatus.toLowerCase()) {
        case 'wifi':
          networkType = 'wifi';
          break;
        case 'mobile':
        case 'cellular':
          networkType = '4g'; // バックエンドは 'cellular' を受け付けないため '4g' に変換
          break;
        case 'ethernet':
          networkType = 'wifi'; // ethernet も wifi として扱う
          break;
        case 'none':
          networkType = 'offline'; // バックエンドは 'none' ではなく 'offline' を期待
          break;
        default:
          networkType = 'unknown';
      }

      // デバッグ: 緊急連絡先数をログ出力
        // 🔴 Building heartbeat request...');
        // 🔴 Emergency contacts count received: $emergencyContactsCount');
      
      final Map<String, dynamic> requestBody = {
        'device_id': deviceId,
        'device_status': {
          if (currentLocation != null) 'location': {
            'latitude': currentLocation.latitude,
            'longitude': currentLocation.longitude,
            'accuracy': currentLocation.accuracy,
          },
          'battery_level': batteryLevel,
          'is_charging': isBatteryCharging,
          'network_type': networkType,
          'signal_strength': 4, // デフォルト値
        },
        'client_context': {
          'current_mode': currentMode,
          'language_code': languageCode,
          'last_sync_timestamp': lastSyncTimestamp?.toIso8601String(),
          if (allAcknowledgedTypes.isNotEmpty)
            'acknowledged_suggestion_types': allAcknowledgedTypes,
          'reset_suggestion_history': resetSuggestionHistory,
          'emergency_contacts_count': emergencyContactsCount,
          'permissions': {
            'location_permission_granted': isLocationPermissionGranted,
            'gps_enabled': isGpsEnabled,
            'notification_permission_granted': isNotificationPermissionGranted,
          },
        },
      };
      
      // デバッグ: リクエストボディの緊急連絡先数を確認
        // 🔴 Request body emergency_contacts_count: ${requestBody['client_context']['emergency_contacts_count']}');
      
      final response = await post<Map<String, dynamic>>(
        '/sync/heartbeat',
        data: requestBody,
      );
      
      // Parse response using the model
      final heartbeatResponse = HeartbeatResponse.fromJson(response);
      
      // Log emergency mode if detected
      if (heartbeatResponse.isEmergencyMode) {
         // 🚨 Server Mode: Emergency - ${heartbeatResponse.disasterStatus.modeReason}');
      }
      
      return heartbeatResponse;
    } catch (e) {
        // Heartbeat API error
      rethrow;
    }
  }

  /// 緊急モード強制解除API
  Future<Map<String, dynamic>> forceEmergencyModeReset(String deviceId) async {
    try {
      final response = await post<Map<String, dynamic>>(
        '/debug/force-emergency-mode-reset?device_id=$deviceId',
        data: {},
      );
      
      return response;
    } catch (e) {
        // Failed to force emergency mode reset: $e');
      rethrow;
    }
  }

  /// 間隔設定を取得API
  Future<Map<String, dynamic>> getIntervalConfig() async {
    try {
      final response = await get<Map<String, dynamic>>(
        '/debug/interval-config',
      );
      
      return response;
    } catch (e) {
        // Failed to get interval config: $e');
      rethrow;
    }
  }

  /// Server-Sent Events (SSE) を使用してリアルタイムで提案をストリーミング受信
  Stream<Map<String, dynamic>> streamSuggestions({
    required String deviceId,
    required String languageCode,
    String currentMode = 'normal',
    LocationModel? currentLocation,
    int? batteryLevel,
    bool? isBatteryCharging,
    String? connectivityStatus,
    bool? isLocationPermissionGranted,
    bool? isGpsEnabled,
    bool? isNotificationPermissionGranted,
    int emergencyContactsCount = 0,
  }) async* {
    try {
      
      // クエリパラメータの構築
      final queryParams = <String, String>{
        'device_id': deviceId,
        'language_code': languageCode,
        'current_mode': currentMode,
      };
      
      // オプショナルパラメータの追加
      if (currentLocation != null) {
        queryParams['latitude'] = currentLocation.latitude.toString();
        queryParams['longitude'] = currentLocation.longitude.toString();
      }
      if (batteryLevel != null) {
        queryParams['battery_level'] = batteryLevel.toString();
      }
      if (isBatteryCharging != null) {
        queryParams['is_charging'] = isBatteryCharging.toString();
      }
      if (connectivityStatus != null) {
        queryParams['connectivity'] = connectivityStatus;
      }
      
      // ハートビート統合SSE接続（POST形式）
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/sync/heartbeat-sse');
      
        // SSE URI: $uri');
      
      // リクエストボディを構築（ハートビート形式）
      final requestBody = {
        'device_id': deviceId,
        'device_status': {
          if (currentLocation != null) 'location': {
            'latitude': currentLocation.latitude,
            'longitude': currentLocation.longitude,
            'accuracy': currentLocation.accuracy,
          },
          'battery_level': batteryLevel ?? 80,
          'is_charging': isBatteryCharging ?? false,
          'network_type': _convertConnectivityToNetworkType(connectivityStatus ?? 'wifi'),
          'signal_strength': 4,
        },
        'client_context': {
          'current_mode': currentMode,
          'language_code': languageCode,
          'last_sync_timestamp': DateTime.now().toIso8601String(),
          'acknowledged_suggestion_types': [],
          'reset_suggestion_history': false,
          'emergency_contacts_count': emergencyContactsCount,
          'permissions': {
            'location_permission_granted': isLocationPermissionGranted ?? false,
            'gps_enabled': isGpsEnabled ?? false,
            'notification_permission_granted': isNotificationPermissionGranted ?? false,
          },
        },
      };
      
        // SSE request body: $requestBody');
      
      // HttpClientを使用してPOST        // SSE接続を作成
      final httpClient = HttpClient();
      httpClient.connectionTimeout = const Duration(seconds: 30);
      httpClient.idleTimeout = const Duration(minutes: 3); // 10分 → 3分に短縮（適切な値）
      
      final request = await httpClient.postUrl(uri);
      request.headers.add('Accept', 'text/event-stream');
      request.headers.add('Cache-Control', 'no-cache');
      request.headers.add('Content-Type', 'application/json');
      
      // デバイスIDヘッダーの追加
      if (deviceId.isNotEmpty) {
        request.headers.add('X-Device-ID', deviceId);
      }
      
      // リクエストボディを送信
      final bodyString = jsonEncode(requestBody);
      request.write(bodyString);
      
      final response = await request.close();
      
      if (response.statusCode != 200) {
          // SSE connection failed: ${response.statusCode}');
        throw Exception('SSE connection failed with status: ${response.statusCode}');
      }
      
        // SSE connection established');
      
      // ストリームを処理
      await for (final data in response.transform(utf8.decoder).transform(const LineSplitter())) {
        if (data.startsWith('data: ')) {
          try {
            final jsonStr = data.substring(6); // "data: "を除去
            if (jsonStr.trim().isEmpty) continue;
            
            final jsonData = jsonDecode(jsonStr) as Map<String, dynamic>;
            
            // 完了シグナルをチェック
            if (jsonData['type'] == 'complete') {
                // SSE stream completed');
              break;
            }
            
            // エラーをチェック
            if (jsonData['type'] == 'error') {
                // SSE stream error: ${jsonData['message']}');
              throw Exception('SSE stream error: ${jsonData['message']}');
            }
            
            // データを出力
            if (jsonData['type'] == 'suggestion' || jsonData['data'] != null) {
              yield jsonData;
            }
          } catch (e) {
              // Failed to parse        // SSE data: $e');
        // Raw data: $data');
          }
        }
      }
      
      httpClient.close();
        // ===        // SSE STREAMING END        // ===');
      
    } catch (e, stackTrace) {
        // SSE streaming error: $e');
        // Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// 完全アプリリセットAPI（Firebaseデータ削除含む）
  Future<Map<String, dynamic>> completeAppReset(String deviceId) async {
        // === COMPLETE APP RESET START        // ===');
        // 🗑️ Complete app reset for device: $deviceId');
        // ⚠️ This will delete ALL Firebase data for this device');
    
    try {
      final response = await post<Map<String, dynamic>>(
        '/debug/complete-app-reset?device_id=$deviceId',
        data: {},
      );
      
        // ✅ Complete app reset successful');
        // 📥 Response: $response');
        // 🗑️ Reset operations: ${response['reset_operations']}');
        // 📊 Total operations: ${response['reset_count']}');
        // === COMPLETE APP RESET END (SUCCESS)        // ===');
      
      return response;
    } catch (e) {
        // ❌        // Failed to complete app reset: $e');
        // === COMPLETE APP RESET END (ERROR)        // ===');
      rethrow;
    }
  }

  /// 接続性ステータスをネットワークタイプに変換
  String _convertConnectivityToNetworkType(String connectivityStatus) {
    switch (connectivityStatus.toLowerCase()) {
      case 'wifi':
        return 'wifi';
      case 'mobile':
      case 'cellular':
        return '4g';
      case 'ethernet':
        return 'wifi';
      case 'none':
        return 'offline';
      default:
        return 'unknown';
    }
  }

  /// 提案履歴をフロントエンド・バックエンド両方から完全にクリア
  Future<Map<String, dynamic>> clearSuggestionHistory({
    required String deviceId,
    required int batteryLevel,
    required bool isBatteryCharging,
    required String connectivityStatus,
    LocationModel? currentLocation,
    String currentMode = 'normal',
    String languageCode = 'ja',
  }) async {
        // === CLEAR SUGGESTION HISTORY START        // ===');
        // 🗑️ Clearing suggestion history on both frontend and backend');
        // 📱 Device ID: $deviceId');
    
    try {
      // 1. フロントエンドの履歴をクリア
        // 🗑️ Clearing frontend suggestion history...');
      await SuggestionHistoryManager.clearHistory();
        // ✅ Frontend history cleared');
      
      // 2. バックエンドに履歴リセット要求を送信（resetSuggestionHistory=trueでハートビート送信）
        // 📡 Sending backend reset request...');
      final response = await sendHeartbeat(
        deviceId: deviceId,
        batteryLevel: batteryLevel,
        isBatteryCharging: isBatteryCharging,
        connectivityStatus: connectivityStatus,
        currentLocation: currentLocation,
        currentMode: currentMode,
        languageCode: languageCode,
        acknowledgedSuggestionTypes: [], // 空のリストで送信
        resetSuggestionHistory: true, // バックエンド履歴リセットフラグ
      );
      
        // ✅ Backend reset request sent successfully');
        // 📥 Backend response: ${response.syncId}');
        // === CLEAR SUGGESTION HISTORY END (SUCCESS)        // ===');
      
      // Convert HeartbeatResponse to Map for backward compatibility
      return {
        'status': 'success',
        'sync_id': response.syncId,
        'server_timestamp': response.serverTimestamp.toIso8601String(),
      };
    } catch (e) {
        // ❌        // Failed to clear suggestion history: $e');
        // === CLEAR SUGGESTION HISTORY END (ERROR)        // ===');
      rethrow;
    }
  }
}
