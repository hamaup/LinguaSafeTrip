import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/core/widgets/shelter_map_widget.dart';

class TimelineShelterMapWidget extends StatelessWidget {
  final List<dynamic> shelters;
  final LatLng? userLocation;
  final List<DisasterProposalModel>? preProcessedShelters;

  const TimelineShelterMapWidget({
    super.key,
    required this.shelters,
    this.userLocation,
    this.preProcessedShelters,
  });

  @override
  Widget build(BuildContext context) {
    // 事前処理済みデータがあれば使用、なければ変換処理
    final shelterModels = preProcessedShelters ?? _convertSheltersToModels(shelters);
    
    return ShelterMapWidget.multiple(
      shelters: shelterModels,
      userLocation: userLocation,
      showNavigationControls: true,
      showShelterCount: true,
    );
  }

  /// 避難所データをモデルに変換（フォールバック用）
  List<DisasterProposalModel> _convertSheltersToModels(List<dynamic> shelters) {
    // Converting shelters to models
    
    return shelters.map((shelterData) {
      // Processing shelter data
      
      // バックエンドの標準形式 location オブジェクトを優先
      final locationData = shelterData['location'] as Map<String, dynamic>?;
      final latitude = locationData?['latitude'] as num?;
      final longitude = locationData?['longitude'] as num?;
      
      // Extracted coordinates
      
      return DisasterProposalModel(
        id: shelterData['card_id'] ?? shelterData['id'] ?? 'unknown',
        proposalType: 'evacuation_shelter',
        content: '${shelterData['title'] ?? shelterData['name'] ?? shelterData['shelter_name'] ?? 'Unknown'}',
        timestamp: DateTime.now(),
        alertLevel: 'warning',
        shelterName: shelterData['title'] ?? shelterData['name'] ?? shelterData['shelter_name'] ?? 'Unknown Shelter',
        shelterStatus: shelterData['status'] ?? 'Available',
        shelterLatitude: latitude?.toDouble(),
        shelterLongitude: longitude?.toDouble(),
        actionData: {
          'address': shelterData['address'] ?? shelterData['shelter_address'] ?? '',
          'shelter_type': shelterData['shelter_type'] ?? '',
          'capacity': shelterData['capacity'] ?? 0,
          'distance_km': shelterData['distance_km'] ?? 0.0,
        },
      );
    }).toList();
  }
}