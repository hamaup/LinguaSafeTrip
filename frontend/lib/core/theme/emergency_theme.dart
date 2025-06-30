import 'package:flutter/material.dart';

/// 緊急時専用のUI テーマ定義
class EmergencyTheme {
  // 緊急時のボタンサイズ
  static const double emergencyButtonHeight = 64.0;
  static const double emergencyIconSize = 32.0;
  static const double emergencyFontSize = 18.0;
  
  // カラーパレット（WCAG準拠）
  static const Color emergencyRed = Color(0xFFD32F2F);
  static const Color warningOrange = Color(0xFFFF8F00);
  static const Color safeGreen = Color(0xFF388E3C);
  static const Color highContrastText = Color(0xFF212121);
  static const Color accessibleSecondary = Color(0xFF757575);

  // 緊急アクションボタンスタイル
  static ButtonStyle emergencyButtonStyle = ElevatedButton.styleFrom(
    backgroundColor: emergencyRed,
    foregroundColor: Colors.white,
    minimumSize: const Size(double.infinity, emergencyButtonHeight),
    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
    textStyle: const TextStyle(
      fontSize: emergencyFontSize,
      fontWeight: FontWeight.bold,
    ),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
    ),
    elevation: 8,
  );

  // 安全確認ボタンスタイル
  static ButtonStyle safeActionButtonStyle = ElevatedButton.styleFrom(
    backgroundColor: safeGreen,
    foregroundColor: Colors.white,
    minimumSize: const Size(double.infinity, emergencyButtonHeight),
    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
    textStyle: const TextStyle(
      fontSize: emergencyFontSize,
      fontWeight: FontWeight.bold,
    ),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
    ),
    elevation: 8,
  );

  // 警告ボタンスタイル
  static ButtonStyle warningButtonStyle = ElevatedButton.styleFrom(
    backgroundColor: warningOrange,
    foregroundColor: Colors.white,
    minimumSize: const Size(double.infinity, emergencyButtonHeight),
    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
    textStyle: const TextStyle(
      fontSize: emergencyFontSize,
      fontWeight: FontWeight.bold,
    ),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
    ),
    elevation: 8,
  );

  // 緊急時テキストスタイル
  static const TextStyle emergencyTitleStyle = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    color: Colors.white,
    height: 1.2,
  );

  static const TextStyle emergencyBodyStyle = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: highContrastText,
    height: 1.4,
  );

  static const TextStyle accessibleBodyStyle = TextStyle(
    fontSize: 16,
    color: highContrastText,
    height: 1.5,
  );

  static const TextStyle accessibleSecondaryStyle = TextStyle(
    fontSize: 14,
    color: accessibleSecondary,
    height: 1.4,
  );

  // アイコンボタンの制約
  static const BoxConstraints iconButtonConstraints = BoxConstraints(
    minWidth: 48,
    minHeight: 48,
  );

  // 緊急時アニメーション設定
  static const Duration emergencyAnimationDuration = Duration(milliseconds: 300);
  static const Duration warningPulseDuration = Duration(milliseconds: 1000);

  // 緊急アラート用コンテナデコレーション
  static BoxDecoration emergencyAlertDecoration = BoxDecoration(
    color: emergencyRed,
    borderRadius: BorderRadius.circular(16),
    boxShadow: [
      BoxShadow(
        color: emergencyRed.withOpacity(0.3),
        blurRadius: 20,
        offset: const Offset(0, 8),
      ),
    ],
  );

  // カード用エレベーション
  static const double emergencyCardElevation = 12.0;
  static const double normalCardElevation = 4.0;

  // スペーシング
  static const double tinySpacing = 4.0;
  static const double smallSpacing = 8.0;
  static const double mediumSpacing = 16.0;
  static const double largeSpacing = 24.0;
  static const double extraLargeSpacing = 32.0;
}

/// 緊急時UI コンポーネント
class EmergencyWidgets {
  
  /// 全画面緊急アラート
  static Widget buildFullScreenAlert({
    required String title,
    required String message,
    required VoidCallback onAction,
    required String actionText,
    VoidCallback? onDismiss,
  }) {
    return Container(
      decoration: EmergencyTheme.emergencyAlertDecoration,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(EmergencyTheme.largeSpacing),
          child: Column(
            children: [
              // アニメーション警告アイコン
              TweenAnimationBuilder<double>(
                duration: EmergencyTheme.warningPulseDuration,
                tween: Tween(begin: 0.8, end: 1.2),
                builder: (context, scale, child) {
                  return Transform.scale(
                    scale: scale,
                    child: const Icon(
                      Icons.warning_amber_rounded,
                      size: 120,
                      color: Colors.white,
                    ),
                  );
                },
              ),
              
              const SizedBox(height: EmergencyTheme.largeSpacing),
              
              // タイトル
              Text(
                title,
                style: EmergencyTheme.emergencyTitleStyle,
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: EmergencyTheme.mediumSpacing),
              
              // メッセージ
              Container(
                padding: const EdgeInsets.all(EmergencyTheme.mediumSpacing),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  message,
                  style: const TextStyle(
                    fontSize: 18,
                    color: Colors.white,
                    height: 1.4,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
              
              const Spacer(),
              
              // アクションボタン
              SizedBox(
                width: double.infinity,
                height: 80,
                child: ElevatedButton.icon(
                  style: EmergencyTheme.safeActionButtonStyle.copyWith(
                    backgroundColor: MaterialStateProperty.all(Colors.white),
                    foregroundColor: MaterialStateProperty.all(EmergencyTheme.emergencyRed),
                  ),
                  icon: const Icon(Icons.check_circle, size: 32),
                  label: Text(
                    actionText,
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  onPressed: onAction,
                ),
              ),
              
              if (onDismiss != null) ...[
                const SizedBox(height: EmergencyTheme.mediumSpacing),
                TextButton(
                  onPressed: onDismiss,
                  child: const Text(
                    'Later',
                    style: TextStyle(color: Colors.white, fontSize: 16),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  /// 緊急アクションボタン
  static Widget buildEmergencyActionButton({
    required String label,
    required IconData icon,
    required VoidCallback onPressed,
    bool isLoading = false,
  }) {
    return Semantics(
      label: '$label (Emergency Action)',
      button: true,
      child: SizedBox(
        width: double.infinity,
        height: EmergencyTheme.emergencyButtonHeight,
        child: ElevatedButton.icon(
          style: EmergencyTheme.emergencyButtonStyle,
          icon: isLoading 
              ? const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    color: Colors.white,
                    strokeWidth: 2,
                  ),
                )
              : Icon(icon, size: EmergencyTheme.emergencyIconSize),
          label: Text(label),
          onPressed: isLoading ? null : onPressed,
        ),
      ),
    );
  }

  /// コンテキスト付きローディング
  static Widget buildContextualLoading({
    required String message,
    VoidCallback? onCancel,
    double? progress,
  }) {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Card(
          elevation: EmergencyTheme.emergencyCardElevation,
          child: Padding(
            padding: const EdgeInsets.all(EmergencyTheme.extraLargeSpacing),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (progress != null)
                  LinearProgressIndicator(
                    value: progress,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(EmergencyTheme.safeGreen),
                  )
                else
                  const CircularProgressIndicator(
                    strokeWidth: 4,
                  ),
                
                const SizedBox(height: EmergencyTheme.largeSpacing),
                
                Text(
                  message,
                  style: EmergencyTheme.emergencyBodyStyle,
                  textAlign: TextAlign.center,
                ),
                
                if (onCancel != null) ...[
                  const SizedBox(height: EmergencyTheme.mediumSpacing),
                  TextButton(
                    onPressed: onCancel,
                    child: const Text(
                      'Cancel',
                      style: TextStyle(fontSize: 16),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// アクセシブルなカード
  static Widget buildAccessibleCard({
    required Widget child,
    String? semanticsLabel,
    VoidCallback? onTap,
    bool isEmergency = false,
  }) {
    return Semantics(
      label: semanticsLabel,
      button: onTap != null,
      child: Card(
        elevation: isEmergency 
            ? EmergencyTheme.emergencyCardElevation 
            : EmergencyTheme.normalCardElevation,
        margin: const EdgeInsets.symmetric(
          horizontal: EmergencyTheme.mediumSpacing,
          vertical: EmergencyTheme.smallSpacing,
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(EmergencyTheme.mediumSpacing),
            child: child,
          ),
        ),
      ),
    );
  }
}