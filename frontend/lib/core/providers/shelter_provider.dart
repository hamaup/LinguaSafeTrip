import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/core/services/timeline_storage_service.dart';

part 'shelter_provider.freezed.dart';
part 'shelter_provider.g.dart';

@freezed
class ShelterState with _$ShelterState {
  const factory ShelterState({
    @Default({}) Map<String, Map<String, dynamic>> shelterDataCache,
    @Default({}) Map<String, String> chatIdToShelterDataId,
    @Default({}) Map<String, List<DisasterProposalModel>> processedShelters,
    @Default(false) bool isLoading,
    String? errorMessage,
  }) = _ShelterState;
}

@Riverpod(keepAlive: true)
class Shelter extends _$Shelter {
  @override
  ShelterState build() {
    // アプリ起動時に保存されたデータを読み込む
    _loadSavedData();
    return const ShelterState();
  }

  /// 保存されたデータを読み込む
  Future<void> _loadSavedData() async {
    try {
      final savedShelterCache = await TimelineStorageService.loadShelterDataCache();
      final savedChatToShelterMapping = await TimelineStorageService.loadChatToShelterMapping();
      
      if (savedShelterCache.isNotEmpty || savedChatToShelterMapping.isNotEmpty) {
        state = state.copyWith(
          shelterDataCache: savedShelterCache,
          chatIdToShelterDataId: savedChatToShelterMapping,
        );
      }
    } catch (e) {
      if (kDebugMode) {
        if (kDebugMode) print('[ShelterProvider] Error loading saved data: $e');
      }
    }
  }

  /// データを保存
  Future<void> _saveData() async {
    try {
      await Future.wait([
        TimelineStorageService.saveShelterDataCache(state.shelterDataCache),
        TimelineStorageService.saveChatToShelterMapping(state.chatIdToShelterDataId),
      ]);
    } catch (e) {
      if (kDebugMode) {
        if (kDebugMode) print('[ShelterProvider] Error saving data: $e');
      }
    }
  }

  /// 避難所データを処理して保存
  Future<List<DisasterProposalModel>> preprocessShelterData(List<dynamic> shelterCards) async {
    if (shelterCards.isEmpty) return [];

    try {
      state = state.copyWith(isLoading: true);

      final List<DisasterProposalModel> processedShelters = [];
      final Map<String, Map<String, dynamic>> newShelterCache = Map.from(state.shelterDataCache);

      for (final card in shelterCards) {
        if (card is Map<String, dynamic>) {
          final cardType = card['card_type'] as String?;
          
          if (cardType == 'shelter_search' && card.containsKey('shelters')) {
            final shelters = card['shelters'] as List<dynamic>? ?? [];
            
            for (final shelter in shelters) {
              if (shelter is Map<String, dynamic>) {
                try {
                  final shelterModel = _convertToDisasterProposalModel(shelter);
                  processedShelters.add(shelterModel);
                  
                  // キャッシュに保存
                  final shelterHash = _generateShelterDataHash(shelter);
                  newShelterCache[shelterHash] = shelter;
                } catch (e) {
                  if (kDebugMode) {
                    if (kDebugMode) print('[ShelterProvider] Error processing shelter: $e');
                  }
                }
              }
            }
          }
        }
      }

      // 状態を更新
      final shelterDataId = 'shelter_${DateTime.now().millisecondsSinceEpoch}';
      state = state.copyWith(
        shelterDataCache: newShelterCache,
        processedShelters: {
          ...state.processedShelters,
          shelterDataId: processedShelters,
        },
        isLoading: false,
      );

      // データを保存
      await _saveData();

      return processedShelters;

    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );

      if (kDebugMode) {
        if (kDebugMode) print('[ShelterProvider] Error preprocessing shelter data: $e');
      }
      rethrow;
    }
  }

  /// チャットIDと避難所データIDのマッピングを設定
  void setChatToShelterMapping(String chatId, String shelterDataId) {
    state = state.copyWith(
      chatIdToShelterDataId: {
        ...state.chatIdToShelterDataId,
        chatId: shelterDataId,
      },
    );
    _saveData();
  }

  /// チャットIDから避難所データを取得
  List<DisasterProposalModel>? getSheltersForChat(String chatId) {
    final shelterDataId = state.chatIdToShelterDataId[chatId];
    if (shelterDataId != null) {
      return state.processedShelters[shelterDataId];
    }
    return null;
  }

  /// 避難所データハッシュを生成
  String _generateShelterDataHash(Map<String, dynamic> shelterData) {
    try {
      // 位置情報とIDを基にハッシュを生成
      final locationData = shelterData['location'] as Map<String, dynamic>?;
      final dataField = shelterData['data'] as Map<String, dynamic>?;
      
      final lat = locationData?['latitude']?.toString() ?? 
                  dataField?['latitude']?.toString() ?? 
                  shelterData['shelter_latitude']?.toString() ?? '0';
      
      final lng = locationData?['longitude']?.toString() ?? 
                  dataField?['longitude']?.toString() ?? 
                  shelterData['shelter_longitude']?.toString() ?? '0';
      
      final name = shelterData['title']?.toString() ?? 
                   shelterData['name']?.toString() ?? 
                   shelterData['shelter_name']?.toString() ?? 'unknown';
      
      final hashSource = '${name}_${lat}_${lng}';
      return hashSource.hashCode.toString();
    } catch (e) {
      if (kDebugMode) {
        if (kDebugMode) print('[ShelterProvider] Error generating hash: $e');
      }
      return DateTime.now().millisecondsSinceEpoch.toString();
    }
  }

  /// 避難所データをDisasterProposalModelに変換
  DisasterProposalModel _convertToDisasterProposalModel(Map<String, dynamic> shelterData) {
    // バックエンドの標準形式 location オブジェクトを優先
    final locationData = shelterData['location'] as Map<String, dynamic>?;
    
    // 位置情報をlocationオブジェクトから取得（バックエンド標準形式）
    final latitude = locationData?['latitude'] as num?;
    final longitude = locationData?['longitude'] as num?;
    
    // デバッグログ: 位置情報の取得状況を確認
    if (kDebugMode) print('[ShelterProvider] Processing shelter: ${shelterData['title'] ?? shelterData['name'] ?? 'Unknown'}');
    if (kDebugMode) print('[ShelterProvider] Location data: $locationData');
    if (kDebugMode) print('[ShelterProvider] Extracted - lat: $latitude, lng: $longitude');
    
    // 位置情報が取得できない場合の警告
    if (latitude == null || longitude == null) {
      if (kDebugMode) print('[ShelterProvider] ⚠️ Missing location data for shelter: ${shelterData['title'] ?? 'Unknown'}');
      if (kDebugMode) print('[ShelterProvider] Full shelter data: $shelterData');
    }
    
    return DisasterProposalModel(
      id: shelterData['card_id']?.toString() ?? 
          shelterData['id']?.toString() ?? 
          'unknown_${DateTime.now().millisecondsSinceEpoch}',
      proposalType: 'evacuation_shelter',
      content: shelterData['title']?.toString() ?? 
               shelterData['name']?.toString() ?? 
               shelterData['shelter_name']?.toString() ?? 
               'Unknown Shelter',
      timestamp: DateTime.now(),
      alertLevel: 'warning',
      shelterName: shelterData['title']?.toString() ?? 
                   shelterData['name']?.toString() ?? 
                   shelterData['shelter_name']?.toString() ?? 
                   'Unknown Shelter',
      shelterStatus: shelterData['status']?.toString() ?? 'Available',
      shelterLatitude: latitude?.toDouble(),
      shelterLongitude: longitude?.toDouble(),
      actionData: {
        'address': shelterData['address']?.toString() ?? 
                   shelterData['shelter_address']?.toString() ?? '',
        'shelter_type': shelterData['shelter_type']?.toString() ?? '',
        'capacity': shelterData['capacity'] ?? 0,
        'distance_km': shelterData['distance_km'] ?? 0.0,
        'phone': shelterData['phone']?.toString() ?? '',
        'facilities': shelterData['facilities'] ?? [],
      },
    );
  }

  /// 避難所データをクリア
  void clearShelterData() {
    state = state.copyWith(
      shelterDataCache: {},
      chatIdToShelterDataId: {},
      processedShelters: {},
    );
    _saveData();
  }

  /// 特定のチャットIDのマッピングを削除
  void removeChatMapping(String chatId) {
    final newMapping = Map<String, String>.from(state.chatIdToShelterDataId);
    newMapping.remove(chatId);
    
    state = state.copyWith(chatIdToShelterDataId: newMapping);
    _saveData();
  }

  /// エラーをクリア
  void clearError() {
    state = state.copyWith(errorMessage: null);
  }

  /// 統計情報を取得
  Map<String, int> getStatistics() {
    return {
      'total_shelters_cached': state.shelterDataCache.length,
      'total_chat_mappings': state.chatIdToShelterDataId.length,
      'total_processed_groups': state.processedShelters.length,
    };
  }

  /// デバッグ情報を取得
  Map<String, dynamic> getDebugInfo() {
    return {
      'shelter_cache_keys': state.shelterDataCache.keys.toList(),
      'chat_mappings': state.chatIdToShelterDataId,
      'processed_shelter_ids': state.processedShelters.keys.toList(),
      'statistics': getStatistics(),
    };
  }
}