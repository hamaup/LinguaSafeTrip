import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:frontend/core/services/local_storage_service.dart';
import 'package:frontend/core/models/emergency_contact_model.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'package:url_launcher/url_launcher.dart';

/// SMS確認ダイアログ - バックエンドからの指示に基づいて表示
class SMSConfirmationDialog extends StatefulWidget {
  final Map<String, dynamic> actionData;
  final Function(Map<String, dynamic>)? onSent;

  const SMSConfirmationDialog({
    Key? key,
    required this.actionData,
    this.onSent,
  }) : super(key: key);

  static Future<void> show(
    BuildContext context,
    Map<String, dynamic> actionData, {
    Function(Map<String, dynamic>)? onSent,
  }) async {
    final formData = actionData['form_data'] as Map<String, dynamic>?;
    if (formData == null) return;

    // 緊急連絡先を取得
    final localStorageService = LocalStorageService();
    final emergencyContacts = await localStorageService.getEmergencyContacts();
    
    if (emergencyContacts.isEmpty) {
      // 緊急連絡先が登録されていない場合
      if (context.mounted) {
        await showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(AppLocalizations.of(context)!.emergencyContactRequiredTitle),
            content: Text(AppLocalizations.of(context)!.emergencyContactRequiredMessage),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text(AppLocalizations.of(context)!.ok),
              ),
            ],
          ),
        );
      }
      return;
    }

    if (context.mounted) {
      await showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => SMSConfirmationDialog(
          actionData: actionData,
          onSent: onSent,
        ),
      );
    }
  }

  @override
  State<SMSConfirmationDialog> createState() => _SMSConfirmationDialogState();
}

class _SMSConfirmationDialogState extends State<SMSConfirmationDialog> {
  late TextEditingController _messageController;
  bool _includeLocation = true;
  String _selectedTemplate = 'recommended';
  List<EmergencyContactModel> _emergencyContacts = [];
  Set<String> _selectedContacts = {};
  Map<String, dynamic> _formData = {};
  Map<String, dynamic> _templates = {};
  Map<String, dynamic> _uiLabels = {};

  @override
  void initState() {
    super.initState();
    _formData = widget.actionData['form_data'] ?? {};
    _templates = _formData['message_templates'] ?? {};
    _uiLabels = _formData['ui_labels'] ?? {};
    
    final defaultMessage = _templates['recommended'] ?? 
        _formData['default_template'] ?? 
        AppLocalizations.of(context)!.iAmSafe;
    
    _messageController = TextEditingController(text: defaultMessage);
    _includeLocation = _formData['include_location'] ?? true;
    
    _loadContacts();
  }

  Future<void> _loadContacts() async {
    final localStorageService = LocalStorageService();
    final contacts = await localStorageService.getEmergencyContacts();
    
    setState(() {
      _emergencyContacts = contacts;
      // デフォルト選択を適用
      final defaultSelection = List<String>.from(
        _formData['contact_groups']?['default_selection'] ?? ['family', 'emergency']
      );
      
      // Select all contacts by default in emergency mode
      if (_formData['disaster_context']?['is_emergency'] == true) {
        for (final contact in contacts) {
          _selectedContacts.add(contact.phoneNumber);
        }
      }
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  void _onTemplateChanged(String? templateKey) {
    if (templateKey != null && _templates.containsKey(templateKey)) {
      setState(() {
        _selectedTemplate = templateKey;
        _messageController.text = _templates[templateKey] ?? '';
      });
    }
  }

  void _updateMessageWithLocation() {
    // Use appropriate template based on location setting
    final baseTemplate = _templates['recommended'] ?? 'I am safe.';
    final locationTemplate = _templates['recommended_with_location'] ?? baseTemplate;
    
    if (_includeLocation && _formData['user_location'] != null) {
      _messageController.text = locationTemplate;
    } else {
      _messageController.text = baseTemplate;
    }
  }

  Future<void> _sendSMS() async {
    final selectedPhones = _selectedContacts.toList();
    if (selectedPhones.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_uiLabels['recipients_required'] ?? 
              AppLocalizations.of(context)!.selectAtLeastOneContact),
        ),
      );
      return;
    }

    final message = _messageController.text.trim();
    if (message.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_uiLabels['message_required'] ?? 
              AppLocalizations.of(context)!.messageCannotBeEmpty),
        ),
      );
      return;
    }

    int successCount = 0;
    int failCount = 0;

    for (final phone in selectedPhones) {
      final success = await _sendSingleSMS(phone, message);
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
    }

    // Report back to backend if callback provided (no personal info)
    if (widget.onSent != null) {
      widget.onSent!({
        'sent_count': successCount,
        'failed_count': failCount,
        'message_type': _selectedTemplate,
        'included_location': _includeLocation,
        'is_emergency': _formData['disaster_context']?['is_emergency'] ?? false,
        'disaster_type': _formData['disaster_context']?['disaster_type'] ?? 'general',
      });
    }

    if (mounted) {
      Navigator.of(context).pop();
      
      if (successCount > 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)!.smsAppOpened),
            backgroundColor: Colors.green,
          ),
        );
      }
    }
  }

  Future<bool> _sendSingleSMS(String phoneNumber, String message) async {
    final Uri smsUri = Uri(
      scheme: 'sms',
      path: phoneNumber,
      queryParameters: {'body': message},
    );
    
    try {
      if (await canLaunchUrl(smsUri)) {
        await launchUrl(smsUri);
        return true;
      }
    } catch (e) {
      // debugPrint('Error sending SMS to $phoneNumber: $e');
    }
    return false;
  }

  Widget _buildContactsList() {
    if (_emergencyContacts.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(
            AppLocalizations.of(context)!.noEmergencyContacts,
            style: TextStyle(color: Colors.grey[600]),
          ),
        ),
      );
    }
    
    return Column(
      children: _emergencyContacts.map((contact) {
        final isSelected = _selectedContacts.contains(contact.phoneNumber);
        
        return CheckboxListTile(
          title: Text(contact.name),
          subtitle: Text(contact.phoneNumber),
          secondary: contact.relationship != null
              ? Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Theme.of(context).brightness == Brightness.dark
                        ? Colors.grey[700]!.withOpacity(0.6)
                        : const Color(0xFF00E5CC).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    contact.relationship!,
                    style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.grey[300]
                          : null,
                    ),
                  ),
                )
              : null,
          value: isSelected,
          onChanged: (value) {
            setState(() {
              if (value ?? false) {
                _selectedContacts.add(contact.phoneNumber);
              } else {
                _selectedContacts.remove(contact.phoneNumber);
              }
            });
          },
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final dialogTitle = _uiLabels['dialog_title'] ?? l10n.sendSafetySms;
    
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: 600,
          maxHeight: MediaQuery.of(context).size.height * 0.9,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: Theme.of(context).brightness == Brightness.dark
                ? [
                    Colors.grey[900]!.withOpacity(0.95),
                    Colors.grey[850]!.withOpacity(0.85),
                  ]
                : [
                    Colors.white.withOpacity(0.95),
                    Colors.white.withOpacity(0.85),
                  ],
          ),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: const Color(0xFF00E5CC).withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Theme.of(context).brightness == Brightness.dark
                    ? Colors.grey[800]!.withOpacity(0.5)
                    : const Color(0xFF00E5CC).withOpacity(0.1),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(24),
                  topRight: Radius.circular(24),
                ),
              ),
              child: Row(
                children: [
                  const Icon(Icons.message, size: 28),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      dialogTitle,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            
            // Content
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Step 1: Select Recipients
                    _buildStep(
                      stepNumber: '1',
                      title: _uiLabels['select_recipients'] ?? l10n.selectRecipients,
                      color: const Color(0xFF00E5CC),
                      child: Column(
                        children: [
                          // Quick actions
                          Row(
                            children: [
                              Expanded(
                                child: TextButton.icon(
                                  icon: const Icon(Icons.check_box),
                                  label: Text(l10n.selectAll),
                                  onPressed: () {
                                    setState(() {
                                      for (final contact in _emergencyContacts) {
                                        _selectedContacts.add(contact.phoneNumber);
                                      }
                                    });
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: TextButton.icon(
                                  icon: const Icon(Icons.check_box_outline_blank),
                                  label: Text(l10n.deselectAll),
                                  onPressed: () {
                                    setState(() {
                                      _selectedContacts.clear();
                                    });
                                  },
                                ),
                              ),
                            ],
                          ),
                          const Divider(),
                          // Contacts list
                          _buildContactsList(),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Step 2: Edit Message
                    _buildStep(
                      stepNumber: '2',
                      title: _uiLabels['message_body'] ?? l10n.message,
                      color: const Color(0xFF00D9FF),
                      child: Column(
                        children: [
                          // Template selector removed - simplified to use only recommended template
                          
                          // Message editor
                          TextField(
                            controller: _messageController,
                            maxLines: 3,
                            decoration: InputDecoration(
                              labelText: _uiLabels['message_body'] ?? l10n.message,
                              border: const OutlineInputBorder(),
                              counterText: '${_messageController.text.length}/160',
                            ),
                            onChanged: (value) {
                              setState(() {
                                // Trigger rebuild for counter
                              });
                            },
                          ),
                          const SizedBox(height: 16),
                          
                          // Include location checkbox (simplified)
                          if (_formData['user_location'] != null)
                            CheckboxListTile(
                              title: Text(_uiLabels['include_location'] ?? l10n.includeLocation),
                              value: _includeLocation,
                              onChanged: (value) {
                                setState(() {
                                  _includeLocation = value ?? false;
                                  _updateMessageWithLocation();
                                });
                              },
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Actions
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Theme.of(context).brightness == Brightness.dark
                    ? Colors.grey[800]!.withOpacity(0.3)
                    : Colors.grey.withOpacity(0.05),
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(24),
                  bottomRight: Radius.circular(24),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Flexible(
                    child: Text(
                      '${_selectedContacts.length} ${l10n.contactsSelected}',
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: Text(_uiLabels['cancel_button'] ?? l10n.cancel),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.send, size: 16),
                        label: Text(_uiLabels['send_button'] ?? l10n.send),
                        onPressed: _selectedContacts.isNotEmpty ? _sendSMS : null,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF00E5CC),
                          foregroundColor: Colors.black,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
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
    );
  }

  Widget _buildStep({
    required String stepNumber,
    required String title,
    required Color color,
    required Widget child,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        color: isDark 
            ? Colors.grey[800]!.withOpacity(0.4)
            : color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark 
              ? Colors.grey[600]!.withOpacity(0.5)
              : color.withOpacity(0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isDark 
                  ? Colors.grey[700]!.withOpacity(0.6)
                  : color.withOpacity(0.1),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      stepNumber,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: child,
          ),
        ],
      ),
    );
  }

  String _getTemplateLabel(String key) {
    final labels = {
      'recommended': AppLocalizations.of(context)!.recommended,
      'detailed': AppLocalizations.of(context)!.detailed,
      'check_in': AppLocalizations.of(context)!.checkIn,
      'recommended_with_location': '${AppLocalizations.of(context)!.recommended} (📍)',
      'detailed_with_location': '${AppLocalizations.of(context)!.detailed} (📍)',
      'check_in_with_location': '${AppLocalizations.of(context)!.checkIn} (📍)',
    };
    
    return labels[key] ?? key;
  }
}