import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';

class LocaleNotifier extends StateNotifier<Locale> {
  LocaleNotifier(this.ref) : super(_getInitialLocale()) {
    // 設定プロバイダーの変更を監視（循環依存を防ぐため条件付き）
    ref.listen(settingsProvider, (previous, next) {
      // 設定が完全に初期化されている場合のみ処理
      if (!next.isLoading && next.currentUserSettings != null) {
        final languageCode = next.currentUserSettings?.languageCode;
        if (languageCode != null && _getLocaleString(state) != languageCode) {
          setLocale(languageCode);
        }
      }
    });
  }

  static Locale _getInitialLocale() {
    // デバイスのロケールに基づいて初期値を決定
    final deviceLocale = WidgetsBinding.instance.platformDispatcher.locale;
    if (deviceLocale.languageCode == 'ja') {
      return const Locale('ja');
    } else if (deviceLocale.languageCode == 'zh') {
      return const Locale('zh');
    }
    return const Locale('en'); // デフォルトは英語
  }

  final Ref ref;

  // Localeを文字列に変換するヘルパーメソッド
  String _getLocaleString(Locale locale) {
    if (locale.countryCode != null && locale.countryCode!.isNotEmpty) {
      return '${locale.languageCode}_${locale.countryCode}';
    }
    return locale.languageCode;
  }

  void setLocale(String languageCode) {
    if (languageCode.contains('_')) {
      // 地域コード付きの場合（例：zh_CN, zh_TW, en_US）
      final parts = languageCode.split('_');
      state = Locale(parts[0], parts[1]);
    } else {
      // 言語コードのみの場合
      state = Locale(languageCode);
    }
  }
}

final localeProvider = StateNotifierProvider<LocaleNotifier, Locale>((ref) {
  return LocaleNotifier(ref);
});