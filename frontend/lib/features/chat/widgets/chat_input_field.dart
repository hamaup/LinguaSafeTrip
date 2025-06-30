import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
// import 'package:frontend/features/chat/providers/voice_input_provider.dart'; // Temporarily disabled
import 'package:frontend/features/chat/providers/chat_provider.dart';
import 'package:frontend/features/chat/widgets/voice_recording_ripple.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';
import 'package:frontend/l10n/app_localizations.dart';

class ChatInputField extends ConsumerStatefulWidget {
  const ChatInputField({super.key});

  @override
  ConsumerState<ChatInputField> createState() => _ChatInputFieldState();
}

class _ChatInputFieldState extends ConsumerState<ChatInputField> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _sendMessage() async {
    final message = _controller.text.trim();
    if (message.isNotEmpty) {
      _controller.clear();
      
      try {
        // チャットメッセージ送信
        final chatItem = await ref.read(chatProvider.notifier).sendMessage(message);
        
        // タイムラインに追加
        if (chatItem != null) {
          ref.read(timelineProvider.notifier).addTimelineItem(chatItem);
        }
      } catch (e) {
        // エラーハンドリング
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('メッセージの送信に失敗しました: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isChatLoading = ref.watch(chatProvider.select((state) => state.isLoading));
    
    // Voice input temporarily disabled
    // final voiceInputState = ref.watch(voiceInputProvider);
    const isListening = false;
    const recognizedText = '';
    const isVoiceInputEnabled = false; // Temporarily disabled
    
    // 音声認識のテキストがある場合、自動的にテキストフィールドに設定
    // Temporarily disabled
    // if (recognizedText.isNotEmpty && _controller.text != recognizedText) {
    //   _controller.text = recognizedText;
    //   _controller.selection = TextSelection.fromPosition(
    //     TextPosition(offset: _controller.text.length),
    //   );
    // }

    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.fromLTRB(12.0, 12.0, 12.0, 12.0),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.9),
            border: Border(
              top: BorderSide(
                color: Colors.grey.withValues(alpha: 0.3),
                width: 1,
              ),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 8,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            children: [
              // マイクボタン with ripple animation (音声入力が有効な場合のみ表示)
              if (isVoiceInputEnabled)
                Stack(
                  alignment: Alignment.center,
                  children: [
                    VoiceRecordingRipple(
                      isRecording: isListening,
                      size: 48.0,
                    ),
                    IconButton(
                      icon: Icon(
                        isListening ? Icons.mic : Icons.mic_none,
                        color: isListening ? Colors.red : null,
                      ),
                      onPressed: null, // Voice input temporarily disabled
                    ),
                  ],
                ),
              Expanded(
                child: Stack(
                  children: [
                    TextField(
                      key: const Key('chat_input_field'),
                      controller: _controller,
                      decoration: InputDecoration(
                        hintText: AppLocalizations.of(context)?.messageInputHint ?? 'メッセージを入力...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24.0),
                          borderSide: BorderSide(
                            color: isListening ? Colors.red : Colors.grey,
                            width: isListening ? 2.0 : 1.0,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24.0),
                          borderSide: BorderSide(
                            color: isListening ? Colors.red : Colors.grey,
                            width: isListening ? 2.0 : 1.0,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24.0),
                          borderSide: BorderSide(
                            color: isListening ? Colors.red : Theme.of(context).primaryColor,
                            width: 2.0,
                          ),
                        ),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
                      ),
                      onChanged: (value) => ref
                          .read(timelineProvider.notifier)
                          .updateChatInput(value),
                      onSubmitted: (_) => _sendMessage(),
                      maxLines: null,
                      enabled: !isListening, // 録音中は編集不可
                    ),
                    // 録音中のアニメーション
                    if (isListening)
                      Positioned.fill(
                        child: IgnorePointer(
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 1000),
                            curve: Curves.easeInOut,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(24.0),
                              border: Border.all(
                                color: Colors.red.withValues(alpha: 0.3),
                                width: 2.0,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              isChatLoading
                  ? Stack(
                      alignment: Alignment.center,
                      children: [
                        const SizedBox(
                          width: 48,
                          height: 48,
                          child: Padding(
                            padding: EdgeInsets.all(12.0),
                            child: CircularProgressIndicator(
                              strokeWidth: 2.0,
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                            ),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.stop_circle_outlined, color: Colors.red, size: 20),
                          onPressed: () {
                            ref.read(chatProvider.notifier).cancelChat();
                          },
                          tooltip: '中止',
                        ),
                      ],
                    )
                  : IconButton(
                      key: const Key('chat_send_button'),
                      icon: const Icon(Icons.send),
                      onPressed: isListening ? null : _sendMessage,
                    ),
            ],
          ),
        ),
      ),
    );
  }
}
