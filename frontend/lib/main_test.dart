import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart' show dotenv;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/providers/locale_provider.dart';
import 'package:frontend/core/config/app_config.dart';

/// E2Eテスト用のmain関数（権限リクエストをスキップ）
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await dotenv.load(fileName: ".env");
    print("✅ .envファイル読み込み成功");
    print("API_BASE_URL: ${dotenv.env['API_BASE_URL']}");
    print("TEST_MODE: ${dotenv.env['TEST_MODE']}");
  } catch (e) {
    print("❌ 警告: .envファイルの読み込みに失敗しました。 $e");
  }

  // E2Eテスト環境では、Firebase初期化と権限リクエストをスキップ
  print("🧪 E2Eテストモード: Firebase初期化と権限リクエストをスキップします");

  final container = ProviderContainer();
  
  runApp(
    UncontrolledProviderScope(
      container: container,
      child: const MyApp(),
    ),
  );
}

class MyApp extends ConsumerStatefulWidget {
  const MyApp({super.key});

  @override
  ConsumerState<MyApp> createState() => _MyAppState();
}

class _MyAppState extends ConsumerState<MyApp> {
  @override
  Widget build(BuildContext context) {
    final goRouter = ref.watch(goRouterProvider);
    final locale = ref.watch(localeProvider);

    return MaterialApp.router(
      routerConfig: goRouter,
      debugShowCheckedModeBanner: false,
      showPerformanceOverlay: false,
      locale: locale,
      onGenerateTitle: (BuildContext context) {
        final localizations = AppLocalizations.of(context);
        return localizations?.appName ?? 'Safety App Frontend';
      },
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    );
  }
}