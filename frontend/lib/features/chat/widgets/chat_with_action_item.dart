import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/core/services/local_storage_service.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/main_timeline/widgets/sms_confirmation_dialog.dart';
import 'package:frontend/l10n/app_localizations.dart';

/// チャット応答にアクション（SMSフォーム表示など）が含まれる場合のウィジェット
class ChatWithActionItem extends ConsumerStatefulWidget {
  final String id;
  final String messageText;
  final String senderNickname;
  final bool isOwnMessage;
  final DateTime timestamp;
  final String? requiresAction;
  final Map<String, dynamic>? actionData;

  const ChatWithActionItem({
    Key? key,
    required this.id,
    required this.messageText,
    required this.senderNickname,
    required this.isOwnMessage,
    required this.timestamp,
    this.requiresAction,
    this.actionData,
  }) : super(key: key);

  @override
  ConsumerState<ChatWithActionItem> createState() => _ChatWithActionItemState();
}

class _ChatWithActionItemState extends ConsumerState<ChatWithActionItem> {
  bool _actionExecuted = false; // アクション実行済みフラグ

  @override
  void initState() {
    super.initState();
    // 🔍 SMS フォーム関連のデバッグログ
    debugPrint('[ChatWithActionItem] initState - requiresAction: ${widget.requiresAction}');
    debugPrint('[ChatWithActionItem] initState - actionData: ${widget.actionData != null ? 'Present' : 'null'}');
    
    // アクションがある場合は自動的に処理（一度のみ）
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && !_actionExecuted) {
        _handleAction();
      }
    });
  }

  Future<void> _handleAction() async {
    debugPrint('[ChatWithActionItem] _handleAction called');
    debugPrint('[ChatWithActionItem] requiresAction: ${widget.requiresAction}');
    debugPrint('[ChatWithActionItem] actionData present: ${widget.actionData != null}');
    debugPrint('[ChatWithActionItem] actionExecuted: $_actionExecuted');
    
    if (widget.requiresAction == null || widget.actionData == null || _actionExecuted) {
      debugPrint('[ChatWithActionItem] Action skipped - conditions not met');
      return;
    }

    _actionExecuted = true; // フラグを設定して重複実行を防ぐ
    debugPrint('[ChatWithActionItem] Processing action: ${widget.requiresAction}');

    switch (widget.requiresAction) {
      case 'show_sms_confirmation_form':
        debugPrint('[ChatWithActionItem] Showing SMS confirmation form');
        await _showSMSConfirmationForm();
        break;
      // 他のアクションタイプもここに追加可能
      default:
        debugPrint('[ChatWithActionItem] Unknown action type: ${widget.requiresAction}');
    }
  }

  Future<void> _showSMSConfirmationForm() async {
    final formData = widget.actionData?['form_data'] as Map<String, dynamic>?;
    if (formData == null) return;

    // 新しいSMSダイアログを使用
    await SMSConfirmationDialog.show(
      context,
      widget.actionData!,
      onSent: (result) async {
        // 送信結果をバックエンドに報告
        await _reportSMSResult(result);
        
        // アクション完了後、タイムラインからこのアイテムのアクション状態をクリア
        _clearActionFromTimeline();
      },
    );
  }

  void _clearActionFromTimeline() {
    // タイムラインプロバイダーからアクション状態をクリア
    try {
      ref.read(timelineProvider.notifier).clearItemAction(widget.id);
    } catch (e) {
      // エラーは無視
    }
  }

  Future<void> _reportSMSResult(Map<String, dynamic> result) async {
    // Log the result for debugging (no personal info included)
      // debugPrint('SMS Send Result: $result');
    
    // Backend reporting can be implemented here if needed
    // Note: result contains no personal information, only counts and metadata
  }

  @override
  Widget build(BuildContext context) {
    // 通常のチャットアイテムと同じ表示
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
      child: Row(
        mainAxisAlignment: widget.isOwnMessage ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!widget.isOwnMessage) ...[
            _buildAvatar(widget.senderNickname),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: _buildMessageBubble(),
          ),
          if (widget.isOwnMessage) ...[
            const SizedBox(width: 8),
            _buildAvatar(widget.senderNickname),
          ],
        ],
      ),
    );
  }

  Widget _buildAvatar(String nickname) {
    return CircleAvatar(
      radius: 18,
      backgroundColor: widget.isOwnMessage 
          ? const Color(0xFF00E5CC)
          : const Color(0xFF00D9FF),
      child: Text(
        nickname.isNotEmpty ? nickname[0].toUpperCase() : '?',
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
      ),
    );
  }

  Widget _buildMessageBubble() {
    return ClipRRect(
      borderRadius: BorderRadius.only(
        topLeft: const Radius.circular(16),
        topRight: const Radius.circular(16),
        bottomLeft: Radius.circular(widget.isOwnMessage ? 16 : 4),
        bottomRight: Radius.circular(widget.isOwnMessage ? 4 : 16),
      ),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
        child: Container(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.75,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: widget.isOwnMessage 
                ? const Color(0xFF00E5CC).withValues(alpha: 0.08)
                : Colors.white.withValues(alpha: 0.92),
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft: Radius.circular(widget.isOwnMessage ? 16 : 4),
              bottomRight: Radius.circular(widget.isOwnMessage ? 4 : 16),
            ),
            border: Border.all(
              color: widget.isOwnMessage 
                ? const Color(0xFF00E5CC).withValues(alpha: 0.3)
                : const Color(0xFFE8FFFC).withValues(alpha: 0.5),
              width: 0.5,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              MarkdownBody(
                data: widget.messageText,
                styleSheet: MarkdownStyleSheet(
                  p: TextStyle(
                    color: widget.isOwnMessage ? Colors.black87 : Colors.black87,
                    fontSize: 15,
                    height: 1.4,
                  ),
                ),
                onTapLink: (text, href, title) {
                  if (href != null) {
                    launchUrl(Uri.parse(href));
                  }
                },
                shrinkWrap: true,
              ),
              // AI応答の不確実性注記
              if (!widget.isOwnMessage) ...[
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    AppLocalizations.of(context)!.aiResponseDisclaimer,
                    style: TextStyle(
                      fontSize: 10,
                      color: const Color(0xFF9ECECE),
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}