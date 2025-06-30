import 'package:flutter/material.dart';

/// Utility class for font-related operations
class FontUtils {
  FontUtils._();

  /// Detects if the text contains Japanese characters
  static bool containsJapanese(String text) {
    // Check for Hiragana, Katakana, and Kanji
    final japaneseRegex = RegExp(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]');
    return japaneseRegex.hasMatch(text);
  }

  /// Detects if the text contains CJK (Chinese, Japanese, Korean) characters
  static bool containsCJK(String text) {
    // Comprehensive CJK Unicode ranges
    final cjkRegex = RegExp(
      r'[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]'
    );
    return cjkRegex.hasMatch(text);
  }

  /// Returns appropriate font features for better text rendering
  static List<FontFeature> getFontFeatures({bool isJapanese = false}) {
    if (isJapanese) {
      return const [
        FontFeature.proportionalFigures(),
        FontFeature.enable('kern'), // Kerning
        FontFeature.enable('liga'), // Standard ligatures
      ];
    }
    return const [
      FontFeature.proportionalFigures(),
      FontFeature.enable('kern'),
      FontFeature.enable('liga'),
      FontFeature.enable('calt'), // Contextual alternates
    ];
  }

  /// Creates a TextStyle optimized for the given text content
  static TextStyle optimizeTextStyle(
    TextStyle baseStyle,
    String text, {
    bool forceJapanese = false,
  }) {
    final isJapanese = forceJapanese || containsJapanese(text);
    
    if (isJapanese) {
      // Adjust line height and letter spacing for Japanese text
      return baseStyle.copyWith(
        height: baseStyle.height ?? 1.4,
        letterSpacing: 0.05,
        fontFeatures: getFontFeatures(isJapanese: true),
      );
    }
    
    return baseStyle.copyWith(
      fontFeatures: getFontFeatures(isJapanese: false),
    );
  }

  /// Get platform-specific Japanese font family
  static String getPlatformJapaneseFont(BuildContext context) {
    final platform = Theme.of(context).platform;
    
    switch (platform) {
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
        return 'Hiragino Sans';
      case TargetPlatform.windows:
        return 'Yu Gothic';
      case TargetPlatform.android:
      case TargetPlatform.fuchsia:
      case TargetPlatform.linux:
      default:
        return 'NotoSansJP';
    }
  }

  /// Creates a font family fallback list optimized for the current platform
  static List<String> getPlatformFontFallbacks(BuildContext context) {
    final platform = Theme.of(context).platform;
    
    switch (platform) {
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
        return [
          'NotoSansJP',
          'Hiragino Sans',
          'Hiragino Kaku Gothic ProN',
          '.SF NS Text',
          'sans-serif',
        ];
      case TargetPlatform.windows:
        return [
          'NotoSansJP',
          'Yu Gothic',
          'Meiryo',
          'MS Gothic',
          'sans-serif',
        ];
      case TargetPlatform.android:
        return [
          'NotoSansJP',
          'Noto Sans CJK JP',
          'Droid Sans Japanese',
          'sans-serif',
        ];
      case TargetPlatform.linux:
      case TargetPlatform.fuchsia:
      default:
        return [
          'NotoSansJP',
          'Noto Sans CJK JP',
          'sans-serif',
        ];
    }
  }
}

/// Extension for easy text optimization
extension TextOptimizationExtension on Text {
  /// Creates a new Text widget with optimized TextStyle for its content
  Text optimized({bool forceJapanese = false}) {
    final optimizedStyle = FontUtils.optimizeTextStyle(
      style ?? const TextStyle(),
      data ?? '',
      forceJapanese: forceJapanese,
    );
    
    return Text(
      data ?? '',
      key: key,
      style: optimizedStyle,
      strutStyle: strutStyle,
      textAlign: textAlign,
      textDirection: textDirection,
      locale: locale,
      softWrap: softWrap,
      overflow: overflow,
      textScaler: textScaler,
      maxLines: maxLines,
      semanticsLabel: semanticsLabel,
      textWidthBasis: textWidthBasis,
      textHeightBehavior: textHeightBehavior,
    );
  }
}