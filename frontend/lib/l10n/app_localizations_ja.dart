// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Japanese (`ja`).
class AppLocalizationsJa extends AppLocalizations {
  AppLocalizationsJa([String locale = 'ja']) : super(locale);

  @override
  String get appName => 'SafetyBee';

  @override
  String get permissionRequiredTitle => '権限のリクエスト';

  @override
  String get permissionRequestSubtitle => 'アプリの機能を有効にする';

  @override
  String get permissionLaterInfo => 'これらの権限は安全機能のために重要ですが、後で設定することもできます。';

  @override
  String get locationPermissionTitle => '位置情報の利用許可';

  @override
  String get locationPermissionRationale =>
      'このアプリはあなたの位置情報を使用して、近くの避難所や危険区域を通知します。';

  @override
  String get notificationPermissionTitle => '通知の許可';

  @override
  String get notificationPermissionRationale => '災害発生時や重要な更新情報を通知します。';

  @override
  String get next => '次へ';

  @override
  String get settings => '設定';

  @override
  String get language => '言語';

  @override
  String get selectLanguage => '言語を選択';

  @override
  String get cancel => 'キャンセル';

  @override
  String get ok => 'OK';

  @override
  String get settingsLoadFailed => '設定の読み込みに失敗しました。もう一度お試しください。';

  @override
  String get notificationSettings => '通知設定';

  @override
  String get notificationSettingsDescription => 'アプリの通知設定を変更';

  @override
  String get messageInputHint => 'メッセージを入力...';

  @override
  String get listening => '聞いています';

  @override
  String get voiceInput => '音声入力';

  @override
  String get voiceInputDescription => '音声でメッセージを入力';

  @override
  String get emergencyContacts => '緊急連絡先';

  @override
  String get addEmergencyContact => '緊急連絡先を追加';

  @override
  String get name => '名前';

  @override
  String get phoneNumber => '電話番号';

  @override
  String get save => '保存';

  @override
  String get registerEmergencyContact => '緊急連絡先を登録';

  @override
  String get emergencyContactAdded => '緊急連絡先を追加しました';

  @override
  String get pleaseEnterNameAndPhone => '名前と電話番号を入力してください';

  @override
  String errorOccurred(Object error) {
    return 'エラーが発生しました';
  }

  @override
  String get tapForDetails => 'タップして詳細';

  @override
  String get welcome => 'ようこそ';

  @override
  String get nickname => 'ニックネーム';

  @override
  String get enterNickname => 'ニックネームを入力してください';

  @override
  String get nicknameHint => 'ニックネームを入力...';

  @override
  String get emergencyContactSetup => '緊急連絡先の設定';

  @override
  String get addContactPrompt => '安全のため緊急連絡先を追加してください。';

  @override
  String get contactName => '連絡先名';

  @override
  String get contactNameHint => '連絡先名を入力...';

  @override
  String get contactPhone => '電話番号';

  @override
  String get contactPhoneHint => '電話番号を入力...';

  @override
  String get addContact => '連絡先を追加';

  @override
  String get removeContact => '削除';

  @override
  String get completeSetup => '設定完了';

  @override
  String get skip => 'スキップ';

  @override
  String get continueButton => '続行';

  @override
  String get finish => '完了';

  @override
  String get locationPermissionGranted => '位置情報は許可済み';

  @override
  String get allowLocationPermission => '位置情報を許可する';

  @override
  String get notificationPermissionGranted => '通知は許可済み';

  @override
  String get allowNotificationPermission => '通知を許可する';

  @override
  String get backToHome => 'ホームに戻る';

  @override
  String get notSet => '未設定';

  @override
  String get waitingForResponse => '回答待ち';

  @override
  String get tapToConfirm => 'タップで確認';

  @override
  String get askQuestion => '質問可能';

  @override
  String get emergencyActionRequired => '⚠️ 緊急行動が必要です';

  @override
  String get evacuationInfo => '🚨 避難情報';

  @override
  String get shelterInfo => '🏠 避難所情報';

  @override
  String get emergencyAlert => '🚨 緊急アラート';

  @override
  String get safetyConfirmation => '✅ 安否確認';

  @override
  String get hazardMapInfo => '🗺️ ハザードマップ情報';

  @override
  String get disasterLatestInfo => '📡 最新災害情報';

  @override
  String get disasterRelatedInfo => '🌀 災害関連情報';

  @override
  String get questionSent => '質問を送信しました';

  @override
  String get notificationConfirmed => '通知を確認しました';

  @override
  String get loading => '読み込み中...';

  @override
  String get timelineEmpty => 'タイムラインは空です';

  @override
  String get loadingTimeline => 'タイムラインを読み込み中...';

  @override
  String get gettingLatestInfo => 'SafeBeeeの最新情報を取得中';

  @override
  String get infoWillAppearSoon => '間もなく情報が表示されます。お待ちください。';

  @override
  String get userNickname => 'ユーザーニックネーム';

  @override
  String get emergencyContactsList => '緊急連絡先一覧';

  @override
  String get noEmergencyContacts => '緊急連絡先が登録されていません';

  @override
  String get contacts => '件';

  @override
  String get contact => '件';

  @override
  String get resetAppToInitialState => 'アプリを初期状態にリセット';

  @override
  String get confirmation => '確認';

  @override
  String get resetConfirmationMessage => 'すべての設定とデータを削除して初期状態に戻します。よろしいですか？';

  @override
  String get reset => 'リセット';

  @override
  String get editEmergencyContact => '緊急連絡先を編集';

  @override
  String get deleteEmergencyContactConfirmation => 'この緊急連絡先を削除しますか？';

  @override
  String get delete => '削除';

  @override
  String get gpsEnabled => 'GPS有効';

  @override
  String get gpsDisabled => 'GPS無効';

  @override
  String get gpsPermissionDenied => '許可なし';

  @override
  String get mobile => 'モバイル';

  @override
  String get ethernet => '有線';

  @override
  String get offline => 'オフライン';

  @override
  String get emergencySms => '緊急SMS';

  @override
  String sendToAllContacts(int count) {
    return '全員に送信 ($count名)';
  }

  @override
  String get selectIndividually => '個別に選択';

  @override
  String get smsSafetyMessage => '[SafeBeee] 私は無事で安全な場所にいます。';

  @override
  String get smsTemplateRecommended => '[SafeBeee] 私は無事です。';

  @override
  String get smsTemplateDetailed => '[SafeBeee] 私は無事で、安全な場所にいます。心配しないでください。';

  @override
  String get smsTemplateCheckIn => '[SafeBeee] 定期連絡です。私は元気です。';

  @override
  String smsTemplateRecommendedWithLocation(String location) {
    return '[SafeBeee] 私は無事です。現在地: $location';
  }

  @override
  String get smsAppOpened => 'SMSアプリを開きました';

  @override
  String get smsSent => 'SMS送信完了';

  @override
  String get smsFailedToOpen => 'SMSアプリを開けませんでした';

  @override
  String recipientCount(int count) {
    return '$count名';
  }

  @override
  String get openHazardMap => 'ハザードマップを開く';

  @override
  String get externalSiteWarning => '外部サイトが開きます';

  @override
  String get hazardMapUrl => 'ハザードマップURL';

  @override
  String get openInBrowser => 'ブラウザで開く';

  @override
  String get close => '閉じる';

  @override
  String get sendComplete => '送信完了';

  @override
  String get smsPrepared => 'SMS送信準備完了';

  @override
  String get copiedToClipboard => 'クリップボードにコピーしました';

  @override
  String get recipient => '宛先';

  @override
  String get message => 'メッセージ';

  @override
  String get smsInstructions => '手順:';

  @override
  String get openSmsApp => 'SMSアプリを開く';

  @override
  String get enterPhoneNumber => '2. 電話番号を入力または選択';

  @override
  String get pasteAndSend => '3. メッセージを貼り付けて送信';

  @override
  String get smsAppOpenedButton => 'SMSアプリを開きました';

  @override
  String smsAppOpenedMessage(String name, String phone) {
    return '$name ($phone) 宛にSMSアプリを開きました';
  }

  @override
  String get smsSendInstructions => 'SMSを送信したら「送信完了」ボタンを押してください';

  @override
  String get smsManualInstructions => '手動でSMSを送信する方法:';

  @override
  String get smsCopyButtonInstruction => '1. 「コピー」ボタンで連絡先とメッセージをコピー';

  @override
  String get smsOpenAppInstruction => '2. SMSアプリを手動で開く';

  @override
  String get smsPasteAndSendInstruction => '3. 電話番号とメッセージを貼り付けて送信';

  @override
  String get smsFailedToOpenApp => 'SMSアプリを自動で開くことができませんでした';

  @override
  String get errorDetails => 'エラー詳細:';

  @override
  String get sendTo => '送信先:';

  @override
  String get messageContent => 'メッセージ内容:';

  @override
  String allContactsSmsSuccess(int count) {
    return '$count名にSMSを送信しました';
  }

  @override
  String get allContactsSmsFailed => '全ての連絡先へのSMS送信に失敗しました';

  @override
  String smsFailedWithError(String error) {
    return 'SMSの送信に失敗しました: $error';
  }

  @override
  String get editMessage => 'メッセージを編集';

  @override
  String get copy => 'コピー';

  @override
  String failedToOpenHazardMap(String error) {
    return 'ハザードマップを開けませんでした: $error';
  }

  @override
  String get hazardMapOpened => 'ハザードマップを開きました';

  @override
  String get hazardMapPortalSite => 'ハザードマップポータルサイト';

  @override
  String get checkDisasterRiskInfo => '全国の災害リスク情報を確認';

  @override
  String get checkVariousSettings => '各種設定など';

  @override
  String get add => '追加';

  @override
  String get edit => '編集';

  @override
  String get loadingSettings => '設定を読み込み中...';

  @override
  String get heartbeatInterval => 'ハートビート間隔';

  @override
  String get normalTime => '平常時';

  @override
  String get disasterTime => '災害時';

  @override
  String get minutes => '分';

  @override
  String get seconds => '秒';

  @override
  String get debugFeatures => 'デバッグ機能';

  @override
  String get currentSystemStatus => '現在のシステム状態';

  @override
  String get operationMode => '動作モード';

  @override
  String get emergencyMode => '緊急モード';

  @override
  String get normalMode => '平常モード';

  @override
  String get connectionStatus => '接続状態';

  @override
  String get locationStatus => '位置情報';

  @override
  String get enabled => '有効';

  @override
  String get disabled => '無効';

  @override
  String get battery => 'バッテリー';

  @override
  String get charging => '充電中';

  @override
  String get emergencyModeActive => '緊急モード中：ハートビート間隔が短縮されています';

  @override
  String get testAlert => 'テストアラート発報';

  @override
  String get switchToNormalMode => '平常モードに戻す';

  @override
  String get switchToEmergencyMode => '緊急モードに切り替え';

  @override
  String get emergencyModeToggle => '緊急モード切り替え';

  @override
  String get showSuggestionHistory => '提案履歴を表示';

  @override
  String get completeReset => '完全削除（デバッグ専用）';

  @override
  String get completeResetWarning => '全データ・設定・履歴・連絡先・Firebaseを完全削除';

  @override
  String get showIntervalSettings => '間隔設定を表示';

  @override
  String get debugNote => '※ デバッグ機能は.envでTEST_MODE=trueの場合のみ表示されます';

  @override
  String get suggestionHistory => '提案履歴（デバッグ用）';

  @override
  String get currentTypeBasedHistory => '現在のタイプベース履歴';

  @override
  String get typeBasedHistoryEmpty => 'タイプベースの履歴はありません';

  @override
  String get legacyIdBasedHistory => '旧いIDベース履歴';

  @override
  String get idBasedHistoryEmpty => 'IDベースの履歴はありません';

  @override
  String andMore(int count) {
    return 'あと$count件';
  }

  @override
  String get debugInfo => 'デバッグ情報';

  @override
  String get historyNote =>
      '・ タイプベースは現在使用中の履歴管理方式\n・ IDベースは旧い方式（非推奨）\n・ 提案が表示されない場合は履歴をクリア';

  @override
  String get selectTestAlertType => 'テストアラート種別を選択';

  @override
  String get earthquake => '地震';

  @override
  String get earthquakeTest => '緊急地震速報のテスト';

  @override
  String get tsunami => '津波';

  @override
  String get tsunamiTest => '津波警報のテスト';

  @override
  String get heavyRain => '豪雨';

  @override
  String get heavyRainTest => '大雨特別警報のテスト';

  @override
  String get fire => '火災';

  @override
  String get fireTest => '火災警報のテスト';

  @override
  String get forceResetEmergency => '緊急モード強制解除';

  @override
  String get forceResetEmergencyDesc => '緊急モードを強制的に解除（デバッグ用）';

  @override
  String get forceResetConfirm => '緊急モード強制解除';

  @override
  String get forceResetMessage =>
      '緊急モードを強制的に解除しますか？\n\n※この操作は5分間有効で、デバッグ目的でのみ使用してください。';

  @override
  String get performReset => '解除する';

  @override
  String get resettingEmergencyMode => '緊急モードを解除中...';

  @override
  String get emergencyModeResetSuccess => '緊急モード解除成功';

  @override
  String get emergencyModeResetFailed => '緊急モード解除に失敗しました';

  @override
  String get triggeringAlert => 'アラートを発報中...';

  @override
  String alertTriggerSuccess(String message) {
    return 'アラート発報成功！\n$message';
  }

  @override
  String alertTriggerFailed(String error) {
    return 'アラート発報失敗: $error';
  }

  @override
  String get debugAlertTest => '緊急アラート（テスト）';

  @override
  String get debugAlertDescription => 'これはデバッグ機能から発報されたテストアラートです。';

  @override
  String get emergencyModeToggleConfirm => '緊急モード切り替え';

  @override
  String get emergencyModeToggleMessage =>
      'デバッグ用の緊急モード切り替えを実行しますか？\n\n・normal → emergency: 緊急モード有効化\n・emergency → normal: 緊急モード解除\n\n※ハートビート間隔も自動調整されます';

  @override
  String get performToggle => '切り替え実行';

  @override
  String get switchedToEmergencyMode => '緊急モードに切り替えました';

  @override
  String get switchedToNormalMode => '平常モードに切り替えました';

  @override
  String emergencyModeToggleFailed(String error) {
    return '緊急モード切り替えに失敗しました: $error';
  }

  @override
  String get completeAppReset => '完全アプリリセット';

  @override
  String get completeResetConfirm => '完全デバッグリセット';

  @override
  String get completeResetConfirmMessage => '完全デバッグリセットを実行しますか？';

  @override
  String get deleteTargets => '削除対象（取り消し不可）:';

  @override
  String get deleteTargetsList =>
      '🗑️ 全ローカル設定・履歴\n🗑️ Firebaseデータ（完全削除）\n🗑️ 提案履歴（フロントエンド・バックエンド）\n🗑️ 災害モード・緊急モード状態\n🗑️ 緊急連絡先\n🗑️ チャット履歴・タイムライン\n\n⚠️ デバッグ専用機能です';

  @override
  String get performCompleteReset => '完全リセット';

  @override
  String get executingCompleteReset => '完全リセット実行中...';

  @override
  String get initializingData => 'Firebase・ローカルデータ・タイムライン履歴・災害モードを初期化しています';

  @override
  String get completeResetSuccess => '完全リセットが完了しました。オンボーディングに移動します...';

  @override
  String completeResetFailed(String error) {
    return '完全リセットに失敗しました: $error';
  }

  @override
  String get systemIntervalSettings => 'システム間隔設定';

  @override
  String get currentMode => '現在のモード';

  @override
  String get disasterMonitoringInterval => '災害監視間隔';

  @override
  String get disasterMonitoringExplanation => '災害監視間隔とは？';

  @override
  String get disasterMonitoringDescription =>
      'JMA（気象庁）等から災害情報を取得する頻度です。\n地震、津波、豪雨などの災害発生を自動的にチェックし、\n新しい災害が検出されると該当地域のユーザーに通知します。';

  @override
  String get testModeSettings => 'テストモード設定';

  @override
  String get normalModeSettings => '平常時の設定';

  @override
  String get emergencyModeSettings => '災害緊急時の設定';

  @override
  String get intervalDescriptions => '各間隔の説明:';

  @override
  String get disasterMonitoring => '災害監視';

  @override
  String get newsCollection => 'ニュース収集';

  @override
  String get periodicDataCollection => '定期データ収集';

  @override
  String get heartbeat => 'ハートビート';

  @override
  String get criticalAlert => '重大アラート時';

  @override
  String get suggestionCooldown => '提案クールダウン';

  @override
  String get heartbeatIntervalSettings => 'ハートビート間隔設定';

  @override
  String get heartbeatIntervalDescription =>
      'デバイスの状態をサーバーに送信する間隔を設定します。\n短い間隔ほどバッテリーを消費します。';

  @override
  String get normalTimeLabel => '平常時:';

  @override
  String get disasterTimeLabel => '災害時:';

  @override
  String get heartbeatNote => '※ 災害時は自動的に短い間隔に切り替わります';

  @override
  String get heartbeatIntervalUpdated => 'ハートビート間隔を更新しました';

  @override
  String settingsSaveFailed(String error) {
    return '設定の保存に失敗しました: $error';
  }

  @override
  String get fetchingIntervalConfig => '間隔設定を取得中...';

  @override
  String intervalConfigFetchFailed(String error) {
    return '間隔設定の取得に失敗しました: $error';
  }

  @override
  String get emergencyEarthquakeAlertTest => '🚨 緊急地震速報（テスト）';

  @override
  String get tsunamiWarningTest => '🌊 津波警報（テスト）';

  @override
  String get heavyRainSpecialWarningTest => '🌧️ 大雨特別警報（テスト）';

  @override
  String get fireWarningTest => '🔥 火災警報（テスト）';

  @override
  String get emergencyAlertTest => '🚨 緊急アラート（テスト）';

  @override
  String get earthquakeAlertTestDescription =>
      'これはテスト用の緊急地震速報です。強い揺れに警戒してください。（テスト）';

  @override
  String get tsunamiAlertTestDescription => 'これはテスト用の津波警報です。高台に避難してください。（テスト）';

  @override
  String get heavyRainAlertTestDescription =>
      'これはテスト用の大雨特別警報です。命を守る行動をとってください。（テスト）';

  @override
  String get fireAlertTestDescription => 'これはテスト用の火災警報です。速やかに避難してください。（テスト）';

  @override
  String get debugAlertTestDescription => 'これはデバッグ機能から発報されたテストアラートです。';

  @override
  String get checkNationwideDisasterInfo => '全国災害情報を確認';

  @override
  String get viewHazardMap => 'ハザードマップを確認';

  @override
  String get sendEmergencySMS => '緊急SMS送信';

  @override
  String get checkSafetyInfo => '安全情報を確認';

  @override
  String get evacuationGuidance => '避難案内';

  @override
  String get emergencyContactInfo => '緊急連絡先情報';

  @override
  String smsSelectedSentSuccess(int successCount, int totalCount) {
    return '選択した$totalCount名中$successCount名にSMSを送信しました';
  }

  @override
  String get selectedContactsSmsFailed => '選択した連絡先へのSMS送信に失敗しました';

  @override
  String get sendSafetyConfirmationMessage => '安全確認のメッセージを送信';

  @override
  String get sendMessage => '送信メッセージ';

  @override
  String get individualSmsMode => '個別SMS送信';

  @override
  String get enterMessage => 'メッセージを入力';

  @override
  String get selectRecipients => '送信先を選択';

  @override
  String get selectAll => 'すべて選択';

  @override
  String get deselectAll => '選択解除';

  @override
  String sendToSelected(int count) {
    return '選択した$count名に送信';
  }

  @override
  String get emergencyDefaultOverview =>
      '緊急事態が発生しています。落ち着いて状況を確認し、適切な安全行動を取ってください。最新の情報に注意し、必要に応じて避難の準備を行ってください。';

  @override
  String get earthquakeOverview =>
      '強い地震活動が検出されました。机の下に隠れるなど安全を確保してください。落下物から身を守り、余震に備えてください。';

  @override
  String get tsunamiOverview =>
      '津波警報が発表されました。直ちに高台に避難してください。海岸には近づかず、避難指示に従ってください。';

  @override
  String get fireOverview =>
      '火災が発生しています。エレベーターは使わず階段で速やかに避難してください。煙の吸入を避けるため低い姿勢を保ってください。';

  @override
  String get typhoonOverview =>
      '台風が接近しています。外出を控え、窓ガラスを補強してください。浸水危険地域では早期避難し、停電・断水に備えてください。';

  @override
  String get floodOverview =>
      '洪水警報が発表されています。直ちに高台に避難してください。冠水した道路の歩行・運転は避け、緊急放送を確認してください。';

  @override
  String get volcanicOverview =>
      '火山活動が活発化しています。火山灰や噴石に注意し、指定された避難区域から離れてください。マスクやタオルで口鼻を覆い、火山灰の吸入を防いでください。';

  @override
  String get landslideOverview =>
      '土砂災害の危険があります。山際や急傾斜地から離れ、安全な場所に避難してください。前兆現象（湧水・地鳴り等）に注意し、早めの避難を心がけてください。';

  @override
  String get tornadoOverview =>
      '竜巻が発生する可能性があります。頑丈な建物の中に避難し、窓から離れてください。屋外にいる場合は低い場所に身を伏せ、飛来物から身を守ってください。';

  @override
  String get earthquakeActions =>
      '1. 身の安全を最優先に確保\n2. 机の下に隠れる等の安全行動\n3. 火の始末と避難経路確保\n4. 正確な情報収集';

  @override
  String get tsunamiActions =>
      '1. 直ちに高台へ避難\n2. 車での避難は避ける\n3. 津波警報解除まで海岸に近づかない\n4. 避難指示に従う';

  @override
  String get fireActions =>
      '1. 煙を吸わないよう低い姿勢で\n2. 出口を確保して速やかに避難\n3. エレベーター使用禁止\n4. 119番通報';

  @override
  String get typhoonActions =>
      '1. 外出を控える\n2. 窓ガラスの補強\n3. 浸水危険地域は早期避難\n4. 停電・断水に備える';

  @override
  String get defaultEmergencyActions =>
      '1. 落ち着いて状況を確認\n2. 安全な場所に移動\n3. 正確な情報を収集\n4. 避難準備を整える';

  @override
  String get emergencyActions => '緊急時の対応';

  @override
  String get emergencyContactSetupSubtitle => '災害時に連絡する人を登録';

  @override
  String get nicknameSetupSubtitle => 'あなたの呼び名を設定';

  @override
  String get nearbyShelters => '近くの避難所';

  @override
  String shelterCount(int count) {
    return '$count件の避難所';
  }

  @override
  String safetySmsDefaultMessage(String location) {
    return '私は無事です。現在地: $location';
  }

  @override
  String get emergencyContactRequiredTitle => '緊急連絡先が必要です';

  @override
  String get emergencyContactRequiredMessage => '先に緊急連絡先を登録してください。';

  @override
  String get selectContacts => '連絡先を選択';

  @override
  String get send => '送信';

  @override
  String get smsSentSuccessfully => 'SMSを送信しました';

  @override
  String get smsFailedToSend => 'SMS送信に失敗しました';

  @override
  String get sendSafetySms => '安否確認SMSを送信';

  @override
  String get step1SelectRecipients => 'ステップ1: 送信先を選択';

  @override
  String get step2EditMessage => 'ステップ2: メッセージを編集';

  @override
  String get selectTemplate => 'テンプレートを選択';

  @override
  String get editSmsMessage => 'SMSメッセージを編集...';

  @override
  String get aiResponseDisclaimer =>
      '※ AI の回答には不確実性が含まれる場合があります。緊急時は公式情報源もご確認ください。';

  @override
  String get currentLocation => 'Current Location';

  @override
  String get selectAtLeastOneContact => '連絡先を1つ以上選択してください';

  @override
  String get messageCannotBeEmpty => 'メッセージは空にできません';

  @override
  String get includeLocation => '位置情報を含める';

  @override
  String get contactsSelected => '件の連絡先を選択';

  @override
  String get recommended => '推奨';

  @override
  String get detailed => '詳細';

  @override
  String get checkIn => '安否確認';

  @override
  String get smsPartialSuccess => '一部送信完了';

  @override
  String get smsFailed => '送信失敗';

  @override
  String successCount(int count) {
    return '$count件のメッセージを送信しました';
  }

  @override
  String failedCount(int count) {
    return '$count件のメッセージが送信に失敗しました';
  }

  @override
  String get suggestionDeleted => '提案を削除しました';

  @override
  String get hazardMapUrlNotFound => 'ハザードマップのURLが見つかりません';

  @override
  String get to => '宛先';

  @override
  String get safetyConfirmationSms => '安否確認SMS';

  @override
  String get confirmSendSms => 'SMS送信確認';

  @override
  String get smsContentPreview => 'SMS内容プレビュー';

  @override
  String get greeting => 'こんにちは';

  @override
  String get sendToAll => '全員に送信';

  @override
  String get loadingEmergencyInfo => '緊急情報を読み込んでいます...';

  @override
  String get iAmSafe => '私は無事です。';

  @override
  String voiceInputError(String error) {
    return '音声入力エラー: $error';
  }

  @override
  String recordingSeconds(int seconds) {
    return '録音中... $seconds秒';
  }

  @override
  String get sending => '送信中...';

  @override
  String get wifi => 'Wi-Fi';

  @override
  String get locationPermissionEnabled => '📍 位置情報の許可が有効になりました';

  @override
  String get locationPermissionRequired =>
      '❌ 位置情報の許可を有効にしてください\n設定 > アプリ > SafeBeee > 位置情報';

  @override
  String get locationDiagnosticPerformed => '🔍 位置情報許可の詳細診断を実行しました\nログをご確認ください';

  @override
  String get gpsServiceDisabled => '📱 GPS サービスが無効です\n設定で位置情報サービスを有効にしてください';

  @override
  String itemCount(int count) {
    return '$count 件';
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
    return '警戒レベル: $level';
  }

  @override
  String announcementTime(String time) {
    return '発表時刻: $time';
  }

  @override
  String shelter(String name) {
    return '避難所: $name';
  }

  @override
  String errorSavingContact(String error) {
    return '保存中にエラーが発生しました: $error';
  }
}
