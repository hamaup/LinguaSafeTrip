// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => 'Autorisation Requise';

  @override
  String get permissionRequestSubtitle =>
      'Définir les autorisations pour les fonctions de base de l\'application';

  @override
  String get permissionLaterInfo =>
      'Ces autorisations sont importantes pour les fonctionnalités de sécurité mais peuvent être définies plus tard.';

  @override
  String get locationPermissionTitle => 'Autorisation de Localisation';

  @override
  String get locationPermissionRationale =>
      'Cette application utilise votre localisation pour vous notifier des abris à proximité et des zones dangereuses.';

  @override
  String get notificationPermissionTitle => 'Autorisation de Notifications';

  @override
  String get notificationPermissionRationale =>
      'Nous vous enverrons des notifications concernant les alertes de catastrophe et les mises à jour importantes.';

  @override
  String get next => 'Suivant';

  @override
  String get settings => 'Paramètres';

  @override
  String get language => 'Langue';

  @override
  String get selectLanguage => 'Sélectionner la Langue';

  @override
  String get cancel => 'Annuler';

  @override
  String get ok => 'OK';

  @override
  String get settingsLoadFailed =>
      'Échec du chargement des paramètres. Veuillez réessayer.';

  @override
  String get notificationSettings => 'Paramètres de Notifications';

  @override
  String get notificationSettingsDescription =>
      'Modifier les paramètres de notification de l\'application';

  @override
  String get messageInputHint => 'Tapez un message...';

  @override
  String get listening => 'Listening';

  @override
  String get voiceInput => 'Voice Input';

  @override
  String get voiceInputDescription => 'Input messages by voice';

  @override
  String get emergencyContacts => 'Contacts d\'Urgence';

  @override
  String get addEmergencyContact => 'Ajouter un Contact d\'Urgence';

  @override
  String get name => 'Nom';

  @override
  String get phoneNumber => 'Numéro de Téléphone';

  @override
  String get save => 'Enregistrer';

  @override
  String get registerEmergencyContact => 'Enregistrer un Contact d\'Urgence';

  @override
  String get emergencyContactAdded => 'Contact d\'urgence ajouté';

  @override
  String get pleaseEnterNameAndPhone =>
      'Veuillez saisir le nom et le numéro de téléphone';

  @override
  String errorOccurred(Object error) {
    return 'Une erreur s\'est produite : $error';
  }

  @override
  String get tapForDetails => 'Appuyez pour les détails';

  @override
  String get welcome => 'Bienvenue';

  @override
  String get nickname => 'Surnom';

  @override
  String get enterNickname => 'Veuillez saisir votre surnom';

  @override
  String get nicknameHint => 'Entrez votre surnom...';

  @override
  String get emergencyContactSetup => 'Configuration des Contacts d\'Urgence';

  @override
  String get addContactPrompt =>
      'Veuillez ajouter des contacts d\'urgence pour la sécurité.';

  @override
  String get contactName => 'Nom du Contact';

  @override
  String get contactNameHint => 'Entrez le nom du contact...';

  @override
  String get contactPhone => 'Numéro de Téléphone';

  @override
  String get contactPhoneHint => 'Entrez le numéro de téléphone...';

  @override
  String get addContact => 'Ajouter un Contact';

  @override
  String get removeContact => 'Supprimer';

  @override
  String get completeSetup => 'Terminer la Configuration';

  @override
  String get skip => 'Ignorer';

  @override
  String get continueButton => 'Continuer';

  @override
  String get finish => 'Terminer';

  @override
  String get locationPermissionGranted =>
      'Autorisation de localisation accordée';

  @override
  String get allowLocationPermission =>
      'Autoriser l\'Autorisation de Localisation';

  @override
  String get notificationPermissionGranted =>
      'Autorisation de notifications accordée';

  @override
  String get allowNotificationPermission =>
      'Autoriser l\'Autorisation de Notifications';

  @override
  String get backToHome => 'Retour à l\'Accueil';

  @override
  String get notSet => 'Non défini';

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
  String get userNickname => 'Surnom de l\'Utilisateur';

  @override
  String get emergencyContactsList => 'Liste des Contacts d\'Urgence';

  @override
  String get noEmergencyContacts => 'Aucun contact d\'urgence enregistré';

  @override
  String get contacts => 'contacts';

  @override
  String get contact => 'contact';

  @override
  String get resetAppToInitialState =>
      'Réinitialiser l\'application à l\'état initial';

  @override
  String get confirmation => 'Confirmation';

  @override
  String get resetConfirmationMessage =>
      'Tous les paramètres et données seront supprimés et l\'état initial sera restauré. Êtes-vous sûr ?';

  @override
  String get reset => 'Réinitialiser';

  @override
  String get editEmergencyContact => 'Modifier le Contact d\'Urgence';

  @override
  String get deleteEmergencyContactConfirmation =>
      'Êtes-vous sûr de vouloir supprimer ce contact d\'urgence ?';

  @override
  String get delete => 'Supprimer';

  @override
  String get gpsEnabled => 'GPS Activé';

  @override
  String get gpsDisabled => 'GPS Désactivé';

  @override
  String get gpsPermissionDenied => 'Permission Denied';

  @override
  String get mobile => 'Mobile';

  @override
  String get ethernet => 'Ethernet';

  @override
  String get offline => 'Hors ligne';

  @override
  String get emergencySms => 'Emergency SMS';

  @override
  String sendToAllContacts(int count) {
    return 'Send to all contacts ($count)';
  }

  @override
  String get selectIndividually => 'Select Individually';

  @override
  String get smsSafetyMessage =>
      '[SafeBeee] I am safe and in a secure location.';

  @override
  String get smsTemplateRecommended => '[SafeBeee] I am safe and secure.';

  @override
  String get smsTemplateDetailed =>
      '[SafeBeee] I am safe and in a secure location. Please don\'t worry about me.';

  @override
  String get smsTemplateCheckIn =>
      '[SafeBeee] Regular check-in. I am doing well.';

  @override
  String smsTemplateRecommendedWithLocation(String location) {
    return '[SafeBeee] I am safe and secure. Current location: $location';
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
      '※ Les réponses IA peuvent contenir des incertitudes. Vérifiez les sources officielles lors d\'urgences.';

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
