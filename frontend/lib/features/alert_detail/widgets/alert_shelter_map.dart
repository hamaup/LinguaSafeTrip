import 'package:flutter/material.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/core/widgets/shelter_map_widget.dart';

class AlertShelterMapWidget extends StatelessWidget {
  final DisasterProposalModel proposal;

  const AlertShelterMapWidget({
    super.key,
    required this.proposal,
  });

  @override
  Widget build(BuildContext context) {
    return ShelterMapWidget.single(
      shelter: proposal,
      showDetailsPanel: true,
    );
  }
}