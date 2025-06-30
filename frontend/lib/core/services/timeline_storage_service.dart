import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:flutter/foundation.dart';

class TimelineStorageService {
  static const String _timelineKey = 'app_timeline_items_v1';
  static const String _shelterDataCacheKey = 'app_shelter_data_cache_v1';
  static const String _chatToShelterMappingKey = 'app_chat_to_shelter_mapping_v1';
  static const int _maxStoredItems = 100; // 最大保存件数
  
  /// タイムラインアイテムを保存
  static Future<void> saveTimelineItems(List<TimelineItemModel> items) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      // 最新の_maxStoredItems件のみ保存（古いものは削除）
      final itemsToSave = items.length > _maxStoredItems 
          ? items.sublist(items.length - _maxStoredItems)
          : items;
      
      final jsonList = itemsToSave.map((item) => item.toJson()).toList();
      final jsonString = jsonEncode(jsonList);
      
      await prefs.setString(_timelineKey, jsonString);
        // Saved ${itemsToSave.length} timeline items');
    } catch (e) {
        // Error saving timeline items: $e');
    }
  }
  
  /// タイムラインアイテムを読み込み
  static Future<List<TimelineItemModel>> loadTimelineItems() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = prefs.getString(_timelineKey);
      
      if (jsonString == null || jsonString.isEmpty) {
        // No saved timeline items found');
        return [];
      }
      
      final jsonList = jsonDecode(jsonString) as List<dynamic>;
      final items = jsonList
          .map((json) => TimelineItemModel.fromJson(json as Map<String, dynamic>))
          .toList();
      
        // Loaded ${items.length} timeline items');
      return items;
    } catch (e) {
        // Error loading timeline items: $e');
      return [];
    }
  }
  
  /// タイムラインアイテムをクリア
  static Future<void> clearTimelineItems() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_timelineKey);
        // Timeline items cleared');
    } catch (e) {
        // Error clearing timeline items: $e');
    }
  }
  
  /// アプリ起動時のクリーンアップ（古いチャットメッセージを削除）
  static Future<List<TimelineItemModel>> cleanupOldItems(List<TimelineItemModel> items) async {
    try {
      final now = DateTime.now();
      final cutoffTime = now.subtract(const Duration(days: 7)); // 7日以上前のアイテムを削除
      
      final filteredItems = items.where((item) {
        // チャットメッセージは7日で削除
        if (item.type == TimelineItemType.chat) {
          return item.timestamp?.isAfter(cutoffTime) ?? false;
        }
        // 提案とアラートは保持
        return true;
      }).toList();
      
        // Cleaned up ${items.length - filteredItems.length} old items');
      return filteredItems;
    } catch (e) {
        // Error cleaning up old items: $e');
      return items;
    }
  }
  
  /// 避難所データキャッシュを保存
  static Future<void> saveShelterDataCache(Map<String, Map<String, dynamic>> shelterDataCache) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = jsonEncode(shelterDataCache);
      await prefs.setString(_shelterDataCacheKey, jsonString);
        // Saved ${shelterDataCache.length} shelter data entries');
    } catch (e) {
        // Error saving shelter data cache: $e');
    }
  }
  
  /// 避難所データキャッシュを読み込み
  static Future<Map<String, Map<String, dynamic>>> loadShelterDataCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = prefs.getString(_shelterDataCacheKey);
      
      if (jsonString == null || jsonString.isEmpty) {
        // No saved shelter data cache found');
        return {};
      }
      
      final jsonData = jsonDecode(jsonString) as Map<String, dynamic>;
      final result = jsonData.map((key, value) => MapEntry(key, value as Map<String, dynamic>));
      
        // Loaded ${result.length} shelter data entries');
      return result;
    } catch (e) {
        // Error loading shelter data cache: $e');
      return {};
    }
  }
  
  /// チャットIDから避難所データIDへのマッピングを保存
  static Future<void> saveChatToShelterMapping(Map<String, String> chatIdToShelterDataId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = jsonEncode(chatIdToShelterDataId);
      await prefs.setString(_chatToShelterMappingKey, jsonString);
        // Saved ${chatIdToShelterDataId.length} chat-to-shelter mappings');
    } catch (e) {
        // Error saving chat-to-shelter mapping: $e');
    }
  }
  
  /// チャットIDから避難所データIDへのマッピングを読み込み
  static Future<Map<String, String>> loadChatToShelterMapping() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = prefs.getString(_chatToShelterMappingKey);
      
      if (jsonString == null || jsonString.isEmpty) {
        // No saved chat-to-shelter mapping found');
        return {};
      }
      
      final jsonData = jsonDecode(jsonString) as Map<String, dynamic>;
      final result = jsonData.map((key, value) => MapEntry(key, value as String));
      
        // Loaded ${result.length} chat-to-shelter mappings');
      return result;
    } catch (e) {
        // Error loading chat-to-shelter mapping: $e');
      return {};
    }
  }
  
  /// 避難所関連データをクリア
  static Future<void> clearShelterData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_shelterDataCacheKey);
      await prefs.remove(_chatToShelterMappingKey);
        // Shelter data cleared');
    } catch (e) {
        // Error clearing shelter data: $e');
    }
  }
}