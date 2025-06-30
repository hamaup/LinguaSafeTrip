import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_de.dart';
import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
import 'app_localizations_fr.dart';
import 'app_localizations_it.dart';
import 'app_localizations_ja.dart';
import 'app_localizations_ko.dart';
import 'app_localizations_pt.dart';
import 'app_localizations_ru.dart';
import 'app_localizations_zh.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('de'),
    Locale('en'),
    Locale('es'),
    Locale('fr'),
    Locale('it'),
    Locale('ja'),
    Locale('ko'),
    Locale('pt'),
    Locale('ru'),
    Locale('zh'),
    Locale('zh', 'CN'),
    Locale('zh', 'TW'),
  ];

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'SafetyBee'**
  String get appName;

  /// No description provided for @permissionRequiredTitle.
  ///
  /// In en, this message translates to:
  /// **'Permission Required'**
  String get permissionRequiredTitle;

  /// No description provided for @permissionRequestSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Enable app functions'**
  String get permissionRequestSubtitle;

  /// No description provided for @permissionLaterInfo.
  ///
  /// In en, this message translates to:
  /// **'These permissions are important for safety features but can be set later.'**
  String get permissionLaterInfo;

  /// No description provided for @locationPermissionTitle.
  ///
  /// In en, this message translates to:
  /// **'Location Permission'**
  String get locationPermissionTitle;

  /// No description provided for @locationPermissionRationale.
  ///
  /// In en, this message translates to:
  /// **'This app uses your location to notify you about nearby shelters and danger zones.'**
  String get locationPermissionRationale;

  /// No description provided for @notificationPermissionTitle.
  ///
  /// In en, this message translates to:
  /// **'Notification Permission'**
  String get notificationPermissionTitle;

  /// No description provided for @notificationPermissionRationale.
  ///
  /// In en, this message translates to:
  /// **'We will send you notifications about disaster alerts and important updates.'**
  String get notificationPermissionRationale;

  /// No description provided for @next.
  ///
  /// In en, this message translates to:
  /// **'Next'**
  String get next;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @selectLanguage.
  ///
  /// In en, this message translates to:
  /// **'Select Language'**
  String get selectLanguage;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @ok.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get ok;

  /// No description provided for @settingsLoadFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to load settings. Please try again.'**
  String get settingsLoadFailed;

  /// No description provided for @notificationSettings.
  ///
  /// In en, this message translates to:
  /// **'Notification Settings'**
  String get notificationSettings;

  /// No description provided for @notificationSettingsDescription.
  ///
  /// In en, this message translates to:
  /// **'Change app notification settings'**
  String get notificationSettingsDescription;

  /// No description provided for @messageInputHint.
  ///
  /// In en, this message translates to:
  /// **'Type a message...'**
  String get messageInputHint;

  /// No description provided for @listening.
  ///
  /// In en, this message translates to:
  /// **'Listening'**
  String get listening;

  /// No description provided for @voiceInput.
  ///
  /// In en, this message translates to:
  /// **'Voice Input'**
  String get voiceInput;

  /// No description provided for @voiceInputDescription.
  ///
  /// In en, this message translates to:
  /// **'Input messages by voice'**
  String get voiceInputDescription;

  /// No description provided for @emergencyContacts.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contacts'**
  String get emergencyContacts;

  /// No description provided for @addEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Add Emergency Contact'**
  String get addEmergencyContact;

  /// No description provided for @name.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get name;

  /// No description provided for @phoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Phone Number'**
  String get phoneNumber;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @registerEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Register Emergency Contact'**
  String get registerEmergencyContact;

  /// No description provided for @emergencyContactAdded.
  ///
  /// In en, this message translates to:
  /// **'Emergency contact added'**
  String get emergencyContactAdded;

  /// No description provided for @pleaseEnterNameAndPhone.
  ///
  /// In en, this message translates to:
  /// **'Please enter name and phone number'**
  String get pleaseEnterNameAndPhone;

  /// No description provided for @errorOccurred.
  ///
  /// In en, this message translates to:
  /// **'An error occurred'**
  String errorOccurred(Object error);

  /// No description provided for @tapForDetails.
  ///
  /// In en, this message translates to:
  /// **'Tap for details'**
  String get tapForDetails;

  /// No description provided for @welcome.
  ///
  /// In en, this message translates to:
  /// **'Welcome'**
  String get welcome;

  /// No description provided for @nickname.
  ///
  /// In en, this message translates to:
  /// **'Nickname'**
  String get nickname;

  /// No description provided for @enterNickname.
  ///
  /// In en, this message translates to:
  /// **'Please enter your nickname'**
  String get enterNickname;

  /// No description provided for @nicknameHint.
  ///
  /// In en, this message translates to:
  /// **'Enter your nickname...'**
  String get nicknameHint;

  /// No description provided for @emergencyContactSetup.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contact Setup'**
  String get emergencyContactSetup;

  /// No description provided for @addContactPrompt.
  ///
  /// In en, this message translates to:
  /// **'Please add emergency contacts for safety purposes.'**
  String get addContactPrompt;

  /// No description provided for @contactName.
  ///
  /// In en, this message translates to:
  /// **'Contact Name'**
  String get contactName;

  /// No description provided for @contactNameHint.
  ///
  /// In en, this message translates to:
  /// **'Enter contact name...'**
  String get contactNameHint;

  /// No description provided for @contactPhone.
  ///
  /// In en, this message translates to:
  /// **'Phone Number'**
  String get contactPhone;

  /// No description provided for @contactPhoneHint.
  ///
  /// In en, this message translates to:
  /// **'Enter phone number...'**
  String get contactPhoneHint;

  /// No description provided for @addContact.
  ///
  /// In en, this message translates to:
  /// **'Add Contact'**
  String get addContact;

  /// No description provided for @removeContact.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get removeContact;

  /// No description provided for @completeSetup.
  ///
  /// In en, this message translates to:
  /// **'Complete Setup'**
  String get completeSetup;

  /// No description provided for @skip.
  ///
  /// In en, this message translates to:
  /// **'Skip'**
  String get skip;

  /// No description provided for @continueButton.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continueButton;

  /// No description provided for @finish.
  ///
  /// In en, this message translates to:
  /// **'Finish'**
  String get finish;

  /// No description provided for @locationPermissionGranted.
  ///
  /// In en, this message translates to:
  /// **'Location permission granted'**
  String get locationPermissionGranted;

  /// No description provided for @allowLocationPermission.
  ///
  /// In en, this message translates to:
  /// **'Allow Location Permission'**
  String get allowLocationPermission;

  /// No description provided for @notificationPermissionGranted.
  ///
  /// In en, this message translates to:
  /// **'Notification permission granted'**
  String get notificationPermissionGranted;

  /// No description provided for @allowNotificationPermission.
  ///
  /// In en, this message translates to:
  /// **'Allow Notification Permission'**
  String get allowNotificationPermission;

  /// No description provided for @backToHome.
  ///
  /// In en, this message translates to:
  /// **'Back to Home'**
  String get backToHome;

  /// No description provided for @notSet.
  ///
  /// In en, this message translates to:
  /// **'Not set'**
  String get notSet;

  /// No description provided for @waitingForResponse.
  ///
  /// In en, this message translates to:
  /// **'Waiting for response'**
  String get waitingForResponse;

  /// No description provided for @tapToConfirm.
  ///
  /// In en, this message translates to:
  /// **'Tap to confirm'**
  String get tapToConfirm;

  /// No description provided for @askQuestion.
  ///
  /// In en, this message translates to:
  /// **'Ask question'**
  String get askQuestion;

  /// No description provided for @emergencyActionRequired.
  ///
  /// In en, this message translates to:
  /// **'⚠️ Emergency action required'**
  String get emergencyActionRequired;

  /// No description provided for @evacuationInfo.
  ///
  /// In en, this message translates to:
  /// **'🚨 Evacuation information'**
  String get evacuationInfo;

  /// No description provided for @shelterInfo.
  ///
  /// In en, this message translates to:
  /// **'🏠 Shelter information'**
  String get shelterInfo;

  /// No description provided for @emergencyAlert.
  ///
  /// In en, this message translates to:
  /// **'🚨 Emergency alert'**
  String get emergencyAlert;

  /// No description provided for @safetyConfirmation.
  ///
  /// In en, this message translates to:
  /// **'✅ Safety confirmation'**
  String get safetyConfirmation;

  /// No description provided for @hazardMapInfo.
  ///
  /// In en, this message translates to:
  /// **'🗺️ Hazard map information'**
  String get hazardMapInfo;

  /// No description provided for @disasterLatestInfo.
  ///
  /// In en, this message translates to:
  /// **'📡 Latest disaster information'**
  String get disasterLatestInfo;

  /// No description provided for @disasterRelatedInfo.
  ///
  /// In en, this message translates to:
  /// **'🌀 Disaster-related information'**
  String get disasterRelatedInfo;

  /// No description provided for @questionSent.
  ///
  /// In en, this message translates to:
  /// **'Question sent'**
  String get questionSent;

  /// No description provided for @notificationConfirmed.
  ///
  /// In en, this message translates to:
  /// **'Notification confirmed'**
  String get notificationConfirmed;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading...'**
  String get loading;

  /// No description provided for @timelineEmpty.
  ///
  /// In en, this message translates to:
  /// **'Timeline is empty'**
  String get timelineEmpty;

  /// No description provided for @loadingTimeline.
  ///
  /// In en, this message translates to:
  /// **'Loading timeline...'**
  String get loadingTimeline;

  /// No description provided for @gettingLatestInfo.
  ///
  /// In en, this message translates to:
  /// **'Getting latest SafeBeee information'**
  String get gettingLatestInfo;

  /// No description provided for @infoWillAppearSoon.
  ///
  /// In en, this message translates to:
  /// **'Information will appear soon. Please wait.'**
  String get infoWillAppearSoon;

  /// No description provided for @userNickname.
  ///
  /// In en, this message translates to:
  /// **'User Nickname'**
  String get userNickname;

  /// No description provided for @emergencyContactsList.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contacts List'**
  String get emergencyContactsList;

  /// No description provided for @noEmergencyContacts.
  ///
  /// In en, this message translates to:
  /// **'No emergency contacts registered'**
  String get noEmergencyContacts;

  /// No description provided for @contacts.
  ///
  /// In en, this message translates to:
  /// **'contacts'**
  String get contacts;

  /// No description provided for @contact.
  ///
  /// In en, this message translates to:
  /// **'contact'**
  String get contact;

  /// No description provided for @resetAppToInitialState.
  ///
  /// In en, this message translates to:
  /// **'Reset app to initial state'**
  String get resetAppToInitialState;

  /// No description provided for @confirmation.
  ///
  /// In en, this message translates to:
  /// **'Confirmation'**
  String get confirmation;

  /// No description provided for @resetConfirmationMessage.
  ///
  /// In en, this message translates to:
  /// **'All settings and data will be deleted and returned to initial state. Are you sure?'**
  String get resetConfirmationMessage;

  /// No description provided for @reset.
  ///
  /// In en, this message translates to:
  /// **'Reset'**
  String get reset;

  /// No description provided for @editEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Edit Emergency Contact'**
  String get editEmergencyContact;

  /// No description provided for @deleteEmergencyContactConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to delete this emergency contact?'**
  String get deleteEmergencyContactConfirmation;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @gpsEnabled.
  ///
  /// In en, this message translates to:
  /// **'GPS Enabled'**
  String get gpsEnabled;

  /// No description provided for @gpsDisabled.
  ///
  /// In en, this message translates to:
  /// **'GPS Disabled'**
  String get gpsDisabled;

  /// No description provided for @gpsPermissionDenied.
  ///
  /// In en, this message translates to:
  /// **'Permission Denied'**
  String get gpsPermissionDenied;

  /// No description provided for @mobile.
  ///
  /// In en, this message translates to:
  /// **'Mobile'**
  String get mobile;

  /// No description provided for @ethernet.
  ///
  /// In en, this message translates to:
  /// **'Ethernet'**
  String get ethernet;

  /// No description provided for @offline.
  ///
  /// In en, this message translates to:
  /// **'Offline'**
  String get offline;

  /// No description provided for @emergencySms.
  ///
  /// In en, this message translates to:
  /// **'Emergency SMS'**
  String get emergencySms;

  /// No description provided for @sendToAllContacts.
  ///
  /// In en, this message translates to:
  /// **'Send to all contacts ({count})'**
  String sendToAllContacts(int count);

  /// No description provided for @selectIndividually.
  ///
  /// In en, this message translates to:
  /// **'Select Individually'**
  String get selectIndividually;

  /// No description provided for @smsSafetyMessage.
  ///
  /// In en, this message translates to:
  /// **'[SafeBeee] I am safe and in a secure location.'**
  String get smsSafetyMessage;

  /// No description provided for @smsTemplateRecommended.
  ///
  /// In en, this message translates to:
  /// **'[SafeBeee] I am safe and secure.'**
  String get smsTemplateRecommended;

  /// No description provided for @smsTemplateDetailed.
  ///
  /// In en, this message translates to:
  /// **'[SafeBeee] I am safe and in a secure location. Please don\'t worry about me.'**
  String get smsTemplateDetailed;

  /// No description provided for @smsTemplateCheckIn.
  ///
  /// In en, this message translates to:
  /// **'[SafeBeee] Regular check-in. I am doing well.'**
  String get smsTemplateCheckIn;

  /// No description provided for @smsTemplateRecommendedWithLocation.
  ///
  /// In en, this message translates to:
  /// **'[SafeBeee] I am safe and secure. Current location: {location}'**
  String smsTemplateRecommendedWithLocation(String location);

  /// No description provided for @smsAppOpened.
  ///
  /// In en, this message translates to:
  /// **'SMS app opened'**
  String get smsAppOpened;

  /// No description provided for @smsSent.
  ///
  /// In en, this message translates to:
  /// **'SMS Sent'**
  String get smsSent;

  /// No description provided for @smsFailedToOpen.
  ///
  /// In en, this message translates to:
  /// **'Failed to open SMS app'**
  String get smsFailedToOpen;

  /// No description provided for @recipientCount.
  ///
  /// In en, this message translates to:
  /// **'{count} recipients'**
  String recipientCount(int count);

  /// No description provided for @openHazardMap.
  ///
  /// In en, this message translates to:
  /// **'Open Hazard Map'**
  String get openHazardMap;

  /// No description provided for @externalSiteWarning.
  ///
  /// In en, this message translates to:
  /// **'External site will open'**
  String get externalSiteWarning;

  /// No description provided for @hazardMapUrl.
  ///
  /// In en, this message translates to:
  /// **'Hazard Map URL'**
  String get hazardMapUrl;

  /// No description provided for @openInBrowser.
  ///
  /// In en, this message translates to:
  /// **'Open in Browser'**
  String get openInBrowser;

  /// No description provided for @close.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get close;

  /// No description provided for @sendComplete.
  ///
  /// In en, this message translates to:
  /// **'Send Complete'**
  String get sendComplete;

  /// No description provided for @smsPrepared.
  ///
  /// In en, this message translates to:
  /// **'SMS Prepared'**
  String get smsPrepared;

  /// No description provided for @copiedToClipboard.
  ///
  /// In en, this message translates to:
  /// **'Copied to clipboard'**
  String get copiedToClipboard;

  /// No description provided for @recipient.
  ///
  /// In en, this message translates to:
  /// **'Recipient'**
  String get recipient;

  /// No description provided for @message.
  ///
  /// In en, this message translates to:
  /// **'Message'**
  String get message;

  /// No description provided for @smsInstructions.
  ///
  /// In en, this message translates to:
  /// **'Instructions:'**
  String get smsInstructions;

  /// No description provided for @openSmsApp.
  ///
  /// In en, this message translates to:
  /// **'Open SMS App'**
  String get openSmsApp;

  /// No description provided for @enterPhoneNumber.
  ///
  /// In en, this message translates to:
  /// **'2. Enter or select phone number'**
  String get enterPhoneNumber;

  /// No description provided for @pasteAndSend.
  ///
  /// In en, this message translates to:
  /// **'3. Paste message and send'**
  String get pasteAndSend;

  /// No description provided for @smsAppOpenedButton.
  ///
  /// In en, this message translates to:
  /// **'SMS app opened'**
  String get smsAppOpenedButton;

  /// No description provided for @smsAppOpenedMessage.
  ///
  /// In en, this message translates to:
  /// **'SMS app opened for {name} ({phone})'**
  String smsAppOpenedMessage(String name, String phone);

  /// No description provided for @smsSendInstructions.
  ///
  /// In en, this message translates to:
  /// **'Please press \'Send Complete\' button after sending the SMS'**
  String get smsSendInstructions;

  /// No description provided for @smsManualInstructions.
  ///
  /// In en, this message translates to:
  /// **'Manual SMS sending instructions:'**
  String get smsManualInstructions;

  /// No description provided for @smsCopyButtonInstruction.
  ///
  /// In en, this message translates to:
  /// **'1. Press \'Copy\' button to copy contact and message'**
  String get smsCopyButtonInstruction;

  /// No description provided for @smsOpenAppInstruction.
  ///
  /// In en, this message translates to:
  /// **'2. Manually open SMS app'**
  String get smsOpenAppInstruction;

  /// No description provided for @smsPasteAndSendInstruction.
  ///
  /// In en, this message translates to:
  /// **'3. Paste phone number and message, then send'**
  String get smsPasteAndSendInstruction;

  /// No description provided for @smsFailedToOpenApp.
  ///
  /// In en, this message translates to:
  /// **'Failed to open SMS app automatically'**
  String get smsFailedToOpenApp;

  /// No description provided for @errorDetails.
  ///
  /// In en, this message translates to:
  /// **'Error details:'**
  String get errorDetails;

  /// No description provided for @sendTo.
  ///
  /// In en, this message translates to:
  /// **'Send to:'**
  String get sendTo;

  /// No description provided for @messageContent.
  ///
  /// In en, this message translates to:
  /// **'Message content:'**
  String get messageContent;

  /// No description provided for @allContactsSmsSuccess.
  ///
  /// In en, this message translates to:
  /// **'SMS sent to {count} contacts'**
  String allContactsSmsSuccess(int count);

  /// No description provided for @allContactsSmsFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to send SMS to all contacts'**
  String get allContactsSmsFailed;

  /// No description provided for @smsFailedWithError.
  ///
  /// In en, this message translates to:
  /// **'Failed to send SMS: {error}'**
  String smsFailedWithError(String error);

  /// No description provided for @editMessage.
  ///
  /// In en, this message translates to:
  /// **'Edit Message'**
  String get editMessage;

  /// No description provided for @copy.
  ///
  /// In en, this message translates to:
  /// **'Copy'**
  String get copy;

  /// No description provided for @failedToOpenHazardMap.
  ///
  /// In en, this message translates to:
  /// **'Failed to open hazard map: {error}'**
  String failedToOpenHazardMap(String error);

  /// No description provided for @hazardMapOpened.
  ///
  /// In en, this message translates to:
  /// **'Hazard map opened successfully'**
  String get hazardMapOpened;

  /// No description provided for @hazardMapPortalSite.
  ///
  /// In en, this message translates to:
  /// **'Hazard Map Portal Site'**
  String get hazardMapPortalSite;

  /// No description provided for @checkDisasterRiskInfo.
  ///
  /// In en, this message translates to:
  /// **'Check nationwide disaster risk information'**
  String get checkDisasterRiskInfo;

  /// No description provided for @checkVariousSettings.
  ///
  /// In en, this message translates to:
  /// **'Various settings'**
  String get checkVariousSettings;

  /// No description provided for @add.
  ///
  /// In en, this message translates to:
  /// **'Add'**
  String get add;

  /// No description provided for @edit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get edit;

  /// No description provided for @loadingSettings.
  ///
  /// In en, this message translates to:
  /// **'Loading settings...'**
  String get loadingSettings;

  /// No description provided for @heartbeatInterval.
  ///
  /// In en, this message translates to:
  /// **'Heartbeat Interval'**
  String get heartbeatInterval;

  /// No description provided for @normalTime.
  ///
  /// In en, this message translates to:
  /// **'Normal time'**
  String get normalTime;

  /// No description provided for @disasterTime.
  ///
  /// In en, this message translates to:
  /// **'Disaster time'**
  String get disasterTime;

  /// No description provided for @minutes.
  ///
  /// In en, this message translates to:
  /// **'minutes'**
  String get minutes;

  /// No description provided for @seconds.
  ///
  /// In en, this message translates to:
  /// **'seconds'**
  String get seconds;

  /// No description provided for @debugFeatures.
  ///
  /// In en, this message translates to:
  /// **'Debug Features'**
  String get debugFeatures;

  /// No description provided for @currentSystemStatus.
  ///
  /// In en, this message translates to:
  /// **'Current System Status'**
  String get currentSystemStatus;

  /// No description provided for @operationMode.
  ///
  /// In en, this message translates to:
  /// **'Operation Mode'**
  String get operationMode;

  /// No description provided for @emergencyMode.
  ///
  /// In en, this message translates to:
  /// **'Emergency Mode'**
  String get emergencyMode;

  /// No description provided for @normalMode.
  ///
  /// In en, this message translates to:
  /// **'Normal Mode'**
  String get normalMode;

  /// No description provided for @connectionStatus.
  ///
  /// In en, this message translates to:
  /// **'Connection Status'**
  String get connectionStatus;

  /// No description provided for @locationStatus.
  ///
  /// In en, this message translates to:
  /// **'Location Status'**
  String get locationStatus;

  /// No description provided for @enabled.
  ///
  /// In en, this message translates to:
  /// **'Enabled'**
  String get enabled;

  /// No description provided for @disabled.
  ///
  /// In en, this message translates to:
  /// **'Disabled'**
  String get disabled;

  /// No description provided for @battery.
  ///
  /// In en, this message translates to:
  /// **'Battery'**
  String get battery;

  /// No description provided for @charging.
  ///
  /// In en, this message translates to:
  /// **'Charging'**
  String get charging;

  /// No description provided for @emergencyModeActive.
  ///
  /// In en, this message translates to:
  /// **'Emergency mode active: Heartbeat interval shortened'**
  String get emergencyModeActive;

  /// No description provided for @testAlert.
  ///
  /// In en, this message translates to:
  /// **'Test Alert'**
  String get testAlert;

  /// No description provided for @switchToNormalMode.
  ///
  /// In en, this message translates to:
  /// **'Switch to Normal Mode'**
  String get switchToNormalMode;

  /// No description provided for @switchToEmergencyMode.
  ///
  /// In en, this message translates to:
  /// **'Switch to Emergency Mode'**
  String get switchToEmergencyMode;

  /// No description provided for @emergencyModeToggle.
  ///
  /// In en, this message translates to:
  /// **'Emergency Mode Toggle'**
  String get emergencyModeToggle;

  /// No description provided for @showSuggestionHistory.
  ///
  /// In en, this message translates to:
  /// **'Show Suggestion History'**
  String get showSuggestionHistory;

  /// No description provided for @completeReset.
  ///
  /// In en, this message translates to:
  /// **'Complete Reset (Debug Only)'**
  String get completeReset;

  /// No description provided for @completeResetWarning.
  ///
  /// In en, this message translates to:
  /// **'All data, settings, history, contacts, and Firebase will be completely deleted'**
  String get completeResetWarning;

  /// No description provided for @showIntervalSettings.
  ///
  /// In en, this message translates to:
  /// **'Show Interval Settings'**
  String get showIntervalSettings;

  /// No description provided for @debugNote.
  ///
  /// In en, this message translates to:
  /// **'Debug features are only visible when TEST_MODE=true in .env'**
  String get debugNote;

  /// No description provided for @suggestionHistory.
  ///
  /// In en, this message translates to:
  /// **'Suggestion History (Debug)'**
  String get suggestionHistory;

  /// No description provided for @currentTypeBasedHistory.
  ///
  /// In en, this message translates to:
  /// **'Current Type-based History'**
  String get currentTypeBasedHistory;

  /// No description provided for @typeBasedHistoryEmpty.
  ///
  /// In en, this message translates to:
  /// **'No type-based history'**
  String get typeBasedHistoryEmpty;

  /// No description provided for @legacyIdBasedHistory.
  ///
  /// In en, this message translates to:
  /// **'Legacy ID-based History'**
  String get legacyIdBasedHistory;

  /// No description provided for @idBasedHistoryEmpty.
  ///
  /// In en, this message translates to:
  /// **'No ID-based history'**
  String get idBasedHistoryEmpty;

  /// No description provided for @andMore.
  ///
  /// In en, this message translates to:
  /// **'and {count} more'**
  String andMore(int count);

  /// No description provided for @debugInfo.
  ///
  /// In en, this message translates to:
  /// **'Debug Information'**
  String get debugInfo;

  /// No description provided for @historyNote.
  ///
  /// In en, this message translates to:
  /// **'・ Type-based is the current history management method\n・ ID-based is the old method (deprecated)\n・ Clear history if suggestions are not displayed'**
  String get historyNote;

  /// No description provided for @selectTestAlertType.
  ///
  /// In en, this message translates to:
  /// **'Select Test Alert Type'**
  String get selectTestAlertType;

  /// No description provided for @earthquake.
  ///
  /// In en, this message translates to:
  /// **'Earthquake'**
  String get earthquake;

  /// No description provided for @earthquakeTest.
  ///
  /// In en, this message translates to:
  /// **'Emergency Earthquake Alert Test'**
  String get earthquakeTest;

  /// No description provided for @tsunami.
  ///
  /// In en, this message translates to:
  /// **'Tsunami'**
  String get tsunami;

  /// No description provided for @tsunamiTest.
  ///
  /// In en, this message translates to:
  /// **'Tsunami Warning Test'**
  String get tsunamiTest;

  /// No description provided for @heavyRain.
  ///
  /// In en, this message translates to:
  /// **'Heavy Rain'**
  String get heavyRain;

  /// No description provided for @heavyRainTest.
  ///
  /// In en, this message translates to:
  /// **'Heavy Rain Special Warning Test'**
  String get heavyRainTest;

  /// No description provided for @fire.
  ///
  /// In en, this message translates to:
  /// **'Fire'**
  String get fire;

  /// No description provided for @fireTest.
  ///
  /// In en, this message translates to:
  /// **'Fire Warning Test'**
  String get fireTest;

  /// No description provided for @forceResetEmergency.
  ///
  /// In en, this message translates to:
  /// **'Force Emergency Mode Reset'**
  String get forceResetEmergency;

  /// No description provided for @forceResetEmergencyDesc.
  ///
  /// In en, this message translates to:
  /// **'Forcefully reset emergency mode (debug only)'**
  String get forceResetEmergencyDesc;

  /// No description provided for @forceResetConfirm.
  ///
  /// In en, this message translates to:
  /// **'Force Emergency Mode Reset'**
  String get forceResetConfirm;

  /// No description provided for @forceResetMessage.
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to forcefully reset emergency mode?\n\n※This operation is valid for 5 minutes and should only be used for debugging purposes.'**
  String get forceResetMessage;

  /// No description provided for @performReset.
  ///
  /// In en, this message translates to:
  /// **'Reset'**
  String get performReset;

  /// No description provided for @resettingEmergencyMode.
  ///
  /// In en, this message translates to:
  /// **'Resetting emergency mode...'**
  String get resettingEmergencyMode;

  /// No description provided for @emergencyModeResetSuccess.
  ///
  /// In en, this message translates to:
  /// **'Emergency mode reset successful'**
  String get emergencyModeResetSuccess;

  /// No description provided for @emergencyModeResetFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to reset emergency mode'**
  String get emergencyModeResetFailed;

  /// No description provided for @triggeringAlert.
  ///
  /// In en, this message translates to:
  /// **'Triggering alert...'**
  String get triggeringAlert;

  /// No description provided for @alertTriggerSuccess.
  ///
  /// In en, this message translates to:
  /// **'Alert triggered successfully!\n{message}'**
  String alertTriggerSuccess(String message);

  /// No description provided for @alertTriggerFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to trigger alert: {error}'**
  String alertTriggerFailed(String error);

  /// No description provided for @debugAlertTest.
  ///
  /// In en, this message translates to:
  /// **'Debug Alert (Test)'**
  String get debugAlertTest;

  /// No description provided for @debugAlertDescription.
  ///
  /// In en, this message translates to:
  /// **'This is a test alert triggered from debug features.'**
  String get debugAlertDescription;

  /// No description provided for @emergencyModeToggleConfirm.
  ///
  /// In en, this message translates to:
  /// **'Emergency Mode Toggle'**
  String get emergencyModeToggleConfirm;

  /// No description provided for @emergencyModeToggleMessage.
  ///
  /// In en, this message translates to:
  /// **'Execute debug emergency mode toggle?\n\n・normal → emergency: Enable emergency mode\n・emergency → normal: Disable emergency mode\n\n※Heartbeat interval will be automatically adjusted'**
  String get emergencyModeToggleMessage;

  /// No description provided for @performToggle.
  ///
  /// In en, this message translates to:
  /// **'Toggle'**
  String get performToggle;

  /// No description provided for @switchedToEmergencyMode.
  ///
  /// In en, this message translates to:
  /// **'Switched to emergency mode'**
  String get switchedToEmergencyMode;

  /// No description provided for @switchedToNormalMode.
  ///
  /// In en, this message translates to:
  /// **'Switched to normal mode'**
  String get switchedToNormalMode;

  /// No description provided for @emergencyModeToggleFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to toggle emergency mode: {error}'**
  String emergencyModeToggleFailed(String error);

  /// No description provided for @completeAppReset.
  ///
  /// In en, this message translates to:
  /// **'Complete App Reset'**
  String get completeAppReset;

  /// No description provided for @completeResetConfirm.
  ///
  /// In en, this message translates to:
  /// **'Complete Debug Reset'**
  String get completeResetConfirm;

  /// No description provided for @completeResetConfirmMessage.
  ///
  /// In en, this message translates to:
  /// **'Execute complete debug reset?'**
  String get completeResetConfirmMessage;

  /// No description provided for @deleteTargets.
  ///
  /// In en, this message translates to:
  /// **'Delete Targets (Irreversible):'**
  String get deleteTargets;

  /// No description provided for @deleteTargetsList.
  ///
  /// In en, this message translates to:
  /// **'🗑️ All local settings and history\n🗑️ Firebase data (complete deletion)\n🗑️ Suggestion history (frontend and backend)\n🗑️ Disaster mode and emergency mode status\n🗑️ Emergency contacts\n🗑️ Chat history and timeline\n\n⚠️ Debug-only feature'**
  String get deleteTargetsList;

  /// No description provided for @performCompleteReset.
  ///
  /// In en, this message translates to:
  /// **'Complete Reset'**
  String get performCompleteReset;

  /// No description provided for @executingCompleteReset.
  ///
  /// In en, this message translates to:
  /// **'Executing complete reset...'**
  String get executingCompleteReset;

  /// No description provided for @initializingData.
  ///
  /// In en, this message translates to:
  /// **'Initializing Firebase, local data, timeline history, and disaster mode'**
  String get initializingData;

  /// No description provided for @completeResetSuccess.
  ///
  /// In en, this message translates to:
  /// **'Complete reset successful. Moving to onboarding...'**
  String get completeResetSuccess;

  /// No description provided for @completeResetFailed.
  ///
  /// In en, this message translates to:
  /// **'Complete reset failed: {error}'**
  String completeResetFailed(String error);

  /// No description provided for @systemIntervalSettings.
  ///
  /// In en, this message translates to:
  /// **'System Interval Settings'**
  String get systemIntervalSettings;

  /// No description provided for @currentMode.
  ///
  /// In en, this message translates to:
  /// **'Current Mode'**
  String get currentMode;

  /// No description provided for @disasterMonitoringInterval.
  ///
  /// In en, this message translates to:
  /// **'Disaster Monitoring Interval'**
  String get disasterMonitoringInterval;

  /// No description provided for @disasterMonitoringExplanation.
  ///
  /// In en, this message translates to:
  /// **'Disaster Monitoring Interval?'**
  String get disasterMonitoringExplanation;

  /// No description provided for @disasterMonitoringDescription.
  ///
  /// In en, this message translates to:
  /// **'Frequency of retrieving disaster information from JMA (Japan Meteorological Agency) and other sources.\nAutomatically checks for earthquakes, tsunamis, heavy rain, and other disasters,\nand notifies users in affected areas when new disasters are detected.'**
  String get disasterMonitoringDescription;

  /// No description provided for @testModeSettings.
  ///
  /// In en, this message translates to:
  /// **'Test Mode Settings'**
  String get testModeSettings;

  /// No description provided for @normalModeSettings.
  ///
  /// In en, this message translates to:
  /// **'Normal Mode Settings'**
  String get normalModeSettings;

  /// No description provided for @emergencyModeSettings.
  ///
  /// In en, this message translates to:
  /// **'Emergency Mode Settings'**
  String get emergencyModeSettings;

  /// No description provided for @intervalDescriptions.
  ///
  /// In en, this message translates to:
  /// **'Interval Descriptions:'**
  String get intervalDescriptions;

  /// No description provided for @disasterMonitoring.
  ///
  /// In en, this message translates to:
  /// **'Disaster Monitoring'**
  String get disasterMonitoring;

  /// No description provided for @newsCollection.
  ///
  /// In en, this message translates to:
  /// **'News Collection'**
  String get newsCollection;

  /// No description provided for @periodicDataCollection.
  ///
  /// In en, this message translates to:
  /// **'Periodic Data Collection'**
  String get periodicDataCollection;

  /// No description provided for @heartbeat.
  ///
  /// In en, this message translates to:
  /// **'Heartbeat'**
  String get heartbeat;

  /// No description provided for @criticalAlert.
  ///
  /// In en, this message translates to:
  /// **'Critical Alert'**
  String get criticalAlert;

  /// No description provided for @suggestionCooldown.
  ///
  /// In en, this message translates to:
  /// **'Suggestion Cooldown'**
  String get suggestionCooldown;

  /// No description provided for @heartbeatIntervalSettings.
  ///
  /// In en, this message translates to:
  /// **'Heartbeat Interval Settings'**
  String get heartbeatIntervalSettings;

  /// No description provided for @heartbeatIntervalDescription.
  ///
  /// In en, this message translates to:
  /// **'Set the interval for sending device status to the server.\nShorter intervals consume more battery.'**
  String get heartbeatIntervalDescription;

  /// No description provided for @normalTimeLabel.
  ///
  /// In en, this message translates to:
  /// **'Normal time:'**
  String get normalTimeLabel;

  /// No description provided for @disasterTimeLabel.
  ///
  /// In en, this message translates to:
  /// **'Disaster time:'**
  String get disasterTimeLabel;

  /// No description provided for @heartbeatNote.
  ///
  /// In en, this message translates to:
  /// **'※ Automatically switches to shorter interval during disasters'**
  String get heartbeatNote;

  /// No description provided for @heartbeatIntervalUpdated.
  ///
  /// In en, this message translates to:
  /// **'Heartbeat interval updated'**
  String get heartbeatIntervalUpdated;

  /// No description provided for @settingsSaveFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to save settings: {error}'**
  String settingsSaveFailed(String error);

  /// No description provided for @fetchingIntervalConfig.
  ///
  /// In en, this message translates to:
  /// **'Fetching interval configuration...'**
  String get fetchingIntervalConfig;

  /// No description provided for @intervalConfigFetchFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to fetch interval configuration: {error}'**
  String intervalConfigFetchFailed(String error);

  /// No description provided for @emergencyEarthquakeAlertTest.
  ///
  /// In en, this message translates to:
  /// **'🚨 Emergency Earthquake Alert (Test)'**
  String get emergencyEarthquakeAlertTest;

  /// No description provided for @tsunamiWarningTest.
  ///
  /// In en, this message translates to:
  /// **'🌊 Tsunami Warning (Test)'**
  String get tsunamiWarningTest;

  /// No description provided for @heavyRainSpecialWarningTest.
  ///
  /// In en, this message translates to:
  /// **'🌧️ Heavy Rain Special Warning (Test)'**
  String get heavyRainSpecialWarningTest;

  /// No description provided for @fireWarningTest.
  ///
  /// In en, this message translates to:
  /// **'🔥 Fire Warning (Test)'**
  String get fireWarningTest;

  /// No description provided for @emergencyAlertTest.
  ///
  /// In en, this message translates to:
  /// **'🚨 Emergency Alert (Test)'**
  String get emergencyAlertTest;

  /// No description provided for @earthquakeAlertTestDescription.
  ///
  /// In en, this message translates to:
  /// **'This is a test emergency earthquake alert. Be prepared for strong shaking. (Test)'**
  String get earthquakeAlertTestDescription;

  /// No description provided for @tsunamiAlertTestDescription.
  ///
  /// In en, this message translates to:
  /// **'This is a test tsunami warning. Evacuate to higher ground. (Test)'**
  String get tsunamiAlertTestDescription;

  /// No description provided for @heavyRainAlertTestDescription.
  ///
  /// In en, this message translates to:
  /// **'This is a test heavy rain special warning. Take life-saving actions. (Test)'**
  String get heavyRainAlertTestDescription;

  /// No description provided for @fireAlertTestDescription.
  ///
  /// In en, this message translates to:
  /// **'This is a test fire warning. Evacuate immediately. (Test)'**
  String get fireAlertTestDescription;

  /// No description provided for @debugAlertTestDescription.
  ///
  /// In en, this message translates to:
  /// **'This is a test alert triggered from debug features.'**
  String get debugAlertTestDescription;

  /// No description provided for @checkNationwideDisasterInfo.
  ///
  /// In en, this message translates to:
  /// **'Check nationwide disaster information'**
  String get checkNationwideDisasterInfo;

  /// No description provided for @viewHazardMap.
  ///
  /// In en, this message translates to:
  /// **'View hazard map'**
  String get viewHazardMap;

  /// No description provided for @sendEmergencySMS.
  ///
  /// In en, this message translates to:
  /// **'Send emergency SMS'**
  String get sendEmergencySMS;

  /// No description provided for @checkSafetyInfo.
  ///
  /// In en, this message translates to:
  /// **'Check safety information'**
  String get checkSafetyInfo;

  /// No description provided for @evacuationGuidance.
  ///
  /// In en, this message translates to:
  /// **'Evacuation guidance'**
  String get evacuationGuidance;

  /// No description provided for @emergencyContactInfo.
  ///
  /// In en, this message translates to:
  /// **'Emergency contact information'**
  String get emergencyContactInfo;

  /// No description provided for @smsSelectedSentSuccess.
  ///
  /// In en, this message translates to:
  /// **'SMS sent successfully to {successCount} out of {totalCount} selected contacts'**
  String smsSelectedSentSuccess(int successCount, int totalCount);

  /// No description provided for @selectedContactsSmsFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to send SMS to selected contacts'**
  String get selectedContactsSmsFailed;

  /// No description provided for @sendSafetyConfirmationMessage.
  ///
  /// In en, this message translates to:
  /// **'Send safety confirmation message'**
  String get sendSafetyConfirmationMessage;

  /// No description provided for @sendMessage.
  ///
  /// In en, this message translates to:
  /// **'Message to send'**
  String get sendMessage;

  /// No description provided for @individualSmsMode.
  ///
  /// In en, this message translates to:
  /// **'Individual SMS Mode'**
  String get individualSmsMode;

  /// No description provided for @enterMessage.
  ///
  /// In en, this message translates to:
  /// **'Enter message'**
  String get enterMessage;

  /// No description provided for @selectRecipients.
  ///
  /// In en, this message translates to:
  /// **'Select Recipients'**
  String get selectRecipients;

  /// No description provided for @selectAll.
  ///
  /// In en, this message translates to:
  /// **'Select All'**
  String get selectAll;

  /// No description provided for @deselectAll.
  ///
  /// In en, this message translates to:
  /// **'Deselect All'**
  String get deselectAll;

  /// No description provided for @sendToSelected.
  ///
  /// In en, this message translates to:
  /// **'Send to {count} selected'**
  String sendToSelected(int count);

  /// No description provided for @emergencyDefaultOverview.
  ///
  /// In en, this message translates to:
  /// **'An emergency situation has occurred. Stay calm, assess the situation, and take appropriate safety actions. Pay attention to the latest information and prepare for evacuation if necessary.'**
  String get emergencyDefaultOverview;

  /// No description provided for @earthquakeOverview.
  ///
  /// In en, this message translates to:
  /// **'Strong earthquake activity detected. Take cover under a sturdy desk or table. Stay away from falling objects and prepare for potential aftershocks.'**
  String get earthquakeOverview;

  /// No description provided for @tsunamiOverview.
  ///
  /// In en, this message translates to:
  /// **'Tsunami warning has been issued. Evacuate to higher ground immediately. Do not approach the coast and follow evacuation instructions.'**
  String get tsunamiOverview;

  /// No description provided for @fireOverview.
  ///
  /// In en, this message translates to:
  /// **'Fire alert has been detected. Evacuate the building immediately using stairs, not elevators. Stay low to avoid smoke inhalation.'**
  String get fireOverview;

  /// No description provided for @typhoonOverview.
  ///
  /// In en, this message translates to:
  /// **'Typhoon is approaching. Stay indoors, secure windows, and avoid flooded areas. Prepare for power outages and water service disruptions.'**
  String get typhoonOverview;

  /// No description provided for @floodOverview.
  ///
  /// In en, this message translates to:
  /// **'Flood warning is in effect. Move to higher ground immediately. Avoid walking or driving through flood water. Monitor emergency broadcasts.'**
  String get floodOverview;

  /// No description provided for @volcanicOverview.
  ///
  /// In en, this message translates to:
  /// **'Volcanic activity has increased. Beware of volcanic ash and projectiles. Stay away from designated evacuation zones and cover nose and mouth.'**
  String get volcanicOverview;

  /// No description provided for @landslideOverview.
  ///
  /// In en, this message translates to:
  /// **'Landslide risk has increased. Stay away from mountainous areas and steep slopes. Watch for warning signs like springs and ground rumbling.'**
  String get landslideOverview;

  /// No description provided for @tornadoOverview.
  ///
  /// In en, this message translates to:
  /// **'Tornado activity detected. Take shelter in a sturdy building away from windows. If outdoors, lie flat in a low area and protect yourself from flying debris.'**
  String get tornadoOverview;

  /// No description provided for @earthquakeActions.
  ///
  /// In en, this message translates to:
  /// **'1. Ensure personal safety first\n2. Take cover under desk or table\n3. Extinguish fires and secure escape routes\n4. Gather accurate information'**
  String get earthquakeActions;

  /// No description provided for @tsunamiActions.
  ///
  /// In en, this message translates to:
  /// **'1. Evacuate to higher ground immediately\n2. Avoid vehicle evacuation\n3. Stay away from coast until warning is lifted\n4. Follow evacuation orders'**
  String get tsunamiActions;

  /// No description provided for @fireActions.
  ///
  /// In en, this message translates to:
  /// **'1. Stay low to avoid smoke\n2. Secure exit and evacuate quickly\n3. Do not use elevators\n4. Call emergency services'**
  String get fireActions;

  /// No description provided for @typhoonActions.
  ///
  /// In en, this message translates to:
  /// **'1. Stay indoors\n2. Reinforce windows\n3. Early evacuation from flood-prone areas\n4. Prepare for power and water outages'**
  String get typhoonActions;

  /// No description provided for @defaultEmergencyActions.
  ///
  /// In en, this message translates to:
  /// **'1. Stay calm and assess situation\n2. Move to safe location\n3. Gather accurate information\n4. Prepare for evacuation'**
  String get defaultEmergencyActions;

  /// No description provided for @emergencyActions.
  ///
  /// In en, this message translates to:
  /// **'Emergency Actions'**
  String get emergencyActions;

  /// No description provided for @emergencyContactSetupSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Register people to contact during disasters'**
  String get emergencyContactSetupSubtitle;

  /// No description provided for @nicknameSetupSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Set your display name'**
  String get nicknameSetupSubtitle;

  /// No description provided for @nearbyShelters.
  ///
  /// In en, this message translates to:
  /// **'Nearby Shelters'**
  String get nearbyShelters;

  /// No description provided for @shelterCount.
  ///
  /// In en, this message translates to:
  /// **'{count} shelters'**
  String shelterCount(int count);

  /// No description provided for @safetySmsDefaultMessage.
  ///
  /// In en, this message translates to:
  /// **'I am safe. Location: {location}'**
  String safetySmsDefaultMessage(String location);

  /// No description provided for @emergencyContactRequiredTitle.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contacts Required'**
  String get emergencyContactRequiredTitle;

  /// No description provided for @emergencyContactRequiredMessage.
  ///
  /// In en, this message translates to:
  /// **'Please register emergency contacts first.'**
  String get emergencyContactRequiredMessage;

  /// No description provided for @selectContacts.
  ///
  /// In en, this message translates to:
  /// **'Select Contacts'**
  String get selectContacts;

  /// No description provided for @send.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get send;

  /// No description provided for @smsSentSuccessfully.
  ///
  /// In en, this message translates to:
  /// **'SMS sent successfully'**
  String get smsSentSuccessfully;

  /// No description provided for @smsFailedToSend.
  ///
  /// In en, this message translates to:
  /// **'Failed to send SMS'**
  String get smsFailedToSend;

  /// No description provided for @sendSafetySms.
  ///
  /// In en, this message translates to:
  /// **'Send Safety SMS'**
  String get sendSafetySms;

  /// No description provided for @step1SelectRecipients.
  ///
  /// In en, this message translates to:
  /// **'Step 1: Select Recipients'**
  String get step1SelectRecipients;

  /// No description provided for @step2EditMessage.
  ///
  /// In en, this message translates to:
  /// **'Step 2: Edit Message'**
  String get step2EditMessage;

  /// No description provided for @selectTemplate.
  ///
  /// In en, this message translates to:
  /// **'Select Template'**
  String get selectTemplate;

  /// No description provided for @editSmsMessage.
  ///
  /// In en, this message translates to:
  /// **'Edit your SMS message...'**
  String get editSmsMessage;

  /// No description provided for @aiResponseDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'※ AI responses may contain uncertainties. Please verify with official sources during emergencies.'**
  String get aiResponseDisclaimer;

  /// No description provided for @currentLocation.
  ///
  /// In en, this message translates to:
  /// **'Current Location'**
  String get currentLocation;

  /// No description provided for @selectAtLeastOneContact.
  ///
  /// In en, this message translates to:
  /// **'Please select at least one contact'**
  String get selectAtLeastOneContact;

  /// No description provided for @messageCannotBeEmpty.
  ///
  /// In en, this message translates to:
  /// **'Message cannot be empty'**
  String get messageCannotBeEmpty;

  /// No description provided for @includeLocation.
  ///
  /// In en, this message translates to:
  /// **'Include Location'**
  String get includeLocation;

  /// No description provided for @contactsSelected.
  ///
  /// In en, this message translates to:
  /// **'contacts selected'**
  String get contactsSelected;

  /// No description provided for @recommended.
  ///
  /// In en, this message translates to:
  /// **'Recommended'**
  String get recommended;

  /// No description provided for @detailed.
  ///
  /// In en, this message translates to:
  /// **'Detailed'**
  String get detailed;

  /// No description provided for @checkIn.
  ///
  /// In en, this message translates to:
  /// **'Check In'**
  String get checkIn;

  /// No description provided for @smsPartialSuccess.
  ///
  /// In en, this message translates to:
  /// **'Partially Sent'**
  String get smsPartialSuccess;

  /// No description provided for @smsFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to Send'**
  String get smsFailed;

  /// No description provided for @successCount.
  ///
  /// In en, this message translates to:
  /// **'{count} messages sent successfully'**
  String successCount(int count);

  /// No description provided for @failedCount.
  ///
  /// In en, this message translates to:
  /// **'{count} messages failed to send'**
  String failedCount(int count);

  /// No description provided for @suggestionDeleted.
  ///
  /// In en, this message translates to:
  /// **'Suggestion deleted'**
  String get suggestionDeleted;

  /// No description provided for @hazardMapUrlNotFound.
  ///
  /// In en, this message translates to:
  /// **'Hazard map URL not found'**
  String get hazardMapUrlNotFound;

  /// No description provided for @to.
  ///
  /// In en, this message translates to:
  /// **'To'**
  String get to;

  /// No description provided for @safetyConfirmationSms.
  ///
  /// In en, this message translates to:
  /// **'Safety Confirmation SMS'**
  String get safetyConfirmationSms;

  /// No description provided for @confirmSendSms.
  ///
  /// In en, this message translates to:
  /// **'Confirm SMS Send'**
  String get confirmSendSms;

  /// No description provided for @smsContentPreview.
  ///
  /// In en, this message translates to:
  /// **'SMS Content Preview'**
  String get smsContentPreview;

  /// No description provided for @greeting.
  ///
  /// In en, this message translates to:
  /// **'Hello'**
  String get greeting;

  /// No description provided for @sendToAll.
  ///
  /// In en, this message translates to:
  /// **'Send to All'**
  String get sendToAll;

  /// No description provided for @loadingEmergencyInfo.
  ///
  /// In en, this message translates to:
  /// **'Loading emergency information...'**
  String get loadingEmergencyInfo;

  /// No description provided for @iAmSafe.
  ///
  /// In en, this message translates to:
  /// **'I am safe.'**
  String get iAmSafe;

  /// No description provided for @voiceInputError.
  ///
  /// In en, this message translates to:
  /// **'Voice input error: {error}'**
  String voiceInputError(String error);

  /// No description provided for @recordingSeconds.
  ///
  /// In en, this message translates to:
  /// **'Recording... {seconds} seconds'**
  String recordingSeconds(int seconds);

  /// No description provided for @sending.
  ///
  /// In en, this message translates to:
  /// **'Sending...'**
  String get sending;

  /// No description provided for @wifi.
  ///
  /// In en, this message translates to:
  /// **'Wi-Fi'**
  String get wifi;

  /// No description provided for @locationPermissionEnabled.
  ///
  /// In en, this message translates to:
  /// **'📍 Location permission has been enabled'**
  String get locationPermissionEnabled;

  /// No description provided for @locationPermissionRequired.
  ///
  /// In en, this message translates to:
  /// **'❌ Please enable location permission\nSettings > Apps > SafeBeee > Location'**
  String get locationPermissionRequired;

  /// No description provided for @locationDiagnosticPerformed.
  ///
  /// In en, this message translates to:
  /// **'🔍 Location permission diagnostic performed\nPlease check the logs'**
  String get locationDiagnosticPerformed;

  /// No description provided for @gpsServiceDisabled.
  ///
  /// In en, this message translates to:
  /// **'📱 GPS service is disabled\nPlease enable location services in settings'**
  String get gpsServiceDisabled;

  /// No description provided for @itemCount.
  ///
  /// In en, this message translates to:
  /// **'{count} items'**
  String itemCount(int count);

  /// No description provided for @location.
  ///
  /// In en, this message translates to:
  /// **'Location'**
  String get location;

  /// No description provided for @latitude.
  ///
  /// In en, this message translates to:
  /// **'Lat'**
  String get latitude;

  /// No description provided for @longitude.
  ///
  /// In en, this message translates to:
  /// **'Lng'**
  String get longitude;

  /// No description provided for @accuracy.
  ///
  /// In en, this message translates to:
  /// **'Accuracy'**
  String get accuracy;

  /// No description provided for @alertLevel.
  ///
  /// In en, this message translates to:
  /// **'Alert Level: {level}'**
  String alertLevel(String level);

  /// No description provided for @announcementTime.
  ///
  /// In en, this message translates to:
  /// **'Announcement Time: {time}'**
  String announcementTime(String time);

  /// No description provided for @shelter.
  ///
  /// In en, this message translates to:
  /// **'Shelter: {name}'**
  String shelter(String name);

  /// No description provided for @errorSavingContact.
  ///
  /// In en, this message translates to:
  /// **'Error occurred while saving: {error}'**
  String errorSavingContact(String error);
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>[
    'de',
    'en',
    'es',
    'fr',
    'it',
    'ja',
    'ko',
    'pt',
    'ru',
    'zh',
  ].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when language+country codes are specified.
  switch (locale.languageCode) {
    case 'zh':
      {
        switch (locale.countryCode) {
          case 'CN':
            return AppLocalizationsZhCn();
          case 'TW':
            return AppLocalizationsZhTw();
        }
        break;
      }
  }

  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'de':
      return AppLocalizationsDe();
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
    case 'fr':
      return AppLocalizationsFr();
    case 'it':
      return AppLocalizationsIt();
    case 'ja':
      return AppLocalizationsJa();
    case 'ko':
      return AppLocalizationsKo();
    case 'pt':
      return AppLocalizationsPt();
    case 'ru':
      return AppLocalizationsRu();
    case 'zh':
      return AppLocalizationsZh();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
