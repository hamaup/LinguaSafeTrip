// 国番号の定義
class CountryCode {
  final String code;
  final String name;
  final String dialCode;
  final String flag;

  const CountryCode({
    required this.code,
    required this.name,
    required this.dialCode,
    required this.flag,
  });
}

// よく使われる国の国番号リスト
const List<CountryCode> countryCodes = [
  CountryCode(code: 'JP', name: '日本', dialCode: '+81', flag: '🇯🇵'),
  CountryCode(code: 'US', name: 'アメリカ', dialCode: '+1', flag: '🇺🇸'),
  CountryCode(code: 'CN', name: '中国', dialCode: '+86', flag: '🇨🇳'),
  CountryCode(code: 'KR', name: '韓国', dialCode: '+82', flag: '🇰🇷'),
  CountryCode(code: 'TW', name: '台湾', dialCode: '+886', flag: '🇹🇼'),
  CountryCode(code: 'GB', name: 'イギリス', dialCode: '+44', flag: '🇬🇧'),
  CountryCode(code: 'FR', name: 'フランス', dialCode: '+33', flag: '🇫🇷'),
  CountryCode(code: 'DE', name: 'ドイツ', dialCode: '+49', flag: '🇩🇪'),
  CountryCode(code: 'IT', name: 'イタリア', dialCode: '+39', flag: '🇮🇹'),
  CountryCode(code: 'ES', name: 'スペイン', dialCode: '+34', flag: '🇪🇸'),
  CountryCode(code: 'PT', name: 'ポルトガル', dialCode: '+351', flag: '🇵🇹'),
  CountryCode(code: 'RU', name: 'ロシア', dialCode: '+7', flag: '🇷🇺'),
  CountryCode(code: 'AU', name: 'オーストラリア', dialCode: '+61', flag: '🇦🇺'),
  CountryCode(code: 'NZ', name: 'ニュージーランド', dialCode: '+64', flag: '🇳🇿'),
  CountryCode(code: 'TH', name: 'タイ', dialCode: '+66', flag: '🇹🇭'),
  CountryCode(code: 'SG', name: 'シンガポール', dialCode: '+65', flag: '🇸🇬'),
  CountryCode(code: 'MY', name: 'マレーシア', dialCode: '+60', flag: '🇲🇾'),
  CountryCode(code: 'ID', name: 'インドネシア', dialCode: '+62', flag: '🇮🇩'),
  CountryCode(code: 'PH', name: 'フィリピン', dialCode: '+63', flag: '🇵🇭'),
  CountryCode(code: 'VN', name: 'ベトナム', dialCode: '+84', flag: '🇻🇳'),
  CountryCode(code: 'IN', name: 'インド', dialCode: '+91', flag: '🇮🇳'),
  CountryCode(code: 'BR', name: 'ブラジル', dialCode: '+55', flag: '🇧🇷'),
  CountryCode(code: 'MX', name: 'メキシコ', dialCode: '+52', flag: '🇲🇽'),
  CountryCode(code: 'CA', name: 'カナダ', dialCode: '+1', flag: '🇨🇦'),
];

// デフォルト国番号（日本）
const CountryCode defaultCountryCode = CountryCode(
  code: 'JP',
  name: '日本',
  dialCode: '+81',
  flag: '🇯🇵',
);