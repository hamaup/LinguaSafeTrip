// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => 'Permiso Requerido';

  @override
  String get permissionRequestSubtitle =>
      'Configurar permisos para funciones básicas de la aplicación';

  @override
  String get permissionLaterInfo =>
      'Estos permisos son importantes para las funciones de seguridad pero se pueden configurar más tarde.';

  @override
  String get locationPermissionTitle => 'Permiso de Ubicación';

  @override
  String get locationPermissionRationale =>
      'Esta aplicación utiliza su ubicación para notificarle sobre refugios cercanos y zonas de peligro.';

  @override
  String get notificationPermissionTitle => 'Permiso de Notificaciones';

  @override
  String get notificationPermissionRationale =>
      'Le enviaremos notificaciones sobre alertas de desastres y actualizaciones importantes.';

  @override
  String get next => 'Siguiente';

  @override
  String get settings => 'Configuración';

  @override
  String get language => 'Idioma';

  @override
  String get selectLanguage => 'Seleccionar Idioma';

  @override
  String get cancel => 'Cancelar';

  @override
  String get ok => 'OK';

  @override
  String get settingsLoadFailed =>
      'Error al cargar la configuración. Por favor, intente de nuevo.';

  @override
  String get notificationSettings => 'Configuración de Notificaciones';

  @override
  String get notificationSettingsDescription =>
      'Cambiar configuración de notificaciones de la aplicación';

  @override
  String get messageInputHint => 'Escriba un mensaje...';

  @override
  String get listening => 'Listening';

  @override
  String get voiceInput => 'Voice Input';

  @override
  String get voiceInputDescription => 'Input messages by voice';

  @override
  String get emergencyContacts => 'Contactos de Emergencia';

  @override
  String get addEmergencyContact => 'Agregar Contacto de Emergencia';

  @override
  String get name => 'Nombre';

  @override
  String get phoneNumber => 'Número de Teléfono';

  @override
  String get save => 'Guardar';

  @override
  String get registerEmergencyContact => 'Registrar Contacto de Emergencia';

  @override
  String get emergencyContactAdded => 'Contacto de emergencia agregado';

  @override
  String get pleaseEnterNameAndPhone =>
      'Por favor ingrese nombre y número de teléfono';

  @override
  String errorOccurred(Object error) {
    return 'Ocurrió un error: $error';
  }

  @override
  String get tapForDetails => 'Toque para ver detalles';

  @override
  String get welcome => 'Bienvenido';

  @override
  String get nickname => 'Apodo';

  @override
  String get enterNickname => 'Por favor ingrese su apodo';

  @override
  String get nicknameHint => 'Ingrese su apodo...';

  @override
  String get emergencyContactSetup =>
      'Configuración de Contactos de Emergencia';

  @override
  String get addContactPrompt =>
      'Por favor agregue contactos de emergencia por seguridad.';

  @override
  String get contactName => 'Nombre del Contacto';

  @override
  String get contactNameHint => 'Ingrese nombre del contacto...';

  @override
  String get contactPhone => 'Número de Teléfono';

  @override
  String get contactPhoneHint => 'Ingrese número de teléfono...';

  @override
  String get addContact => 'Agregar Contacto';

  @override
  String get removeContact => 'Eliminar';

  @override
  String get completeSetup => 'Completar Configuración';

  @override
  String get skip => 'Saltar';

  @override
  String get continueButton => 'Continuar';

  @override
  String get finish => 'Finalizar';

  @override
  String get locationPermissionGranted => 'Permiso de ubicación concedido';

  @override
  String get allowLocationPermission => 'Permitir Permiso de Ubicación';

  @override
  String get notificationPermissionGranted =>
      'Permiso de notificaciones concedido';

  @override
  String get allowNotificationPermission =>
      'Permitir Permiso de Notificaciones';

  @override
  String get backToHome => 'Volver al Inicio';

  @override
  String get notSet => 'No configurado';

  @override
  String get waitingForResponse => 'Esperando respuesta';

  @override
  String get tapToConfirm => 'Toca para confirmar';

  @override
  String get askQuestion => 'Hacer pregunta';

  @override
  String get emergencyActionRequired => '⚠️ Se requiere acción de emergencia';

  @override
  String get evacuationInfo => '🚨 Información de evacuación';

  @override
  String get shelterInfo => '🏠 Información de refugio';

  @override
  String get emergencyAlert => '🚨 Alerta de emergencia';

  @override
  String get safetyConfirmation => '✅ Confirmación de seguridad';

  @override
  String get hazardMapInfo => '🗺️ Información del mapa de peligros';

  @override
  String get disasterLatestInfo =>
      '📡 Información más reciente sobre desastres';

  @override
  String get disasterRelatedInfo => '🌀 Información relacionada con desastres';

  @override
  String get questionSent => 'Pregunta enviada';

  @override
  String get notificationConfirmed => 'Notificación confirmada';

  @override
  String get loading => 'Cargando...';

  @override
  String get timelineEmpty => 'La línea de tiempo está vacía';

  @override
  String get loadingTimeline => 'Cargando línea de tiempo...';

  @override
  String get gettingLatestInfo =>
      'Obteniendo la información más reciente de SafeBeee';

  @override
  String get infoWillAppearSoon =>
      'La información aparecerá pronto. Por favor espera.';

  @override
  String get userNickname => 'Apodo del Usuario';

  @override
  String get emergencyContactsList => 'Lista de Contactos de Emergencia';

  @override
  String get noEmergencyContacts =>
      'No hay contactos de emergencia registrados';

  @override
  String get contacts => 'contactos';

  @override
  String get contact => 'contacto';

  @override
  String get resetAppToInitialState =>
      'Restablecer aplicación al estado inicial';

  @override
  String get confirmation => 'Confirmación';

  @override
  String get resetConfirmationMessage =>
      'Toda la configuración y datos serán eliminados y se volverá al estado inicial. ¿Está seguro?';

  @override
  String get reset => 'Restablecer';

  @override
  String get editEmergencyContact => 'Editar Contacto de Emergencia';

  @override
  String get deleteEmergencyContactConfirmation =>
      '¿Está seguro de que desea eliminar este contacto de emergencia?';

  @override
  String get delete => 'Eliminar';

  @override
  String get gpsEnabled => 'GPS Habilitado';

  @override
  String get gpsDisabled => 'GPS Deshabilitado';

  @override
  String get gpsPermissionDenied => 'Permission Denied';

  @override
  String get mobile => 'Móvil';

  @override
  String get ethernet => 'Ethernet';

  @override
  String get offline => 'Sin conexión';

  @override
  String get emergencySms => 'SMS de emergencia';

  @override
  String sendToAllContacts(int count) {
    return 'Enviar a todos';
  }

  @override
  String get selectIndividually => 'Seleccionar individualmente';

  @override
  String get smsSafetyMessage =>
      '[SafeBeee] Estoy a salvo y en un lugar seguro.';

  @override
  String get smsTemplateRecommended => '[SafeBeee] Estoy bien y a salvo.';

  @override
  String get smsTemplateDetailed =>
      '[SafeBeee] Estoy bien y en un lugar seguro. No se preocupen por mí.';

  @override
  String get smsTemplateCheckIn =>
      '[SafeBeee] Contacto regular. Me encuentro bien.';

  @override
  String smsTemplateRecommendedWithLocation(String location) {
    return '[SafeBeee] Estoy bien y a salvo. Ubicación actual: $location';
  }

  @override
  String get smsAppOpened => 'Aplicación de SMS abierta';

  @override
  String get smsSent => 'SMS enviado';

  @override
  String get smsFailedToOpen => 'No se pudo abrir la aplicación de SMS';

  @override
  String recipientCount(int count) {
    return '$count destinatarios';
  }

  @override
  String get openHazardMap => 'Abrir mapa de riesgos';

  @override
  String get externalSiteWarning => 'Se abrirá un sitio externo';

  @override
  String get hazardMapUrl => 'URL del mapa de riesgos';

  @override
  String get openInBrowser => 'Abrir en navegador';

  @override
  String get close => 'Cerrar';

  @override
  String get sendComplete => 'Envío completo';

  @override
  String get smsPrepared => 'SMS preparado';

  @override
  String get copiedToClipboard => 'Copiado al portapapeles';

  @override
  String get recipient => 'Destinatario';

  @override
  String get message => 'Mensaje';

  @override
  String get smsInstructions => 'Instrucciones:';

  @override
  String get openSmsApp => '1. Abrir aplicación de SMS';

  @override
  String get enterPhoneNumber =>
      '2. Ingrese o seleccione el número de teléfono';

  @override
  String get pasteAndSend => '3. Pegue el mensaje y envíe';

  @override
  String get smsAppOpenedButton => 'Aplicación de SMS abierta';

  @override
  String smsAppOpenedMessage(String name, String phone) {
    return 'Aplicación de SMS abierta para $name ($phone)';
  }

  @override
  String get smsSendInstructions =>
      'Por favor presione el botón \'Envío completo\' después de enviar el SMS';

  @override
  String get smsManualInstructions =>
      'Instrucciones para enviar SMS manualmente:';

  @override
  String get smsCopyButtonInstruction =>
      '1. Presione el botón \'Copiar\' para copiar contacto y mensaje';

  @override
  String get smsOpenAppInstruction =>
      '2. Abra manualmente la aplicación de SMS';

  @override
  String get smsPasteAndSendInstruction =>
      '3. Pegue el número de teléfono y el mensaje, luego envíe';

  @override
  String get smsFailedToOpenApp =>
      'No se pudo abrir la aplicación de SMS automáticamente';

  @override
  String get errorDetails => 'Detalles del error:';

  @override
  String get sendTo => 'Enviar a:';

  @override
  String get messageContent => 'Contenido del mensaje:';

  @override
  String allContactsSmsSuccess(int count) {
    return 'SMS enviado a $count contactos';
  }

  @override
  String get allContactsSmsFailed =>
      'Error al enviar SMS a todos los contactos';

  @override
  String smsFailedWithError(String error) {
    return 'Error al enviar SMS: $error';
  }

  @override
  String get editMessage => 'Editar mensaje';

  @override
  String get copy => 'Copiar';

  @override
  String failedToOpenHazardMap(String error) {
    return 'Error al abrir el mapa de riesgos: $error';
  }

  @override
  String get hazardMapOpened => 'Mapa de riesgos abierto exitosamente';

  @override
  String get hazardMapPortalSite => 'Sitio Portal del Mapa de Riesgos';

  @override
  String get checkDisasterRiskInfo =>
      'Verificar información de riesgo de desastres a nivel nacional';

  @override
  String get checkVariousSettings => 'Varias configuraciones';

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
      'Verificar información de desastres a nivel nacional';

  @override
  String get viewHazardMap => 'Ver mapa de riesgos';

  @override
  String get sendEmergencySMS => 'Enviar SMS de emergencia';

  @override
  String get checkSafetyInfo => 'Verificar información de seguridad';

  @override
  String get evacuationGuidance => 'Guía de evacuación';

  @override
  String get emergencyContactInfo => 'Información de contactos de emergencia';

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
      '※ Las respuestas de IA pueden contener incertidumbres. Verifique con fuentes oficiales durante emergencias.';

  @override
  String get currentLocation => 'Ubicación actual';

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
  String get loadingEmergencyInfo => 'Cargando información de emergencia...';

  @override
  String get iAmSafe => 'Estoy a salvo.';

  @override
  String voiceInputError(String error) {
    return 'Error de entrada de voz: $error';
  }

  @override
  String recordingSeconds(int seconds) {
    return 'Grabando... $seconds segundos';
  }

  @override
  String get sending => 'Enviando...';

  @override
  String get wifi => 'Wi-Fi';

  @override
  String get locationPermissionEnabled => '📍 Permiso de ubicación habilitado';

  @override
  String get locationPermissionRequired =>
      '❌ Por favor habilite el permiso de ubicación\nAjustes > Aplicaciones > SafeBeee > Ubicación';

  @override
  String get locationDiagnosticPerformed =>
      '🔍 Diagnóstico de permiso de ubicación realizado\nPor favor revise los registros';

  @override
  String get gpsServiceDisabled =>
      '📱 El servicio GPS está deshabilitado\nPor favor habilite los servicios de ubicación en ajustes';

  @override
  String itemCount(int count) {
    return '$count elementos';
  }

  @override
  String get location => 'Ubicación';

  @override
  String get latitude => 'Lat';

  @override
  String get longitude => 'Lng';

  @override
  String get accuracy => 'Precisión';

  @override
  String alertLevel(String level) {
    return 'Nivel de alerta: $level';
  }

  @override
  String announcementTime(String time) {
    return 'Hora del anuncio: $time';
  }

  @override
  String shelter(String name) {
    return 'Refugio: $name';
  }

  @override
  String errorSavingContact(String error) {
    return 'Error al guardar: $error';
  }
}
