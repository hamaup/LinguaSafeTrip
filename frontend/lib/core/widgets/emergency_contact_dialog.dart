import 'dart:ui';
import 'package:flutter/material.dart';
import '../../l10n/app_localizations.dart';
import '../constants/country_codes.dart';
import '../utils/phone_validator.dart';
import 'country_code_selector.dart';

class EmergencyContactDialog extends StatefulWidget {
  final Function(String name, String phone) onSave;
  final String? initialName;
  final String? initialPhone;
  final bool isEdit;

  const EmergencyContactDialog({
    super.key,
    required this.onSave,
    this.initialName,
    this.initialPhone,
    this.isEdit = false,
  });

  @override
  State<EmergencyContactDialog> createState() => _EmergencyContactDialogState();
}

class _EmergencyContactDialogState extends State<EmergencyContactDialog> {
  late final TextEditingController _nameController;
  late final TextEditingController _phoneController;
  late CountryCode _selectedCountry;
  String? _phoneError;
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.initialName);
    _phoneController = TextEditingController(text: widget.initialPhone);
    _selectedCountry = defaultCountryCode; // デフォルトは日本
    
    // 既存の電話番号から国番号を推測
    if (widget.initialPhone != null && widget.initialPhone!.startsWith('+')) {
      for (final country in countryCodes) {
        if (widget.initialPhone!.startsWith(country.dialCode)) {
          _selectedCountry = country;
          _phoneController.text = widget.initialPhone!.substring(country.dialCode.length);
          break;
        }
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  void _validatePhone() {
    setState(() {
      _phoneError = PhoneValidator.getErrorMessage(
        _phoneController.text,
        _selectedCountry.code,
      );
    });
  }

  String _getPhoneHint() {
    switch (_selectedCountry.code) {
      case 'JP':
        return '090-1234-5678';
      case 'US':
      case 'CA':
        return '(123) 456-7890';
      case 'CN':
        return '138 1234 5678';
      case 'KR':
        return '010-1234-5678';
      default:
        return '電話番号を入力';
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    
    return BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 40, sigmaY: 40),
      child: Dialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(28),
        ),
        elevation: 0,
        backgroundColor: Colors.transparent,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(28),
            color: Colors.white.withValues(alpha: 0.98),
            border: Border.all(
              color: const Color(0xFFE8FFFC).withValues(alpha: 0.4),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF00E5CC).withValues(alpha: 0.08),
                blurRadius: 40,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // ヘッダー
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [
                            Color(0xFF00D9FF),  // Fresh cyan
                            Color(0xFF00E5CC),  // Mint green
                          ],
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Icon(
                        widget.isEdit ? Icons.edit_rounded : Icons.person_add_rounded,
                        color: Colors.white,
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.isEdit 
                                ? (l10n?.editEmergencyContact ?? '緊急連絡先を編集')
                                : (l10n?.addEmergencyContact ?? '緊急連絡先を追加'),
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF2D4A4A),  // Fresh dark teal
                              letterSpacing: -0.5,
                            ),
                          ),
                          Text(
                            '大切な人の連絡先を登録',
                            style: TextStyle(
                              fontSize: 14,
                              color: const Color(0xFF7FC4C4),  // Light teal
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                // 入力フィールド
                Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0FFFE).withValues(alpha: 0.5),  // Mint tint
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFFB2F5EA).withValues(alpha: 0.5),
                      width: 0.5,
                    ),
                  ),
                  child: TextField(
                    controller: _nameController,
                    decoration: InputDecoration(
                      labelText: l10n?.contactName ?? '名前',
                      hintText: l10n?.contactNameHint ?? '連絡先名を入力...',
                      prefixIcon: Icon(Icons.person_outline_rounded, color: const Color(0xFF00D9FF)),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.all(16),
                      labelStyle: TextStyle(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? Colors.grey[400]
                            : const Color(0xFF5FA8A8),
                      ),
                      hintStyle: TextStyle(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? Colors.grey[600]
                            : Colors.grey[500],
                      ),
                      floatingLabelStyle: const TextStyle(color: Color(0xFF00D9FF)),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: const Color(0xFFF0FFFE).withValues(alpha: 0.5),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: _phoneError != null 
                              ? Colors.red.withValues(alpha: 0.5)
                              : const Color(0xFFB2F5EA).withValues(alpha: 0.5),
                          width: 0.5,
                        ),
                      ),
                      child: Row(
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(left: 8),
                            child: CountryCodeSelector(
                              selectedCountry: _selectedCountry,
                              onCountrySelected: (country) {
                                setState(() {
                                  _selectedCountry = country;
                                  _validatePhone();
                                });
                              },
                            ),
                          ),
                          Container(
                            width: 1,
                            height: 48,
                            color: const Color(0xFFB2F5EA).withValues(alpha: 0.3),
                            margin: const EdgeInsets.symmetric(horizontal: 8),
                          ),
                          Expanded(
                            child: TextField(
                              controller: _phoneController,
                              onChanged: (_) => _validatePhone(),
                              decoration: InputDecoration(
                                hintText: _getPhoneHint(),
                                border: InputBorder.none,
                                contentPadding: const EdgeInsets.only(right: 16),
                                hintStyle: TextStyle(
                                  color: Theme.of(context).brightness == Brightness.dark
                                      ? Colors.grey[600]
                                      : Colors.grey[500],
                                ),
                              ),
                              keyboardType: TextInputType.phone,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_phoneError != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8, left: 16),
                        child: Text(
                          _phoneError!,
                          style: TextStyle(
                            color: Colors.red,
                            fontSize: 12,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 24),
                // アクションボタン
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Flexible(
                      child: TextButton(
                        onPressed: () => Navigator.pop(context),
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: Text(
                          l10n?.cancel ?? 'キャンセル',
                          style: TextStyle(
                            color: const Color(0xFF5FA8A8),
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Container(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [
                            Color(0xFF00D9FF),  // Fresh cyan
                            Color(0xFF00E5CC),  // Mint green
                          ],
                        ),
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF00E5CC).withValues(alpha: 0.25),
                            blurRadius: 16,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: () {
                            _validatePhone();
                            if (_nameController.text.isNotEmpty && 
                                _phoneController.text.isNotEmpty &&
                                _phoneError == null) {
                              // 国際電話番号形式に変換してから保存
                              final internationalPhone = PhoneValidator.toInternationalFormat(
                                _phoneController.text,
                                _selectedCountry.dialCode,
                              );
                              widget.onSave(_nameController.text, internationalPhone);
                              Navigator.pop(context);
                            }
                          },
                          borderRadius: BorderRadius.circular(12),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.save_rounded, color: Colors.white, size: 18),
                                const SizedBox(width: 6),
                                Flexible(
                                  child: Text(
                                    l10n?.save ?? '保存',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w600,
                                      fontSize: 14,
                                    ),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
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
    );
  }
}