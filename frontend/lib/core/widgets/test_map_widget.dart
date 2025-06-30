import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter/foundation.dart';

class TestMapWidget extends StatelessWidget {
  const TestMapWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Google Maps Test'),
      ),
      body: Center(
        child: Container(
          height: 400,
          margin: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            border: Border.all(color: Colors.blue, width: 2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: GoogleMap(
              initialCameraPosition: const CameraPosition(
                target: LatLng(35.6812362, 139.7671248), // Tokyo Station
                zoom: 15,
              ),
              onMapCreated: (GoogleMapController controller) {
                if (kDebugMode) {
                  print('[TestMap] Map created successfully');
                }
              },
              markers: {
                const Marker(
                  markerId: MarkerId('test'),
                  position: LatLng(35.6812362, 139.7671248),
                  infoWindow: InfoWindow(title: 'Test Marker'),
                ),
              },
            ),
          ),
        ),
      ),
    );
  }
}