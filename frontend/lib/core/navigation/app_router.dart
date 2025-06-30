import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/settings/screens/settings_screen.dart';
import 'package:frontend/features/splash/splash_screen.dart';
import 'package:frontend/features/onboarding/screens/welcome_screen.dart';
import 'package:frontend/features/onboarding/screens/permission_request_screen.dart';
import 'package:frontend/features/onboarding/screens/nickname_input_screen.dart';
import 'package:frontend/features/onboarding/screens/emergency_contact_input_screen.dart';
import 'package:frontend/features/main_timeline/screens/main_timeline_screen.dart';
import 'package:frontend/features/alert_detail/screens/alert_detail_screen.dart';
import 'package:frontend/features/shelter_search/screens/shelter_search_screen.dart';
import 'package:frontend/core/models/alert_detail_model.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:frontend/core/config/app_config.dart';

final goRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: AppRoutes.splash,
    debugLogDiagnostics: true,
    routes: <RouteBase>[
      GoRoute(
        path: AppRoutes.splash,
        name: AppRoutes.splash,
        builder: (BuildContext context, GoRouterState state) {
          return const SplashScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.onboardingWelcome,
        name: AppRoutes.onboardingWelcome,
        builder: (BuildContext context, GoRouterState state) {
          return const WelcomeScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.onboardingPermission,
        name: AppRoutes.onboardingPermission,
        builder: (BuildContext context, GoRouterState state) {
          return const PermissionRequestScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.onboardingNickname,
        name: AppRoutes.onboardingNickname,
        builder: (BuildContext context, GoRouterState state) {
          return const NicknameInputScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.onboardingEmergencyContact,
        name: AppRoutes.onboardingEmergencyContact,
        builder: (BuildContext context, GoRouterState state) {
          return const EmergencyContactInputScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.mainTimeline,
        name: AppRoutes.mainTimeline,
        builder: (BuildContext context, GoRouterState state) {
          return const MainTimelineScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.settings,
        name: AppRoutes.settings,
        builder: (BuildContext context, GoRouterState state) {
          return const SettingsScreen();
        },
      ),
      GoRoute(
        path: AppRoutes.alertDetail,
        name: AppRoutes.alertDetail,
        builder: (BuildContext context, GoRouterState state) {
          final alertData = state.extra as Map<String, dynamic>;
          final alertModel = AlertDetailModel.fromJson(alertData);
          return AlertDetailScreen(alertDetails: alertModel);
        },
      ),
      GoRoute(
        path: AppRoutes.shelterSearch,
        name: AppRoutes.shelterSearch,
        builder: (BuildContext context, GoRouterState state) {
          final data = state.extra as Map<String, dynamic>;
          final shelters = (data['shelters'] as List<dynamic>)
              .map((e) => DisasterProposalModel.fromJson(e))
              .toList();
          final userLocation = data['userLocation'] as LatLng?;
          return ShelterSearchScreen(
            shelters: shelters,
            userLocation: userLocation,
          );
        },
      ),
    ],
  );
});

class AppRoutes {
  static const String splash = '/';
  static const String onboardingWelcome = '/onboarding/welcome';
  static const String onboardingPermission = '/onboarding/permission';
  static const String onboardingNickname = '/onboarding/nickname';
  static const String onboardingEmergencyContact = '/onboarding/emergency_contact';
  static const String mainTimeline = '/timeline';
  static const String settings = '/settings';
  static const String alertDetail = '/alert-detail';
  static const String shelterSearch = '/shelter-search';
  static const String settingsEmergencyContacts = 'emergency-contacts';
}
