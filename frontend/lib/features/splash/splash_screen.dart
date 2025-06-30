import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/features/onboarding/providers/onboarding_provider.dart';
import 'package:frontend/features/settings/providers/settings_provider.dart';
import 'package:frontend/core/providers/service_providers.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // スプラッシュ画面表示時間を確保
    await Future.delayed(const Duration(seconds: 1));

    try {
      final localStorageService = ref.read(localStorageServiceProvider);
      final bool onboardingComplete = await localStorageService.getOnboardingComplete();

      if (mounted) {
        if (onboardingComplete) {
          // オンボーディングが完了している場合、設定プロバイダーを初期化
      // debugPrint('[SplashScreen] Onboarding complete, initializing settings...');
          // 設定プロバイダーを読み込んでloadInitialSettingsを呼び出す
          ref.read(settingsProvider);
          context.goNamed(AppRoutes.mainTimeline);
        } else {
          context.goNamed(AppRoutes.onboardingWelcome);
        }
      }
    } catch (e) {
      // debugPrint('[SplashScreen] Error during initialization: $e');
      if (mounted) {
        // エラー時は安全策としてオンボーディング画面へ遷移
        context.goNamed(AppRoutes.onboardingWelcome);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Image.asset(
                  'assets/icon/app_icon.png',
                  width: 100,
                  height: 100,
                  fit: BoxFit.contain,
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text("Safety App",
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
