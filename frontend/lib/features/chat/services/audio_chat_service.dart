import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:http_parser/http_parser.dart';
import '../../../core/services/api_service.dart';
import '../../../core/utils/logger.dart';
import '../../../core/models/chat_message.dart';

class AudioChatService {
  final ApiService _apiService;
  
  AudioChatService(this._apiService);
  
  /// 音声データをバックエンドに送信してチャット応答を取得
  Future<ChatMessage?> sendAudioChat({
    required Uint8List audioData,
    required String deviceId,
    required String sessionId,
    String mimeType = 'audio/wav',
    double? latitude,
    double? longitude,
    String languageCode = 'ja',
  }) async {
    try {
      logger.d('Sending audio chat: ${audioData.length} bytes, deviceId: $deviceId');
      
      // FormDataを作成
      final formData = FormData.fromMap({
        'audio_file': MultipartFile.fromBytes(
          audioData,
          filename: 'voice_input.wav',
          contentType: MediaType.parse(mimeType),
        ),
        'device_id': deviceId,
        'session_id': sessionId,
        'language_code': languageCode,
        if (latitude != null) 'latitude': latitude,
        if (longitude != null) 'longitude': longitude,
      });
      
      // 音声エンドポイントに送信
      final response = await _apiService.post<Map<String, dynamic>>(
        '/api/v1/chat/audio',
        data: formData,
        options: Options(
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          sendTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 60),
        ),
      );
      
      logger.d('Audio chat response received');
      
      // レスポンスからChatMessageを作成
      final data = response;
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: data['responseText'] ?? '',
        sender: MessageSender.ai,
        timestamp: DateTime.now(),
        sessionId: data['sessionId'] ?? sessionId,
        metadata: {
          'currentTaskType': data['currentTaskType'],
          'isEmergencyResponse': data['isEmergencyResponse'],
          'audioProcessing': data['metadata']?['audio_processing'],
          if (data['generatedCardsForFrontend'] != null)
            'cards': data['generatedCardsForFrontend'],
          if (data['actionCards'] != null)
            'actionCards': data['actionCards'],
        },
      );
      
    } catch (e, stackTrace) {
      logger.e('Failed to send audio chat', e, stackTrace);
      
      // エラーメッセージを含むChatMessageを返す
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: _getErrorMessage(e),
        sender: MessageSender.system,
        timestamp: DateTime.now(),
        sessionId: sessionId,
        metadata: {
          'error': true,
          'errorType': e.runtimeType.toString(),
        },
      );
    }
  }
  
  /// 音声ファイルの検証
  Future<Map<String, dynamic>?> validateAudioFile(Uint8List audioData, String filename) async {
    try {
      final formData = FormData.fromMap({
        'audio_file': MultipartFile.fromBytes(
          audioData,
          filename: filename,
        ),
      });
      
      final response = await _apiService.post<Map<String, dynamic>>(
        '/api/v1/chat/audio/validate',
        data: formData,
      );
      
      return response;
    } catch (e) {
      logger.e('Failed to validate audio file', e);
      return null;
    }
  }
  
  /// 音声処理の制限を取得
  Future<Map<String, dynamic>?> getAudioLimits() async {
    try {
      final response = await _apiService.get<Map<String, dynamic>>('/api/v1/chat/audio/limits');
      
      return response;
    } catch (e) {
      logger.e('Failed to get audio limits', e);
      return null;
    }
  }
  
  String _getErrorMessage(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.sendTimeout:
          return '音声送信がタイムアウトしました。もう一度お試しください。';
        case DioExceptionType.receiveTimeout:
          return '応答待機中にタイムアウトしました。もう一度お試しください。';
        case DioExceptionType.badResponse:
          final statusCode = error.response?.statusCode;
          if (statusCode == 413) {
            return '音声ファイルが大きすぎます。60秒以内で録音してください。';
          } else if (statusCode == 415) {
            return 'サポートされていない音声形式です。';
          } else if (statusCode == 503) {
            return '音声処理サービスが一時的に利用できません。';
          }
          return 'サーバーエラーが発生しました。';
        case DioExceptionType.connectionError:
          return 'ネットワーク接続を確認してください。';
        default:
          return '音声送信中にエラーが発生しました。';
      }
    }
    return '予期しないエラーが発生しました。';
  }
}