import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/core/models/alert_model.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'dart:ui';

class AlertTimelineItem extends ConsumerStatefulWidget {
  final TimelineItemModel model;
  final bool shouldHighlight;

  const AlertTimelineItem({
    super.key,
    required this.model,
    this.shouldHighlight = false,
  });

  @override
  ConsumerState<AlertTimelineItem> createState() => _AlertTimelineItemState();
}

class _AlertTimelineItemState extends ConsumerState<AlertTimelineItem> 
    with SingleTickerProviderStateMixin {
  late AnimationController _highlightController;
  late Animation<double> _highlightAnimation;

  @override
  void initState() {
    super.initState();
    _highlightController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _highlightAnimation = CurvedAnimation(
      parent: _highlightController,
      curve: Curves.easeInOut,
    );

    if (widget.shouldHighlight) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _highlightController.forward().then((_) {
          _highlightController.reverse();
        });
      });
    }
  }

  @override
  void dispose() {
    _highlightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.model.when(
      alert: (id, timestamp, severity, title, message) => _buildAlertItem(
        context,
        severity: severity,
        title: title,
        message: message,
        timestamp: timestamp,
      ),
      suggestion: (id, suggestionType, timestamp, content, actionData, actionQuery, actionDisplayText) =>
          const SizedBox.shrink(),
      chat: (id, timestamp, messageText, senderNickname, isOwnMessage) =>
          const SizedBox.shrink(),
      chatWithAction: (id, timestamp, messageText, senderNickname, isOwnMessage, requiresAction, actionData) =>
          const SizedBox.shrink(),
    );
  }

  Widget _buildAlertItem(
    BuildContext context, {
    required String severity,
    required String title,
    required String message,
    required DateTime timestamp,
  }) {

    final isEmergency = _isEmergencyAlert(severity);
    
    return AnimatedBuilder(
      animation: _highlightAnimation,
      builder: (context, child) {
        return Container(
          margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              if (_highlightAnimation.value > 0)
                BoxShadow(
                  color: isEmergency 
                    ? Colors.red.withValues(alpha: 0.6 * _highlightAnimation.value)
                    : Colors.orange.withValues(alpha: 0.6 * _highlightAnimation.value),
                  blurRadius: 20 * _highlightAnimation.value,
                  spreadRadius: 5 * _highlightAnimation.value,
                ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(
              color: isEmergency 
                ? Colors.red.withValues(alpha: 0.1)
                : Colors.white.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isEmergency 
                  ? Colors.red.withValues(alpha: 0.3)
                  : Colors.white.withValues(alpha: 0.3),
                width: 1.5,
              ),
              boxShadow: isEmergency ? [
                BoxShadow(
                  color: Colors.red.withValues(alpha: 0.2),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ] : null,
            ),
            child: InkWell(
              borderRadius: BorderRadius.circular(20),
              onTap: () => _showAlertDetails(
                context,
                title: title,
                message: message,
                severity: severity,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (isEmergency) _buildEmergencyHeader(context, severity),
                  Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: isEmergency 
                                    ? [Colors.red, Colors.orange]
                                    : [const Color(0xFF00D9FF), const Color(0xFF00E5CC)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(12),
                                boxShadow: [
                                  BoxShadow(
                                    color: isEmergency 
                                      ? Colors.red.withValues(alpha: 0.3)
                                      : const Color(0xFF00E5CC).withValues(alpha: 0.3),
                                    blurRadius: 10,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Icon(
                                _getSeverityIconData(severity),
                                color: Colors.white,
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                title,
                                style: TextStyle(
                                  fontSize: isEmergency ? 18 : 16,
                                  fontWeight: FontWeight.w700,
                                  color: isEmergency 
                                    ? Colors.red[900]
                                    : const Color(0xFF1A3333),
                                ),
                              ),
                            ),
                            if (isEmergency)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [Colors.red, Colors.orange],
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                  ),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: const Text(
                                  '緊急',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          message,
                          style: TextStyle(
                            fontSize: 14,
                            color: isEmergency 
                              ? Colors.red[800]
                              : const Color(0xFF2D4A4A),
                            fontWeight: isEmergency ? FontWeight.w600 : FontWeight.w500,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              _formatDateTime(timestamp),
                              style: TextStyle(
                                fontSize: 12,
                                color: const Color(0xFF2D4A4A).withValues(alpha: 0.7),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
        },
      );
  }

  void _showAlertDetails(
    BuildContext context, {
    required String title,
    required String message,
    String? severity,
  }) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.5),
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Dialog(
          backgroundColor: Colors.transparent,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.9),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.3),
                    width: 1.5,
                  ),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Header
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: severity != null && _isEmergencyAlert(severity)
                            ? [Colors.red.withValues(alpha: 0.1), Colors.orange.withValues(alpha: 0.1)]
                            : [const Color(0xFF00D9FF).withValues(alpha: 0.1), const Color(0xFF00E5CC).withValues(alpha: 0.1)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: const BorderRadius.only(
                          topLeft: Radius.circular(20),
                          topRight: Radius.circular(20),
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: severity != null && _isEmergencyAlert(severity)
                                  ? [Colors.red, Colors.orange]
                                  : [const Color(0xFF00D9FF), const Color(0xFF00E5CC)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Icon(
                              severity != null ? _getSeverityIconData(severity) : Icons.info,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              title,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF1A3333),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Content
                    Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text(
                        message,
                        style: const TextStyle(
                          fontSize: 15,
                          color: Color(0xFF2D4A4A),
                          fontWeight: FontWeight.w500,
                          height: 1.4,
                        ),
                      ),
                    ),
                    // Actions
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                      child: SizedBox(
                        width: double.infinity,
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: BackdropFilter(
                            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                            child: Container(
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFF00D9FF), Color(0xFF00E5CC)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Material(
                                color: Colors.transparent,
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(12),
                                  onTap: () => Navigator.pop(context),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(vertical: 14),
                                    child: const Text(
                                      '閉じる',
                                      style: TextStyle(
                                        fontSize: 15,
                                        fontWeight: FontWeight.w600,
                                        color: Colors.white,
                                      ),
                                      textAlign: TextAlign.center,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  IconData _getSeverityIconData(String severity) {
    switch (severity.toLowerCase()) {
      case 'high':
      case 'emergency':
      case 'critical':
        return Icons.warning;
      case 'medium':
        return Icons.warning_amber;
      default:
        return Icons.info;
    }
  }





  bool _isEmergencyAlert(String severity) {
    return severity.toLowerCase() == 'high' || 
           severity.toLowerCase() == 'emergency' ||
           severity.toLowerCase() == 'critical';
  }

  Widget _buildEmergencyHeader(BuildContext context, String severity) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Colors.red, Colors.orange],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.warning,
              color: Colors.white,
              size: 16,
            ),
          ),
          const SizedBox(width: 10),
          const Text(
            '緊急アラート',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
              fontSize: 16,
            ),
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              severity.toUpperCase(),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }



  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.year}/${dateTime.month}/${dateTime.day} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
  }
}

class AlertBanner extends StatelessWidget {
  final AlertModel alert;
  final VoidCallback? onDismiss;

  const AlertBanner({
    super.key,
    required this.alert,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: _getAlertColor(alert.severity),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(8),
          bottomRight: Radius.circular(8),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    _getAlertIcon(alert.source),
                    color: Colors.white,
                    size: 24,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      alert.title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (onDismiss != null)
                    IconButton(
                      icon: const Icon(
                        Icons.close,
                        color: Colors.white,
                        size: 20,
                      ),
                      onPressed: onDismiss,
                      constraints: const BoxConstraints(),
                      padding: const EdgeInsets.all(4),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                alert.message,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      alert.severity.name.toUpperCase(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    '${alert.timestamp.hour.toString().padLeft(2, '0')}:${alert.timestamp.minute.toString().padLeft(2, '0')}',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.8),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getAlertColor(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.emergency:
      case AlertSeverity.critical:
        return Colors.red.shade600;
      case AlertSeverity.danger:
        return Colors.orange.shade600;
      case AlertSeverity.warning:
        return Colors.amber.shade600;
      case AlertSeverity.info:
        return Colors.blue.shade600;
    }
  }

  IconData _getAlertIcon(String alertType) {
    switch (alertType.toLowerCase()) {
      case 'earthquake':
        return Icons.vibration;
      case 'tsunami':
        return Icons.waves;
      case 'typhoon':
      case 'hurricane':
        return Icons.tornado;
      case 'flood':
        return Icons.water_damage;
      case 'fire':
        return Icons.local_fire_department;
      case 'volcano':
        return Icons.landscape;
      case 'weather':
        return Icons.wb_cloudy;
      case 'emergency':
      default:
        return Icons.warning;
    }
  }
}
