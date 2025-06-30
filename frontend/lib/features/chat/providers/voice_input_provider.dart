import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter/foundation.dart';
import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';

part 'voice_input_provider.freezed.dart';
part 'voice_input_provider.g.dart';

@freezed
class VoiceInputState with _$VoiceInputState {
  const factory VoiceInputState({
    @Default(false) bool isListening,
    @Default(false) bool isAvailable,
    @Default(false) bool isLoading,
    @Default('') String recognizedText,
    @Default('') String lastError,
    @Default(0) int recordingSeconds,
    @Default(false) bool permissionGranted,
    @Default(false) bool isRecording,
    String? audioFilePath,
    Uint8List? audioData,
    @Default(false) bool isUploading,
  }) = _VoiceInputState;
}

@riverpod
class VoiceInput extends _$VoiceInput {
  late final SpeechToText _speechToText;
  late final AudioRecorder _audioRecorder;
  Timer? _recordingTimer;
  static const int maxRecordingSeconds = 60; // バックエンドの制限に合わせて60秒
  
  @override
  VoiceInputState build() {
    _speechToText = SpeechToText();
    _audioRecorder = AudioRecorder();
    
    // プロバイダーが破棄される時にクリーンアップ
    ref.onDispose(() {
      _recordingTimer?.cancel();
      if (state.isListening) {
        _speechToText.stop();
      }
      if (state.isRecording) {
        _audioRecorder.stop();
      }
      // 一時ファイルを削除
      if (state.audioFilePath != null) {
        File(state.audioFilePath!).delete().catchError((_) {});
      }
    });
    
    // 初期化は後で実行するようにスケジュール
    Future.microtask(() => _initialize());
    
    return const VoiceInputState();
  }

  Future<void> _initialize() async {
        // Initializing speech recognition...');
    state = state.copyWith(isLoading: true);
    
    try {
      // マイク権限チェック
      final micPermission = await Permission.microphone.status;
      if (!micPermission.isGranted) {
        final result = await Permission.microphone.request();
        if (!result.isGranted) {
          state = state.copyWith(
            isAvailable: false,
            isLoading: false,
            permissionGranted: false,
            lastError: 'Microphone permission denied',
          );
          return;
        }
      }
      
      // Speech to Text初期化
      final available = await _speechToText.initialize(
        onStatus: _handleStatus,
        onError: _handleError,
        debugLogging: kDebugMode,
      );
      
      // Audio Recorder初期化
      final canRecord = await _audioRecorder.hasPermission();
      
      state = state.copyWith(
        isAvailable: available && canRecord,
        isLoading: false,
        permissionGranted: available && canRecord,
      );
      
        // Speech recognition available: $available, Audio recording: $canRecord');
    } catch (e) {
        // Initialization error: $e');
      state = state.copyWith(
        isAvailable: false,
        isLoading: false,
        lastError: e.toString(),
      );
    }
  }

  /// 音声認識開始（テキスト変換のみ）
  Future<void> startListening() async {
    if (!state.isAvailable || state.isListening) {
        // Cannot start: available=${state.isAvailable}, listening=${state.isListening}');
      return;
    }

        // Starting speech recognition...');
    
    // Reset recognized text
    state = state.copyWith(
      recognizedText: '',
      lastError: '',
      recordingSeconds: 0,
    );

    try {
      await _speechToText.listen(
        onResult: (result) {
        // Recognition result: ${result.recognizedWords}');
          state = state.copyWith(
            recognizedText: result.recognizedWords,
          );
        },
        listenFor: Duration(seconds: maxRecordingSeconds),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        cancelOnError: true,
        listenMode: ListenMode.confirmation,
        localeId: 'ja_JP', // 日本語に設定
      );

      state = state.copyWith(isListening: true);
      _startRecordingTimer();
      
    } catch (e) {
        // Start listening error: $e');
      state = state.copyWith(
        lastError: e.toString(),
        isListening: false,
      );
    }
  }

  /// 音声録音開始（バックエンド送信用）
  Future<void> startRecording() async {
    if (!state.isAvailable || state.isRecording) {
        // Cannot start recording: available=${state.isAvailable}, recording=${state.isRecording}');
      return;
    }

        // Starting audio recording...');
    
    // Reset state
    state = state.copyWith(
      audioFilePath: null,
      audioData: null,
      lastError: '',
      recordingSeconds: 0,
      isRecording: true,
    );

    try {
      // 一時ファイルパスを作成
      final tempDir = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final filePath = '${tempDir.path}/voice_record_$timestamp.wav';
      
      // WAV形式で録音開始
      await _audioRecorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000, // 16kHz (Gemini推奨)
          numChannels: 1, // モノラル
          bitRate: 128000,
        ),
        path: filePath,
      );
      
      state = state.copyWith(
        audioFilePath: filePath,
        isRecording: true,
      );
      
      _startRecordingTimer();
      
    } catch (e) {
        // Start recording error: $e');
      state = state.copyWith(
        lastError: e.toString(),
        isRecording: false,
      );
    }
  }

  /// 音声認識停止
  Future<void> stopListening() async {
    if (!state.isListening) return;

        // Stopping speech recognition...');
    
    _recordingTimer?.cancel();
    _recordingTimer = null;
    
    await _speechToText.stop();
    state = state.copyWith(
      isListening: false,
      recordingSeconds: 0,
    );
  }

  /// 音声録音停止
  Future<void> stopRecording() async {
    if (!state.isRecording) return;

        // Stopping audio recording...');
    
    _recordingTimer?.cancel();
    _recordingTimer = null;
    
    try {
      final path = await _audioRecorder.stop();
      
      if (path != null) {
        // 録音ファイルを読み込む
        final file = File(path);
        final audioData = await file.readAsBytes();
        
        state = state.copyWith(
          isRecording: false,
          recordingSeconds: 0,
          audioFilePath: path,
          audioData: audioData,
        );
        
        // Recording saved: $path (${audioData.length} bytes)');
      } else {
        state = state.copyWith(
          isRecording: false,
          recordingSeconds: 0,
          lastError: 'Recording failed - no file path',
        );
      }
    } catch (e) {
        // Stop recording error: $e');
      state = state.copyWith(
        isRecording: false,
        recordingSeconds: 0,
        lastError: e.toString(),
      );
    }
  }

  /// 録音した音声データを取得（バックエンド送信用）
  Uint8List? getAudioData() {
    return state.audioData;
  }

  /// 録音した音声ファイルパスを取得
  String? getAudioFilePath() {
    return state.audioFilePath;
  }

  /// アップロード状態を設定
  void setUploading(bool isUploading) {
    state = state.copyWith(isUploading: isUploading);
  }

  void _startRecordingTimer() {
    _recordingTimer?.cancel();
    _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      final newSeconds = state.recordingSeconds + 1;
      state = state.copyWith(recordingSeconds: newSeconds);
      
      if (newSeconds >= maxRecordingSeconds) {
        // Max recording time reached');
        if (state.isListening) {
          stopListening();
        }
        if (state.isRecording) {
          stopRecording();
        }
      }
    });
  }

  void _handleStatus(String status) {
        // Status: $status');
    
    if (status == 'done' || status == 'notListening') {
      if (state.isListening) {
        stopListening();
      }
    }
  }

  void _handleError(dynamic error) {
        // Error: $error');
    state = state.copyWith(
      lastError: error.toString(),
      isListening: false,
    );
    _recordingTimer?.cancel();
  }

  void clearText() {
    state = state.copyWith(recognizedText: '');
  }

  void clearAudioData() {
    // 一時ファイルを削除
    if (state.audioFilePath != null) {
      File(state.audioFilePath!).delete().catchError((_) {});
    }
    state = state.copyWith(
      audioFilePath: null,
      audioData: null,
    );
  }

  Future<void> requestPermission() async {
        // Requesting microphone permission...');
    await _initialize();
  }
}