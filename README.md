# LinguaSafeTrip - 言葉の壁をなくし、災害から旅を守る !

LinguaSafeTrip は、訪日外国人観光客のための、多言語対応の災害特化型エージェントです。平常時は防災情報の提供、緊急時は迅速な安全確認と避難支援を行います。

## 概要

### 主な機能

- **プロアクティブ提案**: 位置情報や気象データに基づく防災情報の自動提案
- **多言語対応**: 日本語、英語、中国語、韓国語などに対応
- **緊急モード**: 災害発生時の自動検知と緊急支援機能
- **安全確認**: SMS による家族・友人への安全状況通知
- **避難所案内**: 最寄りの避難所情報案内

### 技術スタック

- **フロントエンド**: Flutter (iOS/Android 対応)
- **バックエンド**: FastAPI + LangGraph
- **AI/ML**: Claude 3.5 Sonnet, Gemini Pro
- **インフラ**: Google Cloud Platform (Cloud Run, Firestore)

## 使い方

Flutter web版は通知や位置情報を有効にすると避難所検索や災害アラート機能が使用できます。

### 平常時の利用

1. **プロアクティブ提案の利用**

   - ホーム画面の各種提案をタップ
   - 現在地や時間帯に応じた防災情報が自動表示されます

2. **質問機能**
   - チャット入力欄に質問を入力
   - 例：「最寄りの避難所はどこ？」「地震の時の対処法は？」
   - AI アシスタントが適切な情報を提供します

### 緊急時の利用

1. **緊急アラートの発動方法**

   - 設定画面を開く
   - 「テストアラート発報」をタップ
   - 緊急モードが起動

### 初期設定

1. **アプリ起動時**

   - 位置情報の使用許可
   - 通知の受信許可
   - 緊急連絡先の登録（スキップ可能）

2. **プロフィール設定**
   - 言語設定
   - ニックネーム
   - 緊急連絡先の追加・編集

### 初期化リセット

- 設定画面の完全削除を押下

## セキュリティとプライバシー

- ユーザーの個人情報は端末内に保存され、サーバーには送信されません
- 位置情報は災害情報の取得にのみ使用されます
- 全ての通信は HTTPS で暗号化されています

## 提出物について

### テストモードでの動作

※ 提出するプロダクトは、現実の災害情報がないため、実際の Web 検索ではなく事前に Web 検索から取得したモックデータを災害時用に加工して使用しています。

### 動作確認環境

- **Android**
- **Web**

### 主要機能の確認方法

1. **多言語対応**: オンボーディング画面から言語を変更して確認
2. **プロアクティブ提案**: タイムライン上に自動表示される提案をタップ
3. **緊急モード**: 設定 → 災害アラートから起動
4. **避難所検索**: チャットで「最寄りの避難所」と入力

## コンタクト

- [GitHub Issues](https://github.com/hamaup/linguasafetrip/issues)

## 外部 API クレジット・ライセンス

本アプリケーションは以下の外部 API を実際に使用しています：

### 公的機関 API

#### 気象庁（JMA）

- **利用データ**: 防災情報 XML フィード（地震・津波・気象警報）
- **出典**: 気象庁防災情報 XML フィード（https://xml.kishou.go.jp/）
- **ライセンス**: 気象庁ホームページ利用規約
- **注記**: 本アプリで表示する情報は、気象庁が発表したデータを再編集して提供しています

#### 国土地理院（GSI）

- **利用データ**:
  - 地理院タイル（標高タイル）- 標高情報の取得
  - ハザードマップポータル - 災害リスク情報
  - 指定緊急避難場所データ - 避難所位置情報
- **出典**: 国土地理院（https://maps.gsi.go.jp/ ほか）
- **ライセンス**: 国土地理院コンテンツ利用規約
- **加工**: LinguaSafeTrip アプリにて位置情報と統合して表示

- **OpenStreetMap Nominatim**: 逆ジオコーディング（座標 → 住所変換）
  - ライセンス: ODbL (Open Database License)
  - 利用規約: https://operations.osmfoundation.org/policies/nominatim/
  - User-Agent: LinguaSafeTrip/1.0

### データ利用に関する注意事項

- 公的機関のデータは公共データ利用規約に基づき、出典を明示して利用しています
- 災害情報の正確性・最新性については各提供元の免責事項が適用されます
- 本アプリは気象業務法における「予報業務」は行っておらず、公的機関の発表情報を転載・加工して提供しています
