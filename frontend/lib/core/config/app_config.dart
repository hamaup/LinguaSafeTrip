import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// アプリケーション設定クラス
/// 
/// 環境変数の優先順位:
/// 1. --dart-define (最優先、本番ビルド用)
/// 2. .env ファイル (開発用フォールバック)
/// 3. デフォルト値
class AppConfig {
  // Google Cloud API Key (機密情報)
  static String get googleCloudApiKey {
    // まず--dart-defineをチェック
    const fromDefine = String.fromEnvironment('GOOGLE_CLOUD_API_KEY');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    // なければ.envから取得（開発用）
    try {
      return dotenv.env['GOOGLE_CLOUD_API_KEY'] ?? '';
    } catch (e) {
      return '';
    }
  }

  // API Base URL (後方互換のためbaseUrlも保持)
  static String get baseUrl {
    // dart-defineから取得を優先
    const fromDefine = String.fromEnvironment('API_BASE_URL');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    // dart-defineビルドの場合は.envが初期化されていない可能性があるため
    // try-catchで安全にアクセス
    try {
      // Web platform uses different URL
      if (kIsWeb) {
        final webUrl = dotenv.env['API_BASE_URL_WEB'];
        if (webUrl != null && webUrl.isNotEmpty) return webUrl;
      }
      
      final url = dotenv.env['API_BASE_URL'];
      if (url == null || url.isEmpty) {
        if (kDebugMode) print("警告: API_BASE_URLが設定されていません。デフォルトURLを使用します。");
        return 'http://10.0.2.2:8000/api/v1';
      }
      return url;
    } catch (e) {
      // .envアクセスエラー時はデフォルトURLを返す
      return 'http://10.0.2.2:8000/api/v1';
    }
  }

  static bool get isDebugMode {
    const fromDefine = String.fromEnvironment('DEBUG_MODE');
    if (fromDefine.isNotEmpty) return fromDefine.toLowerCase() == 'true';
    
    try {
      final debugMode = dotenv.env['DEBUG_MODE'];
      return debugMode?.toLowerCase() == 'true';
    } catch (e) {
      return false;
    }
  }

  static bool get isTestMode {
    const fromDefine = String.fromEnvironment('TEST_MODE');
    if (fromDefine.isNotEmpty) return fromDefine.toLowerCase() == 'true';
    
    try {
      final testMode = dotenv.env['TEST_MODE'];
      return testMode?.toLowerCase() == 'true';
    } catch (e) {
      return false;
    }
  }

  /// デバッグ機能が有効かどうか（TEST_MODE=trueの場合のみ）
  static bool get isDebugFeaturesEnabled {
    return isTestMode;
  }

  // ハートビート設定は UserSettingsModel で管理（ユーザー設定として分離）

  // 新しいセキュアAPI（--dart-define対応）
  static String get apiBaseUrl {
    const fromDefine = String.fromEnvironment('API_BASE_URL');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    // dart-defineビルドの場合は.envが初期化されていない可能性があるため
    // try-catchで安全にアクセス
    try {
      // Web platform uses different URL
      if (kIsWeb) {
        final webUrl = dotenv.env['API_BASE_URL_WEB'];
        if (webUrl != null && webUrl.isNotEmpty) return webUrl;
      }
      
      final envValue = dotenv.env['API_BASE_URL'];
      final result = envValue ?? 'http://10.0.2.2:8000/api/v1';
      return result;
    } catch (e) {
      // Web版では.envが読み込めないため、プラットフォーム別のデフォルト値を返す
      if (kIsWeb) {
        return 'http://localhost:8000/api/v1';
      }
      return 'http://10.0.2.2:8000/api/v1'; // Android用デフォルト
    }
  }

  // TEST_MODEに統合（DEBUG_MODEは廃止）
  static bool get testMode {
    const fromDefine = String.fromEnvironment('TEST_MODE');
    if (fromDefine.isNotEmpty) return fromDefine.toLowerCase() == 'true';
    
    // dart-defineビルドの場合は.envが初期化されていない可能性があるため
    // try-catchで安全にアクセス
    try {
      final envValue = dotenv.env['TEST_MODE'];
      final result = envValue?.toLowerCase() == 'true';
      return result;
    } catch (e) {
      if (kDebugMode) print('[AppConfig] TEST_MODE error: $e');
      return false; // エラー時はfalseを返す
    }
  }

  // 後方互換性のためのエイリアス（削除予定）
  @Deprecated('Use testMode instead')
  static bool get debugMode => testMode;

  // ハートビート設定は UserSettingsModel で管理
  // 削除予定: heartbeatNormalSeconds, heartbeatEmergencySeconds

  // Firebase設定（--dart-define対応）
  static String get firebaseApiKey {
    const fromDefine = String.fromEnvironment('FIREBASE_API_KEY');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    try {
      // Web platform uses different API key
      if (kIsWeb) {
        final webKey = dotenv.env['FIREBASE_WEB_API_KEY'];
        if (webKey != null && webKey.isNotEmpty) return webKey;
      }
      return dotenv.env['FIREBASE_API_KEY'] ?? '';
    } catch (e) {
      return '';
    }
  }

  static String get firebaseAuthDomain {
    const fromDefine = String.fromEnvironment('FIREBASE_AUTH_DOMAIN');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    try {
      return dotenv.env['FIREBASE_AUTH_DOMAIN'] ?? '';
    } catch (e) {
      return '';
    }
  }

  static String get firebaseProjectId {
    const fromDefine = String.fromEnvironment('FIREBASE_PROJECT_ID');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    try {
      return dotenv.env['FIREBASE_PROJECT_ID'] ?? '';
    } catch (e) {
      return '';
    }
  }

  static String get firebaseStorageBucket {
    const fromDefine = String.fromEnvironment('FIREBASE_STORAGE_BUCKET');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    try {
      return dotenv.env['FIREBASE_STORAGE_BUCKET'] ?? '';
    } catch (e) {
      return '';
    }
  }

  static String get firebaseMessagingSenderId {
    const fromDefine = String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    try {
      return dotenv.env['FIREBASE_MESSAGING_SENDER_ID'] ?? '';
    } catch (e) {
      return '';
    }
  }

  static String get firebaseAppId {
    const fromDefine = String.fromEnvironment('FIREBASE_APP_ID');
    if (fromDefine.isNotEmpty) return fromDefine;
    
    try {
      return dotenv.env['FIREBASE_APP_ID'] ?? '';
    } catch (e) {
      return '';
    }
  }
}
