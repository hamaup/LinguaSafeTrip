import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/core/widgets/modern_app_bar.dart';
import 'package:frontend/l10n/app_localizations.dart';

class ShelterSearchScreen extends StatefulWidget {
  final List<DisasterProposalModel> shelters;
  final LatLng? userLocation;

  const ShelterSearchScreen({
    super.key,
    required this.shelters,
    this.userLocation,
  });

  @override
  State<ShelterSearchScreen> createState() => _ShelterSearchScreenState();
}

class _ShelterSearchScreenState extends State<ShelterSearchScreen> {
  GoogleMapController? _controller;
  Set<Marker> _markers = {};
  int _selectedShelterIndex = -1;
  final Map<int, BitmapDescriptor> _markerIcons = {};

  @override
  void initState() {
    super.initState();
    _sortSheltersByDistance();
    _initializeMarkers();
  }

  void _sortSheltersByDistance() {
    if (widget.userLocation != null) {
      widget.shelters.sort((a, b) {
        final distanceA = _calculateDistance(a) ?? double.infinity;
        final distanceB = _calculateDistance(b) ?? double.infinity;
        return distanceA.compareTo(distanceB);
      });
    }
  }

  Future<void> _initializeMarkers() async {
    await _createNumberedMarkerIcons();
    _createMarkers();
  }

  Future<void> _createNumberedMarkerIcons() async {
    for (int i = 0; i < widget.shelters.length; i++) {
      final icon = await _createNumberedMarkerIcon(i + 1);
      _markerIcons[i] = icon;
    }
  }

  Future<BitmapDescriptor> _createNumberedMarkerIcon(int number) async {
    final ui.PictureRecorder pictureRecorder = ui.PictureRecorder();
    final Canvas canvas = Canvas(pictureRecorder);
    final Paint paint = Paint()..color = Colors.red;
    final Paint borderPaint = Paint()
      ..color = Colors.white
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    const double radius = 20;
    const double size = radius * 2;

    // 赤い円を描画
    canvas.drawCircle(const Offset(radius, radius), radius, paint);
    // 白い境界線を描画
    canvas.drawCircle(const Offset(radius, radius), radius, borderPaint);

    // 番号テキストを描画
    final textPainter = TextPainter(
      text: TextSpan(
        text: number.toString(),
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();
    final textOffset = Offset(
      radius - (textPainter.width / 2),
      radius - (textPainter.height / 2),
    );
    textPainter.paint(canvas, textOffset);

    final ui.Image markerAsImage = await pictureRecorder
        .endRecording()
        .toImage(size.toInt(), size.toInt());

    final ByteData? byteData = await markerAsImage.toByteData(
      format: ui.ImageByteFormat.png,
    );

    final Uint8List uint8List = byteData!.buffer.asUint8List();
    return BitmapDescriptor.bytes(uint8List);
  }

  void _createMarkers() {
    final markers = <Marker>{};
    
    // 避難所のマーカーを作成（番号付きアイコンを使用）
    for (int i = 0; i < widget.shelters.length; i++) {
      final shelter = widget.shelters[i];
      if (shelter.shelterLatitude != null && shelter.shelterLongitude != null) {
        final marker = Marker(
          markerId: MarkerId('shelter_$i'),
          position: LatLng(
            shelter.shelterLatitude!,
            shelter.shelterLongitude!,
          ),
          infoWindow: InfoWindow(
            title: '${i + 1}. ${shelter.shelterName ?? '避難所 ${i + 1}'}',
            snippet: shelter.shelterStatus ?? '詳細情報は下のリストをご確認ください',
          ),
          icon: _markerIcons[i] ?? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          onTap: () {
            setState(() {
              _selectedShelterIndex = i;
            });
          },
        );
        markers.add(marker);
      }
    }

    // ユーザーの現在位置のマーカーを追加
    if (widget.userLocation != null) {
      markers.add(
        Marker(
          markerId: const MarkerId('user_location'),
          position: widget.userLocation!,
          infoWindow: const InfoWindow(
            title: 'あなたの現在地',
            snippet: '現在いる場所',
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        ),
      );
    }

    setState(() {
      _markers = markers;
    });
  }

  LatLng get _initialPosition {
    if (widget.userLocation != null) {
      return widget.userLocation!;
    }
    if (widget.shelters.isNotEmpty && 
        widget.shelters.first.shelterLatitude != null &&
        widget.shelters.first.shelterLongitude != null) {
      return LatLng(
        widget.shelters.first.shelterLatitude!,
        widget.shelters.first.shelterLongitude!,
      );
    }
    // デフォルト位置（東京駅）
    return const LatLng(35.6812362, 139.7671248);
  }

  void _focusOnShelter(int index) {
    final shelter = widget.shelters[index];
    if (shelter.shelterLatitude != null && shelter.shelterLongitude != null && _controller != null) {
      _controller!.animateCamera(
        CameraUpdate.newLatLngZoom(
          LatLng(shelter.shelterLatitude!, shelter.shelterLongitude!),
          16.0,
        ),
      );
      setState(() {
        _selectedShelterIndex = index;
      });
    }
  }

  double? _calculateDistance(DisasterProposalModel shelter) {
    if (widget.userLocation == null || 
        shelter.shelterLatitude == null || 
        shelter.shelterLongitude == null) {
      return null;
    }

    // 簡易的な距離計算（実際のアプリでは geolocator パッケージの distanceBetween を使用）
    const double earthRadius = 6371; // km
    final double lat1Rad = widget.userLocation!.latitude * (pi / 180);
    final double lat2Rad = shelter.shelterLatitude! * (pi / 180);
    final double deltaLatRad = (shelter.shelterLatitude! - widget.userLocation!.latitude) * (pi / 180);
    final double deltaLngRad = (shelter.shelterLongitude! - widget.userLocation!.longitude) * (pi / 180);

    final double a = sin(deltaLatRad / 2) * sin(deltaLatRad / 2) +
        cos(lat1Rad) * cos(lat2Rad) *
        sin(deltaLngRad / 2) * sin(deltaLngRad / 2);
    final double c = 2 * asin(sqrt(a));

    return earthRadius * c;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: ModernAppBar(
        title: AppLocalizations.of(context)?.nearbyShelters ?? '近くの避難所',
        subtitle: AppLocalizations.of(context)?.shelterCount(widget.shelters.length) ?? '${widget.shelters.length}件の避難所',
        backgroundColor: Colors.red[700],
        leading: const Icon(Icons.arrow_back, color: Colors.white),
        onLeadingPressed: () => context.go('/timeline'),
        actions: [
          ModernAppBarAction(
            icon: Icons.my_location,
            onPressed: () {
              if (widget.userLocation != null && _controller != null) {
                _controller!.animateCamera(
                  CameraUpdate.newLatLngZoom(widget.userLocation!, 14.0),
                );
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // 地図表示エリア
          Expanded(
            flex: 3,
            child: GoogleMap(
              initialCameraPosition: CameraPosition(
                target: _initialPosition,
                zoom: 14.0,
              ),
              markers: _markers,
              onMapCreated: (GoogleMapController controller) {
                _controller = controller;
              },
              myLocationEnabled: true,
              myLocationButtonEnabled: false, // カスタムボタンを使用
              zoomControlsEnabled: true,
              mapToolbarEnabled: true,
              compassEnabled: true,
              rotateGesturesEnabled: true,
              scrollGesturesEnabled: true,
              tiltGesturesEnabled: true,
              zoomGesturesEnabled: true,
              mapType: MapType.normal,
            ),
          ),
          
          // 避難所リスト
          Expanded(
            flex: 2,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(
                  top: BorderSide(color: Colors.grey[300]!, width: 1),
                ),
              ),
              child: widget.shelters.isEmpty
                  ? const Center(
                      child: Text(
                        '近くに避難所が見つかりませんでした',
                        style: TextStyle(fontSize: 16, color: Colors.grey),
                      ),
                    )
                  : ListView.builder(
                      itemCount: widget.shelters.length,
                      itemBuilder: (context, index) {
                        final shelter = widget.shelters[index];
                        final distance = _calculateDistance(shelter);
                        final isSelected = _selectedShelterIndex == index;
                        
                        return Card(
                          margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          color: isSelected ? Colors.red[50] : null,
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: Colors.red[700],
                              child: Text(
                                '${index + 1}',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            title: Text(
                              shelter.shelterName ?? '避難所 ${index + 1}',
                              style: TextStyle(
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                if (shelter.shelterStatus != null)
                                  Text(
                                    '状態: ${shelter.shelterStatus}',
                                    style: const TextStyle(fontSize: 12),
                                  ),
                                if (distance != null)
                                  Text(
                                    '距離: ${distance.toStringAsFixed(1)} km',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.blue[700],
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                              ],
                            ),
                            trailing: const Icon(Icons.location_on, color: Colors.red),
                            onTap: () => _focusOnShelter(index),
                          ),
                        );
                      },
                    ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }
}