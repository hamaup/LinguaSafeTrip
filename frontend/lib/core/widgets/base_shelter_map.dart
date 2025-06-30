import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/core/config/app_config.dart';

/// 共通の避難所マップ機能を提供する基底ウィジェット
class BaseShelterMap extends StatefulWidget {
  final List<DisasterProposalModel> shelters;
  final LatLng? userLocation;
  final double height;
  final double initialZoom;
  final bool showMyLocationButton;
  final bool showZoomControls;
  final bool showMapToolbar;
  final bool showCompass;
  final bool enableGestures;
  final Widget? overlayWidget;
  final EdgeInsetsGeometry? margin;
  final BorderRadius? borderRadius;
  final List<BoxShadow>? boxShadow;

  const BaseShelterMap({
    super.key,
    required this.shelters,
    this.userLocation,
    this.height = 250,
    this.initialZoom = 15.0,
    this.showMyLocationButton = true,
    this.showZoomControls = true,
    this.showMapToolbar = true,
    this.showCompass = true,
    this.enableGestures = true,
    this.overlayWidget,
    this.margin,
    this.borderRadius,
    this.boxShadow,
  });

  @override
  State<BaseShelterMap> createState() => _BaseShelterMapState();
}

class _BaseShelterMapState extends State<BaseShelterMap> with AutomaticKeepAliveClientMixin {
  GoogleMapController? _controller;
  late Set<Marker> _markers;
  bool _isMapInitialized = false;
  static final Map<String, Set<Marker>> _markerCache = {};
  String? _lastCacheKey;
  bool _isDisposed = false;

  @override
  bool get wantKeepAlive => true;

  @override
  void dispose() {
    _isDisposed = true;
    _isMapInitialized = false;
    _controller?.dispose();
    _controller = null;
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _createMarkers();
  }

  void _createMarkers() {
    
    // マーカーキャッシュの活用
    final cacheKey = widget.shelters.map((s) => s.id).join('_');
    if (_lastCacheKey == cacheKey && _markerCache.containsKey(cacheKey)) {
      _markers = _markerCache[cacheKey]!;
      return;
    }
    
    _markers = {};
    
    // 最適化：最大30個のマーカーに制限（ImageReader buffer overflow対策）
    final sheltersToShow = widget.shelters.length > 30 
        ? widget.shelters.take(30).toList()
        : widget.shelters;
    
    for (final shelter in sheltersToShow) {
      
      if (shelter.shelterLatitude != null && shelter.shelterLongitude != null) {
        _markers.add(
          Marker(
            markerId: MarkerId(shelter.id),
            position: LatLng(
              shelter.shelterLatitude!,
              shelter.shelterLongitude!,
            ),
            infoWindow: InfoWindow(
              title: shelter.shelterName ?? 'Shelter',
              snippet: shelter.shelterStatus ?? 'Status Unknown',
            ),
            icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          ),
        );
      } else {
      }
    }
    
    // キャッシュに保存（最大10エントリ）
    if (_markerCache.length >= 10) {
      _markerCache.clear();
    }
    _markerCache[cacheKey] = Set.from(_markers);
    _lastCacheKey = cacheKey;
  }

  LatLng get _initialPosition {
    // ユーザーの位置を優先
    if (widget.userLocation != null) {
      return widget.userLocation!;
    }
    
    // 次に最初の避難所の位置
    if (widget.shelters.isNotEmpty) {
      final firstShelter = widget.shelters.first;
      if (firstShelter.shelterLatitude != null && 
          firstShelter.shelterLongitude != null) {
        return LatLng(
          firstShelter.shelterLatitude!,
          firstShelter.shelterLongitude!,
        );
      }
    }
    
    // デフォルト位置（東京駅）
    return const LatLng(35.6812362, 139.7671248);
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    // 表示可能な避難所がない場合
    // デバッグログを初回のみに制限
    if (kDebugMode && !_isMapInitialized) {
      print('[BaseShelterMap] Building map with ${widget.shelters.length} shelters');
      for (var shelter in widget.shelters) {
        print('[BaseShelterMap] Shelter: ${shelter.shelterName}, lat: ${shelter.shelterLatitude}, lng: ${shelter.shelterLongitude}');
      }
    }
    
    if (widget.shelters.isEmpty || 
        !widget.shelters.any((s) => s.shelterLatitude != null && s.shelterLongitude != null)) {
      if (kDebugMode) {
        print('[BaseShelterMap] No valid shelters found, returning empty widget');
      }
      return const SizedBox.shrink();
    }

    Widget mapWidget;
    
    try {
      
      mapWidget = GoogleMap(
        initialCameraPosition: CameraPosition(
          target: _initialPosition,
          zoom: widget.initialZoom,
        ),
        markers: _markers,
        onMapCreated: (GoogleMapController controller) {
          if (_isMapInitialized || _isDisposed) {
            return;
          }
          _controller = controller;
          _isMapInitialized = true;
          
          // Android specific optimization for ImageReader buffer issue
          if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
            Future.delayed(const Duration(milliseconds: 100), () {
              if (!_isDisposed && _controller != null) {
                _controller!.setMapStyle('[]');
              }
            });
          }
          
          if (kDebugMode) {
            print('[BaseShelterMap] Google Maps initialized successfully');
          }
        },
        myLocationEnabled: true,
        myLocationButtonEnabled: widget.showMyLocationButton,
        zoomControlsEnabled: widget.showZoomControls,
        mapToolbarEnabled: widget.showMapToolbar,
        compassEnabled: widget.showCompass,
        rotateGesturesEnabled: widget.enableGestures,
        scrollGesturesEnabled: widget.enableGestures,
        tiltGesturesEnabled: widget.enableGestures,
        zoomGesturesEnabled: widget.enableGestures,
        minMaxZoomPreference: const MinMaxZoomPreference(10.0, 18.0),
        mapType: MapType.normal,
        // Android optimization to prevent ImageReader buffer overflow
        buildingsEnabled: !kIsWeb && defaultTargetPlatform == TargetPlatform.android ? false : true,
        indoorViewEnabled: false,
        trafficEnabled: false,
      );
    } catch (e) {
      if (kDebugMode) {
        print('[BaseShelterMap] Error creating Google Maps: $e');
        print('[BaseShelterMap] Stack trace: ${StackTrace.current}');
      }
      
      // エラー時のフォールバック表示
      mapWidget = Container(
        height: widget.height,
        decoration: BoxDecoration(
          color: Colors.grey[200],
          borderRadius: widget.borderRadius,
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.map, size: 48, color: Colors.grey[600]),
              const SizedBox(height: 8),
              Text(
                'マップを表示できません',
                style: TextStyle(color: Colors.grey[600]),
              ),
              if (kDebugMode) ...[  
                const SizedBox(height: 4),
                Text(
                  'エラー: ${e.toString()}',
                  style: TextStyle(color: Colors.red[400], fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ],
            ],
          ),
        ),
      );
    }

    // オーバーレイがある場合はStackで包む
    if (widget.overlayWidget != null) {
      mapWidget = Stack(
        children: [
          mapWidget,
          widget.overlayWidget!,
        ],
      );
    }

    // BorderRadiusが指定されている場合はClipRRectで包む
    if (widget.borderRadius != null) {
      mapWidget = ClipRRect(
        borderRadius: widget.borderRadius!,
        child: mapWidget,
      );
    }

    return Container(
      height: widget.height,
      margin: widget.margin,
      decoration: BoxDecoration(
        borderRadius: widget.borderRadius,
        boxShadow: widget.boxShadow,
      ),
      child: mapWidget,
    );
  }

  @override
  void didUpdateWidget(BaseShelterMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 避難所データが変更された場合のみマーカーを再作成
    if (oldWidget.shelters != widget.shelters) {
      _createMarkers();
    }
  }
}