import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart' show dotenv;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/l10n/app_localizations.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/providers/locale_provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:frontend/core/services/fcm_service.dart';
import 'package:frontend/core/services/local_notification_service.dart';
import 'package:frontend/core/utils/device_id_util.dart';
import 'package:frontend/core/config/app_config.dart';

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

  try {
    if (kIsWeb) {
      await Firebase.initializeApp(
        options: FirebaseOptions(
          apiKey: AppConfig.firebaseApiKey,
          authDomain: AppConfig.firebaseAuthDomain,
          projectId: AppConfig.firebaseProjectId,
          storageBucket: AppConfig.firebaseStorageBucket,
          messagingSenderId: AppConfig.firebaseMessagingSenderId,
          appId: AppConfig.firebaseAppId,
        ),
      );
    } else {
      await Firebase.initializeApp();
    }
    
    // LocalNotificationServiceを先に初期化
    final localNotificationService = LocalNotificationService();
    await localNotificationService.initialize();
    
    final fcmService = FCMService();
    await fcmService.initialize();

    try {
      final deviceId = await DeviceIdUtil.initializeAndGetDeviceId();
      if (kDebugMode) {
        print("Initialized Device ID: $deviceId");
      }
    } catch (e) {
      if (kDebugMode) {
        print("デバイスID初期化エラー: $e");
      }
    }
  } catch (e) {
    print("Firebase初期化エラー: $e");
  }

  final container = ProviderContainer();
  
  // Set provider container for FCM service to access
  FCMService.setProviderContainer(container);
  
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
  void didChangeDependencies() {
    super.didChangeDependencies();
    // FCMサービスにコンテキストを設定
    FCMService.setContext(context);
  }

  @override
  Widget build(BuildContext context) {
    final goRouter = ref.watch(goRouterProvider);
    final locale = ref.watch(localeProvider);

    return MaterialApp.router(
      routerConfig: goRouter,
      debugShowCheckedModeBanner: false,
      showPerformanceOverlay: false, // パフォーマンスオーバーレイを無効化
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
