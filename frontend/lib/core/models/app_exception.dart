import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

class AppException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic underlyingError; // 元のエラーオブジェクトを保持

  AppException({
    required this.message,
    this.statusCode,
    this.underlyingError,
  });

  factory AppException.fromDioError(DioException dioError) {
    String errorMessage;
    switch (dioError.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        errorMessage = "通信がタイムアウトしました。ネットワーク環境を確認してください。";
        break;
      case DioExceptionType.badResponse:
        // statusCodeやレスポンスボディに応じて、より具体的なメッセージを生成
        errorMessage = _extractMessageFromErrorResponse(dioError.response);
        break;
      case DioExceptionType.cancel:
        errorMessage = "リクエストがキャンセルされました。";
        break;
      case DioExceptionType.connectionError:
        errorMessage = "接続エラーが発生しました。インターネット接続を確認してください。";
        break;
      case DioExceptionType.unknown:
      default:
        if (dioError.message != null && dioError.message!.toLowerCase().contains('socketexception')) {
          errorMessage = "インターネットに接続できませんでした。";
        } else if (dioError.message != null && dioError.message!.toLowerCase().contains('handshakeexception')) {
          errorMessage = "サーバーとの安全な接続を確立できませんでした。";
        }
        else {
          errorMessage = "予期せぬエラーが発生しました。";
        }
        break;
    }
    if (kDebugMode) {
        print("AppException from DioError: Type=${dioError.type}, Status=${dioError.response?.statusCode}, Msg=$errorMessage");
    }
    return AppException(
      message: errorMessage,
      statusCode: dioError.response?.statusCode,
      underlyingError: dioError,
    );
  }

  static String _extractMessageFromErrorResponse(Response? response) {
    if (response?.data != null && response!.data is Map) {
      final responseData = response.data as Map<String, dynamic>;
      // バックエンドが返すエラーメッセージのキーを想定 (例: 'detail', 'message', 'error')
      if (responseData.containsKey('detail') && responseData['detail'] is String) {
        return responseData['detail'];
      }
      if (responseData.containsKey('message') && responseData['message'] is String) {
        return responseData['message'];
      }
      if (responseData.containsKey('error') && responseData['error'] is String) {
        return responseData['error'];
      }
    }
    // より一般的なHTTPステータスメッセージ
    switch (response?.statusCode) {
      case 400: return 'リクエストが不正です。';
      case 401: return '認証に失敗しました。';
      case 403: return 'アクセス権限がありません。';
      case 404: return 'お探しの情報は見つかりませんでした。';
      case 500: return 'サーバー内部でエラーが発生しました。しばらくしてから再度お試しください。';
      default: return 'サーバーとの通信で問題が発生しました (ステータスコード: ${response?.statusCode})。';
    }
  }

  @override
  String toString() {
    return 'AppException: $message (StatusCode: $statusCode)';
  }
}
