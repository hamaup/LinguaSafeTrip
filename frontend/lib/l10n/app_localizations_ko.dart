// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Korean (`ko`).
class AppLocalizationsKo extends AppLocalizations {
  AppLocalizationsKo([String locale = 'ko']) : super(locale);

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => '권한이 필요합니다';

  @override
  String get permissionRequestSubtitle => '앱 기본 기능에 필요한 권한을 설정합니다';

  @override
  String get permissionLaterInfo => '이러한 권한은 안전 기능에 중요하지만 나중에 설정할 수도 있습니다.';

  @override
  String get locationPermissionTitle => '위치 권한';

  @override
  String get locationPermissionRationale =>
      '이 앱은 근처 대피소와 위험 지역을 알려주기 위해 귀하의 위치를 사용합니다.';

  @override
  String get notificationPermissionTitle => '알림 권한';

  @override
  String get notificationPermissionRationale =>
      '재해 경보와 중요한 업데이트에 대한 알림을 보내드립니다.';

  @override
  String get next => '다음';

  @override
  String get settings => '설정';

  @override
  String get language => '언어';

  @override
  String get selectLanguage => '언어 선택';

  @override
  String get cancel => '취소';

  @override
  String get ok => '확인';

  @override
  String get settingsLoadFailed => '설정을 불러오지 못했습니다. 다시 시도해주세요.';

  @override
  String get notificationSettings => '알림 설정';

  @override
  String get notificationSettingsDescription => '앱 알림 설정 변경';

  @override
  String get messageInputHint => '메시지 입력...';

  @override
  String get listening => 'Listening';

  @override
  String get voiceInput => 'Voice Input';

  @override
  String get voiceInputDescription => 'Input messages by voice';

  @override
  String get emergencyContacts => '비상 연락처';

  @override
  String get addEmergencyContact => '비상 연락처 추가';

  @override
  String get name => '이름';

  @override
  String get phoneNumber => '전화번호';

  @override
  String get save => '저장';

  @override
  String get registerEmergencyContact => '비상 연락처 등록';

  @override
  String get emergencyContactAdded => '비상 연락처가 추가되었습니다';

  @override
  String get pleaseEnterNameAndPhone => '이름과 전화번호를 입력해주세요';

  @override
  String errorOccurred(Object error) {
    return '오류가 발생했습니다: $error';
  }

  @override
  String get tapForDetails => '자세히 보려면 탭하세요';

  @override
  String get welcome => '환영합니다';

  @override
  String get nickname => '닉네임';

  @override
  String get enterNickname => '닉네임을 입력해주세요';

  @override
  String get nicknameHint => '닉네임 입력...';

  @override
  String get emergencyContactSetup => '비상 연락처 설정';

  @override
  String get addContactPrompt => '안전을 위해 비상 연락처를 추가해주세요.';

  @override
  String get contactName => '연락처 이름';

  @override
  String get contactNameHint => '연락처 이름 입력...';

  @override
  String get contactPhone => '전화번호';

  @override
  String get contactPhoneHint => '전화번호 입력...';

  @override
  String get addContact => '연락처 추가';

  @override
  String get removeContact => '삭제';

  @override
  String get completeSetup => '설정 완료';

  @override
  String get skip => '건너뛰기';

  @override
  String get continueButton => '계속';

  @override
  String get finish => '완료';

  @override
  String get locationPermissionGranted => '위치 권한이 허용되었습니다';

  @override
  String get allowLocationPermission => '위치 권한 허용';

  @override
  String get notificationPermissionGranted => '알림 권한이 허용되었습니다';

  @override
  String get allowNotificationPermission => '알림 권한 허용';

  @override
  String get backToHome => '홈으로 돌아가기';

  @override
  String get notSet => '설정되지 않음';

  @override
  String get waitingForResponse => '응답 대기 중';

  @override
  String get tapToConfirm => '탭하여 확인';

  @override
  String get askQuestion => '질문하기';

  @override
  String get emergencyActionRequired => '⚠️ 긴급 조치가 필요합니다';

  @override
  String get evacuationInfo => '🚨 대피 정보';

  @override
  String get shelterInfo => '🏠 대피소 정보';

  @override
  String get emergencyAlert => '🚨 긴급 경보';

  @override
  String get safetyConfirmation => '✅ 안전 확인';

  @override
  String get hazardMapInfo => '🗺️ 위험 지도 정보';

  @override
  String get disasterLatestInfo => '📡 최신 재해 정보';

  @override
  String get disasterRelatedInfo => '🌀 재해 관련 정보';

  @override
  String get questionSent => '질문을 보냈습니다';

  @override
  String get notificationConfirmed => '알림을 확인했습니다';

  @override
  String get loading => '로딩 중...';

  @override
  String get timelineEmpty => '타임라인이 비어 있습니다';

  @override
  String get loadingTimeline => '타임라인 로딩 중...';

  @override
  String get gettingLatestInfo => 'SafeBeee의 최신 정보를 가져오는 중';

  @override
  String get infoWillAppearSoon => '곧 정보가 표시됩니다. 잠시 기다려 주세요.';

  @override
  String get userNickname => '사용자 닉네임';

  @override
  String get emergencyContactsList => '비상 연락처 목록';

  @override
  String get noEmergencyContacts => '등록된 비상 연락처가 없습니다';

  @override
  String get contacts => '개';

  @override
  String get contact => '개';

  @override
  String get resetAppToInitialState => '앱을 초기 상태로 재설정';

  @override
  String get confirmation => '확인';

  @override
  String get resetConfirmationMessage =>
      '모든 설정과 데이터가 삭제되고 초기 상태로 돌아갑니다. 확실하신가요?';

  @override
  String get reset => '재설정';

  @override
  String get editEmergencyContact => '비상 연락처 편집';

  @override
  String get deleteEmergencyContactConfirmation => '이 비상 연락처를 삭제하시겠습니까?';

  @override
  String get delete => '삭제';

  @override
  String get gpsEnabled => 'GPS 활성화';

  @override
  String get gpsDisabled => 'GPS 비활성화';

  @override
  String get gpsPermissionDenied => 'Permission Denied';

  @override
  String get mobile => '모바일';

  @override
  String get ethernet => '이더넷';

  @override
  String get offline => '오프라인';

  @override
  String get emergencySms => '긴급 SMS';

  @override
  String sendToAllContacts(int count) {
    return '전체 전송';
  }

  @override
  String get selectIndividually => '개별 선택';

  @override
  String get smsSafetyMessage => '[SafeBeee] 저는 안전하며 안전한 장소에 있습니다.';

  @override
  String get smsTemplateRecommended => '[SafeBeee] 저는 안전합니다.';

  @override
  String get smsTemplateDetailed =>
      '[SafeBeee] 저는 안전하며 안전한 장소에 있습니다. 걱정하지 마세요.';

  @override
  String get smsTemplateCheckIn => '[SafeBeee] 정기 연락입니다. 저는 잘 지내고 있습니다.';

  @override
  String smsTemplateRecommendedWithLocation(String location) {
    return '[SafeBeee] 저는 안전합니다. 현재 위치: $location';
  }

  @override
  String get smsAppOpened => 'SMS 앱이 열렸습니다';

  @override
  String get smsSent => 'SMS가 전송되었습니다';

  @override
  String get smsFailedToOpen => 'SMS 앱을 열 수 없습니다';

  @override
  String recipientCount(int count) {
    return '$count명';
  }

  @override
  String get openHazardMap => '위험 지도 열기';

  @override
  String get externalSiteWarning => '외부 사이트가 열립니다';

  @override
  String get hazardMapUrl => '위험 지도 URL';

  @override
  String get openInBrowser => '브라우저에서 열기';

  @override
  String get close => '닫기';

  @override
  String get sendComplete => '전송 완료';

  @override
  String get smsPrepared => 'SMS 준비 완료';

  @override
  String get copiedToClipboard => '클립보드에 복사됨';

  @override
  String get recipient => '수신자';

  @override
  String get message => '메시지';

  @override
  String get smsInstructions => '순서:';

  @override
  String get openSmsApp => '1. SMS 앱 열기';

  @override
  String get enterPhoneNumber => '2. 전화번호 입력 또는 선택';

  @override
  String get pasteAndSend => '3. 메시지 붙여넣기 후 전송';

  @override
  String get smsAppOpenedButton => 'SMS 앱이 열렸습니다';

  @override
  String smsAppOpenedMessage(String name, String phone) {
    return '$name ($phone)님께 SMS 앱을 열었습니다';
  }

  @override
  String get smsSendInstructions => 'SMS를 보낸 후 \'전송 완료\' 버튼을 눌러주세요';

  @override
  String get smsManualInstructions => '수동으로 SMS 보내는 방법:';

  @override
  String get smsCopyButtonInstruction => '1. \'복사\' 버튼으로 연락처와 메시지 복사';

  @override
  String get smsOpenAppInstruction => '2. SMS 앱을 수동으로 열기';

  @override
  String get smsPasteAndSendInstruction => '3. 전화번호와 메시지를 붙여넣고 전송';

  @override
  String get smsFailedToOpenApp => 'SMS 앱을 자동으로 열 수 없습니다';

  @override
  String get errorDetails => '오류 세부사항:';

  @override
  String get sendTo => '보낼 곳:';

  @override
  String get messageContent => '메시지 내용:';

  @override
  String allContactsSmsSuccess(int count) {
    return '$count명에게 SMS를 보냈습니다';
  }

  @override
  String get allContactsSmsFailed => '모든 연락처로 SMS 전송에 실패했습니다';

  @override
  String smsFailedWithError(String error) {
    return 'SMS 전송 실패: $error';
  }

  @override
  String get editMessage => '메시지 편집';

  @override
  String get copy => '복사';

  @override
  String failedToOpenHazardMap(String error) {
    return '위험 지도를 열 수 없습니다: $error';
  }

  @override
  String get hazardMapOpened => '위험 지도가 성공적으로 열렸습니다';

  @override
  String get hazardMapPortalSite => '위험 지도 포털 사이트';

  @override
  String get checkDisasterRiskInfo => '전국 재해 위험 정보 확인';

  @override
  String get checkVariousSettings => '각종 설정 등';

  @override
  String get add => 'Add';

  @override
  String get edit => 'Edit';

  @override
  String get loadingSettings => 'Loading settings...';

  @override
  String get heartbeatInterval => 'Heartbeat Interval';

  @override
  String get normalTime => 'Normal time';

  @override
  String get disasterTime => 'Disaster time';

  @override
  String get minutes => 'minutes';

  @override
  String get seconds => 'seconds';

  @override
  String get debugFeatures => 'Debug Features';

  @override
  String get currentSystemStatus => 'Current System Status';

  @override
  String get operationMode => 'Operation Mode';

  @override
  String get emergencyMode => 'Emergency Mode';

  @override
  String get normalMode => 'Normal Mode';

  @override
  String get connectionStatus => 'Connection Status';

  @override
  String get locationStatus => 'Location Status';

  @override
  String get enabled => 'Enabled';

  @override
  String get disabled => 'Disabled';

  @override
  String get battery => 'Battery';

  @override
  String get charging => 'Charging';

  @override
  String get emergencyModeActive =>
      'Emergency mode active: Heartbeat interval shortened';

  @override
  String get testAlert => 'Test Alert';

  @override
  String get switchToNormalMode => 'Switch to Normal Mode';

  @override
  String get switchToEmergencyMode => 'Switch to Emergency Mode';

  @override
  String get emergencyModeToggle => 'Emergency Mode Toggle';

  @override
  String get showSuggestionHistory => 'Show Suggestion History';

  @override
  String get completeReset => 'Complete Reset (Debug Only)';

  @override
  String get completeResetWarning =>
      'All data, settings, history, contacts, and Firebase will be completely deleted';

  @override
  String get showIntervalSettings => 'Show Interval Settings';

  @override
  String get debugNote =>
      'Debug features are only visible when TEST_MODE=true in .env';

  @override
  String get suggestionHistory => 'Suggestion History (Debug)';

  @override
  String get currentTypeBasedHistory => 'Current Type-based History';

  @override
  String get typeBasedHistoryEmpty => 'No type-based history';

  @override
  String get legacyIdBasedHistory => 'Legacy ID-based History';

  @override
  String get idBasedHistoryEmpty => 'No ID-based history';

  @override
  String andMore(int count) {
    return 'and $count more';
  }

  @override
  String get debugInfo => 'Debug Information';

  @override
  String get historyNote =>
      '・ Type-based is the current history management method\n・ ID-based is the old method (deprecated)\n・ Clear history if suggestions are not displayed';

  @override
  String get selectTestAlertType => 'Select Test Alert Type';

  @override
  String get earthquake => 'Earthquake';

  @override
  String get earthquakeTest => 'Emergency Earthquake Alert Test';

  @override
  String get tsunami => 'Tsunami';

  @override
  String get tsunamiTest => 'Tsunami Warning Test';

  @override
  String get heavyRain => 'Heavy Rain';

  @override
  String get heavyRainTest => 'Heavy Rain Special Warning Test';

  @override
  String get fire => 'Fire';

  @override
  String get fireTest => 'Fire Warning Test';

  @override
  String get forceResetEmergency => 'Force Emergency Mode Reset';

  @override
  String get forceResetEmergencyDesc =>
      'Forcefully reset emergency mode (debug only)';

  @override
  String get forceResetConfirm => 'Force Emergency Mode Reset';

  @override
  String get forceResetMessage =>
      'Are you sure you want to forcefully reset emergency mode?\n\n※This operation is valid for 5 minutes and should only be used for debugging purposes.';

  @override
  String get performReset => 'Reset';

  @override
  String get resettingEmergencyMode => 'Resetting emergency mode...';

  @override
  String get emergencyModeResetSuccess => 'Emergency mode reset successful';

  @override
  String get emergencyModeResetFailed => 'Failed to reset emergency mode';

  @override
  String get triggeringAlert => 'Triggering alert...';

  @override
  String alertTriggerSuccess(String message) {
    return 'Alert triggered successfully!\n$message';
  }

  @override
  String alertTriggerFailed(String error) {
    return 'Failed to trigger alert: $error';
  }

  @override
  String get debugAlertTest => 'Debug Alert (Test)';

  @override
  String get debugAlertDescription =>
      'This is a test alert triggered from debug features.';

  @override
  String get emergencyModeToggleConfirm => 'Emergency Mode Toggle';

  @override
  String get emergencyModeToggleMessage =>
      'Execute debug emergency mode toggle?\n\n・normal → emergency: Enable emergency mode\n・emergency → normal: Disable emergency mode\n\n※Heartbeat interval will be automatically adjusted';

  @override
  String get performToggle => 'Toggle';

  @override
  String get switchedToEmergencyMode => 'Switched to emergency mode';

  @override
  String get switchedToNormalMode => 'Switched to normal mode';

  @override
  String emergencyModeToggleFailed(String error) {
    return 'Failed to toggle emergency mode: $error';
  }

  @override
  String get completeAppReset => 'Complete App Reset';

  @override
  String get completeResetConfirm => 'Complete Debug Reset';

  @override
  String get completeResetConfirmMessage => 'Execute complete debug reset?';

  @override
  String get deleteTargets => 'Delete Targets (Irreversible):';

  @override
  String get deleteTargetsList =>
      '🗑️ All local settings and history\n🗑️ Firebase data (complete deletion)\n🗑️ Suggestion history (frontend and backend)\n🗑️ Disaster mode and emergency mode status\n🗑️ Emergency contacts\n🗑️ Chat history and timeline\n\n⚠️ Debug-only feature';

  @override
  String get performCompleteReset => 'Complete Reset';

  @override
  String get executingCompleteReset => 'Executing complete reset...';

  @override
  String get initializingData =>
      'Initializing Firebase, local data, timeline history, and disaster mode';

  @override
  String get completeResetSuccess =>
      'Complete reset successful. Moving to onboarding...';

  @override
  String completeResetFailed(String error) {
    return 'Complete reset failed: $error';
  }

  @override
  String get systemIntervalSettings => 'System Interval Settings';

  @override
  String get currentMode => 'Current Mode';

  @override
  String get disasterMonitoringInterval => 'Disaster Monitoring Interval';

  @override
  String get disasterMonitoringExplanation => 'Disaster Monitoring Interval?';

  @override
  String get disasterMonitoringDescription =>
      'Frequency of retrieving disaster information from JMA (Japan Meteorological Agency) and other sources.\nAutomatically checks for earthquakes, tsunamis, heavy rain, and other disasters,\nand notifies users in affected areas when new disasters are detected.';

  @override
  String get testModeSettings => 'Test Mode Settings';

  @override
  String get normalModeSettings => 'Normal Mode Settings';

  @override
  String get emergencyModeSettings => 'Emergency Mode Settings';

  @override
  String get intervalDescriptions => 'Interval Descriptions:';

  @override
  String get disasterMonitoring => 'Disaster Monitoring';

  @override
  String get newsCollection => 'News Collection';

  @override
  String get periodicDataCollection => 'Periodic Data Collection';

  @override
  String get heartbeat => 'Heartbeat';

  @override
  String get criticalAlert => 'Critical Alert';

  @override
  String get suggestionCooldown => 'Suggestion Cooldown';

  @override
  String get heartbeatIntervalSettings => 'Heartbeat Interval Settings';

  @override
  String get heartbeatIntervalDescription =>
      'Set the interval for sending device status to the server.\nShorter intervals consume more battery.';

  @override
  String get normalTimeLabel => 'Normal time:';

  @override
  String get disasterTimeLabel => 'Disaster time:';

  @override
  String get heartbeatNote =>
      '※ Automatically switches to shorter interval during disasters';

  @override
  String get heartbeatIntervalUpdated => 'Heartbeat interval updated';

  @override
  String settingsSaveFailed(String error) {
    return 'Failed to save settings: $error';
  }

  @override
  String get fetchingIntervalConfig => 'Fetching interval configuration...';

  @override
  String intervalConfigFetchFailed(String error) {
    return 'Failed to fetch interval configuration: $error';
  }

  @override
  String get emergencyEarthquakeAlertTest =>
      '🚨 Emergency Earthquake Alert (Test)';

  @override
  String get tsunamiWarningTest => '🌊 Tsunami Warning (Test)';

  @override
  String get heavyRainSpecialWarningTest =>
      '🌧️ Heavy Rain Special Warning (Test)';

  @override
  String get fireWarningTest => '🔥 Fire Warning (Test)';

  @override
  String get emergencyAlertTest => '🚨 Emergency Alert (Test)';

  @override
  String get earthquakeAlertTestDescription =>
      'This is a test emergency earthquake alert. Be prepared for strong shaking. (Test)';

  @override
  String get tsunamiAlertTestDescription =>
      'This is a test tsunami warning. Evacuate to higher ground. (Test)';

  @override
  String get heavyRainAlertTestDescription =>
      'This is a test heavy rain special warning. Take life-saving actions. (Test)';

  @override
  String get fireAlertTestDescription =>
      'This is a test fire warning. Evacuate immediately. (Test)';

  @override
  String get debugAlertTestDescription =>
      'This is a test alert triggered from debug features.';

  @override
  String get checkNationwideDisasterInfo => '전국 재해 정보 확인';

  @override
  String get viewHazardMap => '위험 지도 확인';

  @override
  String get sendEmergencySMS => '긴급 SMS 전송';

  @override
  String get checkSafetyInfo => '안전 정보 확인';

  @override
  String get evacuationGuidance => '대피 안내';

  @override
  String get emergencyContactInfo => '비상 연락처 정보';

  @override
  String smsSelectedSentSuccess(int successCount, int totalCount) {
    return 'SMS sent successfully to $successCount out of $totalCount selected contacts';
  }

  @override
  String get selectedContactsSmsFailed =>
      'Failed to send SMS to selected contacts';

  @override
  String get sendSafetyConfirmationMessage =>
      'Send safety confirmation message';

  @override
  String get sendMessage => 'Message to send';

  @override
  String get individualSmsMode => 'Individual SMS Mode';

  @override
  String get enterMessage => 'Enter message';

  @override
  String get selectRecipients => 'Select Recipients';

  @override
  String get selectAll => 'Select All';

  @override
  String get deselectAll => 'Deselect All';

  @override
  String sendToSelected(int count) {
    return 'Send to $count selected';
  }

  @override
  String get emergencyDefaultOverview =>
      'An emergency situation has occurred. Stay calm, assess the situation, and take appropriate safety actions. Pay attention to the latest information and prepare for evacuation if necessary.';

  @override
  String get earthquakeOverview =>
      'Strong earthquake activity detected. Take cover under a sturdy desk or table. Stay away from falling objects and prepare for potential aftershocks.';

  @override
  String get tsunamiOverview =>
      'Tsunami warning has been issued. Evacuate to higher ground immediately. Do not approach the coast and follow evacuation instructions.';

  @override
  String get fireOverview =>
      'Fire alert has been detected. Evacuate the building immediately using stairs, not elevators. Stay low to avoid smoke inhalation.';

  @override
  String get typhoonOverview =>
      'Typhoon is approaching. Stay indoors, secure windows, and avoid flooded areas. Prepare for power outages and water service disruptions.';

  @override
  String get floodOverview =>
      'Flood warning is in effect. Move to higher ground immediately. Avoid walking or driving through flood water. Monitor emergency broadcasts.';

  @override
  String get volcanicOverview =>
      'Volcanic activity has increased. Beware of volcanic ash and projectiles. Stay away from designated evacuation zones and cover nose and mouth.';

  @override
  String get landslideOverview =>
      'Landslide risk has increased. Stay away from mountainous areas and steep slopes. Watch for warning signs like springs and ground rumbling.';

  @override
  String get tornadoOverview =>
      'Tornado activity detected. Take shelter in a sturdy building away from windows. If outdoors, lie flat in a low area and protect yourself from flying debris.';

  @override
  String get earthquakeActions =>
      '1. Ensure personal safety first\n2. Take cover under desk or table\n3. Extinguish fires and secure escape routes\n4. Gather accurate information';

  @override
  String get tsunamiActions =>
      '1. Evacuate to higher ground immediately\n2. Avoid vehicle evacuation\n3. Stay away from coast until warning is lifted\n4. Follow evacuation orders';

  @override
  String get fireActions =>
      '1. Stay low to avoid smoke\n2. Secure exit and evacuate quickly\n3. Do not use elevators\n4. Call emergency services';

  @override
  String get typhoonActions =>
      '1. Stay indoors\n2. Reinforce windows\n3. Early evacuation from flood-prone areas\n4. Prepare for power and water outages';

  @override
  String get defaultEmergencyActions =>
      '1. Stay calm and assess situation\n2. Move to safe location\n3. Gather accurate information\n4. Prepare for evacuation';

  @override
  String get emergencyActions => 'Emergency Actions';

  @override
  String get emergencyContactSetupSubtitle =>
      'Register people to contact during disasters';

  @override
  String get nicknameSetupSubtitle => 'Set your display name';

  @override
  String get nearbyShelters => 'Nearby Shelters';

  @override
  String shelterCount(int count) {
    return '$count shelters';
  }

  @override
  String safetySmsDefaultMessage(String location) {
    return 'I am safe. Location: $location';
  }

  @override
  String get emergencyContactRequiredTitle => 'Emergency Contacts Required';

  @override
  String get emergencyContactRequiredMessage =>
      'Please register emergency contacts first.';

  @override
  String get selectContacts => 'Select Contacts';

  @override
  String get send => 'Send';

  @override
  String get smsSentSuccessfully => 'SMS sent successfully';

  @override
  String get smsFailedToSend => 'Failed to send SMS';

  @override
  String get sendSafetySms => 'Send Safety SMS';

  @override
  String get step1SelectRecipients => 'Step 1: Select Recipients';

  @override
  String get step2EditMessage => 'Step 2: Edit Message';

  @override
  String get selectTemplate => 'Select Template';

  @override
  String get editSmsMessage => 'Edit your SMS message...';

  @override
  String get aiResponseDisclaimer =>
      '※ 답변에는 불확실성이 포함될 수 있습니다. 응급 상황에서는 공식 정보원을 확인하세요.';

  @override
  String get currentLocation => '현재 위치';

  @override
  String get selectAtLeastOneContact => 'Please select at least one contact';

  @override
  String get messageCannotBeEmpty => 'Message cannot be empty';

  @override
  String get includeLocation => 'Include Location';

  @override
  String get contactsSelected => 'contacts selected';

  @override
  String get recommended => 'Recommended';

  @override
  String get detailed => 'Detailed';

  @override
  String get checkIn => 'Check In';

  @override
  String get smsPartialSuccess => 'Partially Sent';

  @override
  String get smsFailed => 'Failed to Send';

  @override
  String successCount(int count) {
    return '$count messages sent successfully';
  }

  @override
  String failedCount(int count) {
    return '$count messages failed to send';
  }

  @override
  String get suggestionDeleted => 'Suggestion deleted';

  @override
  String get hazardMapUrlNotFound => 'Hazard map URL not found';

  @override
  String get to => 'To';

  @override
  String get safetyConfirmationSms => 'Safety Confirmation SMS';

  @override
  String get confirmSendSms => 'Confirm SMS Send';

  @override
  String get smsContentPreview => 'SMS Content Preview';

  @override
  String get greeting => 'Hello';

  @override
  String get sendToAll => 'Send to All';

  @override
  String get loadingEmergencyInfo => '긴급 정보를 로딩 중입니다...';

  @override
  String get iAmSafe => '저는 안전합니다.';

  @override
  String voiceInputError(String error) {
    return '음성 입력 오류: $error';
  }

  @override
  String recordingSeconds(int seconds) {
    return '녹음 중... $seconds초';
  }

  @override
  String get sending => '전송 중...';

  @override
  String get wifi => 'Wi-Fi';

  @override
  String get locationPermissionEnabled => '📍 위치 권한이 활성화되었습니다';

  @override
  String get locationPermissionRequired =>
      '❌ 위치 권한을 활성화해주세요\n설정 > 앱 > SafeBeee > 위치';

  @override
  String get locationDiagnosticPerformed => '🔍 위치 권한 진단이 수행되었습니다\n로그를 확인해주세요';

  @override
  String get gpsServiceDisabled =>
      '📱 GPS 서비스가 비활성화되어 있습니다\n설정에서 위치 서비스를 활성화해주세요';

  @override
  String itemCount(int count) {
    return '$count 개';
  }

  @override
  String get location => '위치';

  @override
  String get latitude => '위도';

  @override
  String get longitude => '경도';

  @override
  String get accuracy => '정확도';

  @override
  String alertLevel(String level) {
    return '경보 단계: $level';
  }

  @override
  String announcementTime(String time) {
    return '발표 시간: $time';
  }

  @override
  String shelter(String name) {
    return '대피소: $name';
  }

  @override
  String errorSavingContact(String error) {
    return '저장 중 오류 발생: $error';
  }
}
