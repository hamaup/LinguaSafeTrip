from typing import Any, Dict, Union
from pydantic import BaseModel

def get_state_value(state: Union[dict, BaseModel], key: str, default: Any = None) -> Any:
    """状態オブジェクト/辞書から安全に値を取得"""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)

def ensure_dict_output(data: Any) -> Dict[str, Any]:
    """出力を必ず辞書形式に変換"""
    if isinstance(data, BaseModel):
        return data.dict()
    elif isinstance(data, dict):
        return data
    elif hasattr(data, '__iter__') and not isinstance(data, str):
        return {'results': list(data)}
    return {'result': data}
