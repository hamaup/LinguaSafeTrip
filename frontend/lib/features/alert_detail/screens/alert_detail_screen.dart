import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/features/alert_detail/widgets/alert_shelter_map.dart';
import 'package:intl/intl.dart';

class AlertDetailScreen extends StatelessWidget {
  final AlertDetailModel alertDetails;

  const AlertDetailScreen({
    super.key,
    required this.alertDetails,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(alertDetails.title),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/timeline'),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              alertDetails.body,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            ...alertDetails.disasterProposals.map((proposal) => _buildProposalCard(proposal, context)),
          ],
        ),
      ),
    );
  }

  Widget _buildProposalCard(DisasterProposalModel proposal, BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              proposal.proposalType,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(proposal.content),
            const SizedBox(height: 12),
            Text(
              '警戒レベル: ${proposal.alertLevel}',
              style: Theme.of(context).textTheme.labelLarge,
            ),
            Text(
              '発表時刻: ${DateFormat('yyyy/MM/dd HH:mm').format(proposal.timestamp)}',
              style: Theme.of(context).textTheme.labelMedium,
            ),
            if (proposal.shelterName != null) ...[
              const SizedBox(height: 8),
              Text(
                '避難所: ${proposal.shelterName}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
            // 避難所の位置情報がある場合は地図を表示
            if (proposal.shelterLatitude != null && proposal.shelterLongitude != null) ...[
              const SizedBox(height: 16),
              AlertShelterMapWidget(proposal: proposal),
            ],
          ],
        ),
      ),
    );
  }
}
