from datetime import datetime
from typing import Optional

def get_current_season(date: Optional[datetime] = None) -> str:
    """現在の季節を判定するユーティリティ関数

    Args:
        date: 判定基準日時 (Noneの場合は現在日時)

    Returns:
        str: "春"|"夏"|"秋"|"冬"
    """
    target_date = date or datetime.now()
    month = target_date.month

    if 3 <= month <= 5:
        return "春"
    elif 6 <= month <= 8:
        return "夏"
    elif 9 <= month <= 11:
        return "秋"
    else:
        return "冬"
