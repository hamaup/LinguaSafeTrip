/// 電話番号バリデーションユーティリティ
class PhoneValidator {
  /// 電話番号の基本的なバリデーション
  static bool isValidPhoneNumber(String phoneNumber, String countryCode) {
    // 空文字チェック
    if (phoneNumber.isEmpty) return false;
    
    // 数字、ハイフン、スペース、括弧のみ許可
    final validChars = RegExp(r'^[\d\s\-\(\)]+$');
    if (!validChars.hasMatch(phoneNumber)) return false;
    
    // 数字のみを抽出
    final digitsOnly = phoneNumber.replaceAll(RegExp(r'[^\d]'), '');
    
    // 国別のバリデーション
    switch (countryCode) {
      case 'JP':
        // 日本の電話番号: 10桁または11桁（0から始まる）
        if (digitsOnly.startsWith('0')) {
          return digitsOnly.length == 10 || digitsOnly.length == 11;
        }
        // 国番号なしの場合（090, 080, 070, 03など）
        return digitsOnly.length >= 10 && digitsOnly.length <= 11;
        
      case 'US':
      case 'CA':
        // アメリカ・カナダ: 10桁
        return digitsOnly.length == 10;
        
      case 'CN':
        // 中国: 11桁（1から始まる）
        return digitsOnly.length == 11 && digitsOnly.startsWith('1');
        
      case 'KR':
        // 韓国: 10-11桁
        return digitsOnly.length >= 10 && digitsOnly.length <= 11;
        
      default:
        // その他の国: 7-15桁の範囲で許可
        return digitsOnly.length >= 7 && digitsOnly.length <= 15;
    }
  }
  
  /// 電話番号をフォーマット
  static String formatPhoneNumber(String phoneNumber, String countryCode) {
    final digitsOnly = phoneNumber.replaceAll(RegExp(r'[^\d]'), '');
    
    switch (countryCode) {
      case 'JP':
        // 日本の電話番号フォーマット
        if (digitsOnly.length == 10) {
          // 固定電話: 03-1234-5678
          return '${digitsOnly.substring(0, 2)}-${digitsOnly.substring(2, 6)}-${digitsOnly.substring(6)}';
        } else if (digitsOnly.length == 11) {
          // 携帯電話: 090-1234-5678
          return '${digitsOnly.substring(0, 3)}-${digitsOnly.substring(3, 7)}-${digitsOnly.substring(7)}';
        }
        break;
        
      case 'US':
      case 'CA':
        // アメリカ・カナダ: (123) 456-7890
        if (digitsOnly.length == 10) {
          return '(${digitsOnly.substring(0, 3)}) ${digitsOnly.substring(3, 6)}-${digitsOnly.substring(6)}';
        }
        break;
        
      default:
        // その他: そのまま返す
        return phoneNumber;
    }
    
    return phoneNumber;
  }
  
  /// 国際電話番号形式に変換（SMS送信用）
  static String toInternationalFormat(String phoneNumber, String dialCode) {
    var digitsOnly = phoneNumber.replaceAll(RegExp(r'[^\d]'), '');
    
    // 先頭の0を削除（日本の場合など）
    if (digitsOnly.startsWith('0')) {
      digitsOnly = digitsOnly.substring(1);
    }
    
    // すでに国番号が含まれている場合はそのまま返す
    if (phoneNumber.startsWith('+') || phoneNumber.startsWith(dialCode.substring(1))) {
      return phoneNumber;
    }
    
    return '$dialCode$digitsOnly';
  }
  
  /// エラーメッセージを取得
  static String? getErrorMessage(String phoneNumber, String countryCode) {
    if (phoneNumber.isEmpty) {
      return '電話番号を入力してください';
    }
    
    if (!isValidPhoneNumber(phoneNumber, countryCode)) {
      switch (countryCode) {
        case 'JP':
          return '有効な日本の電話番号を入力してください（10-11桁）';
        case 'US':
        case 'CA':
          return '有効な電話番号を入力してください（10桁）';
        case 'CN':
          return '有効な中国の電話番号を入力してください（11桁）';
        default:
          return '有効な電話番号を入力してください';
      }
    }
    
    return null;
  }
}