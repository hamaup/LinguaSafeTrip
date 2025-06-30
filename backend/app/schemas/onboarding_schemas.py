# app/schemas/onboarding_schemas.py
from pydantic import BaseModel, Field
from typing import Literal # 特定の文字列リテラルのみを許可する場合

class OnboardingInitResponse(BaseModel):
    """
    オンボーディング開始API (/api/onboarding/init) のレスポンススキーマ。
    AIが生成した最初の質問メッセージ（言語を尋ねる内容）を含む。
    """
    ai_message: str = Field(
        ..., # '...' は必須フィールドであることを示す
        description="AIが生成した、ユーザーに言語を尋ねるウェルカムメッセージ。",
        examples=["Welcome to SafetyBeacon! To assist you better, please tell me your preferred language. We primarily support English and Chinese."]
    )

class UserLanguageSelectionRequest(BaseModel): # P1-F07-05 で新規または修正
    """
    ユーザーが選択した言語コードをバックエンドに送信する際のリクエストスキーマ。
    """
    selected_language_code: Literal["en", "zh", "ja"] = Field( # サポート言語をリテラルで指定
        ...,
        description="ユーザーが選択した言語コード（'en', 'zh', 'ja' のいずれか）。",
        examples=["en"]
    )
    # user_id: Optional[str] = Field(None, description="ユーザーID (認証連携後に利用)")

class SetNamePromptResponse(BaseModel): # P1-F07-05 で新規または修正 (needs_retry削除)
    """
    言語設定API (/api/onboarding/setLanguage) の成功時レスポンススキーマ。
    AIが生成した名前を尋ねるメッセージと、確認済み言語コードを含む。
    """
    confirmed_language_code: str = Field(
        ...,
        description="バックエンドで確認・保存された言語コード ('en', 'zh', 'ja')。",
        examples=["en"]
    )
    ai_message: str = Field(
        ...,
        description="AIからの次のメッセージ（名前を尋ねる質問）。"
    )

class SetUserNameRequest(BaseModel): # ★ クラス名変更
    """
    ユーザーが入力した名前と現在の言語コードをバックエンドに送信する際のリクエストスキーマ。
    """
    display_name: str = Field( # ★ フィールド名変更
        ...,
        min_length=1,
        max_length=50,
        description="ユーザーが入力した表示名。",
        examples=["Safety Taro"]
    )
    language_code: Literal["en", "zh", "ja"] = Field(
        ...,
        description="現在のユーザーの言語設定コード。",
        examples=["ja"]
    )

class SetNameConfirmationResponse(BaseModel): # ★ クラス名変更
    """
    名前設定API (/api/onboarding/setName) の成功時レスポンススキーマ。
    AIが生成した、名前設定完了と連絡先登録を促すメッセージを含む。
    """
    ai_message: str = Field(
        ...,
        description="AIからの次のメッセージ（名前設定完了の確認と連絡先登録への誘導）。"
    )
    # is_success: bool = Field(True, description="処理が成功したかどうかを示すフラグ。") # 不要なためコメントアウト
