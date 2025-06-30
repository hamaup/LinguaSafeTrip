part of 'onboarding_provider.dart';

class OnboardingState {
  final PermissionStatus permissionStatusLocation;
  final PermissionStatus permissionStatusNotification;
  final String nickname;
  final String selectedLanguageCode;
  final List<EmergencyContactModel> emergencyContacts;
  final bool isLoading;
  final BuildContext? context;

  OnboardingState({
    required this.permissionStatusLocation,
    required this.permissionStatusNotification,
    required this.nickname,
    required this.selectedLanguageCode,
    required this.emergencyContacts,
    required this.isLoading,
    this.context,
  });

  OnboardingState copyWith({
    PermissionStatus? permissionStatusLocation,
    PermissionStatus? permissionStatusNotification,
    String? nickname,
    String? selectedLanguageCode,
    List<EmergencyContactModel>? emergencyContacts,
    bool? isLoading,
    BuildContext? context,
  }) {
    return OnboardingState(
      permissionStatusLocation:
          permissionStatusLocation ?? this.permissionStatusLocation,
      permissionStatusNotification:
          permissionStatusNotification ?? this.permissionStatusNotification,
      nickname: nickname ?? this.nickname,
      selectedLanguageCode: selectedLanguageCode ?? this.selectedLanguageCode,
      emergencyContacts: emergencyContacts ?? this.emergencyContacts,
      isLoading: isLoading ?? this.isLoading,
      context: context ?? this.context,
    );
  }
}
