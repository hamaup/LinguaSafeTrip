import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/core/theme/emergency_theme.dart';
import 'package:frontend/core/widgets/emergency_contact_dialog.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/services/local_storage_service.dart';
import 'package:frontend/core/models/emergency_contact_model.dart';
import 'package:frontend/features/main_timeline/widgets/sms_confirmation_dialog.dart';

class SuggestionTimelineItem extends ConsumerStatefulWidget {
  final TimelineItemModel model;
  final Function(String suggestionId)? onRemoveFromStreaming;

  const SuggestionTimelineItem({
    super.key,
    required this.model,
    this.onRemoveFromStreaming,
  });

  @override
  ConsumerState<SuggestionTimelineItem> createState() => _SuggestionTimelineItemState();
}

class _SuggestionTimelineItemState extends ConsumerState<SuggestionTimelineItem> {
  bool _isLocalLoading = false;
  bool _isDisposed = false;

  @override
  void initState() {
    super.initState();
    // 提案表示時の自動記録を無効化
    // ユーザーが明確に操作した場合のみ履歴に記録
    // debugPrint('[SuggestionTimelineItem] Suggestion displayed but NOT auto-recorded to history');
  }

  @override
  void dispose() {
    _isDisposed = true;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isChatLoading = ref.watch(timelineProvider.select((state) => state.isChatLoading));
    
    return widget.model.when(
      alert: (id, timestamp, severity, title, message) => const SizedBox.shrink(),
      chat: (id, timestamp, messageText, senderNickname, isOwnMessage) => const SizedBox.shrink(),
      chatWithAction: (id, timestamp, messageText, senderNickname, isOwnMessage, requiresAction, actionData) => const SizedBox.shrink(),
      suggestion: (id, suggestionType, timestamp, content, actionData, actionQuery, actionDisplayText) => _buildSuggestionItem(
        context,
        isChatLoading: isChatLoading,
        id: id,
        suggestionType: suggestionType,
        content: content,
        actionData: actionData,
        timestamp: timestamp,
        actionQuery: actionQuery,
        actionDisplayText: actionDisplayText,
      ),
    );
  }

  Widget _buildSuggestionItem(
    BuildContext context, {
    required bool isChatLoading,
    required String id,
    required String suggestionType,
    required String content,
    required Map<String, dynamic>? actionData,
    required DateTime timestamp,
    String? actionQuery,
    String? actionDisplayText,
  }) {
    return Consumer(
      builder: (context, ref, child) {
        // 現在の緊急モード状態を取得（Consumerで状態変化を監視）
        final deviceStatusState = ref.watch(deviceStatusProvider);
        final isCurrentlyEmergencyMode = deviceStatusState.currentMode == 'emergency';
        
        // 緊急タイプ判定：タイプとコンテキストで判断
        final isEmergencyType = _isEmergencySuggestion(suggestionType, actionData, isCurrentlyEmergencyMode);
        
        // shelter_map_displayタイプは表示しない（避難所マップはチャットメッセージ内でのみ表示）
        if (suggestionType == 'shelter_map_display') {
          return const SizedBox.shrink();
        }
        
    
    // SMS提案は削除不可
    final isDismissible = suggestionType != 'safety_confirmation_sms_proposal' && 
                         suggestionType != 'contact_sms_proposal';
    
    return Dismissible(
      key: Key(id),
      direction: isDismissible ? DismissDirection.horizontal : DismissDirection.none,
      onDismissed: isDismissible ? (direction) {
        // カードを削除
        ref.read(timelineProvider.notifier).removeTimelineItem(id);
        
        // フィードバック
        HapticFeedback.lightImpact();
        
        // スナックバー表示
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(context)!.suggestionDeleted,
            ),
            backgroundColor: const Color(0xFF00E5CC),
            duration: const Duration(seconds: 2),
          ),
        );
      } : null,
      background: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF00E5CC).withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(20),
        ),
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: 20),
        child: Icon(
          Icons.delete_sweep,
          color: const Color(0xFF00E5CC),
          size: 28,
        ),
      ),
      secondaryBackground: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF00E5CC).withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(20),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: Icon(
          Icons.delete_sweep,
          color: const Color(0xFF00E5CC),
          size: 28,
        ),
      ),
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
            child: InkWell(
              borderRadius: BorderRadius.circular(20),
              onTap: (_isLocalLoading || (isChatLoading && !_isNotificationType(actionQuery, actionDisplayText))) ? null : () => _handleSuggestionTap(context, id, suggestionType, content, actionData, actionQuery, actionDisplayText),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: isEmergencyType
                      ? const Color(0xFFFFE5E5).withValues(alpha: 0.9)
                      : _isNotificationType(actionQuery, actionDisplayText)
                          ? const Color(0xFFE8FFF0).withValues(alpha: 0.9)
                          : Colors.white.withValues(alpha: 0.92),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: isEmergencyType
                        ? const Color(0xFFFF6B6B).withValues(alpha: 0.3)
                        : _isNotificationType(actionQuery, actionDisplayText)
                            ? const Color(0xFF00E5CC).withValues(alpha: 0.3)
                            : const Color(0xFFE8FFFC).withValues(alpha: 0.5),
                    width: 0.5,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: isEmergencyType
                          ? const Color(0xFFFF6B6B).withValues(alpha: 0.1)
                          : _isNotificationType(actionQuery, actionDisplayText)
                              ? const Color(0xFF00E5CC).withValues(alpha: 0.08)
                              : const Color(0xFF00D9FF).withValues(alpha: 0.05),
                      blurRadius: 20,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (isEmergencyType) ...[  
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: EmergencyTheme.emergencyRed,
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(12),
                        topRight: Radius.circular(12),
                      ),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.warning_amber_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _getEmergencyTitle(suggestionType),
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ),
                        if (!_isLocalLoading && !isChatLoading)
                          Container(
                            padding: const EdgeInsets.all(4),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.3),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.priority_high,
                              color: Colors.white,
                              size: 16,
                            ),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
                Row(
                  children: [
                    if (isEmergencyType)
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: EmergencyTheme.emergencyRed.withValues(alpha: 0.1),
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: EmergencyTheme.emergencyRed.withValues(alpha: 0.3),
                            width: 2,
                          ),
                        ),
                        child: _getSuggestionIcon(suggestionType),
                      )
                    else
                      _getSuggestionIcon(suggestionType),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          MarkdownBody(
                            data: content.replaceAll('\\n', '\n'),
                            styleSheet: MarkdownStyleSheet(
                          p: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: Colors.black87,
                          ),
                          strong: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                          em: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontStyle: FontStyle.italic,
                            color: Colors.black87,
                          ),
                          code: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontFamily: 'monospace',
                            backgroundColor: Colors.grey[100],
                            color: Colors.black87,
                          ),
                          blockquote: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: Colors.grey[700],
                            fontStyle: FontStyle.italic,
                          ),
                          h1: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            color: Colors.black87,
                          ),
                          h2: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Colors.black87,
                          ),
                          h3: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: Colors.black87,
                          ),
                        ),
                        onTapLink: (text, href, title) {
                          if (href != null) {
                            _launchUrl(href);
                          }
                        },
                            shrinkWrap: true,
                            selectable: false,
                          ),
                          // hazard_map_urlタイプの場合はボタンラベルを大きく表示
                          if (suggestionType == 'hazard_map_url') ...[
                            const SizedBox(height: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: Colors.blue.withAlpha((0.1 * 255).round()),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.blue.withAlpha((0.3 * 255).round())),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.open_in_new, size: 16, color: Colors.blue),
                                  const SizedBox(width: 4),
                                  Flexible(
                                    child: Text(
                                      AppLocalizations.of(context)!.checkDisasterRiskInfo,
                                      style: const TextStyle(
                                        color: Colors.blue,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatDateTime(timestamp),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: _isNotificationType(actionQuery, actionDisplayText)
                              ? Colors.green.withValues(alpha: 0.1)
                              : Colors.blue.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _isNotificationType(actionQuery, actionDisplayText)
                                  ? Icons.check_circle_outline
                                  : Icons.chat_bubble_outline,
                              size: 12,
                              color: _isNotificationType(actionQuery, actionDisplayText)
                                  ? Colors.green
                                  : Colors.blue,
                            ),
                            const SizedBox(width: 4),
                            if (isChatLoading && !_isNotificationType(actionQuery, actionDisplayText)) ...[
                              const SizedBox(
                                width: 12,
                                height: 12,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(Colors.grey),
                                ),
                              ),
                              const SizedBox(width: 4),
                              Text(
                                AppLocalizations.of(context)!.waitingForResponse,
                                style: const TextStyle(
                                  fontSize: 10,
                                  color: Colors.grey,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ] else
                              Flexible(
                                child: Text(
                                  _isNotificationType(actionQuery, actionDisplayText)
                                      ? AppLocalizations.of(context)!.tapToConfirm
                                      : _getLocalizedActionText(suggestionType, actionDisplayText),
                                  style: TextStyle(
                                    fontSize: 10,
                                    color: _isNotificationType(actionQuery, actionDisplayText)
                                        ? Colors.green
                                        : Colors.blue,
                                    fontWeight: FontWeight.w500,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                  maxLines: 1,
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
              ),
            ),
          ),
        ),
      ),
    );
      },
    );
  }

  /// 災害関連の提案タイプかどうかを判定（緊急デザインは現在のモード状態も考慮）
  bool _isEmergencySuggestionType(String type) {
    const emergencyTypes = {
      'immediate_safety_action',
      'evacuation_prompt',
      'evacuation_shelter',
      'emergency',
      'emergency_guidance',
      'emergency_disaster_news',
      'disaster_info',
      // disaster_newsはコンテキストベースで判断するため除外
      'disaster_news_update',
      'evacuation_instruction',
      'publicSafetyInfoForCurrentLocation',
      'safety_confirmation_sms_proposal',
      'hazard_map_url',
      'shelter_search',
      'shelter_info',
      'shelter_status_update',
    };
    
    return emergencyTypes.contains(type);
  }
  
  /// 緊急提案かどうかをタイプとコンテキストで判断
  bool _isEmergencySuggestion(String type, Map<String, dynamic>? actionData, bool isCurrentlyEmergencyMode) {
    // disaster_newsの場合はコンテキストで判断
    if (type == 'disaster_news') {
      // 緊急モード中か、action_dataに緊急フラグがある場合
      if (isCurrentlyEmergencyMode) return true;
      if (actionData != null) {
        final priority = actionData['priority'] as String?;
        final isEmergency = actionData['is_emergency'] as bool?;
        return priority == 'critical' || priority == 'urgent' || isEmergency == true;
      }
      return false;
    }
    
    // その他のタイプは既存ロジックで判断
    return _isEmergencySuggestionType(type) && isCurrentlyEmergencyMode;
  }
  
  /// 緊急提案のタイトルを取得
  String _getEmergencyTitle(String type) {
    final l10n = AppLocalizations.of(context)!;
    
    switch (type) {
      case 'immediate_safety_action':
        return l10n.emergencyActionRequired;
      case 'evacuation_prompt':
      case 'evacuation_shelter':
      case 'evacuation_instruction':
        return l10n.evacuationInfo;
      case 'emergency_disaster_news':
      case 'disaster_news':  // emergency_alert, disaster_updateも統合
      case 'disaster_news_update':
        return l10n.disasterLatestInfo;
      case 'safety_confirmation_sms_proposal':
        return l10n.safetyConfirmation;
      case 'hazard_map_url':
        return l10n.hazardMapInfo;
      case 'shelter_search':
      case 'shelter_info':
      case 'shelter_status_update':
        return l10n.shelterInfo;
      case 'notification_permission_reminder':
        return l10n.notificationSettings; // または適切なローカライゼーションキー
      default:
        return l10n.disasterRelatedInfo;
    }
  }

  Widget _getSuggestionIcon(String type) {
    final deviceStatusState = ref.watch(deviceStatusProvider);
    final isCurrentlyEmergencyMode = deviceStatusState.currentMode == 'emergency';
    final isEmergency = _isEmergencySuggestionType(type) && isCurrentlyEmergencyMode;
    final iconColor = isEmergency ? EmergencyTheme.emergencyRed : null;
    
    switch (type) {
      case 'contact_registration_reminder':
        return Icon(Icons.contacts, color: iconColor ?? Colors.blue);
      case 'emergency_contact_setup':
        return Icon(Icons.emergency, color: iconColor ?? Colors.red);
      case 'guide_recommendation':
        return Icon(Icons.menu_book, color: iconColor ?? Colors.green);
      case 'guide_info':
        return Icon(Icons.library_books, color: iconColor ?? Colors.blue);
      case 'app_feature_introduction':
        return Icon(Icons.lightbulb, color: iconColor ?? Colors.orange);
      case 'welcome_message':
        return Icon(Icons.waving_hand, color: iconColor ?? Colors.purple);
      case 'shelter_search':
      case 'evacuation_shelter':
        return Icon(Icons.home, color: iconColor ?? Colors.red);
      case 'immediate_safety_action':
        return Icon(Icons.warning, color: iconColor ?? Colors.red);
      case 'evacuation_prompt':
        return Icon(Icons.location_on, color: iconColor ?? Colors.orange);
      case 'official_info_check_prompt':
        return Icon(Icons.tv, color: iconColor ?? Colors.blue);
      case 'safety_confirmation_sms_proposal':
      case 'contact_sms_proposal':
        return Icon(Icons.sms, color: iconColor ?? Colors.green);
      case 'emergency':
      case 'emergency_guidance':
        return Icon(Icons.warning_amber, color: iconColor ?? Colors.red);
      case 'emergency_disaster_news':
      case 'disaster_info':
        return Icon(Icons.crisis_alert, color: iconColor ?? Colors.red);
      case 'disaster_news':
        return Icon(Icons.newspaper, color: iconColor ?? Colors.red);
      case 'disaster_preparedness':
        return Icon(Icons.school, color: iconColor ?? Colors.blue);
      case 'evacuation_instruction':
        return Icon(Icons.directions_run, color: iconColor ?? Colors.orange);
      case 'location_based_info':
        return Icon(Icons.location_on, color: iconColor ?? Colors.blue);
      case 'seasonal_alert':
        return Icon(Icons.warning, color: iconColor ?? Colors.orange);
      case 'app_feature_recommendation':
        return Icon(Icons.settings, color: iconColor ?? Colors.blue);
      case 'shelter_info':
        return Icon(Icons.home, color: iconColor ?? Colors.green);
      case 'hazard_map_url':
        return Icon(Icons.map, color: iconColor ?? Colors.blue);
      case 'notification_permission_reminder':
        return Icon(Icons.notifications, color: iconColor ?? Colors.orange);
      case 'action':
      case 'action_selection':
        return Icon(Icons.touch_app, color: iconColor ?? Colors.blue);
      case 'preparedness_tip':
        return Icon(Icons.checklist, color: iconColor ?? Colors.green);
      default:
        return Icon(Icons.info, color: iconColor ?? Colors.blue);
    }
  }

  
  /// 提案タイプがボタン不要の通知タイプかどうか判定
  bool _isNotificationOnlyType(String type) {
    // 通知のみ（ボタン不要）の提案タイプ
    const notificationOnlyTypes = {
      'welcome_message',
      'low_battery_warning',
      'emergency_contact_setup',     // 通知タイプに変更
      'contact_registration_reminder', // 通知タイプに変更
      'notification_permission_reminder', // 通知設定リマインダーも通知型
    };
    
    return notificationOnlyTypes.contains(type);
  }


  Future<void> _showAddContactDialog(BuildContext context) async {
    if (!context.mounted) {
      return;
    }
    
    try {
      await showDialog(
        context: context,
        barrierDismissible: true,
        builder: (dialogContext) {
          return EmergencyContactDialog(
            onSave: (name, phone) async {
              await _saveEmergencyContactFromDialog(dialogContext, name, phone);
            },
          );
        },
      );
    } catch (e) {
      // debugPrint('[SuggestionTimelineItem] Error showing contact dialog: $e');
    }
  }

  Future<void> _saveEmergencyContactFromDialog(BuildContext context, String name, String phoneNumber) async {
    if (name.isEmpty || phoneNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context)?.pleaseEnterNameAndPhone ?? '名前と電話番号を入力してください'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    try {
      // SettingsProviderを使って緊急連絡先を追加
      await ref.read(settingsProvider.notifier).addEmergencyContact(name, phoneNumber);

      // 連絡先追加が成功したらカードは削除（実行型タスク）
      final suggestionType = widget.model.when(
        alert: (_, __, ___, ____, _____) => '',
        suggestion: (_, suggestionType, __, ___, ____, _____, ______) => suggestionType,
        chat: (_, __, ___, ____, _____) => '',
        chatWithAction: (_, __, ___, ____, _____, ______, _______) => '',
      );
      
      // カードの削除は呼び出し元で処理されるため、ここでは削除しない
      
      if (context.mounted && Navigator.canPop(context)) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)?.emergencyContactAdded ?? '緊急連絡先を追加しました'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)?.errorOccurred(e.toString()) ?? '保存中にエラーが発生しました: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }


  /// プロアクティブ提案が通知型かどうかを判定
  bool _isNotificationType(String? actionQuery, String? actionDisplayText) {
    // 提案タイプから判定（より正確）
    final suggestionType = widget.model.when(
      alert: (_, __, ___, ____, _____) => '',
      suggestion: (_, suggestionType, __, ___, ____, _____, ______) => suggestionType,
      chat: (_, __, ___, ____, _____) => '',
      chatWithAction: (_, __, ___, ____, _____, ______, _______) => '',
    );
    
    // SMS提案は通知型ではない（特別な処理が必要）
    if (suggestionType == 'safety_confirmation_sms_proposal' || 
        suggestionType == 'contact_sms_proposal') {
      return false;
    }
    
    // 通知専用タイプの場合は常に通知型
    if (_isNotificationOnlyType(suggestionType)) {
      return true;
    }
    
    
    // action_queryがあれば質問型（action_display_textの有無は問わない）
    // action_queryが null または空文字の場合のみ通知型
    return actionQuery == null || actionQuery.isEmpty;
  }

  /// 提案カードがタップされた時の処理
  void _handleSuggestionTap(
    BuildContext context,
    String id,
    String suggestionType,
    String content,
    Map<String, dynamic>? actionData,
    String? actionQuery,
    String? actionDisplayText,
  ) async {
    if (_isLocalLoading) return;
    
    // SMS提案の場合は詳細ログを出力
    if (suggestionType == 'safety_confirmation_sms_proposal' || suggestionType == 'contact_sms_proposal') {
      // SMS proposal tap handling
    }
    
    setState(() {
      _isLocalLoading = true;
    });
    
    try {
    debugPrint('[SuggestionTimelineItem] === SUGGESTION TAP DEBUG START ===');
    debugPrint('[SuggestionTimelineItem] 🎯 Tapped suggestion details:');
    debugPrint('[SuggestionTimelineItem]   - id: $id');
    debugPrint('[SuggestionTimelineItem]   - suggestionType: $suggestionType');
    debugPrint('[SuggestionTimelineItem]   - content: ${content.substring(0, content.length.clamp(0, 50))}...');
    debugPrint('[SuggestionTimelineItem]   - actionQuery: $actionQuery');
    debugPrint('[SuggestionTimelineItem]   - actionDisplayText: $actionDisplayText');
    debugPrint('[SuggestionTimelineItem]   - actionData: $actionData');
    debugPrint('[SuggestionTimelineItem] 🔍 Type detection result: ${_isNotificationType(actionQuery, actionDisplayText) ? "NOTIFICATION" : "QUESTION"}');
    
    // hazard_map_urlは特別処理（直接URLを開く）
    if (suggestionType == 'hazard_map_url') {
      // debugPrint('[SuggestionTimelineItem] 🗺️ HAZARD MAP URL - special handling for direct URL opening');
      // 通知型判定をスキップして、下の特別処理に進む
    } else if (_isNotificationType(actionQuery, actionDisplayText)) {
      // 通知型の場合は、単にカードを消去
      // debugPrint('[SuggestionTimelineItem] ✅ Notification type detected - removing card');
      // debugPrint('[SuggestionTimelineItem] actionQuery: $actionQuery');
      // debugPrint('[SuggestionTimelineItem] actionDisplayText: $actionDisplayText');
      
      // 緊急連絡先提案の特別処理：モーダルを開く
      if (suggestionType == 'emergency_contact_setup' || 
          suggestionType == 'contact_registration_reminder') {
        // まずローディング状態をリセット
        if (mounted) {
          setState(() {
            _isLocalLoading = false;
          });
        }
        
        // ダイアログを表示（保存・キャンセル問わずダイアログ後にカード削除）
        if (context.mounted) {
          await _showAddContactDialog(context);
        }
        
        // ダイアログが閉じた後にカードを削除（保存・キャンセル問わず）
        if (!_isDisposed && mounted) {
          ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
          
          // ストリーミングリストのコールバックがある場合はそれを使用、なければ通常のタイムラインから削除
          if (widget.onRemoveFromStreaming != null) {
            widget.onRemoveFromStreaming!(id);
          } else {
            ref.read(timelineProvider.notifier).removeTimelineItem(id);
          }
        }
        return;
      }
      
      // その他の通知型提案の通常処理
      if (!_isDisposed && mounted) {
        // ユーザーが明確に操作した場合のみ一時的なセッション記録
        // この記録は1時間限定で、バックエンドが再表示タイミングを制御
        ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
        // debugPrint('[SuggestionTimelineItem] User interaction recorded - temporary session record: $suggestionType (1-hour limit)');
        
        // タイムラインからカードを削除
        ref.read(timelineProvider.notifier).removeTimelineItem(id);
      }
      
      // フィードバックメッセージを表示
      if (!_isDisposed && mounted && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ ${AppLocalizations.of(context)!.notificationConfirmed}'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 2),
          ),
        );
      }
      return;
    }
    
    // 質問可能な提案の場合（actionQueryがある場合）
    // debugPrint('[SuggestionTimelineItem] ❓ Question type detected - processing action query');
    // debugPrint('[SuggestionTimelineItem] 📝 Processing details:');
    // debugPrint('[SuggestionTimelineItem]   - actionQuery: $actionQuery');
    // debugPrint('[SuggestionTimelineItem]   - actionDisplayText: $actionDisplayText');
    // debugPrint('[SuggestionTimelineItem]   - suggestionType: $suggestionType');
    // debugPrint('[SuggestionTimelineItem] 💡 Note: Question cards will be removed after sending question');

    // hazard_map_urlの場合 - 確認ダイアログを表示してからURLを開く
    if (suggestionType == 'hazard_map_url') {
      
      // actionDataからURLを取得
      final url = actionData?['url'] as String?;
      // Use localized title instead of backend text
      final title = AppLocalizations.of(context)!.hazardMapPortalSite;
      final description = actionData?['description'] as String? ?? content;
      final defaultUrl = 'https://disaportal.gsi.go.jp/maps/index.html';
      final finalUrl = url ?? defaultUrl;
      
      // 確認ダイアログを表示
      final shouldOpen = await showDialog<bool>(
        context: context,
        barrierDismissible: true,
        builder: (dialogContext) => AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          title: Container(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Colors.blue.shade400,
                        Colors.blue.shade600,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.blue.withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.map, color: Colors.white, size: 28),
                ),
                if (title.isNotEmpty) ...[
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      title,
                      style: const TextStyle(
                        fontSize: 22, 
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1A1A1A),
                        letterSpacing: -0.5,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 説明文
                if (description.isNotEmpty) ...[
                  Text(
                    description,
                    style: const TextStyle(
                      fontSize: 16, 
                      color: Colors.black87,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                // 外部サイト警告
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Colors.amber.withValues(alpha: 0.1),
                        Colors.amber.withValues(alpha: 0.05),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: Colors.amber.withValues(alpha: 0.3),
                      width: 1.5,
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.amber.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.open_in_new, color: Colors.amber[700], size: 22),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          AppLocalizations.of(context)!.externalSiteWarning,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.amber[900],
                            height: 1.3,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                // URL表示
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.blue.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.blue.withValues(alpha: 0.2),
                      width: 1.5,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.link, size: 20, color: Colors.blue[700]),
                          const SizedBox(width: 8),
                          Text(
                            'URL',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: Colors.blue[700],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.blue.withValues(alpha: 0.2)),
                        ),
                        child: SelectableText(
                          finalUrl,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Color(0xFF1A1A1A),
                            fontFamily: 'monospace',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          actionsPadding: const EdgeInsets.all(24),
          actions: [
            Column(
              children: [
                const Divider(height: 1),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          side: BorderSide(color: Colors.grey[400]!, width: 1.5),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        onPressed: () => Navigator.of(dialogContext).pop(false),
                        child: Text(
                          AppLocalizations.of(context)!.cancel,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey[700],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              Colors.blue.shade500,
                              Colors.blue.shade600,
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(14),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.blue.withValues(alpha: 0.3),
                              blurRadius: 8,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.transparent,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            elevation: 0,
                            shadowColor: Colors.transparent,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          onPressed: () => Navigator.of(dialogContext).pop(true),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.open_in_new, size: 20),
                              const SizedBox(width: 8),
                              Flexible(
                                child: Text(
                                  AppLocalizations.of(context)!.openInBrowser,
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      );
      
      if (shouldOpen == true) {
        try {
          // URLを開く
          final uri = Uri.parse(finalUrl);
          await launchUrl(uri, mode: LaunchMode.externalApplication);
          
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  AppLocalizations.of(context)!.hazardMapOpened,
                  style: const TextStyle(color: Colors.white),
                ),
                backgroundColor: Colors.green,
                duration: const Duration(seconds: 2),
              ),
            );
          }
        } catch (e) {
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  AppLocalizations.of(context)!.failedToOpenHazardMap(e.toString()),
                  style: const TextStyle(color: Colors.white),
                ),
                backgroundColor: Colors.red,
              ),
            );
          }
        }
      }
      
      // 開く・キャンセルのどちらの場合もユーザー操作を記録してカードを削除
      if (shouldOpen != null && !_isDisposed && mounted) {
        ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
        ref.read(timelineProvider.notifier).removeTimelineItem(id);
      }
      return;
    }

    // 旧形式のhazard_map_url処理（actionDataにURLが直接含まれている場合）
    if (suggestionType == 'hazard_map_url_direct' && actionData != null) {
      final url = actionData['url'] as String?;
      final title = actionData['title'] as String? ?? AppLocalizations.of(context)!.openHazardMap;
      final description = actionData['description'] as String?;
      
      if (url != null && url.isNotEmpty) {
        
        // 確認ダイアログを表示
        final shouldOpen = await showDialog<bool>(
          context: context,
          barrierDismissible: true,
          builder: (dialogContext) => AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            title: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.map, color: Colors.blue, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.amber.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.amber.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.amber[700], size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          AppLocalizations.of(context)!.externalSiteWarning,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                if (description != null && description.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Text(
                    description,
                    style: const TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                ],
                const SizedBox(height: 16),
                Text(
                  AppLocalizations.of(context)!.openInBrowser,
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.link, size: 16, color: Colors.grey),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          url,
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 2,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(dialogContext).pop(false),
                child: Text(AppLocalizations.of(context)!.cancel),
              ),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                onPressed: () => Navigator.of(dialogContext).pop(true),
                icon: const Icon(Icons.open_in_new, size: 18),
                label: Text(AppLocalizations.of(context)!.openInBrowser),
              ),
            ],
          ),
        );
        
        if (shouldOpen == true) {
          // URLを開く
          await _launchUrl(url);
          
          // ユーザーが明確に操作した場合のみ一時的なセッション記録
          ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
          // debugPrint('[SuggestionTimelineItem] User interaction recorded - temporary session record: $suggestionType (1-hour limit)');
          
          // 成功メッセージを表示
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                AppLocalizations.of(context)!.hazardMapOpened,
                style: const TextStyle(color: Colors.white),
              ),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 2),
            ),
          );
        } else if (shouldOpen == false) {
          // キャンセル時の処理
          // キャンセル時もユーザーが操作したとして一時的なセッション記録
          ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
        }
        
        // 開く・キャンセルのどちらの場合もカードを削除
        if (shouldOpen != null) {
          ref.read(timelineProvider.notifier).removeTimelineItem(id);
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)!.hazardMapUrlNotFound),
            backgroundColor: Colors.red,
          ),
        );
      }
      return;
    }

    // 緊急連絡先関連は通知型として上で既に処理済み

    // SMS送信提案の場合
    if (suggestionType == 'safety_confirmation_sms_proposal' || suggestionType == 'contact_sms_proposal') {
      // SMS suggestion tapped
      
      // SMS送信提案の場合は質問を送信しない（action_queryを送らない）
      
      // ユーザーが明確に操作した場合のみ一時的なセッション記録
      if (!_isDisposed && mounted) {
        ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
        
        // SMS送信ダイアログを表示（await追加）
        if (context.mounted) {
          await _showSafetySMSDialog(context, id, actionData);
        }
      }
      
      // SMS送信ダイアログが閉じた後の処理はonSendToAllコールバック内で行う
      
      return;
    }

    // 避難所検索関連の場合
    if (suggestionType == 'shelter_search' || 
        suggestionType == 'evacuation_shelter' || 
        suggestionType == 'evacuation_prompt' || 
        suggestionType == 'shelter_status_update' || 
        suggestionType == 'shelter_info') {
      if (!_isDisposed && mounted) {
        // デバッグ：避難所検索提案からの位置情報送信状態をログ出力
        if (kDebugMode) {
          print('[SuggestionTimelineItem] 📍 === LOCATION DEBUG START ===');
          print('[SuggestionTimelineItem] 📍 Message type: SUGGESTION CARD TAP');
          print('[SuggestionTimelineItem] 📍 Suggestion type: $suggestionType');
          print('[SuggestionTimelineItem] 📍 Action query: $actionQuery');
          print('[SuggestionTimelineItem] 📍 Location-based suggestion: ${actionData?['location_based'] ?? false}');
          print('[SuggestionTimelineItem] 📍 Shelter search: ${actionData?['shelter_search'] ?? false}');
          print('[SuggestionTimelineItem] 📍 ActionData: $actionData');
          print('[SuggestionTimelineItem] 📍 === LOCATION DEBUG END ===');
        }
        
        // バックエンドのaction_queryを送信してから、避難所検索を実行
        if (actionQuery != null && actionQuery.isNotEmpty) {
          final displayText = actionDisplayText ?? actionQuery;
          ref.read(timelineProvider.notifier).sendActionQuery(
            actionQuery,
            displayText,
          );
        }
        
        // ユーザーが明確に操作した場合のみ一時的なセッション記録
        ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
        // debugPrint('[SuggestionTimelineItem] User interaction recorded - temporary session record: $suggestionType (1-hour limit)');
        
        // 質問送信後はカードを削除
        ref.read(timelineProvider.notifier).removeTimelineItem(id);
        
        if (context.mounted) {
          _handleShelterSearch(context, actionData);
        }
      }
      return;
    }

    // welcome_messageの場合でもバックエンドのactionQueryを優先使用
    if (suggestionType == 'welcome_message' && (actionQuery == null || actionQuery.isEmpty)) {
      // actionQueryがない場合のみフォールバック処理
      final greeting = 'Hello'; // デフォルトの挨拶
      
      ref.read(timelineProvider.notifier).sendActionQuery(
        greeting,
        greeting,
      );
      
      // ユーザーが明確に操作した場合のみ一時的なセッション記録
      ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
      // debugPrint('[SuggestionTimelineItem] User interaction recorded - temporary session record: $suggestionType (1-hour limit)');
      
      // 質問送信後はカードを削除
      ref.read(timelineProvider.notifier).removeTimelineItem(id);
      
      return;
    }

    // バックエンドが生成したaction_queryとaction_display_textを優先的に使用
    // 質問可能な提案は、チャットに送信してからカードを削除
    
    // SMS送信提案タイプは質問送信処理をスキップ
    if (suggestionType == 'safety_confirmation_sms_proposal' || suggestionType == 'contact_sms_proposal') {
      // SMS提案は既に処理済みなので何もしない
      return;
    }
    
    if (actionQuery != null && actionQuery.isNotEmpty && !_isDisposed && mounted) {
      // バックエンドが生成したaction_queryとaction_display_textをそのまま使用
      final displayText = actionDisplayText != null && actionDisplayText.isNotEmpty 
          ? actionDisplayText 
          : actionQuery; // action_display_textがない場合はaction_queryを使用
      
      // TimelineProviderのsendActionQueryを呼び出し
      ref.read(timelineProvider.notifier).sendActionQuery(
        actionQuery, 
        displayText,
      );
      
      // ユーザーが明確に操作した場合のみ一時的なセッション記録
      ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
      // debugPrint('[SuggestionTimelineItem] User interaction recorded - temporary session record: $suggestionType (1-hour limit)');
      
      // 質問送信後はカードを削除
      ref.read(timelineProvider.notifier).removeTimelineItem(id);
      
      // 質問を送信したことをユーザーに伝える
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('💬 ${AppLocalizations.of(context)!.questionSent}'),
            backgroundColor: Colors.blue,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } else if (actionData != null && actionData.containsKey('action_query')) {
      // SMS送信提案タイプはフォールバック処理もスキップ
      if (suggestionType == 'safety_confirmation_sms_proposal' || suggestionType == 'contact_sms_proposal') {
        return;
      }
      
      // actionDataからaction_queryを取得（フォールバック）
      final fallbackActionQuery = actionData['action_query'] as String;
      final fallbackDisplayText = actionDisplayText != null && actionDisplayText.isNotEmpty 
          ? actionDisplayText 
          : fallbackActionQuery;
      
      ref.read(timelineProvider.notifier).sendActionQuery(
        fallbackActionQuery, 
        fallbackDisplayText,
      );
      
      // ユーザーが明確に操作した場合のみ一時的なセッション記録
      ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
      // debugPrint('[SuggestionTimelineItem] User interaction recorded - temporary session record: $suggestionType (1-hour limit)');
      
      // 質問送信後はカードを削除
      ref.read(timelineProvider.notifier).removeTimelineItem(id);
      
      // 質問を送信したことをユーザーに伝える
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('💬 ${AppLocalizations.of(context)!.questionSent}'),
          backgroundColor: Colors.blue,
          duration: const Duration(seconds: 2),
        ),
      );
    } else {
      // SMS送信提案タイプはデフォルト処理もスキップ
      if (suggestionType == 'safety_confirmation_sms_proposal' || suggestionType == 'contact_sms_proposal') {
        return;
      }
      
      // actionQueryがない場合はデフォルトの動作
      // No actionQuery found - using default tap handler
      _handleDefaultSuggestionTap(context, id, suggestionType, content);
    }
    
    // debugPrint('[SuggestionTimelineItem] === SUGGESTION TAP DEBUG END ===');
    } finally {
      if (mounted) {
        setState(() {
          _isLocalLoading = false;
        });
      }
    }
  }

  /// actionQueryがない場合のデフォルト動作
  void _handleDefaultSuggestionTap(
    BuildContext context,
    String id,
    String suggestionType,
    String content,
  ) {
    // ハードコードされた日本語を削除し、提案内容をそのまま使用
    // バックエンドが適切な言語で生成したcontentを信頼する
    ref.read(timelineProvider.notifier).sendActionQuery(
      content, 
      content,
    );
    
    // ユーザーが明確に操作した場合のみ一時的なセッション記録
    ref.read(deviceStatusProvider.notifier).acknowledgeSuggestionType(suggestionType);
    
    // 質問送信後はカードを削除
    ref.read(timelineProvider.notifier).removeTimelineItem(id);
  }

  // _getDisplayTextForQuery関数を削除
  // バックエンドが生成したaction_display_textを直接使用するため不要

  /// 安否確認SMS送信ダイアログを表示（統合版）
  Future<void> _showSafetySMSDialog(BuildContext context, String itemId, Map<String, dynamic>? actionData) async {
    try {
      // debugPrint('[SuggestionTimelineItem] _showSafetySMSDialog called with actionData: $actionData');
      
      final localStorageService = LocalStorageService();
      final emergencyContacts = await localStorageService.getEmergencyContacts();
      
      if (emergencyContacts.isEmpty) {
        if (context.mounted) {
          _showContactRequiredDialog(context);
        }
        return;
      }

      // actionDataがnullまたはform_dataがない場合、デフォルトのform_dataを作成
      // 変更不可能なマップの場合があるので、新しいマップを作成
      final l10n = AppLocalizations.of(context)!;
      
      // actionDataが変更不可能な場合があるため、深くコピーを作成
      final Map<String, dynamic> finalActionData = {};
      if (actionData != null) {
        for (final entry in actionData.entries) {
          if (entry.value is Map) {
            finalActionData[entry.key] = Map<String, dynamic>.from(entry.value as Map);
          } else {
            finalActionData[entry.key] = entry.value;
          }
        }
      }
      
      if (!finalActionData.containsKey('form_data')) {
        // バックエンドの形式に合わせたデフォルト値
        finalActionData['form_data'] = {
          'message_templates': {
            'recommended': l10n.smsTemplateRecommended,
          },
          'default_template': l10n.smsTemplateRecommended,
          'include_location': true,
          'priority': 'normal',
          'disaster_context': {
            'is_emergency': false,
            'disaster_type': 'general',
            'timestamp': DateTime.now().toIso8601String(),
          },
          'ui_labels': {
            'dialog_title': l10n.safetyConfirmationSms,
            'send_button': l10n.send,
            'cancel_button': l10n.cancel,
            'send_to_all': l10n.sendToAllContacts,
            'send_to_selected': l10n.selectIndividually,
          },
        };
      }

      // Use unified SMSConfirmationDialog
      if (context.mounted) {
        bool smsSent = false;
        
        await SMSConfirmationDialog.show(
          context,
          finalActionData,
          onSent: (result) {
            // Mark as sent
            smsSent = true;
            
            // Remove card after SMS sent
            ref.read(timelineProvider.notifier).removeTimelineItem(itemId);
            
            // Log the result
      // debugPrint('[SuggestionTimelineItem] SMS Send Result: $result');
          },
        );
        
        // Remove card if dialog was cancelled (not sent)
        if (context.mounted && !smsSent) {
          ref.read(timelineProvider.notifier).removeTimelineItem(itemId);
        }
      }
    } catch (e) {
      // debugPrint('[SuggestionTimelineItem] Error in _showSafetySMSDialog: $e');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('エラーが発生しました: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }


  /// 連絡先が必要な場合のダイアログ
  void _showContactRequiredDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.warning, color: EmergencyTheme.warningOrange, size: 32),
            const SizedBox(width: EmergencyTheme.smallSpacing),
            Expanded(
              child: Text(
                AppLocalizations.of(context)!.emergencyContacts,
                style: EmergencyTheme.emergencyBodyStyle,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              AppLocalizations.of(context)!.pleaseEnterNameAndPhone,
              style: EmergencyTheme.accessibleBodyStyle,
            ),
            const SizedBox(height: EmergencyTheme.mediumSpacing),
            EmergencyWidgets.buildEmergencyActionButton(
              label: AppLocalizations.of(context)!.registerEmergencyContact,
              icon: Icons.person_add,
              onPressed: () {
                Navigator.of(context).pop();
                _showAddContactDialog(context);
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(AppLocalizations.of(context)!.skip),
          ),
        ],
      ),
    );
  }

  /// 日時をフォーマットする
  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 0) {
      return '${difference.inDays}日前';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}時間前';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}分前';
    } else {
      return 'たった今';
    }
  }

  /// URLを開く
  Future<void> _launchUrl(String url) async {
    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('URLを開けませんでした: $url'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      // debugPrint('Error launching URL: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('エラーが発生しました: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// ローカライズされたアクションテキストを取得
  String _getLocalizedActionText(String suggestionType, String? actionDisplayText) {
    if (actionDisplayText != null && actionDisplayText.isNotEmpty) {
      return actionDisplayText;
    }

    // フォールバック：タイプベースのデフォルトテキスト
    final l10n = AppLocalizations.of(context)!;
    switch (suggestionType) {
      case 'emergency_action':
        return l10n.emergencyActionRequired;
      case 'evacuation_info':
        return l10n.evacuationInfo;
      case 'shelter_info':
        return l10n.shelterInfo;
      case 'safety_confirmation':
        return l10n.safetyConfirmation;
      case 'hazard_map_info':
        return l10n.hazardMapInfo;
      case 'disaster_info':
        return l10n.disasterLatestInfo;
      default:
        return l10n.askQuestion;
    }
  }

  /// 避難所検索を処理する
  void _handleShelterSearch(BuildContext context, Map<String, dynamic>? actionData) {
    // 避難所検索の質問は既に上で送信済みなので、ここでは追加の処理のみ行う
    // 必要に応じて、地図表示などの追加処理をここに実装
    if (kDebugMode) {
      print('[SuggestionTimelineItem] 📍 Shelter search handled - actionData: $actionData');
    }
  }
}
