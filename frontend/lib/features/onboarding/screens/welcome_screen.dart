import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/onboarding_provider.dart';
import '../../../core/navigation/app_router.dart';
import '../../../core/providers/locale_provider.dart';
import '../../../core/widgets/animated_gradient_background.dart';
import '../../../core/providers/service_providers.dart';
import '../../../core/config/app_config.dart';
import 'dart:ui';

class WelcomeScreen extends ConsumerStatefulWidget {
  const WelcomeScreen({super.key});

  @override
  ConsumerState<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends ConsumerState<WelcomeScreen> {
  @override
  void initState() {
    super.initState();
    // Warm up the backend with a health check
    _warmUpBackend();
  }
  
  Future<void> _warmUpBackend() async {
    try {
      final apiService = ref.read(apiServiceProvider);
      await apiService.performHealthCheck();
    } catch (e) {
      // Ignore errors - this is just a warm-up
    }
  }

  static const Map<String, String> _languages = {
    'ja': 'こんにちは',
    'en': 'Hello',
    'zh_CN': '你好 (简体)',
    'zh_TW': '你好 (繁體)',
    'ko': '안녕하세요',
    'es': 'Hola',
    'fr': 'Bonjour',
    'de': 'Hallo',
    'it': 'Ciao',
    'pt': 'Olá',
  };

  @override
  Widget build(BuildContext context) {
    final selectedLanguage = ref.watch(onboardingProvider.select((state) => state.selectedLanguageCode));
    final notifier = ref.read(onboardingProvider.notifier);

    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),
                // App Icon and Title
                Column(
                  children: [
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF00E5CC).withValues(alpha: 0.3),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: Image.asset(
                          'assets/icon/app_icon.png',
                          width: 64,
                          height: 64,
                          fit: BoxFit.contain,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    ShaderMask(
                      shaderCallback: (bounds) => const LinearGradient(
                        colors: [
                          Color(0xFF00D9FF),
                          Color(0xFF00E5CC),
                        ],
                      ).createShader(bounds),
                      child: Text(
                        'LinguaSafeTrip',
                        style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                          fontSize: 28,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _getWelcomeMessage(selectedLanguage),
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFF2D4A4A),
                        fontWeight: FontWeight.w500,
                        height: 1.3,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                
                // Language Selection Title
                ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.3),
                          width: 1,
                        ),
                      ),
                      child: Text(
                        _getLanguageSelectionTitle(selectedLanguage),
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF1A3333),
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                
                // Language Grid
                Expanded(
                  child: GridView.builder(
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 16,
                      mainAxisSpacing: 16,
                      childAspectRatio: 3.2,
                    ),
                    itemCount: _languages.length,
                    itemBuilder: (context, index) {
                      final languageCode = _languages.keys.elementAt(index);
                      final languageName = _languages[languageCode]!;
                      final isSelected = selectedLanguage == languageCode;
                      
                      return ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                          child: Material(
                            color: isSelected 
                              ? const Color(0xFF00E5CC).withValues(alpha: 0.2)
                              : Colors.white.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(16),
                            child: InkWell(
                              borderRadius: BorderRadius.circular(16),
                              onTap: () {
                                notifier.updateLanguage(languageCode);
                                ref.read(localeProvider.notifier).setLocale(languageCode);
                                context.goNamed(AppRoutes.onboardingPermission);
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                    color: isSelected 
                                      ? const Color(0xFF00E5CC).withValues(alpha: 0.4)
                                      : Colors.white.withValues(alpha: 0.3),
                                    width: 1.5,
                                  ),
                                  gradient: isSelected ? const LinearGradient(
                                    colors: [
                                      Color(0x2000D9FF),
                                      Color(0x2000E5CC),
                                    ],
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                  ) : null,
                                ),
                                child: Center(
                                  child: Text(
                                    languageName,
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: isSelected 
                                        ? const Color(0xFF1A3333)
                                        : const Color(0xFF2D4A4A),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
                
                const SizedBox(height: 24),
                
                // テスト用スキップボタン（デバッグ/テストモードでのみ表示）
                if (AppConfig.isTestMode || kDebugMode)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: OutlinedButton(
                      key: const Key('onboarding_skip_button'),
                      onPressed: () async {
                        // テスト用の自動オンボーディング完了
                        final notifier = ref.read(onboardingProvider.notifier);
                        
                        // デフォルト設定で自動完了
                        notifier.updateLanguage('ja'); // 日本語設定
                        notifier.updateNickname('TestUser'); // テスト用ニックネーム
                        
                        // オンボーディング完了処理を実行
                        await notifier.completeOnboarding(context);
                      },
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(color: Colors.grey.withValues(alpha: 0.5)),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      child: const Text(
                        'Auto Complete Onboarding (Test)',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ),
                  ),
                const SizedBox(height: 8),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _getWelcomeMessage(String languageCode) {
    switch (languageCode) {
      case 'en':
        return 'Your safety companion for emergencies and disasters';
      case 'zh_CN':
        return '您的紧急情况和灾难安全伴侣';
      case 'zh_TW':
        return '您的緊急情況和災難安全夥伴';
      case 'ko':
        return '응급상황과 재난에 대비하는 안전 동반자';
      case 'es':
        return 'Tu compañero de seguridad para emergencias y desastres';
      case 'fr':
        return 'Votre compagnon de sécurité pour les urgences et catastrophes';
      case 'de':
        return 'Ihr Sicherheitsbegleiter für Notfälle und Katastrophen';
      case 'it':
        return 'Il tuo compagno di sicurezza per emergenze e disastri';
      case 'pt':
        return 'Seu companheiro de segurança para emergências e desastres';
      default: // 'ja'
        return '緊急時・災害時のあなたの安全パートナー';
    }
  }

  String _getLanguageSelectionTitle(String languageCode) {
    switch (languageCode) {
      case 'en':
        return 'Select Your Language';
      case 'zh_CN':
        return '选择您的语言';
      case 'zh_TW':
        return '選擇您的語言';
      case 'ko':
        return '언어를 선택하세요';
      case 'es':
        return 'Selecciona tu idioma';
      case 'fr':
        return 'Sélectionnez votre langue';
      case 'de':
        return 'Wählen Sie Ihre Sprache';
      case 'it':
        return 'Seleziona la tua lingua';
      case 'pt':
        return 'Selecione seu idioma';
      default: // 'ja'
        return '言語を選択してください';
    }
  }
}