import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:app_settings/app_settings.dart';
import '../providers/settings_provider.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'package:frontend/core/models/emergency_contact_model.dart';
import 'package:frontend/core/models/user_settings_model.dart';
import 'package:frontend/core/services/api_service.dart';
import 'package:frontend/core/utils/device_id_util.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/core/services/suggestion_history_manager.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/core/services/local_notification_service.dart';
import 'package:frontend/core/widgets/modern_app_bar.dart';
import 'package:frontend/core/widgets/emergency_contact_dialog.dart';
import 'package:frontend/core/theme/emergency_theme.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  @override
  void initState() {
    super.initState();
    // 設定が既に読み込まれている場合は再読み込みしない（タイムライン状態保護）
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final settingsState = ref.read(settingsProvider);
      // debugPrint('[SettingsScreen] Checking if need to load settings: currentUserSettings=${settingsState.currentUserSettings != null}, isLoading=${settingsState.isLoading}');
      
      if (settingsState.currentUserSettings == null && !settingsState.isLoading) {
      // debugPrint('[SettingsScreen] Loading initial settings because settings are null');
        ref.read(settingsProvider.notifier).loadInitialSettings();
      } else {
      // debugPrint('[SettingsScreen] Skipping initial settings load to preserve timeline state');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final settingsState = ref.watch(settingsProvider);
    final currentLanguage = settingsState.currentUserSettings?.languageCode;
    
    // タイムライン状態を監視（デバッグ用）
    if (kDebugMode) {
      final timelineState = ref.watch(timelineProvider);
      // debugPrint('[SettingsScreen] Timeline items count: ${timelineState.timelineItems.length}');
    }

    // デバッグ用に状態を表示
    // debugPrint('[SettingsScreen] build called');
    // debugPrint('[SettingsScreen] isLoading: ${settingsState.isLoading}');
    // debugPrint('[SettingsScreen] currentUserSettings: ${settingsState.currentUserSettings?.toJson()}');
    // debugPrint('[SettingsScreen] emergencyContacts count: ${settingsState.currentEmergencyContacts.length}');

    if (settingsState.isLoading) {
      return Scaffold(
        appBar: ModernAppBar(
          title: l10n.settings,
          subtitle: l10n.loadingSettings,
          leading: const Icon(Icons.arrow_back, color: Color(0xFF2D4A4A)),
          onLeadingPressed: () => context.go(AppRoutes.mainTimeline),
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (settingsState.currentUserSettings == null) {
      return Scaffold(
        appBar: ModernAppBar(
          title: l10n.settings,
          subtitle: l10n.errorOccurred(""),
          leading: const Icon(Icons.arrow_back, color: Color(0xFF2D4A4A)),
          onLeadingPressed: () => context.go(AppRoutes.mainTimeline),
        ),
        body: Center(child: Text(l10n.settingsLoadFailed)),
      );
    }

    return Scaffold(
      backgroundColor: Theme.of(context).brightness == Brightness.dark 
          ? Colors.grey[900] 
          : Colors.grey[50],
      appBar: ModernAppBar(
        title: l10n.settings,
        subtitle: l10n.checkVariousSettings,
        leading: const Icon(Icons.arrow_back, color: Color(0xFF2D4A4A)),
        onLeadingPressed: () => context.go(AppRoutes.mainTimeline),
      ),
      body: ListView(
        children: [
          // 言語設定項目
          ListTile(
            leading: const Icon(Icons.language),
            title: Text(l10n.language),
            subtitle: Text(_getLanguageName(currentLanguage ?? 'en')),
            onTap: () => _showLanguageDialog(context, ref),
          ),
          // 位置情報設定項目
          ListTile(
            leading: const Icon(Icons.location_on),
            title: Text(l10n.locationPermissionTitle),
            subtitle: Text(l10n.locationPermissionRationale),
            onTap: () => AppSettings.openAppSettings(type: AppSettingsType.location),
          ),
          // 通知設定項目
          ListTile(
            leading: const Icon(Icons.notifications),
            title: Text(l10n.notificationSettings),
            subtitle: Text(l10n.notificationSettingsDescription),
            onTap: () => AppSettings.openAppSettings(type: AppSettingsType.notification),
          ),
          // ニックネーム表示項目
          ListTile(
            leading: const Icon(Icons.person),
            title: Text(l10n.userNickname),
            subtitle: Text(
              settingsState.currentUserSettings?.nickname ?? l10n.notSet,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            trailing: const Icon(Icons.edit),
            onTap: settingsState.currentUserSettings != null
                ? () => _showNicknameEditDialog(context, ref, settingsState.currentUserSettings!)
                : null,
          ),
          // 緊急連絡先セクション
          const Divider(),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.emergency, color: Colors.red),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        l10n.emergencyContactsList,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    ElevatedButton.icon(
                      icon: const Icon(Icons.add, size: 20),
                      label: Text(l10n.add),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      ),
                      onPressed: () => _showAddEmergencyContactDialog(context, ref),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                if (settingsState.currentUserSettings?.emergencyContacts.isEmpty ?? true)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.info_outline, color: Colors.grey.shade600),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            l10n.noEmergencyContacts,
                            style: TextStyle(color: Colors.grey.shade600),
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  ...settingsState.currentUserSettings!.emergencyContacts.map((contact) => 
                    Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Colors.red.shade100,
                          child: Icon(Icons.person, color: Colors.red.shade700),
                        ),
                        title: Text(
                          contact.name,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(contact.phoneNumber),
                            if (contact.relationship != null)
                              Text(
                                contact.relationship!,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.edit, color: Colors.blue),
                              onPressed: () => _showEditEmergencyContactDialog(
                                context,
                                ref,
                                contact,
                              ),
                              tooltip: l10n.edit,
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () => _showDeleteConfirmationDialog(
                                context,
                                ref,
                                contact.id,
                              ),
                              tooltip: l10n.delete,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ).toList(),
              ],
            ),
          ),
          
          // ハートビート間隔設定
          const Divider(),
          ListTile(
            leading: const Icon(Icons.timer),
            title: Text(l10n.heartbeatInterval),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${l10n.normalTime}: ${settingsState.currentUserSettings?.heartbeatIntervalNormalMinutes ?? 6}${l10n.minutes}'),
                Text('${l10n.disasterTime}: ${settingsState.currentUserSettings?.heartbeatIntervalEmergencyMinutes ?? 6}${l10n.minutes}'),
              ],
            ),
            trailing: const Icon(Icons.arrow_forward_ios),
            onTap: settingsState.currentUserSettings != null 
                ? () => _showHeartbeatIntervalDialog(context, ref, settingsState.currentUserSettings!)
                : null,
          ),
          // 音声入力設定 (一時的に無効化)
          // ListTile(
          //   leading: const Icon(Icons.mic),
          //   title: Text(l10n.voiceInput ?? '音声入力'),
          //   subtitle: Text(l10n.voiceInputDescription ?? '音声でメッセージを入力'),
          //   trailing: Switch(
          //     value: settingsState.currentUserSettings?.isVoiceInputEnabled ?? true,
          //     onChanged: settingsState.currentUserSettings != null
          //         ? (value) async {
          //             await ref.read(settingsProvider.notifier).updateSettings(
          //               settingsState.currentUserSettings!.copyWith(
          //                 isVoiceInputEnabled: value,
          //               ),
          //             );
          //           }
          //         : null,
          //   ),
          // ),
          // デバッグ用アラート発報ボタン (TEST_MODE=trueのみ表示) - 修正済み
          if (AppConfig.testMode)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: Column(
                children: [
                  const Divider(),
                  const SizedBox(height: 8),
                  Text(
                    l10n.debugFeatures,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).textTheme.titleMedium?.color,
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  // 現在のモード表示
                  Consumer(
                    builder: (context, ref, child) {
                      final deviceStatusState = ref.watch(deviceStatusProvider);
                      final currentMode = deviceStatusState.currentMode;
                      final isEmergencyMode = currentMode == 'emergency';
                      
                      return Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).brightness == Brightness.dark
                              ? (isEmergencyMode ? Colors.red.shade900.withValues(alpha: 0.3) : Colors.grey.shade800)
                              : (isEmergencyMode ? Colors.red.shade50 : Colors.grey.shade100),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: Theme.of(context).brightness == Brightness.dark
                                ? (isEmergencyMode ? Colors.red.shade700 : Colors.grey.shade600)
                                : (isEmergencyMode ? Colors.red.shade300 : Colors.grey.shade300),
                            width: isEmergencyMode ? 2 : 1,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  isEmergencyMode ? Icons.warning : Icons.info_outline,
                                  size: 16,
                                  color: Theme.of(context).brightness == Brightness.dark
                                      ? (isEmergencyMode ? Colors.red.shade300 : Colors.blue.shade300)
                                      : (isEmergencyMode ? Colors.red.shade700 : Colors.blue.shade700),
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  l10n.currentSystemStatus,
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: isEmergencyMode ? Colors.red.shade700 : Colors.blue.shade700,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            // 現在のモード表示
                            Row(
                              children: [
                                Icon(
                                  isEmergencyMode ? Icons.emergency : Icons.check_circle,
                                  size: 8,
                                  color: isEmergencyMode ? Colors.red : Colors.green,
                                ),
                                const SizedBox(width: 8),
                                Text('${l10n.operationMode}: '),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: isEmergencyMode ? Colors.red : Colors.green,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    isEmergencyMode ? '🚨 ${l10n.emergencyMode}' : '😌 ${l10n.normalMode}',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(Icons.circle, size: 8, color: Colors.green),
                                const SizedBox(width: 8),
                                Text('${l10n.connectionStatus}: '),
                                Text(
                                  deviceStatusState.connectivityStatus.name,
                                  style: const TextStyle(fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(Icons.circle, size: 8, color: Colors.blue),
                                const SizedBox(width: 8),
                                Text('${l10n.emergencyContacts}: ', style: TextStyle(color: Theme.of(context).textTheme.bodyMedium?.color)),
                                FutureBuilder<int>(
                                  future: ref.read(deviceStatusProvider.notifier).debugGetEmergencyContactsCount(),
                                  builder: (context, snapshot) {
                                    if (snapshot.hasData) {
                                      return Text(
                                        '${snapshot.data} 件',
                                        style: const TextStyle(fontWeight: FontWeight.bold),
                                      );
                                    } else {
                                      return const Text('読み込み中...');
                                    }
                                  },
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(Icons.circle, size: 8, color: Colors.orange),
                                const SizedBox(width: 8),
                                Text('${l10n.locationStatus}: ', style: TextStyle(color: Theme.of(context).textTheme.bodyMedium?.color)),
                                Text(
                                  deviceStatusState.isGpsEnabled ? l10n.enabled : l10n.disabled,
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: deviceStatusState.isGpsEnabled ? Colors.green : Colors.red,
                                  ),
                                ),
                              ],
                            ),
                            if (deviceStatusState.currentLocation != null) ...[
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  const Icon(Icons.circle, size: 8, color: Colors.blue),
                                  const SizedBox(width: 8),
                                  Text('Location: ', style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : Colors.black87)),
                                  Expanded(
                                    child: Text(
                                      '${deviceStatusState.currentLocation!.latitude.toStringAsFixed(6)}, ${deviceStatusState.currentLocation!.longitude.toStringAsFixed(6)}',
                                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(Icons.circle, size: 8, color: Colors.orange),
                                const SizedBox(width: 8),
                                Text('${l10n.battery}: ', style: TextStyle(color: Theme.of(context).textTheme.bodyMedium?.color)),
                                Text(
                                  '${deviceStatusState.batteryLevel}%${deviceStatusState.isBatteryCharging ? ' (${l10n.charging})' : ''}',
                                  style: const TextStyle(fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                            if (isEmergencyMode) ...[
                              const SizedBox(height: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: Colors.red.shade100,
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(color: Colors.red.shade300),
                                ),
                                child: Text(
                                  '⚠️ ${l10n.emergencyModeActive}',
                                  style: const TextStyle(fontSize: 11, color: Colors.red, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ],
                        ),
                      );
                    },
                  ),
                  // === デバッグツール ===
                  
                  // バックエンド接続情報表示
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.blue.shade900.withValues(alpha: 0.3)
                          : Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? Colors.blue.shade700
                            : Colors.blue.shade300,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.cloud, size: 16, color: Theme.of(context).brightness == Brightness.dark ? Colors.blue.shade300 : Colors.blue.shade700),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '🌐 バックエンド接続先',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                  color: Colors.blue.shade700,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          AppConfig.apiBaseUrl.contains('localhost') || AppConfig.apiBaseUrl.contains('10.0.2.2') || AppConfig.apiBaseUrl.contains('127.0.0.1')
                              ? '🔧 ローカル開発環境'
                              : AppConfig.apiBaseUrl.contains('staging')
                                  ? '🚧 ステージング環境'
                                  : '🌍 本番環境',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: Colors.blue.shade600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          AppConfig.apiBaseUrl,
                          style: TextStyle(
                            fontSize: 11,
                            fontFamily: 'monospace',
                            color: Colors.blue.shade800,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  // 位置情報表示
                  Consumer(
                    builder: (context, ref, child) {
                      final deviceStatus = ref.watch(deviceStatusProvider);
                      
                      if (deviceStatus.currentLocation == null) {
                        return const SizedBox.shrink();
                      }
                      
                      return Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: Theme.of(context).brightness == Brightness.dark
                              ? Colors.green.shade900.withValues(alpha: 0.3)
                              : Colors.green.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: Theme.of(context).brightness == Brightness.dark
                                ? Colors.green.shade700
                                : Colors.green.shade300,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.location_on,
                                  size: 16,
                                  color: Theme.of(context).brightness == Brightness.dark
                                      ? Colors.green.shade300
                                      : Colors.green.shade700,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Current Location',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Theme.of(context).brightness == Brightness.dark
                                        ? Colors.green.shade300
                                        : Colors.green.shade700,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Lat: ${deviceStatus.currentLocation!.latitude.toStringAsFixed(6)}',
                              style: TextStyle(fontSize: 11, fontFamily: 'monospace', color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : Colors.black87),
                            ),
                            Text(
                              'Lng: ${deviceStatus.currentLocation!.longitude.toStringAsFixed(6)}',
                              style: TextStyle(fontSize: 11, fontFamily: 'monospace', color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : Colors.black87),
                            ),
                            if (deviceStatus.currentLocation!.accuracy != null)
                              Text(
                                'Accuracy: ±${deviceStatus.currentLocation!.accuracy!.toStringAsFixed(1)}m',
                                style: TextStyle(fontSize: 11, fontFamily: 'monospace', color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : Colors.black87),
                              ),
                          ],
                        ),
                      );
                    },
                  ),
                  
                  // 位置情報再取得ボタン
                  ElevatedButton.icon(
                    icon: const Icon(Icons.location_searching),
                    label: const Text('📍 位置情報を再取得'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(double.infinity, 48),
                    ),
                    onPressed: () => _refreshLocation(context, ref),
                  ),
                  const SizedBox(height: 8),
                  
                  // テストアラート発報（緊急モード切り替え含む）
                  ElevatedButton.icon(
                    icon: const Icon(Icons.warning_amber_rounded),
                    label: Text('🚨 ${l10n.testAlert}'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(double.infinity, 48),
                    ),
                    onPressed: () => _triggerDebugAlert(context, ref),
                  ),
                  const SizedBox(height: 8),
                  
                  // 完全リセット（危険操作）
                  ElevatedButton.icon(
                    icon: const Icon(Icons.delete_forever),
                    label: Text('🗑️ ${l10n.completeReset}'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(double.infinity, 48),
                    ),
                    onPressed: () => _completeDebugReset(context),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '⚠️ ${l10n.completeResetWarning}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    l10n.debugNote,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
              ),
            ),
        ],
      ),
    );
  }


  void _showLanguageDialog(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final currentLanguage = ref.read(settingsProvider).currentUserSettings?.languageCode ?? 'en';
    String? selectedLanguage = currentLanguage;

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: Text(l10n.selectLanguage),
              content: SizedBox(
                width: double.maxFinite,
                child: DropdownButtonFormField<String>(
                  value: selectedLanguage,
                  decoration: InputDecoration(
                    border: const OutlineInputBorder(),
                    labelText: l10n.language,
                  ),
                  items: AppLocalizations.supportedLocales.map((locale) {
                    final localeCode = locale.countryCode != null 
                        ? '${locale.languageCode}_${locale.countryCode}' 
                        : locale.languageCode;
                    return DropdownMenuItem<String>(
                      value: localeCode,
                      child: Text(_getLanguageName(localeCode)),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      selectedLanguage = value;
                    });
                  },
                ),
              ),
              actions: [
                TextButton(
                  child: Text(l10n.cancel),
                  onPressed: () => Navigator.pop(context),
                ),
                TextButton(
                  child: Text(l10n.ok),
                  onPressed: () {
                    if (selectedLanguage != null && selectedLanguage != currentLanguage) {
                      ref.read(settingsProvider.notifier).updateLanguage(context, selectedLanguage!);
                    }
                    Navigator.pop(context);
                  },
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _showAddEmergencyContactDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.5),
      builder: (dialogContext) => EmergencyContactDialog(
        onSave: (name, phone) {
          ref.read(settingsProvider.notifier).addEmergencyContact(name, phone);
        },
      ),
    );
  }

  void _showEditEmergencyContactDialog(
    BuildContext context,
    WidgetRef ref,
    EmergencyContactModel contact,
  ) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.5),
      builder: (dialogContext) => EmergencyContactDialog(
        initialName: contact.name,
        initialPhone: contact.phoneNumber,
        isEdit: true,
        onSave: (name, phone) {
          ref.read(settingsProvider.notifier).updateEmergencyContact(
            contact.copyWith(
              name: name,
              phoneNumber: phone,
            ),
          );
        },
      ),
    );
  }

  void _showDeleteConfirmationDialog(
    BuildContext context,
    WidgetRef ref,
    String contactId,
  ) {
    final l10n = AppLocalizations.of(context)!;
    showDialog(
      context: context,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return AlertDialog(
          title: Text(l10n.confirmation),
        content: Text(l10n.deleteEmergencyContactConfirmation),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () {
              ref.read(settingsProvider.notifier).deleteEmergencyContact(contactId);
              Navigator.pop(context);
            },
            child: Text(l10n.delete, style: const TextStyle(color: Colors.red)),
          ),
        ],
      );
      },
    );
  }

  String _getLanguageName(String code) {
    switch (code) {
      case 'ja': return '日本語';
      case 'en': return 'English';
      case 'zh': return '中文';
      case 'zh_CN': return '简体中文';
      case 'zh_TW': return '繁體中文';
      case 'ko': return '한국어';
      case 'es': return 'Español';
      case 'fr': return 'Français';
      case 'de': return 'Deutsch';
      case 'it': return 'Italiano';
      case 'pt': return 'Português';
      default: return 'English';
    }
  }

  /// 提案履歴を表示
  Future<void> _showSuggestionHistory(BuildContext context) async {
    final l10n = AppLocalizations.of(context)!;
    
    try {
      // debugPrint('[Settings] === SHOWING SUGGESTION HISTORY ===');
      // debugPrint('[Settings] 🔧 Context mounted: ${context.mounted}');
      
      // デバッグ情報を出力
      // debugPrint('[Settings] 📝 Printing SuggestionHistoryManager debug info...');
      // await SuggestionHistoryManager.printDebugInfo();
      
      // 新しいタイプベースの履歴を取得
      // debugPrint('[Settings] 📝 Getting acknowledged suggestion types...');
      final suggestionTypes = await SuggestionHistoryManager.getAcknowledgedSuggestionTypes();
      // debugPrint('[Settings] 📝 Retrieved ${suggestionTypes.length} suggestion types: $suggestionTypes');
      
      // 旧いIDベースの履歴も取得（後方互換性）
      // debugPrint('[Settings] 📝 Getting legacy acknowledged suggestions (IDs)...');
      final suggestions = await SuggestionHistoryManager.getAcknowledgedSuggestions();
      // debugPrint('[Settings] 📝 Retrieved ${suggestions.length} legacy suggestion IDs: $suggestions');
      
      if (!context.mounted) {
      // debugPrint('[Settings] ❌ Context not mounted, cannot show dialog');
        return;
      }
      
      // debugPrint('[Settings] 🎯 About to show dialog with ${suggestionTypes.length} types and ${suggestions.length} IDs');
      
      showDialog(
        context: context,
        builder: (context) {
          final l10n = AppLocalizations.of(context)!;
          return AlertDialog(
            title: Text('📝 ${l10n.suggestionHistory}'),
          content: SizedBox(
            width: double.maxFinite,
            height: 500,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // タイプベースの履歴
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.blue.shade900.withValues(alpha: 0.3)
                          : Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? Colors.blue.shade700
                            : Colors.blue.shade200,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '✅ ${l10n.currentTypeBasedHistory}: ${suggestionTypes.length}${l10n.contacts}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).brightness == Brightness.dark
                                ? Colors.blue.shade300
                                : Colors.blue,
                          ),
                        ),
                        const SizedBox(height: 8),
                        if (suggestionTypes.isEmpty)
                          Text(
                            l10n.typeBasedHistoryEmpty,
                            style: const TextStyle(color: Colors.grey),
                          )
                        else
                          ...suggestionTypes.toList().asMap().entries.map((entry) {
                            final index = entry.key;
                            final type = entry.value;
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 2),
                              child: Row(
                                children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: Theme.of(context).brightness == Brightness.dark
                                        ? Colors.blue.shade800
                                        : Colors.blue.shade100,
                                    child: Text(
                                      '${index + 1}',
                                      style: TextStyle(
                                        color: Theme.of(context).brightness == Brightness.dark
                                          ? Colors.blue.shade200
                                          : Colors.blue.shade800,
                                        fontSize: 10,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      type,
                                      style: const TextStyle(
                                        fontFamily: 'monospace',
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 旧いIDベースの履歴
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange.shade200),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '🔄 ${l10n.legacyIdBasedHistory}: ${suggestions.length}${l10n.contacts}',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.orange),
                        ),
                        const SizedBox(height: 8),
                        if (suggestions.isEmpty)
                          Text(
                            l10n.idBasedHistoryEmpty,
                            style: const TextStyle(color: Colors.grey),
                          )
                        else
                          ...suggestions.take(5).toList().asMap().entries.map((entry) {
                            final index = entry.key;
                            final suggestionId = entry.value;
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 2),
                              child: Row(
                                children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: Colors.orange.shade100,
                                    child: Text(
                                      '${index + 1}',
                                      style: TextStyle(
                                        color: Colors.orange.shade800,
                                        fontSize: 10,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      suggestionId,
                                      style: const TextStyle(
                                        fontFamily: 'monospace',
                                        fontSize: 10,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        if (suggestions.length > 5)
                          Text(
                            l10n.andMore(suggestions.length - 5),
                            style: const TextStyle(color: Colors.grey, fontSize: 12),
                          ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // デバッグ情報
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.grey.shade800
                          : Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? Colors.grey.shade600
                            : Colors.grey.shade300,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '🔧 ${l10n.debugInfo}',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          l10n.historyNote,
                          style: TextStyle(
                            fontSize: 11,
                            color: Colors.grey.shade700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(l10n.close),
            ),
          ],
        );
        },
      );
    } catch (e) {
      // debugPrint('[Settings] ❌ Error showing suggestion history: $e');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.errorOccurred(e.toString()))),
        );
      }
    }
  }



  Future<void> _triggerDebugAlert(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context)!;
    final deviceId = DeviceIdUtil.currentDeviceId;
    if (deviceId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.errorOccurred(""))),
      );
      return;
    }

    // アラート種別を選択するダイアログを表示
    final alertType = await showDialog<String>(
      context: context,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return AlertDialog(
          title: Text(l10n.selectTestAlertType),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              title: Text('🌍 ${l10n.earthquake}'),
              subtitle: Text(l10n.earthquakeTest),
              onTap: () => Navigator.pop(context, 'earthquake'),
            ),
            ListTile(
              title: Text('🌊 ${l10n.tsunami}'),
              subtitle: Text(l10n.tsunamiTest),
              onTap: () => Navigator.pop(context, 'tsunami'),
            ),
            ListTile(
              title: Text('🌀 台風'),
              subtitle: Text('台風接近警報のテスト'),
              onTap: () => Navigator.pop(context, 'typhoon'),
            ),
            ListTile(
              title: Text('🔥 ${l10n.fire}'),
              subtitle: Text(l10n.fireTest),
              onTap: () => Navigator.pop(context, 'fire'),
            ),
            const Divider(),
            ListTile(
              title: Text('😌 ${l10n.forceResetEmergency}'),
              subtitle: Text(l10n.forceResetEmergencyDesc),
              leading: const Icon(Icons.power_settings_new, color: Colors.blue),
              onTap: () => Navigator.pop(context, 'reset_emergency'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, null),
            child: Text(l10n.cancel),
          ),
        ],
      );
      },
    );

    if (alertType == null) return;

    // 緊急モード解除の場合は特別処理
    if (alertType == 'reset_emergency') {
      await _handleEmergencyModeReset(context, ref, deviceId);
      return;
    }

    // 進行状況ダイアログを表示
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return Center(
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text(l10n.triggeringAlert),
                ],
              ),
            ),
          ),
        );
      },
    );

    try {
      final apiService = ApiService();
      final response = await apiService.triggerDebugAlert(
        deviceId: deviceId,
        alertType: alertType,
        severity: 'Emergency',
        customTitle: _getAlertTitle(context, alertType),
        customDescription: _getAlertDescription(context, alertType),
      );

      // 進行状況ダイアログを閉じる
      if (mounted && context.mounted) {
        Navigator.pop(context);
      }

      // 成功メッセージを表示
      if (mounted && context.mounted) {
        // 緊急モードに切り替え
        ref.read(deviceStatusProvider.notifier).setEmergencyModeForDebug(true);
        
        // デバッグアラートをタイムラインに直接追加（FCMが来ない場合のため）
        final alertData = {
          'alert_type': alertType,
          'disaster_type': alertType,
          'severity': 'Emergency',
          'title': _getAlertTitle(context, alertType),
          'body': _getAlertDescription(context, alertType),
          'timestamp': DateTime.now().toIso8601String(),
          'location': '東京都',
          'isDebug': true,
        };
        ref.read(timelineProvider.notifier).handleDisasterAlert(alertData);
        
        // OSレベル通知も表示
        try {
          final localNotificationService = LocalNotificationService();
          await localNotificationService.initialize();
          await localNotificationService.showEmergencyNotification(
            title: _getAlertTitle(context, alertType),
            body: _getAlertDescription(context, alertType),
            payload: 'debug_alert_$alertType',
          );
          
        } catch (e) {
          // エラーは無視
        }
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.alertTriggerSuccess(response['message'] ?? '')),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 5),
          ),
        );

        // メイン画面に戻る（災害緊急モードが発動するはず）
        if (mounted && context.mounted) {
          context.goNamed(AppRoutes.mainTimeline);
        }
      }
    } catch (e) {
      // 進行状況ダイアログを閉じる
      if (mounted && context.mounted) {
        Navigator.pop(context);
      }

      // エラーメッセージを表示
      if (mounted && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.alertTriggerFailed(e.toString())),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  String _getAlertTitle(BuildContext context, String alertType) {
    final l10n = AppLocalizations.of(context)!;
    switch (alertType) {
      case 'earthquake':
        return l10n.emergencyEarthquakeAlertTest;
      case 'tsunami':
        return l10n.tsunamiWarningTest;
      case 'typhoon':
        return '🌀 台風警報（テスト）';
      case 'fire':
        return l10n.fireWarningTest;
      default:
        return l10n.emergencyAlertTest;
    }
  }

  String _getAlertDescription(BuildContext context, String alertType) {
    final l10n = AppLocalizations.of(context)!;
    switch (alertType) {
      case 'earthquake':
        return l10n.earthquakeAlertTestDescription;
      case 'tsunami':
        return l10n.tsunamiAlertTestDescription;
      case 'typhoon':
        return 'これはテスト用の台風警報です。強風・暴雨に警戒してください。（テスト）';
      case 'fire':
        return l10n.fireAlertTestDescription;
      default:
        return l10n.debugAlertTestDescription;
    }
  }

  /// 緊急モード強制解除処理
  Future<void> _handleEmergencyModeReset(BuildContext context, WidgetRef ref, String deviceId) async {
    final l10n = AppLocalizations.of(context)!;
    
    // 確認ダイアログ表示
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return AlertDialog(
          title: Text('😌 ${l10n.forceResetConfirm}'),
        content: Text(l10n.forceResetMessage),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(l10n.cancel),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
            child: Text(l10n.performReset),
          ),
        ],
      );
      },
    );

    if (confirmed != true) return;

    // 進行状況ダイアログを表示
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return Center(
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text(l10n.resettingEmergencyMode),
                ],
              ),
            ),
          ),
        );
      },
    );

    try {
      // フロントエンドの緊急モードを平常時に戻す
      ref.read(deviceStatusProvider.notifier).setEmergencyModeForDebug(false);
      
      final apiService = ApiService();
      final response = await apiService.forceEmergencyModeReset(deviceId);

      // 進行状況ダイアログを閉じる
      if (mounted && context.mounted) {
        Navigator.pop(context);
      }

      // 成功メッセージを表示
      if (mounted && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('😌 ${response['message']}'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 3),
          ),
        );
      }

      // debugPrint('[Settings] Emergency mode reset successful: $response');

    } catch (e) {
      // 進行状況ダイアログを閉じる
      if (mounted && context.mounted) {
        Navigator.pop(context);
      }

      // エラーメッセージを表示
      if (mounted && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ ${l10n.emergencyModeResetFailed}: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }

      // debugPrint('[Settings] Emergency mode reset failed: $e');
    }
  }


  /// 完全デバッグリセット処理
  Future<void> _completeDebugReset(BuildContext context) async {
    final l10n = AppLocalizations.of(context)!;
    
    // 確認ダイアログ表示
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return AlertDialog(
          title: Text('⚠️ ${l10n.completeAppReset}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '⚠️ ${l10n.completeResetConfirmMessage}',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.warning, size: 16, color: Colors.red.shade700),
                      const SizedBox(width: 6),
                      Text(
                        '${l10n.deleteTargets}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.red.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.deleteTargetsList,
                    style: const TextStyle(fontSize: 13),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(l10n.cancel),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text(l10n.performCompleteReset, style: const TextStyle(color: Colors.white)),
          ),
        ],
      );
      },
    );

    if (confirmed != true) return;

    // 進行状況ダイアログを表示
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return Center(
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text(l10n.executingCompleteReset),
                  const SizedBox(height: 8),
                  Text(
                    l10n.initializingData,
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );

    try {
      // Settings Providerの完全リセット機能を実行
      await ref.read(settingsProvider.notifier).completeDebugReset(context);

      // 進行状況ダイアログを閉じる
      if (mounted && context.mounted) {
        Navigator.pop(context);
      }

      // 成功メッセージを表示（短時間で自動的にオンボーディングに遷移するため）
      if (mounted && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.completeResetSuccess),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 2),
          ),
        );
      }

      // debugPrint('[Settings] Complete debug reset successful');

    } catch (e) {
      // 進行状況ダイアログを閉じる
      if (mounted && context.mounted) {
        Navigator.pop(context);
      }

      // エラーメッセージを表示
      if (mounted && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.completeResetFailed(e.toString())),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }

      // debugPrint('[Settings] Complete debug reset failed: $e');
    }
  }



  void _showNicknameEditDialog(BuildContext context, WidgetRef ref, UserSettingsModel settings) {
    final l10n = AppLocalizations.of(context)!;
    final controller = TextEditingController(text: settings.nickname);

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(l10n.userNickname),
          content: TextField(
            controller: controller,
            decoration: InputDecoration(
              labelText: l10n.userNickname,
              border: const OutlineInputBorder(),
            ),
            maxLength: 20,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(l10n.cancel),
            ),
            ElevatedButton(
              onPressed: () async {
                final newNickname = controller.text.trim();
                if (newNickname.isNotEmpty) {
                  await ref.read(settingsProvider.notifier).updateSettings(
                    settings.copyWith(nickname: newNickname),
                  );
                  if (context.mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('ニックネームを更新しました')),
                    );
                  }
                }
              },
              child: Text(l10n.save),
            ),
          ],
        );
      },
    );
  }

  void _showHeartbeatIntervalDialog(BuildContext context, WidgetRef ref, UserSettingsModel settings) {
    final l10n = AppLocalizations.of(context)!;
    int normalMinutes = settings.heartbeatIntervalNormalMinutes;
    int emergencyMinutes = settings.heartbeatIntervalEmergencyMinutes;

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: Text(l10n.heartbeatIntervalSettings),
              content: SizedBox(
                width: double.maxFinite,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      l10n.heartbeatIntervalDescription,
                      style: const TextStyle(fontSize: 14),
                    ),
                    const SizedBox(height: 20),
                    // 平常時間隔設定
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: Text(l10n.normalTimeLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
                        ),
                        Expanded(
                          flex: 3,
                          child: DropdownButtonFormField<int>(
                            value: normalMinutes,
                            decoration: InputDecoration(
                              border: const OutlineInputBorder(),
                              suffixText: l10n.minutes,
                            ),
                            items: [3, 5, 6, 10, 15, 30, 60].map((minutes) {
                              return DropdownMenuItem<int>(
                                value: minutes,
                                child: Text('$minutes${l10n.minutes}'),
                              );
                            }).toList(),
                            onChanged: (value) {
                              if (value != null) {
                                setState(() {
                                  normalMinutes = value;
                                });
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    // 災害時間隔設定
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: Text(l10n.disasterTimeLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
                        ),
                        Expanded(
                          flex: 3,
                          child: DropdownButtonFormField<int>(
                            value: emergencyMinutes,
                            decoration: InputDecoration(
                              border: const OutlineInputBorder(),
                              suffixText: l10n.minutes,
                            ),
                            items: [3, 5, 6, 10, 15, 30].map((minutes) {
                              return DropdownMenuItem<int>(
                                value: minutes,
                                child: Text('$minutes${l10n.minutes}'),
                              );
                            }).toList(),
                            onChanged: (value) {
                              if (value != null) {
                                setState(() {
                                  emergencyMinutes = value;
                                });
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      l10n.heartbeatNote,
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  child: Text(l10n.cancel),
                  onPressed: () => Navigator.pop(context),
                ),
                TextButton(
                  child: Text(l10n.save),
                  onPressed: () async {
                    try {
                      await ref.read(settingsProvider.notifier).updateHeartbeatIntervals(
                        normalMinutes: normalMinutes,
                        emergencyMinutes: emergencyMinutes,
                      );
                      if (context.mounted) {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(l10n.heartbeatIntervalUpdated),
                            backgroundColor: Colors.green,
                          ),
                        );
                      }
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(l10n.settingsSaveFailed(e.toString())),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    }
                  },
                ),
              ],
            );
          },
        );
      },
    );
  }

  /// 位置情報再取得処理
  Future<void> _refreshLocation(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context)!;
    
    try {
      // ローディングダイアログを表示
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          content: Row(
            children: [
              const CircularProgressIndicator(),
              const SizedBox(width: 16),
              Text('📍 位置情報を取得中...'),
            ],
          ),
        ),
      );
      
      // 権限状態を確認・リクエスト
      final deviceStatusNotifier = ref.read(deviceStatusProvider.notifier);
      
      // 権限状態を更新
      await deviceStatusNotifier.refreshLocationPermissionStatus();
      
      // Web版の場合は権限リクエストを実行
      if (kIsWeb) {
        await deviceStatusNotifier.requestLocationPermission();
      }
      
      // 位置情報を強制取得
      final location = await deviceStatusNotifier.forceRefreshLocation();
      
      // ダイアログを閉じる
      if (context.mounted) {
        Navigator.pop(context);
      }
      
      // 結果を表示
      if (context.mounted) {
        if (location != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('📍 位置情報を取得しました\n'
                  '${location.latitude.toStringAsFixed(6)}, ${location.longitude.toStringAsFixed(6)}'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 4),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('⚠️ 位置情報を取得できませんでした\n'
                  '権限設定やGPSを確認してください'),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 4),
            ),
          );
        }
      }
      
    } catch (e) {
      // ダイアログを閉じる
      if (context.mounted) {
        Navigator.pop(context);
      }
      
      // エラーメッセージを表示
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ 位置情報取得エラー: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }
      
      if (kDebugMode) {
        print('[SettingsScreen] Location refresh error: $e');
      }
    }
  }

}
