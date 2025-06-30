# backend/app/utils/token_utils.py
import logging
import os
from typing import List, Union, Sequence, Optional
from dotenv import load_dotenv

# --- Google Vertex AI ---
# google-cloud-aiplatform は countTokens API 用だが、
# langchain_google_vertexai が内部で使っている vertexai SDK を使う方が整合性が取れる可能性
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, Content
    from vertexai.language_models import TextGenerationModel # 古いモデル用だがトークン計算に使えるか？ (GenerativeModel推奨)
    from google.api_core.exceptions import GoogleAPIError
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    GenerativeModel = None # 型ヒント用
    Part = None
    Content = None
    GoogleAPIError = None

# --- LangChain Messages ---
# BaseMessage の型ヒントのためにインポート
try:
    from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
except ImportError:
    BaseMessage = None # 型ヒント用

load_dotenv()
logger = logging.getLogger(__name__)

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1") # agent と合わせる

# Vertex AI クライアント初期化 (モジュールロード時に一度だけ行う)
if VERTEXAI_AVAILABLE and GCP_PROJECT_ID:
    try:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        logger.info(f"Vertex AI initialized successfully for token counting in project {GCP_PROJECT_ID} location {GCP_LOCATION}.")
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI SDK: {e}", exc_info=True)
        VERTEXAI_AVAILABLE = False # 初期化失敗したら利用不可にする
elif not GCP_PROJECT_ID:
     logger.warning("GCP_PROJECT_ID not set, Vertex AI token counting disabled.")
     VERTEXAI_AVAILABLE = False
else:
     logger.warning("Vertex AI SDK not available, token counting disabled.")


def _convert_lc_message_to_vertex_content(message: BaseMessage) -> Optional[Content]:
    """LangChain の BaseMessage を Vertex AI の Content オブジェクトに変換する試み"""
    if not VERTEXAI_AVAILABLE or not Content:
        return None

    role = ""
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "model"
    # SystemMessage は直接 Content に role がないため、user として扱うか、
    # または呼び出し側で特別扱いする必要があるかもしれない。一旦 user 扱い。
    elif isinstance(message, SystemMessage):
        role = "user" # または None や "system" など、モデルのAPI仕様に依存
    else:
        logger.warning(f"Unsupported LangChain message type for Vertex AI conversion: {type(message)}")
        return None # 不明なタイプは無視

    # TODO: ToolCall や ToolResponse も考慮する必要があるか確認
    if isinstance(message.content, str):
        return Content(role=role, parts=[Part.from_text(message.content)])
    elif isinstance(message.content, list): # Parts のリストの場合 (画像など)
         # ここでは単純なテキストのみを想定
         text_parts = [part.get("text", "") for part in message.content if isinstance(part, dict) and "text" in part]
         if text_parts:
             return Content(role=role, parts=[Part.from_text("\n".join(text_parts))])
         else:
             logger.warning(f"Message content list did not contain text parts: {message.content}")
             return None
    else:
        logger.warning(f"Unsupported message content type: {type(message.content)}")
        return None


def count_tokens_gemini(model_name: str, prompt_parts: Union[str, List[Union[str, BaseMessage, Content, Part]]]) -> Optional[int]:
    """
    指定されたモデルとプロンプト部品リストからトークン数を計算する (Vertex AI GenerativeModel API使用)。
    prompt_parts は文字列、LangChainメッセージ、Vertex AI Content/Part オブジェクトのリストなど。
    """
    if not VERTEXAI_AVAILABLE or not GenerativeModel:
        logger.warning("Vertex AI SDK not available or not initialized. Cannot count tokens.")
        return None

    try:
        model = GenerativeModel(model_name)
        contents_for_api: List[Union[str, Content, Part]] = []

        if isinstance(prompt_parts, str):
            contents_for_api = [prompt_parts] # 単一文字列
        elif isinstance(prompt_parts, list):
            for part in prompt_parts:
                if isinstance(part, str):
                    # 文字列はそのまま追加 (APIが処理できるか要確認、Part推奨)
                    # contents_for_api.append(part)
                    # → Part に変換する方が安全
                    if Part: contents_for_api.append(Part.from_text(part))
                elif BaseMessage and isinstance(part, BaseMessage):
                    # LangChain メッセージを Vertex AI Content に変換
                    vertex_content = _convert_lc_message_to_vertex_content(part)
                    if vertex_content:
                        contents_for_api.append(vertex_content)
                elif Content and isinstance(part, Content):
                    contents_for_api.append(part)
                elif Part and isinstance(part, Part):
                    contents_for_api.append(part)
                else:
                    logger.warning(f"Unsupported type in prompt_parts list: {type(part)}. Skipping.")
        else:
            logger.error(f"Unsupported prompt_parts type: {type(prompt_parts)}")
            return None

        if not contents_for_api:
            logger.warning("No valid content found to count tokens.")
            return 0

        # count_tokens API を呼び出す
        response = model.count_tokens(contents_for_api)
        total_tokens = response.total_tokens
        return total_tokens

    except GoogleAPIError as e:
        logger.error(f"Vertex AI API error counting tokens for model '{model_name}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error counting tokens for model '{model_name}': {e}", exc_info=True)
        return None

# --- 近似的なトークン計算 (API呼び出しが難しい場合や trim_messages 用) ---
# tiktoken は OpenAI モデル用だが、Gemini との類似性があれば目安に使える可能性
try:
    import tiktoken
    # tiktoken が利用可能なモデルを確認 (例: "cl100k_base" は GPT-3.5/4 で使われる)
    # Gemini 用の正確なエンコーディングは公開されていない可能性が高い
    # ここでは汎用的なものを試す
    try:
        # cl100k_base がなければ他のエンコーディングを試す
        enc = tiktoken.get_encoding("cl100k_base")
    except:
        enc = tiktoken.get_encoding("gpt2") # より基本的なもの
    TIKTOKEN_AVAILABLE = True
    logger.info(f"Tiktoken initialized with encoding: {enc.name}")
except ImportError:
    TIKTOKEN_AVAILABLE = False
    enc = None
    logger.warning("Tiktoken library not found. Approximate token counting will rely on character count.")

def count_tokens_approximated(data: Union[str, BaseMessage, Sequence[BaseMessage]]) -> int:
    """
    与えられたデータ (文字列、単一BaseMessage、またはBaseMessageのシーケンス) の
    トークン数を近似的に計算する。
    Tiktoken が利用可能ならそれを使用し、なければ文字数ベースの推定を行う。
    """
    if not data:
        return 0

    total_tokens = 0

    if isinstance(data, str):
        # 単一文字列の場合
        if TIKTOKEN_AVAILABLE and enc:
            try:
                total_tokens = len(enc.encode(data, allowed_special="all"))
                return total_tokens
            except Exception as e:
                logger.warning(f"Tiktoken encoding failed for string, falling back to character count: {e}")
        # Tiktoken がない、またはエラーの場合: 文字数ベースの推定
        estimated_tokens = int(len(data) * 1.5)
        return estimated_tokens

    elif BaseMessage and isinstance(data, BaseMessage):
        # 単一 BaseMessage の場合
        content_str = str(data.content) if data.content else ""
        if TIKTOKEN_AVAILABLE and enc:
            try:
                total_tokens = len(enc.encode(content_str, allowed_special="all"))
                return total_tokens
            except Exception as e:
                logger.warning(f"Tiktoken encoding failed for BaseMessage, falling back to character count: {e}")
        # Tiktoken がない、またはエラーの場合: 文字数ベースの推定
        estimated_tokens = int(len(content_str) * 1.5)
        return estimated_tokens

    elif isinstance(data, Sequence):
        # BaseMessage のシーケンスの場合
        if TIKTOKEN_AVAILABLE and enc:
            try:
                for message in data:
                    if BaseMessage and isinstance(message, BaseMessage):
                        content_str = str(message.content) if message.content else ""
                        total_tokens += len(enc.encode(content_str, allowed_special="all"))
                    elif isinstance(message, str): # シーケンス内に文字列が混在している場合も考慮
                        total_tokens += len(enc.encode(message, allowed_special="all"))
                    else:
                        logger.warning(f"Unsupported type in message sequence for tiktoken: {type(message)}")
                return total_tokens
            except Exception as e:
                logger.warning(f"Tiktoken encoding failed for sequence, falling back to character count: {e}")
                total_tokens = 0 # フォールバックのためにリセット

        # Tiktoken がない、またはエラーの場合: 文字数ベースの推定
        char_count = 0
        for message_item in data:
            if BaseMessage and isinstance(message_item, BaseMessage):
                content_str = str(message_item.content) if message_item.content else ""
                char_count += len(content_str)
            elif isinstance(message_item, str): # シーケンス内に文字列が混在している場合
                char_count += len(message_item)
            else:
                logger.warning(f"Unsupported type in message sequence for char count: {type(message_item)}")

        estimated_tokens = int(char_count * 1.5)
        return estimated_tokens

    else:
        logger.warning(f"Unsupported data type for count_tokens_approximated: {type(data)}")
        return 0

# --- 利用例 ---
if __name__ == '__main__':
    # このファイルが直接実行された場合のテストコード
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    if VERTEXAI_AVAILABLE:
        test_model = "gemini-1.5-flash-preview-0514" # テスト用モデル名
        # 1. Simple string
        text1 = "Hello, world!"
        tokens1 = count_tokens_gemini(test_model, text1)
        # 2. List of strings
        text_list = ["What is the weather today?", "In Tokyo."]
        tokens2 = count_tokens_gemini(test_model, text_list)
        # 3. LangChain Messages (if available)
        if BaseMessage:
            lc_messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Translate 'hello' to Japanese."),
            ]
            tokens3 = count_tokens_gemini(test_model, lc_messages)
    else:
        pass
    if BaseMessage:
        lc_messages_long = [
            SystemMessage(content="これはシステムメッセージです。"),
            HumanMessage(content="こんにちは、これはユーザーからのメッセージです。少し長めに書いてみます。"),
            AIMessage(content="はい、承知いたしました。AIからの応答です。"),
        ] * 3 # 少し長くする
        approx_tokens = count_tokens_approximated(lc_messages_long)
    else:
        pass
