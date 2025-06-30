import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'package:frontend/features/main_timeline/widgets/app_header_widget.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';
import 'package:frontend/features/main_timeline/providers/device_status_provider.dart';
import 'package:frontend/core/utils/device_id_util.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';
import 'package:frontend/core/models/timeline_item_model.dart' as models;
import 'package:frontend/features/main_timeline/widgets/device_status_bar.dart';
import 'package:frontend/features/main_timeline/widgets/suggestion_timeline_item.dart';
import 'package:frontend/features/chat/widgets/chat_timeline_item.dart';
import 'package:frontend/features/chat/widgets/chat_with_action_item.dart';
import 'package:frontend/features/chat/widgets/chat_input_field.dart';
import 'package:frontend/features/chat/providers/chat_provider.dart';
import 'package:frontend/features/main_timeline/widgets/alert_timeline_item.dart';
import 'package:frontend/features/main_timeline/widgets/important_alert_banner.dart';
import 'package:frontend/features/main_timeline/widgets/streaming_suggestions_list.dart';
// Removed: AnimatedRippleBackground - using AnimatedGradientBackground instead
import 'package:frontend/core/widgets/animated_gradient_background.dart';
import 'package:frontend/core/widgets/ripple_loading_animation.dart';
import 'package:scrollable_positioned_list/scrollable_positioned_list.dart';

class MainTimelineScreen extends ConsumerStatefulWidget {
  const MainTimelineScreen({super.key});

  @override
  ConsumerState<MainTimelineScreen> createState() => _MainTimelineScreenState();
}

class _MainTimelineScreenState extends ConsumerState<MainTimelineScreen> {
  final ItemScrollController _itemScrollController = ItemScrollController();
  final ItemPositionsListener _itemPositionsListener = ItemPositionsListener.create();
  TimelineScrollBehavior _lastScrollBehavior = TimelineScrollBehavior.none;
  String? _lastTargetResponseId;
  String? _lastTargetAlertId;

  @override
  void initState() {
    super.initState();
    debugPrint('[MainTimelineScreen] initState called');
    
    // 初期化処理
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      // SettingsProviderの初期化（Riverpodが自動処理）
      
      // デバイスステータスプロバイダーを初期化
      if (mounted) {
        await ref.read(deviceStatusProvider.notifier).initialize();
      }
    });
  }

  @override
  void dispose() {
    // ItemScrollController doesn't need explicit disposal
    super.dispose();
  }

  /// スクロール動作を処理
  void _handleScrollBehavior(
    TimelineScrollBehavior scrollBehavior, 
    String? targetResponseId,
    String? targetAlertId,
    List<models.TimelineItemModel> timelineItems,
  ) {
    // スクロール動作が変更された場合のみ処理
    if (scrollBehavior != _lastScrollBehavior || 
        targetResponseId != _lastTargetResponseId ||
        targetAlertId != _lastTargetAlertId) {
      _lastScrollBehavior = scrollBehavior;
      _lastTargetResponseId = targetResponseId;
      _lastTargetAlertId = targetAlertId;

      if (scrollBehavior == TimelineScrollBehavior.none) {
        return;
      }

      WidgetsBinding.instance.addPostFrameCallback((_) {
        // ItemScrollControllerが初期化されているか確認
        if (!_itemScrollController.isAttached) {
          debugPrint('[MainTimelineScreen] ItemScrollController not attached yet, skipping scroll');
          return;
        }

        if (scrollBehavior == TimelineScrollBehavior.toBottom) {
          // 最下部へスクロール
          if (timelineItems.isNotEmpty) {
            final lastIndex = timelineItems.length - 1;
            _itemScrollController.scrollTo(
              index: lastIndex,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut,
            );
          }
        } else if (scrollBehavior == TimelineScrollBehavior.toResponse && 
                   targetResponseId != null) {
          // 特定の回答へスクロール
          final targetIndex = timelineItems.indexWhere(
            (item) => item.id == targetResponseId,
          );
          
          if (targetIndex != -1) {
            _itemScrollController.scrollTo(
              index: targetIndex,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut,
            );
          }
        } else if (scrollBehavior == TimelineScrollBehavior.toAlert && 
                   targetAlertId != null) {
          // 災害アラートへスクロール
          final targetIndex = timelineItems.indexWhere(
            (item) => item.id == targetAlertId,
          );
          
          if (targetIndex != -1) {
            _itemScrollController.scrollTo(
              index: targetIndex,
              duration: const Duration(milliseconds: 500),
              curve: Curves.easeInOut,
              alignment: 0.0, // 画面の上端にアイテムを表示
            );
          }
        }

        // スクロール完了後、状態をリセット（アニメーション完了を待つ）
        // 無限ループ防止: scrollBehaviorがnoneでない場合のみリセット
        if (scrollBehavior != TimelineScrollBehavior.none) {
          Future.delayed(const Duration(milliseconds: 600), () {
            if (mounted && _lastScrollBehavior != TimelineScrollBehavior.none) {
              // 状態を再確認してからリセット
              final currentScrollBehavior = ref.read(timelineProvider).scrollBehavior;
              if (currentScrollBehavior != TimelineScrollBehavior.none) {
                ref.read(timelineProvider.notifier).resetScrollBehavior();
              }
            }
          });
        }
      });
    }
  }


  Widget _buildTimelineContent(
    List<models.TimelineItemModel> timelineItems,
    bool isLoading,
    bool isChatLoading,
    String chatLoadingStatus,
  ) {
    // 初回読み込み中の場合（データがあっても表示）
    if (isLoading) {
      debugPrint('[MainTimelineScreen] Showing loading indicator');
      return _buildLoadingIndicator();
    }
    
    // タイムラインアイテムが存在しない場合（読み込み完了後）
    if (!isLoading && timelineItems.isEmpty) {
      return _buildEmptyState();
    }
    
    // 通常のタイムライン表示
    final itemCount = timelineItems.length + 
        (isChatLoading && chatLoadingStatus.isNotEmpty ? 1 : 0);
    
    // アイテムが0の場合は空のContainerを返す
    if (itemCount == 0) {
      return Container();
    }
    
    return ScrollablePositionedList.builder(
      itemScrollController: _itemScrollController,
      itemPositionsListener: _itemPositionsListener,
      itemCount: itemCount,
      itemBuilder: (context, index) {
        // チャットローディングインジケーターを最後に表示
        if (index == timelineItems.length && 
            isChatLoading && 
            chatLoadingStatus.isNotEmpty) {
          return _buildChatLoadingIndicator(chatLoadingStatus);
        }
        
        final item = timelineItems[index];
        
        if (kDebugMode) {
          print('[MainTimelineScreen] Building item: type=${item.type}, id=${item.id}, index: $index');
        }
        
        return item.when(
          alert: (id, timestamp, severity, title, message) => AlertTimelineItem(model: item),
          suggestion: (id, suggestionType, timestamp, content, actionData, actionQuery, actionDisplayText) => SuggestionTimelineItem(model: item),
          chat: (id, timestamp, messageText, senderNickname, isOwnMessage) => ChatTimelineItem(model: item),
          chatWithAction: (id, timestamp, messageText, senderNickname, isOwnMessage, requiresAction, actionData) => 
              ChatWithActionItem(
                id: id,
                messageText: messageText,
                senderNickname: senderNickname,
                isOwnMessage: isOwnMessage,
                timestamp: timestamp,
                requiresAction: requiresAction,
                actionData: actionData,
              ),
        );
      },
    );
  }

  Widget _buildLoadingIndicator() {
    return Stack(
      fit: StackFit.expand,
      children: [
        // Full screen ripple animation background
        Positioned.fill(
          child: RippleLoadingAnimation(
            size: MediaQuery.of(context).size.width * 1.5, // Cover full screen
            color: Colors.grey[400]!,
          ),
        ),
        // Content in the center - subtle text only
        Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                AppLocalizations.of(context)!.loadingTimeline,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.normal,
                  color: Colors.grey[500],
                ),
              ),
              const SizedBox(height: 4),
              Text(
                AppLocalizations.of(context)!.gettingLatestInfo,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[400],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildChatLoadingIndicator(String loadingStatus) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFFE8FFFC).withValues(alpha: 0.9),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: const Color(0xFF00E5CC).withValues(alpha: 0.3),
                width: 0.5,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      const Color(0xFF00D9FF),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Flexible(
                  child: Text(
                    loadingStatus,
                    style: const TextStyle(
                      color: Color(0xFF2D4A4A),
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    // 空状態の表示（アニメーション波紋背景付き）
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.blue.shade50,
            Colors.white,
          ],
        ),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.3), // より透明に
                borderRadius: BorderRadius.circular(12),
                // ボックスシャドウを削除
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.timeline,
                    size: 32, // 64 → 32 に小さく
                    color: Colors.grey[500], // より薄いグレー
                    ),
                  const SizedBox(height: 8), // 16 → 8 に短縮
                  Text(
                    AppLocalizations.of(context)!.timelineEmpty,
                    style: TextStyle(
                      fontSize: 14, // 18 → 14 に小さく
                      fontWeight: FontWeight.normal, // w500 → normal
                      color: Colors.grey[600], // より薄く
                    ),
                  ),
                  const SizedBox(height: 4), // 8 → 4 に短縮
                  Text(
                    AppLocalizations.of(context)!.infoWillAppearSoon,
                    style: TextStyle(
                      fontSize: 12, // 14 → 12 に小さく
                      color: Colors.grey[500], // より薄く
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ref = this.ref;
    // タイムラインアイテムとローディング状態を個別に監視
    final timelineItems = ref.watch(timelineProvider.select((state) => state.timelineItems));
    final isLoading = ref.watch(timelineProvider.select((state) => state.isLoading));
    final isChatLoading = ref.watch(timelineProvider.select((state) => state.isChatLoading));
    final chatLoadingStatus = ref.watch(timelineProvider.select((state) => state.chatLoadingStatus));
    final errorMessage = ref.watch(timelineProvider.select((state) => state.errorMessage));
    final importantAlert = ref.watch(timelineProvider.select((state) => state.importantAlert));
    final isEmergencyLoading = ref.watch(timelineProvider.select((state) => state.isEmergencyLoading));
    
    // スクロール関連は読み取りのみ（watchしない）
    final timelineState = ref.read(timelineProvider);
    
    debugPrint('[MainTimelineScreen] build called, isLoading: $isLoading, items: ${timelineItems.length}');
    // currentModeの監視を削除（無限ループ防止）
    // 代わりにdeviceStatusProviderのnotifierから直接取得
    final isEmergencyMode = ref.read(deviceStatusProvider.notifier).currentMode == 'emergency';

    // スクロール動作を処理 - WidgetsBinding.addPostFrameCallbackで遅延実行
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final scrollState = ref.read(timelineProvider);
      _handleScrollBehavior(
        scrollState.scrollBehavior,
        scrollState.targetResponseId,
        scrollState.targetAlertId,
        timelineItems,
      );
    });

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: const AppHeaderWidget(),
      body: AnimatedGradientBackground(
        isEmergencyMode: isEmergencyMode,
        child: SafeArea(
          child: MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(
                MediaQuery.of(context).textScaler.scale(1.0).clamp(0.8, 1.3),
              ),
            ),
            child: Column(
            children: [
              // 災害アラートバナー
              if (timelineState.importantAlert != null)
                const ImportantAlertBanner(),

              // デバイス状態
              const DeviceStatusBar(),

              // エラーメッセージ
              if (timelineState.errorMessage != null)
                Container(
                  color: Colors.red[100],
                  padding: const EdgeInsets.all(8),
                  child: Row(
                    children: [
                      Icon(Icons.error, color: Colors.red[700]),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          timelineState.errorMessage!,
                          style: TextStyle(color: Colors.red[700]),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => ref.read(timelineProvider.notifier).clearErrorMessage(),
                      ),
                    ],
                  ),
                ),

              // 緊急モード読み込み中のローディング表示
              if (timelineState.isEmergencyLoading)
                Container(
                  color: Colors.orange[50],
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.orange[700]!),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          AppLocalizations.of(context)!.loadingEmergencyInfo,
                          style: TextStyle(
                            color: Colors.orange[700],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              // タイムラインリスト
              Expanded(
                child: Stack(
                  children: [
                    _buildTimelineContent(
                      timelineItems,
                      isLoading,
                      isChatLoading,
                      chatLoadingStatus,
                    ),
                    // StreamingSuggestionsListを追加（非表示だがSSE接続を管理）
                    Positioned(
                      top: 0,
                      left: 0,
                      width: 0,
                      height: 0,
                      child: const StreamingSuggestionsList(),
                    ),
                  ],
                ),
              ),

              // チャット入力（もう少し上にマージンを追加）
              Container(
                constraints: const BoxConstraints(
                  maxHeight: 120, // 最大高さ制限
                ),
                padding: const EdgeInsets.only(bottom: 16.0),
                child: const ChatInputField(),
              ),
            ],
            ),
          ),
        ),
      ),
    );
  }
}
