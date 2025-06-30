import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:flutter/foundation.dart';

part 'alert_detail_model.freezed.dart';
part 'alert_detail_model.g.dart';

@freezed
class AlertDetailModel with _$AlertDetailModel {
  const factory AlertDetailModel({
    required String title,
    required String body,
    required List<DisasterProposalModel> disasterProposals,
  }) = _AlertDetailModel;

  factory AlertDetailModel.fromJson(Map<String, dynamic> json) =>
      _$AlertDetailModelFromJson(json);
}

@freezed
class DisasterProposalModel with _$DisasterProposalModel {
  const factory DisasterProposalModel({
    required String id,
    @JsonKey(name: 'type') required String proposalType,
    required String content,
    required DateTime timestamp,
    @JsonKey(name: 'alertLevel') required String alertLevel,
    String? sourceName,
    String? sourceUrl,
    String? shelterName,
    String? shelterStatus,
    double? shelterLatitude,
    double? shelterLongitude,
    Map<String, dynamic>? actionData,
  }) = _DisasterProposalModel;

  factory DisasterProposalModel.fromJson(Map<String, dynamic> json) =>
      _$DisasterProposalModelFromJson(json);
}
