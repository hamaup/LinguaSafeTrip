import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:frontend/l10n/app_localizations.dart';

class DeviceStatusBar extends ConsumerWidget {
  const DeviceStatusBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final state = ref.watch(deviceStatusProvider);

    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 3, sigmaY: 3),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
          decoration: BoxDecoration(
            color: Theme.of(context).brightness == Brightness.dark
                ? Colors.grey[850]
                : Colors.white.withValues(alpha: 1.0),
            border: Border(
              bottom: BorderSide(
                color: Colors.grey.withValues(alpha: 0.3),
                width: 1,
              ),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatusItem(
            icon: _getConnectivityIcon(state.connectivityStatus),
            text: _getConnectivityText(state.connectivityStatus, l10n),
            context: context,
          ),
          GestureDetector(
            onTap: () => _handleLocationTap(context, ref, state),
            child: _buildStatusItem(
              icon: Icon(
                _getLocationIcon(state.isGpsEnabled, state.isLocationPermissionGranted),
                color: _getLocationColor(state.isGpsEnabled, state.isLocationPermissionGranted),
              ),
              text: _getLocationText(state.isGpsEnabled, state.isLocationPermissionGranted, l10n),
              context: context,
            ),
          ),
          _buildStatusItem(
            icon: Icon(
              Icons.battery_std,
              color: _getBatteryColor(state.batteryLevel),
            ),
            text: '${state.batteryLevel}%',
            context: context,
          ),
          if (state.isBatteryCharging)
            const Icon(Icons.bolt, color: Colors.amber),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusItem({required Icon icon, required String text, required BuildContext context}) {
    return Row(children: [
      icon, 
      const SizedBox(width: 4), 
      Text(
        text,
        style: TextStyle(
          color: Theme.of(context).brightness == Brightness.dark 
              ? Colors.white70 
              : Colors.black87,
        ),
      ),
    ]);
  }

  Icon _getConnectivityIcon(ConnectivityResult status) {
    switch (status) {
      case ConnectivityResult.wifi:
        return const Icon(Icons.wifi);
      case ConnectivityResult.mobile:
        return const Icon(Icons.network_cell);
      case ConnectivityResult.ethernet:
        return const Icon(Icons.settings_ethernet);
      default:
        return const Icon(Icons.signal_wifi_off);
    }
  }

  String _getConnectivityText(ConnectivityResult status, AppLocalizations l10n) {
    switch (status) {
      case ConnectivityResult.wifi:
        return 'Wi-Fi';
      case ConnectivityResult.mobile:
        return l10n.mobile;
      case ConnectivityResult.ethernet:
        return l10n.ethernet;
      default:
        return l10n.offline;
    }
  }

  Color _getBatteryColor(int level) {
    if (level > 70) return Colors.green;
    if (level > 30) return Colors.orange;
    return Colors.red;
  }

  IconData _getLocationIcon(bool gpsEnabled, bool permissionGranted) {
    if (gpsEnabled && permissionGranted) {
      return Icons.gps_fixed; // GPS有効
    } else if (gpsEnabled && !permissionGranted) {
      return Icons.gps_not_fixed; // GPS有効だが許可なし
    } else {
      return Icons.gps_off; // GPS無効
    }
  }

  Color _getLocationColor(bool gpsEnabled, bool permissionGranted) {
    if (gpsEnabled && permissionGranted) {
      return Colors.green; // 完全に有効
    } else if (gpsEnabled && !permissionGranted) {
      return Colors.orange; // GPS有効だが許可なし
    } else {
      return Colors.red; // GPS無効
    }
  }

  String _getLocationText(bool gpsEnabled, bool permissionGranted, AppLocalizations l10n) {
    if (gpsEnabled && permissionGranted) {
      return l10n.gpsEnabled;
    } else if (gpsEnabled && !permissionGranted) {
      return '${l10n.gpsPermissionDenied} 📱'; // タップヒント追加
    } else {
      return l10n.gpsDisabled;
    }
  }

  void _handleLocationTap(BuildContext context, WidgetRef ref, DeviceStatusState state) async {
    // 常に詳細診断を実行
    await ref.read(deviceStatusProvider.notifier).refreshLocationPermissionStatus();
    
    if (state.isGpsEnabled && !state.isLocationPermissionGranted) {
      // GPS有効だが許可なしの場合、許可をリクエスト
      final granted = await ref.read(deviceStatusProvider.notifier).requestLocationPermission();
      
      if (context.mounted) {
        if (granted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('📍 位置情報の許可が有効になりました'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 2),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('❌ 位置情報の許可を有効にしてください\n設定 > アプリ > SafeBeee > 位置情報'),
              backgroundColor: Colors.orange,
              duration: Duration(seconds: 4),
            ),
          );
        }
      }
    } else if (state.isGpsEnabled && state.isLocationPermissionGranted) {
      // 許可済みの場合でも診断情報を表示
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('🔍 位置情報許可の詳細診断を実行しました\nログをご確認ください'),
            backgroundColor: Colors.blue,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('📱 GPS サービスが無効です\n設定で位置情報サービスを有効にしてください'),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 4),
          ),
        );
      }
    }
  }
}
