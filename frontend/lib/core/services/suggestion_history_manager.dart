import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';

/// ユーザーが操作した提案タイプの履歴管理を行うクラス
/// 
/// 改善ポイント：
/// - 永続的ブロックを廃止し、バックエンドの時間ベース制御を尊重
/// - ユーザー明示操作時のみ一時的記録（セッション限定）
/// - バックエンドが唯一の真実源として重複防止を管理
class SuggestionHistoryManager {
  static const String _typeStorageKey = 'temp_session_suggestion_types';
  static const String _typeTimestampKey = 'temp_session_timestamps';
  static const int _maxHistoryCount = 10; // セッション限定なので少なく
  static const Duration _sessionDuration = Duration(hours: 1); // セッション内のみ有効

  /// 表示済み提案タイプリストを取得
  static Future<List<String>> getAcknowledgedSuggestionTypes() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final suggestionTypes = prefs.getStringList(_typeStorageKey) ?? [];
      
      
      // SharedPreferencesの状態をより詳しく確認
      final allKeys = prefs.getKeys();
      
      return suggestionTypes;
    } catch (e) {
      return [];
    }
  }

  /// 表示済み提案IDリストを取得（後方互換性のため保持）
  static Future<List<String>> getAcknowledgedSuggestions() async {
    // 後方互換性のため空のリストを返す
    return [];
  }

  /// 新しい提案タイプを一時的にセッション内記録（1時間限定）
  static Future<void> addAcknowledgedSuggestionType(String suggestionType) async {
    try {
      if (suggestionType.isEmpty) {
        return;
      }

      final prefs = await SharedPreferences.getInstance();
      final acknowledged = await getAcknowledgedSuggestionTypes();
      final timestamps = await _getTypeTimestamps();

      // セッション内での一時的記録（1時間限定）
      if (!acknowledged.contains(suggestionType)) {
        acknowledged.add(suggestionType);
        timestamps[suggestionType] = DateTime.now().toIso8601String();


        // セッション限定なので最新10個のみ保持
        if (acknowledged.length > _maxHistoryCount) {
          acknowledged.removeRange(0, acknowledged.length - _maxHistoryCount);
        }

        await prefs.setStringList(_typeStorageKey, acknowledged);
        await _saveTypeTimestamps(timestamps);
        
      } else {
      }
    } catch (e) {
    }
  }

  /// 新しい提案IDを追加（後方互換性のため保持）
  static Future<void> addAcknowledgedSuggestion(String suggestionId) async {
    // 新しい実装では何もしない（後方互換性のみ）
  }

  /// 複数の提案タイプを一括追加
  static Future<void> addAcknowledgedSuggestionTypes(List<String> suggestionTypes) async {
    if (suggestionTypes.isEmpty) return;

    
    for (final suggestionType in suggestionTypes) {
      await addAcknowledgedSuggestionType(suggestionType);
    }
    
  }

  /// 複数の提案IDを一括追加（後方互換性のため保持）
  static Future<void> addAcknowledgedSuggestions(List<String> suggestionIds) async {
    // 新しい実装では何もしない（後方互換性のみ）
  }

  /// 古いセッション記録をクリア（1時間以上経過したもの）
  static Future<void> cleanupOldSuggestions() async {
    try {
      
      final prefs = await SharedPreferences.getInstance();
      final acknowledged = await getAcknowledgedSuggestionTypes();
      final timestamps = await _getTypeTimestamps();
      final now = DateTime.now();
      
      final toRemove = <String>[];
      
      for (final suggestionType in acknowledged) {
        final timestampStr = timestamps[suggestionType];
        if (timestampStr != null) {
          final timestamp = DateTime.parse(timestampStr);
          if (now.difference(timestamp) > _sessionDuration) {
            toRemove.add(suggestionType);
          }
        } else {
          // タイムスタンプがない場合は古いものとして削除
          toRemove.add(suggestionType);
        }
      }

      if (toRemove.isNotEmpty) {
        
        for (final suggestionType in toRemove) {
          acknowledged.remove(suggestionType);
          timestamps.remove(suggestionType);
        }

        await prefs.setStringList(_typeStorageKey, acknowledged);
        await _saveTypeTimestamps(timestamps);
        
      } else {
      }
    } catch (e) {
    }
  }

  /// 履歴をクリア（デバッグ用）
  static Future<void> clearHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_typeStorageKey);
      await prefs.remove(_typeTimestampKey);
    } catch (e) {
    }
  }

  /// アプリ初期化/再起動時のセッション記録リセット
  static Future<void> resetHistoryForAppRestart() async {
    try {
      await clearHistory();
    } catch (e) {
    }
  }

  /// デバッグ情報を表示
  static Future<void> printDebugInfo() async {
    if (kDebugMode) {
      try {
        final acknowledged = await getAcknowledgedSuggestionTypes();
        final timestamps = await _getTypeTimestamps();
        final legacySuggestions = await getAcknowledgedSuggestions();
        
        print('[SuggestionHistory] Session Records: ${acknowledged.length} types');
        print('[SuggestionHistory] Legacy Records: ${legacySuggestions.length} items');
        print('[SuggestionHistory] Timestamps: ${timestamps.length} entries');
      } catch (e) {
        print('[SuggestionHistory] Error in debug info: $e');
      }
    }
  }

  /// タイプベースタイムスタンプマップを取得
  static Future<Map<String, String>> _getTypeTimestamps() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final timestampData = prefs.getStringList(_typeTimestampKey) ?? [];
      
      final timestamps = <String, String>{};
      for (final entry in timestampData) {
        final parts = entry.split('|');
        if (parts.length == 2) {
          timestamps[parts[0]] = parts[1];
        }
      }
      
      return timestamps;
    } catch (e) {
      return {};
    }
  }

  /// タイプベースタイムスタンプマップを保存
  static Future<void> _saveTypeTimestamps(Map<String, String> timestamps) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final timestampData = timestamps.entries
          .map((entry) => '${entry.key}|${entry.value}')
          .toList();
      
      await prefs.setStringList(_typeTimestampKey, timestampData);
    } catch (e) {
    }
  }
}