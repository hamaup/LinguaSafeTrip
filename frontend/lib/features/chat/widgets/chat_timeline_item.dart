import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/models/timeline_item_model.dart';
import 'package:frontend/features/main_timeline/widgets/timeline_shelter_map.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/core/providers/shelter_provider.dart';
import 'package:frontend/l10n/app_localizations.dart';

class ChatTimelineItem extends ConsumerWidget {
  final TimelineItemModel model;

  const ChatTimelineItem({
    super.key,
    required this.model,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return model.when(
      alert: (id, timestamp, severity, title, message) => const SizedBox.shrink(),
      suggestion: (id, suggestionType, timestamp, content, actionData, actionQuery, actionDisplayText) => const SizedBox.shrink(),
      chat: (id, timestamp, messageText, senderNickname, isOwnMessage) {
        // TimelineProviderから避難所データを取得
        List<dynamic>? shelters;
        if (!isOwnMessage) {
          final timelineState = ref.watch(timelineProvider);
          final shelterDataId = timelineState.chatIdToShelterDataId[id];
          if (shelterDataId != null) {
            final shelterData = timelineState.shelterDataCache[shelterDataId];
            if (shelterData != null && shelterData['shelters'] != null) {
              shelters = shelterData['shelters'] as List<dynamic>;
              if (kDebugMode) {
                debugPrint('[ChatTimelineItem] Retrieved ${shelters.length} shelters from timeline cache for chat $id');
              }
            }
          }
          
          // TimelineProviderにデータがない場合はShelterProviderからも確認
          if (shelters == null) {
            shelters = ref.read(shelterProvider.notifier).getSheltersForChat(id);
          }
        }
        
        return _buildChatItem(
          context,
          ref,
          messageText: messageText,
          senderNickname: senderNickname,
          isOwnMessage: isOwnMessage,
          timestamp: timestamp,
          shelters: shelters,
        );
      },
      chatWithAction: (id, timestamp, messageText, senderNickname, isOwnMessage, requiresAction, actionData) {
        // TimelineProviderから避難所データを取得
        List<dynamic>? shelters;
        if (!isOwnMessage) {
          final timelineState = ref.watch(timelineProvider);
          final shelterDataId = timelineState.chatIdToShelterDataId[id];
          if (shelterDataId != null) {
            final shelterData = timelineState.shelterDataCache[shelterDataId];
            if (shelterData != null && shelterData['shelters'] != null) {
              shelters = shelterData['shelters'] as List<dynamic>;
              if (kDebugMode) {
                debugPrint('[ChatTimelineItem] Retrieved ${shelters.length} shelters from timeline cache for chatWithAction $id');
              }
            }
          }
          
          // TimelineProviderにデータがない場合はShelterProviderからも確認
          if (shelters == null) {
            shelters = ref.read(shelterProvider.notifier).getSheltersForChat(id);
          }
        }
        
        return _buildChatItem(
          context,
          ref,
          messageText: messageText,
          senderNickname: senderNickname,
          isOwnMessage: isOwnMessage,
          timestamp: timestamp,
          shelters: shelters,
        );
      },
    );
  }

  Widget _buildChatItem(
    BuildContext context,
    WidgetRef ref, {
    required String messageText,
    required String senderNickname,
    required bool isOwnMessage,
    required DateTime timestamp,
    List<dynamic>? shelters,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
      child: Row(
        mainAxisAlignment: isOwnMessage ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isOwnMessage) ...[
            _buildAvatar(senderNickname, isOwnMessage),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: ClipRRect(
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isOwnMessage ? 16 : 4),
                bottomRight: Radius.circular(isOwnMessage ? 4 : 16),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
                child: Container(
                  constraints: BoxConstraints(
                    maxWidth: MediaQuery.of(context).size.width * 0.75,
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: isOwnMessage 
                        ? const Color(0xFF00E5CC).withValues(alpha: 0.08)
                        : Colors.white.withValues(alpha: 0.92),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(isOwnMessage ? 16 : 4),
                      bottomRight: Radius.circular(isOwnMessage ? 4 : 16),
                    ),
                    border: Border.all(
                      color: isOwnMessage 
                        ? const Color(0xFF00E5CC).withValues(alpha: 0.3)
                        : const Color(0xFFE8FFFC).withValues(alpha: 0.5),
                      width: 0.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: isOwnMessage
                            ? const Color(0xFF00E5CC).withValues(alpha: 0.1)
                            : const Color(0xFF00D9FF).withValues(alpha: 0.05),
                        blurRadius: 20,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!isOwnMessage)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        senderNickname,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: const Color(0xFF5FA8A8),
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  MarkdownBody(
                    data: _preprocessMessageText(messageText),
                    onTapLink: (text, href, title) async {
                      if (href != null) {
                        await _launchUrl(href);
                      }
                    },
                    styleSheet: MarkdownStyleSheet(
                      p: TextStyle(
                        fontSize: 15,
                        color: isOwnMessage ? const Color(0xFF2D4A4A) : const Color(0xFF2D4A4A),
                        height: 1.4,
                        letterSpacing: 0.3,
                      ),
                      strong: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: isOwnMessage ? const Color(0xFF1A3333) : const Color(0xFF1A3333),
                      ),
                      em: TextStyle(
                        fontSize: 15,
                        fontStyle: FontStyle.italic,
                        color: isOwnMessage ? const Color(0xFF5FA8A8) : const Color(0xFF5FA8A8),
                      ),
                      code: TextStyle(
                        fontFamily: 'monospace',
                        backgroundColor: const Color(0xFFE8FFFC).withValues(alpha: 0.3),
                        color: const Color(0xFF00D9FF),
                        fontSize: 13,
                      ),
                      blockquote: TextStyle(
                        color: const Color(0xFF7FC4C4),
                        fontStyle: FontStyle.italic,
                      ),
                      h1: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF1A3333),
                      ),
                      h2: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF1A3333),
                      ),
                      h3: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF1A3333),
                      ),
                      a: TextStyle(
                        color: const Color(0xFF00D9FF),
                        decoration: TextDecoration.underline,
                      ),
                    ),
                    shrinkWrap: true,
                    selectable: true,
                  ),
                  // AI応答の不確実性注記
                  if (!isOwnMessage) ...[
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
                  // 避難所マップを表示（避難所データがある場合は常に表示）
                  if (shelters != null && shelters.isNotEmpty) ...[
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: _buildShelterMap(ref, shelters),
                    ),
                  ],
                  const SizedBox(height: 4),
                  Text(
                    _formatTime(timestamp),
                    style: TextStyle(
                      fontSize: 11,
                      color: const Color(0xFF9ECECE),
                    ),
                  ),
                ],
              ),
                ),
              ),
            ),
          ),
          if (isOwnMessage) ...[
            const SizedBox(width: 8),
            _buildAvatar(senderNickname, isOwnMessage),
          ],
        ],
      ),
    );
  }

  Widget _buildAvatar(String senderNickname, bool isOwnMessage) {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isOwnMessage 
            ? [
                const Color(0xFF00D9FF),
                const Color(0xFF00E5CC),
              ]
            : [
                const Color(0xFFB2F5EA),
                const Color(0xFF7FC4C4),
              ],
        ),
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: isOwnMessage
                ? const Color(0xFF00E5CC).withValues(alpha: 0.3)
                : const Color(0xFF7FC4C4).withValues(alpha: 0.3),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: Text(
          isOwnMessage 
            ? 'U'
            : senderNickname.isNotEmpty ? senderNickname[0].toUpperCase() : 'A',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  String _preprocessMessageText(String text) {
    // 改行文字を正規化
    String processed = text.replaceAll('\\n', '\n');
    
    // [domain.com] 形式のリンクを [domain.com](https://domain.com) 形式に変換
    processed = processed.replaceAllMapped(
      RegExp(r'\[([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[/\w.-]*)\]'),
      (match) {
        final url = match.group(1)!;
        return '[$url](https://$url)';
      },
    );
    
    return processed;
  }

  Future<void> _launchUrl(String url) async {
    try {
      // URLにhttpプロトコルが含まれていない場合は追加
      String fullUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        fullUrl = 'https://$url';
      }
      
      final uri = Uri.parse(fullUrl);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
      // debugPrint('Could not launch $fullUrl');
      }
    } catch (e) {
      // debugPrint('Error launching URL: $e');
    }
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'たった今';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}分前';
    } else if (difference.inDays < 1) {
      return '${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
    } else {
      return '${timestamp.month}/${timestamp.day} ${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
    }
  }

  bool _isShelterSearchRelated(String messageText) {
    // 避難所検索に関連するキーワードをチェック
    final shelterKeywords = [
      // Japanese keywords
      '避難所', '避難場所', '避難先', '安全な場所', 
      '近くの避難', '避難所情報', '避難所一覧',
      // English keywords
      'shelter', 'evacuation', 'emergency shelter',
      'safe location', 'refuge', 'evacuation center',
      'evacuation site', 'emergency location',
      // Common patterns in responses
      'found', 'located', 'nearest', 'closest',
      'km away', 'distance', 'sports center', 'center',
      'school', '学校', 'センター', '体育館'
    ];
    
    final lowercaseMessage = messageText.toLowerCase();
    return shelterKeywords.any((keyword) => 
      lowercaseMessage.contains(keyword.toLowerCase()));
  }

  Widget _buildShelterMap(WidgetRef ref, List<dynamic> shelters) {
    if (shelters.isEmpty) {
      return const SizedBox.shrink();
    }

    // 現在の位置情報を取得（必要に応じて）
    LatLng? userLocation;
    // TODO: 必要に応じて位置情報を取得
    
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: SizedBox(
          height: 250,
          child: TimelineShelterMapWidget(
            shelters: shelters,
            userLocation: userLocation,
          ),
        ),
      ),
    );
  }
}