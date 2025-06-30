import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:go_router/go_router.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/core/widgets/base_shelter_map.dart';
import 'package:url_launcher/url_launcher.dart';

enum ShelterMapDisplayMode { single, multiple }

class ShelterMapWidget extends StatelessWidget {
  final List<DisasterProposalModel> shelters;
  final ShelterMapDisplayMode mode;
  final LatLng? userLocation;
  final bool showDetailsPanel;
  final bool showNavigationControls;
  final bool showShelterCount;
  final double height;
  final double initialZoom;
  final bool showMyLocationButton;
  final bool showZoomControls;

  const ShelterMapWidget({
    super.key,
    required this.shelters,
    this.mode = ShelterMapDisplayMode.multiple,
    this.userLocation,
    this.showDetailsPanel = false,
    this.showNavigationControls = false,
    this.showShelterCount = false,
    this.height = 300,
    this.initialZoom = 14,
    this.showMyLocationButton = false,
    this.showZoomControls = false,
  });

  /// Single shelter display factory
  factory ShelterMapWidget.single({
    Key? key,
    required DisasterProposalModel shelter,
    bool showDetailsPanel = true,
  }) {
    return ShelterMapWidget(
      key: key,
      shelters: [shelter],
      mode: ShelterMapDisplayMode.single,
      showDetailsPanel: showDetailsPanel,
      height: 250,
      initialZoom: 15,
      showMyLocationButton: true,
      showZoomControls: true,
    );
  }

  /// Multiple shelters display factory
  factory ShelterMapWidget.multiple({
    Key? key,
    required List<DisasterProposalModel> shelters,
    LatLng? userLocation,
    bool showNavigationControls = true,
    bool showShelterCount = true,
  }) {
    return ShelterMapWidget(
      key: key,
      shelters: shelters,
      mode: ShelterMapDisplayMode.multiple,
      userLocation: userLocation,
      showNavigationControls: showNavigationControls,
      showShelterCount: showShelterCount,
      height: 300,
      initialZoom: 14,
    );
  }

  @override
  Widget build(BuildContext context) {
    // Check if we have valid shelters
    final validShelters = shelters.where((shelter) =>
        shelter.shelterLatitude != null && shelter.shelterLongitude != null).toList();
    
    if (validShelters.isEmpty) {
      return const SizedBox.shrink();
    }

    if (mode == ShelterMapDisplayMode.single) {
      return _buildSingleShelterMap(context, validShelters.first);
    } else {
      return _buildMultipleShelterMap(context, validShelters);
    }
  }

  Widget _buildSingleShelterMap(BuildContext context, DisasterProposalModel shelter) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.red.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.home, color: Colors.red, size: 24),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.location_on, color: Colors.grey, size: 20),
              ],
            ),
          ),
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16.0),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8.0),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: BaseShelterMap(
              shelters: [shelter],
              height: height,
              initialZoom: initialZoom,
              showMyLocationButton: showMyLocationButton,
              showZoomControls: showZoomControls,
              showMapToolbar: true,
              showCompass: true,
              enableGestures: true,
              borderRadius: BorderRadius.circular(8.0),
            ),
          ),
          if (showDetailsPanel && (shelter.shelterName != null || shelter.shelterStatus != null))
            _buildDetailsPanel(context, shelter),
        ],
      ),
    );
  }

  Widget _buildMultipleShelterMap(BuildContext context, List<DisasterProposalModel> validShelters) {
    return BaseShelterMap(
      shelters: validShelters,
      userLocation: userLocation,
      height: height,
      initialZoom: initialZoom,
      showMyLocationButton: showMyLocationButton,
      showZoomControls: showZoomControls,
      showMapToolbar: false,
      showCompass: true,
      enableGestures: true,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      borderRadius: BorderRadius.circular(12),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.1),
          blurRadius: 8,
          offset: const Offset(0, 2),
        ),
      ],
      overlayWidget: _buildOverlayControls(context, validShelters),
    );
  }

  Widget _buildDetailsPanel(BuildContext context, DisasterProposalModel shelter) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (shelter.shelterName != null) ...[
            Row(
              children: [
                const Icon(Icons.home_work, color: Colors.grey, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    shelter.shelterName!,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],
          if (shelter.shelterStatus != null) ...[
            Row(
              children: [
                Icon(
                  shelter.shelterStatus!.toLowerCase().contains('available') ||
                          shelter.shelterStatus!.contains('利用可能')
                      ? Icons.check_circle
                      : Icons.info,
                  color: shelter.shelterStatus!.toLowerCase().contains('available') ||
                          shelter.shelterStatus!.contains('利用可能')
                      ? Colors.green
                      : Colors.orange,
                  size: 18,
                ),
                const SizedBox(width: 8),
                Text(
                  shelter.shelterStatus!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: shelter.shelterStatus!.toLowerCase().contains('available') ||
                            shelter.shelterStatus!.contains('利用可能')
                        ? Colors.green
                        : Colors.orange,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget? _buildOverlayControls(BuildContext context, List<DisasterProposalModel> validShelters) {
    if (!showShelterCount && !showNavigationControls) return null;

    return Stack(
      children: [
        if (showShelterCount)
          Positioned(
            top: 8,
            left: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.1),
                    blurRadius: 4,
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.home, color: Colors.red, size: 16),
                  const SizedBox(width: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      '${validShelters.length}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        if (showNavigationControls)
          Positioned(
            bottom: 8,
            right: 8,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                FloatingActionButton.small(
                  heroTag: 'open_google_maps_${validShelters.hashCode}',
                  backgroundColor: Colors.green,
                  onPressed: () => _openInGoogleMaps(validShelters),
                  child: const Icon(Icons.map, color: Colors.white),
                ),
                const SizedBox(width: 8),
                FloatingActionButton.small(
                  heroTag: 'expand_map_${validShelters.hashCode}',
                  backgroundColor: Theme.of(context).primaryColor,
                  onPressed: () {
                    context.goNamed(
                      AppRoutes.shelterSearch,
                      extra: {
                        'shelters': validShelters.map((s) => s.toJson()).toList(),
                        'userLocation': userLocation,
                      },
                    );
                  },
                  child: const Icon(Icons.fullscreen, color: Colors.white),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Future<void> _openInGoogleMaps(List<DisasterProposalModel> shelters) async {
    if (shelters.isEmpty) return;
    
    final firstShelter = shelters.first;
    if (firstShelter.shelterLatitude == null || firstShelter.shelterLongitude == null) return;
    
    final googleMapsUrl = Uri.parse(
      'https://www.google.com/maps/search/?api=1&query=${firstShelter.shelterLatitude},${firstShelter.shelterLongitude}'
    );
    
    final googleMapsAppUrl = Uri.parse(
      'comgooglemaps://?q=${firstShelter.shelterLatitude},${firstShelter.shelterLongitude}&zoom=14'
    );
    
    try {
      if (await canLaunchUrl(googleMapsAppUrl)) {
        await launchUrl(googleMapsAppUrl);
      } else if (await canLaunchUrl(googleMapsUrl)) {
        await launchUrl(googleMapsUrl, mode: LaunchMode.externalApplication);
      }
    } catch (e) {
      // Silently fail
    }
  }
}