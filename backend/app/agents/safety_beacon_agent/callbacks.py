# backend/app/agents/safety_beacon_agent/callbacks.py
import logging
import uuid
from typing import Optional, Dict, Any, Union

from langchain_core.callbacks import AsyncCallbackHandler
# from langchain_core.agents import AgentAction, AgentFinish # 元のコードでインポートされていたが、このクラス内では未使用

logger = logging.getLogger(__name__)

class SmsToolResultCallbackHandler(AsyncCallbackHandler):
    """
    confirm_contact_and_prepare_sms ツールの成功結果を捕捉し、
    フロントエンドへのアクションデータを準備するためのコールバックハンドラ。
    """

    def __init__(self):
        super().__init__()  # 親クラスのコンストラクタを呼び出す
        self.sms_tool_result: Optional[Dict[str, Any]] = None
        # SmsToolResultCallbackHandler initialized

    async def on_tool_end(
        self,
        output: Union[str, Dict[str, Any]],  # ツールの出力
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tool: Optional[str] = None,  # LangChain 0.1.x 以前はこちらにツール名が入ることがあった
        name: Optional[str] = None,  # LangChain 0.2.x 以降はこちらにツール名が入ることが多い
        inputs: Optional[Dict[str, Any]] = None, # LangChain 0.2.x 以降はツールの入力も渡される
        **kwargs: Any,
    ) -> None:
        """ツール実行が終了した際に呼び出されるメソッド。"""

        # LangChainのバージョンによってツール名の取得方法が異なる場合があるため、両方を確認
        effective_tool_name = name or tool
        if not effective_tool_name and inputs and isinstance(inputs, dict):
             # 稀なケース: inputs辞書からツール名を取得しようと試みる (tool_inputなど特定のキーを想定)
             # これは LangChain の内部構造に依存するため、通常は name か tool で取得できるはず
             pass


        # Tool end callback triggered

        # ターゲットとするツールの名前 (tool_definitions.py で定義された名前と一致させる)
        target_tool_name = "confirm_contact_and_prepare_sms"

        if effective_tool_name == target_tool_name:
            if isinstance(output, dict):
                # SMS tool result captured
                if output.get("status") == "success":
                    # フロントエンドがSMSアプリを起動するために必要な情報を格納
                    self.sms_tool_result = {
                        "action_type": "launch_sms",  # フロントエンドが解釈するアクションタイプ
                        "phone_numbers": output.get("recipients", []), # 電話番号のリスト
                        "message_body": output.get("message_body", "") # SMS本文
                    }
                    # SMS data stored successfully
                else:
                    # ツール実行が成功しなかった場合（例: status が "error" や、期待するキーがない）
                    error_message = output.get("error_message", f"{target_tool_name} did not return a success status.")
                    self.sms_tool_result = {
                        "error": error_message,
                        "details": output # 元の出力もエラー詳細として含める
                    }
                    logger.warning(
                        f"'{target_tool_name}' tool did not succeed or output format unexpected. Stored error result. Details: {output}"
                    )
            else:
                # outputが期待する辞書型でない場合
                logger.warning(
                    f"Result from '{target_tool_name}' was not a dictionary as expected. Output: {output}"
                )