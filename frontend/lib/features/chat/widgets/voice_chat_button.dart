import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/voice_input_provider.dart';
import '../services/audio_chat_service.dart';
import '../../main_timeline/providers/timeline_provider.dart';
import '../../../core/services/api_service.dart';
import '../../../core/providers/service_providers.dart';
import '../../../core/utils/logger.dart';
import '../../../l10n/app_localizations.dart';

class VoiceChatButton extends ConsumerStatefulWidget {
  final String deviceId;
  final String sessionId;
  final double? latitude;
  final double? longitude;
  
  const VoiceChatButton({
    super.key,
    required this.deviceId,
    required this.sessionId,
    this.latitude,
    this.longitude,
  });

  @override
  ConsumerState<VoiceChatButton> createState() => _VoiceChatButtonState();
}

class _VoiceChatButtonState extends ConsumerState<VoiceChatButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  
  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }
  
  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }
  
  Future<void> _handleVoiceInput() async {
    final voiceState = ref.read(voiceInputProvider);
    final voiceNotifier = ref.read(voiceInputProvider.notifier);
    
    try {
      if (voiceState.isRecording) {
        // Stop recording and send audio
        _animationController.stop();
        await voiceNotifier.stopRecording();
        
        final audioData = voiceNotifier.getAudioData();
        if (audioData != null && audioData.isNotEmpty) {
          // Show uploading state
          voiceNotifier.setUploading(true);
          
          // Send audio to backend
          final apiService = ref.read(apiServiceProvider);
          final audioService = AudioChatService(apiService);
          
          final response = await audioService.sendAudioChat(
            audioData: audioData,
            deviceId: widget.deviceId,
            sessionId: widget.sessionId,
            latitude: widget.latitude,
            longitude: widget.longitude,
          );
          
          if (response != null) {
            // Add response to timeline
            ref.read(timelineProvider.notifier).addMessage(response);
          }
          
          // Clear audio data
          voiceNotifier.clearAudioData();
        }
      } else {
        // Start recording
        _animationController.repeat();
        await voiceNotifier.startRecording();
      }
    } catch (e) {
      logger.e('Voice input error', e);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)!.voiceInputError(e.toString())),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      voiceNotifier.setUploading(false);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    final voiceState = ref.watch(voiceInputProvider);
    
    return AnimatedScale(
      scale: voiceState.isRecording ? _scaleAnimation.value : 1.0,
      duration: const Duration(milliseconds: 200),
      child: Container(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: voiceState.isRecording
              ? LinearGradient(
                  colors: [
                    Colors.red.shade400,
                    Colors.red.shade600,
                  ],
                )
              : LinearGradient(
                  colors: [
                    Theme.of(context).primaryColor,
                    Theme.of(context).primaryColor.withOpacity(0.8),
                  ],
                ),
          boxShadow: voiceState.isRecording
              ? [
                  BoxShadow(
                    color: Colors.red.withOpacity(0.3),
                    blurRadius: 12,
                    spreadRadius: 2,
                  ),
                ]
              : [
                  BoxShadow(
                    color: Theme.of(context).primaryColor.withOpacity(0.3),
                    blurRadius: 8,
                    spreadRadius: 1,
                  ),
                ],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: voiceState.isUploading ? null : _handleVoiceInput,
            borderRadius: BorderRadius.circular(50),
            child: Container(
              padding: const EdgeInsets.all(16),
              child: voiceState.isUploading
                  ? SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : Icon(
                      voiceState.isRecording ? Icons.stop : Icons.mic,
                      color: Colors.white,
                      size: 24,
                    ),
            ),
          ),
        ),
      ),
    );
  }
}