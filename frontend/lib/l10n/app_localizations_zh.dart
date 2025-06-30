// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Chinese (`zh`).
class AppLocalizationsZh extends AppLocalizations {
  AppLocalizationsZh([String locale = 'zh']) : super(locale);

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => 'Permission Required';

  @override
  String get permissionRequestSubtitle => 'Enable app functions';

  @override
  String get permissionLaterInfo =>
      'These permissions are important for safety features but can be set later.';

  @override
  String get locationPermissionTitle => 'Location Permission';

  @override
  String get locationPermissionRationale =>
      'This app uses your location to notify you about nearby shelters and danger zones.';

  @override
  String get notificationPermissionTitle => 'Notification Permission';

  @override
  String get notificationPermissionRationale =>
      'We will send you notifications about disaster alerts and important updates.';

  @override
  String get next => 'Next';

  @override
  String get settings => 'Settings';

  @override
  String get language => 'Language';

  @override
  String get selectLanguage => 'Select Language';

  @override
  String get cancel => '取消';

  @override
  String get ok => 'OK';

  @override
  String get settingsLoadFailed => 'Failed to load settings. Please try again.';

  @override
  String get notificationSettings => 'Notification Settings';

  @override
  String get notificationSettingsDescription =>
      'Change app notification settings';

  @override
  String get messageInputHint => 'Type a message...';

  @override
  String get listening => 'Listening';

  @override
  String get voiceInput => 'Voice Input';

  @override
  String get voiceInputDescription => 'Input messages by voice';

  @override
  String get emergencyContacts => 'Emergency Contacts';

  @override
  String get addEmergencyContact => 'Add Emergency Contact';

  @override
  String get name => 'Name';

  @override
  String get phoneNumber => 'Phone Number';

  @override
  String get save => 'Save';

  @override
  String get registerEmergencyContact => 'Register Emergency Contact';

  @override
  String get emergencyContactAdded => 'Emergency contact added';

  @override
  String get pleaseEnterNameAndPhone => 'Please enter name and phone number';

  @override
  String errorOccurred(Object error) {
    return 'An error occurred';
  }

  @override
  String get tapForDetails => 'Tap for details';

  @override
  String get welcome => 'Welcome';

  @override
  String get nickname => 'Nickname';

  @override
  String get enterNickname => 'Please enter your nickname';

  @override
  String get nicknameHint => 'Enter your nickname...';

  @override
  String get emergencyContactSetup => 'Emergency Contact Setup';

  @override
  String get addContactPrompt =>
      'Please add emergency contacts for safety purposes.';

  @override
  String get contactName => 'Contact Name';

  @override
  String get contactNameHint => 'Enter contact name...';

  @override
  String get contactPhone => 'Phone Number';

  @override
  String get contactPhoneHint => 'Enter phone number...';

  @override
  String get addContact => 'Add Contact';

  @override
  String get removeContact => 'Remove';

  @override
  String get completeSetup => 'Complete Setup';

  @override
  String get skip => 'Skip';

  @override
  String get continueButton => 'Continue';

  @override
  String get finish => 'Finish';

  @override
  String get locationPermissionGranted => 'Location permission granted';

  @override
  String get allowLocationPermission => 'Allow Location Permission';

  @override
  String get notificationPermissionGranted => 'Notification permission granted';

  @override
  String get allowNotificationPermission => 'Allow Notification Permission';

  @override
  String get backToHome => 'Back to Home';

  @override
  String get notSet => 'Not set';

  @override
  String get waitingForResponse => 'Waiting for response';

  @override
  String get tapToConfirm => 'Tap to confirm';

  @override
  String get askQuestion => 'Ask question';

  @override
  String get emergencyActionRequired => '⚠️ Emergency action required';

  @override
  String get evacuationInfo => '🚨 Evacuation information';

  @override
  String get shelterInfo => '🏠 Shelter information';

  @override
  String get emergencyAlert => '🚨 Emergency alert';

  @override
  String get safetyConfirmation => '✅ Safety confirmation';

  @override
  String get hazardMapInfo => '🗺️ Hazard map information';

  @override
  String get disasterLatestInfo => '📡 Latest disaster information';

  @override
  String get disasterRelatedInfo => '🌀 Disaster-related information';

  @override
  String get questionSent => 'Question sent';

  @override
  String get notificationConfirmed => 'Notification confirmed';

  @override
  String get loading => 'Loading...';

  @override
  String get timelineEmpty => 'Timeline is empty';

  @override
  String get loadingTimeline => 'Loading timeline...';

  @override
  String get gettingLatestInfo => 'Getting latest SafeBeee information';

  @override
  String get infoWillAppearSoon => 'Information will appear soon. Please wait.';

  @override
  String get userNickname => 'User Nickname';

  @override
  String get emergencyContactsList => 'Emergency Contacts List';

  @override
  String get noEmergencyContacts => 'No emergency contacts registered';

  @override
  String get contacts => 'contacts';

  @override
  String get contact => 'contact';

  @override
  String get resetAppToInitialState => 'Reset app to initial state';

  @override
  String get confirmation => 'Confirmation';

  @override
  String get resetConfirmationMessage =>
      'All settings and data will be deleted and returned to initial state. Are you sure?';

  @override
  String get reset => 'Reset';

  @override
  String get editEmergencyContact => 'Edit Emergency Contact';

  @override
  String get deleteEmergencyContactConfirmation =>
      'Are you sure you want to delete this emergency contact?';

  @override
  String get delete => 'Delete';

  @override
  String get gpsEnabled => 'GPS Enabled';

  @override
  String get gpsDisabled => 'GPS Disabled';

  @override
  String get gpsPermissionDenied => 'Permission Denied';

  @override
  String get mobile => 'Mobile';

  @override
  String get ethernet => 'Ethernet';

  @override
  String get offline => 'Offline';

  @override
  String get emergencySms => '紧急短信';

  @override
  String sendToAllContacts(int count) {
    return '发送给所有人';
  }

  @override
  String get selectIndividually => '单独选择';

  @override
  String get smsSafetyMessage => '[SafeBeee] 我很安全，现在在安全的地方。';

  @override
  String get smsTemplateRecommended => '[SafeBeee] 我很安全，一切都好。';

  @override
  String get smsTemplateDetailed => '[SafeBeee] 我很安全，现在在安全的地方。请不要担心我。';

  @override
  String get smsTemplateCheckIn => '[SafeBeee] 定期联系。我一切都好。';

  @override
  String smsTemplateRecommendedWithLocation(String location) {
    return '[SafeBeee] 我很安全，一切都好。当前位置：$location';
  }

  @override
  String get smsAppOpened => 'SMS app opened';

  @override
  String get smsSent => 'SMS Sent';

  @override
  String get smsFailedToOpen => 'Failed to open SMS app';

  @override
  String recipientCount(int count) {
    return '$count recipients';
  }

  @override
  String get openHazardMap => 'Open Hazard Map';

  @override
  String get externalSiteWarning => 'External site will open';

  @override
  String get hazardMapUrl => 'Hazard Map URL';

  @override
  String get openInBrowser => 'Open in Browser';

  @override
  String get close => 'Close';

  @override
  String get sendComplete => 'Send Complete';

  @override
  String get smsPrepared => 'SMS Prepared';

  @override
  String get copiedToClipboard => 'Copied to clipboard';

  @override
  String get recipient => 'Recipient';

  @override
  String get message => 'Message';

  @override
  String get smsInstructions => 'Instructions:';

  @override
  String get openSmsApp => 'Open SMS App';

  @override
  String get enterPhoneNumber => '2. Enter or select phone number';

  @override
  String get pasteAndSend => '3. Paste message and send';

  @override
  String get smsAppOpenedButton => 'SMS app opened';

  @override
  String smsAppOpenedMessage(String name, String phone) {
    return 'SMS app opened for $name ($phone)';
  }

  @override
  String get smsSendInstructions =>
      'Please press \'Send Complete\' button after sending the SMS';

  @override
  String get smsManualInstructions => 'Manual SMS sending instructions:';

  @override
  String get smsCopyButtonInstruction =>
      '1. Press \'Copy\' button to copy contact and message';

  @override
  String get smsOpenAppInstruction => '2. Manually open SMS app';

  @override
  String get smsPasteAndSendInstruction =>
      '3. Paste phone number and message, then send';

  @override
  String get smsFailedToOpenApp => 'Failed to open SMS app automatically';

  @override
  String get errorDetails => 'Error details:';

  @override
  String get sendTo => 'Send to:';

  @override
  String get messageContent => 'Message content:';

  @override
  String allContactsSmsSuccess(int count) {
    return 'SMS sent to $count contacts';
  }

  @override
  String get allContactsSmsFailed => 'Failed to send SMS to all contacts';

  @override
  String smsFailedWithError(String error) {
    return 'Failed to send SMS: $error';
  }

  @override
  String get editMessage => 'Edit Message';

  @override
  String get copy => 'Copy';

  @override
  String failedToOpenHazardMap(String error) {
    return 'Failed to open hazard map: $error';
  }

  @override
  String get hazardMapOpened => 'Hazard map opened successfully';

  @override
  String get hazardMapPortalSite => 'Hazard Map Portal Site';

  @override
  String get checkDisasterRiskInfo =>
      'Check nationwide disaster risk information';

  @override
  String get checkVariousSettings => 'Various settings';

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
  String get checkNationwideDisasterInfo =>
      'Check nationwide disaster information';

  @override
  String get viewHazardMap => 'View hazard map';

  @override
  String get sendEmergencySMS => 'Send emergency SMS';

  @override
  String get checkSafetyInfo => 'Check safety information';

  @override
  String get evacuationGuidance => 'Evacuation guidance';

  @override
  String get emergencyContactInfo => 'Emergency contact information';

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
  String get send => '发送';

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
      '※ AI responses may contain uncertainties. Please verify with official sources during emergencies.';

  @override
  String get currentLocation => 'Current Location';

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
  String get safetyConfirmationSms => '安全确认短信';

  @override
  String get confirmSendSms => 'Confirm SMS Send';

  @override
  String get smsContentPreview => 'SMS Content Preview';

  @override
  String get greeting => 'Hello';

  @override
  String get sendToAll => 'Send to All';

  @override
  String get loadingEmergencyInfo => 'Loading emergency information...';

  @override
  String get iAmSafe => 'I am safe.';

  @override
  String voiceInputError(String error) {
    return 'Voice input error: $error';
  }

  @override
  String recordingSeconds(int seconds) {
    return 'Recording... $seconds seconds';
  }

  @override
  String get sending => 'Sending...';

  @override
  String get wifi => 'Wi-Fi';

  @override
  String get locationPermissionEnabled =>
      '📍 Location permission has been enabled';

  @override
  String get locationPermissionRequired =>
      '❌ Please enable location permission\nSettings > Apps > SafeBeee > Location';

  @override
  String get locationDiagnosticPerformed =>
      '🔍 Location permission diagnostic performed\nPlease check the logs';

  @override
  String get gpsServiceDisabled =>
      '📱 GPS service is disabled\nPlease enable location services in settings';

  @override
  String itemCount(int count) {
    return '$count items';
  }

  @override
  String get location => 'Location';

  @override
  String get latitude => 'Lat';

  @override
  String get longitude => 'Lng';

  @override
  String get accuracy => 'Accuracy';

  @override
  String alertLevel(String level) {
    return 'Alert Level: $level';
  }

  @override
  String announcementTime(String time) {
    return 'Announcement Time: $time';
  }

  @override
  String shelter(String name) {
    return 'Shelter: $name';
  }

  @override
  String errorSavingContact(String error) {
    return 'Error occurred while saving: $error';
  }
}

/// The translations for Chinese, as used in China (`zh_CN`).
class AppLocalizationsZhCn extends AppLocalizationsZh {
  AppLocalizationsZhCn() : super('zh_CN');

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => '需要权限';

  @override
  String get permissionRequestSubtitle => '设置应用基本功能所需的权限';

  @override
  String get permissionLaterInfo => '这些权限对安全功能很重要，但也可以稍后设置。';

  @override
  String get locationPermissionTitle => '位置权限';

  @override
  String get locationPermissionRationale => '本应用使用您的位置信息来通知您附近的避难所和危险区域。';

  @override
  String get notificationPermissionTitle => '通知权限';

  @override
  String get notificationPermissionRationale => '我们将向您发送有关灾害警报和重要更新的通知。';

  @override
  String get next => '下一步';

  @override
  String get settings => '设置';

  @override
  String get language => '语言';

  @override
  String get selectLanguage => '选择语言';

  @override
  String get cancel => '取消';

  @override
  String get ok => '确定';

  @override
  String get settingsLoadFailed => '加载设置失败。请重试。';

  @override
  String get notificationSettings => '通知设置';

  @override
  String get notificationSettingsDescription => '更改应用通知设置';

  @override
  String get messageInputHint => '输入消息...';

  @override
  String get emergencyContacts => '紧急联系人';

  @override
  String get addEmergencyContact => '添加紧急联系人';

  @override
  String get name => '姓名';

  @override
  String get phoneNumber => '电话号码';

  @override
  String get save => '保存';

  @override
  String get registerEmergencyContact => '注册紧急联系人';

  @override
  String get emergencyContactAdded => '已添加紧急联系人';

  @override
  String get pleaseEnterNameAndPhone => '请输入姓名和电话号码';

  @override
  String errorOccurred(Object error) {
    return '发生错误：$error';
  }

  @override
  String get tapForDetails => '点击查看详情';

  @override
  String get nickname => '昵称';

  @override
  String get enterNickname => '请输入显示用的昵称';

  @override
  String get nicknameHint => '输入昵称...';

  @override
  String get addContactPrompt => '您可以注册紧急时要联系的人（可选）';

  @override
  String get contactName => '联系人姓名';

  @override
  String get contactNameHint => '输入联系人姓名...';

  @override
  String get contactPhone => '电话号码';

  @override
  String get contactPhoneHint => '输入电话号码...';

  @override
  String get addContact => '添加联系人';

  @override
  String get skip => '跳过';

  @override
  String get finish => '完成';

  @override
  String get backToHome => '返回主页';

  @override
  String get notSet => '未设置';

  @override
  String get loading => '加载中...';

  @override
  String get userNickname => '用户昵称';

  @override
  String get emergencyContactsList => '紧急联系人列表';

  @override
  String get noEmergencyContacts => '未设置紧急联系人';

  @override
  String get resetAppToInitialState => '重置应用到初始状态';

  @override
  String get confirmation => '确认';

  @override
  String get resetConfirmationMessage => '这将删除所有数据并重启应用。您确定吗？';

  @override
  String get reset => '重置';

  @override
  String get editEmergencyContact => '编辑紧急联系人';

  @override
  String get deleteEmergencyContactConfirmation => '确定要删除此紧急联系人吗？';

  @override
  String get delete => '删除';

  @override
  String get emergencySms => '紧急短信';

  @override
  String sendToAllContacts(int count) {
    return '发送给所有人';
  }

  @override
  String get selectIndividually => '单独选择';

  @override
  String get smsSafetyMessage => '[SafeBeee] 我很安全，现在在安全的地方。';

  @override
  String get smsTemplateRecommended => '[SafeBeee] 我很安全，一切都好。';

  @override
  String get smsTemplateDetailed => '[SafeBeee] 我很安全，现在在安全的地方。请不要担心我。';

  @override
  String get smsTemplateCheckIn => '[SafeBeee] 定期联系。我一切都好。';

  @override
  String smsTemplateRecommendedWithLocation(String location) {
    return '[SafeBeee] 我很安全，一切都好。当前位置：$location';
  }

  @override
  String get edit => '编辑';

  @override
  String get send => '发送';

  @override
  String get aiResponseDisclaimer => '※ AI 回复可能包含不确定性。紧急情况下请验证官方信息源。';

  @override
  String get currentLocation => '当前位置';

  @override
  String get safetyConfirmationSms => '安全确认短信';

  @override
  String get loadingEmergencyInfo => '正在加载紧急信息...';

  @override
  String get iAmSafe => '我很安全。';

  @override
  String voiceInputError(String error) {
    return '语音输入错误：$error';
  }

  @override
  String recordingSeconds(int seconds) {
    return '录音中... $seconds秒';
  }

  @override
  String get sending => '发送中...';

  @override
  String get wifi => 'Wi-Fi';

  @override
  String get locationPermissionEnabled => '📍 位置权限已启用';

  @override
  String get locationPermissionRequired => '❌ 请启用位置权限\n设置 > 应用 > SafeBeee > 位置';

  @override
  String get locationDiagnosticPerformed => '🔍 已执行位置权限诊断\n请查看日志';

  @override
  String get gpsServiceDisabled => '📱 GPS服务已禁用\n请在设置中启用位置服务';

  @override
  String itemCount(int count) {
    return '$count 项';
  }

  @override
  String get location => '位置';

  @override
  String get latitude => '纬度';

  @override
  String get longitude => '经度';

  @override
  String get accuracy => '精度';

  @override
  String alertLevel(String level) {
    return '警戒级别：$level';
  }

  @override
  String announcementTime(String time) {
    return '发布时间：$time';
  }

  @override
  String shelter(String name) {
    return '避难所：$name';
  }

  @override
  String errorSavingContact(String error) {
    return '保存时发生错误：$error';
  }
}

/// The translations for Chinese, as used in Taiwan (`zh_TW`).
class AppLocalizationsZhTw extends AppLocalizationsZh {
  AppLocalizationsZhTw() : super('zh_TW');

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => '需要權限';

  @override
  String get permissionRequestSubtitle => '設定應用基本功能所需的權限';

  @override
  String get permissionLaterInfo => '這些權限對安全功能很重要，但也可以稍後設定。';

  @override
  String get locationPermissionTitle => '位置權限';

  @override
  String get locationPermissionRationale => '本應用程式使用您的位置資訊來通知您附近的避難所和危險區域。';

  @override
  String get notificationPermissionTitle => '通知權限';

  @override
  String get notificationPermissionRationale => '我們將向您發送有關災害警報和重要更新的通知。';

  @override
  String get next => '下一步';

  @override
  String get settings => '設定';

  @override
  String get language => '語言';

  @override
  String get selectLanguage => '選擇語言';

  @override
  String get cancel => '取消';

  @override
  String get ok => '確定';

  @override
  String get settingsLoadFailed => '載入設定失敗。請重試。';

  @override
  String get notificationSettings => '通知設定';

  @override
  String get notificationSettingsDescription => '更改應用程式通知設定';

  @override
  String get messageInputHint => '輸入訊息...';

  @override
  String get emergencyContacts => '緊急聯絡人';

  @override
  String get addEmergencyContact => '新增緊急聯絡人';

  @override
  String get name => '姓名';

  @override
  String get phoneNumber => '電話號碼';

  @override
  String get save => '儲存';

  @override
  String get registerEmergencyContact => '註冊緊急聯絡人';

  @override
  String get emergencyContactAdded => '已新增緊急聯絡人';

  @override
  String get pleaseEnterNameAndPhone => '請輸入姓名和電話號碼';

  @override
  String errorOccurred(Object error) {
    return '發生錯誤：$error';
  }

  @override
  String get tapForDetails => '點擊檢視詳情';

  @override
  String get nickname => '暱稱';

  @override
  String get enterNickname => '請輸入顯示用的暱稱';

  @override
  String get nicknameHint => '輸入暱稱...';

  @override
  String get addContactPrompt => '您可以註冊緊急時要聯絡的人（可選）';

  @override
  String get contactName => '聯絡人姓名';

  @override
  String get contactNameHint => '輸入聯絡人姓名...';

  @override
  String get contactPhone => '電話號碼';

  @override
  String get contactPhoneHint => '輸入電話號碼...';

  @override
  String get addContact => '新增聯絡人';

  @override
  String get skip => '跳過';

  @override
  String get finish => '完成';

  @override
  String get backToHome => '返回主頁';

  @override
  String get notSet => '未設定';

  @override
  String get userNickname => '使用者暱稱';

  @override
  String get emergencyContactsList => '緊急聯絡人清單';

  @override
  String get noEmergencyContacts => '未設定緊急聯絡人';

  @override
  String get resetAppToInitialState => '重置應用程式到初始狀態';

  @override
  String get confirmation => '確認';

  @override
  String get resetConfirmationMessage => '這將刪除所有資料並重新啟動應用程式。您確定嗎？';

  @override
  String get reset => '重置';

  @override
  String get editEmergencyContact => '編輯緊急聯絡人';

  @override
  String get deleteEmergencyContactConfirmation => '確定要刪除此緊急聯絡人嗎？';

  @override
  String get delete => '刪除';

  @override
  String get edit => '編輯';

  @override
  String get aiResponseDisclaimer => '※ AI 回覆可能包含不確定性。緊急情況下請驗證官方資訊來源。';
}
