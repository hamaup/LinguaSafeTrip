import logging
from typing import List, Optional, Dict, Any
from geopy.distance import geodesic # 距離計算用

from app.schemas.unified_event import UnifiedEventData, LocationModel

logger = logging.getLogger(__name__)

# デフォルトのフィルタリング半径 (km)
DEFAULT_FILTER_RADIUS_KM = 10.0

# J-ALERT（Lアラート経由で配信される国民保護情報など）の対象地域判定はより複雑になる可能性がある
# ここでは、イベントデータに含まれる area_codes (JIS X 0402市区町村コード) や
# location (緯度経度) を利用することを想定する。

def get_event_location(event: UnifiedEventData) -> Optional[LocationModel]:
    """イベントデータから代表的な位置情報を取得する。"""
    if event.location:
        return event.location
    # 他のフィールドから位置情報を推定するロジック（例：area_codesから代表点など）はここでは省略
    return None

def filter_events_by_location(
    events: List[UnifiedEventData],
    current_location: LocationModel,
    radius_km: float = DEFAULT_FILTER_RADIUS_KM,
    target_area_codes: Optional[List[str]] = None # ユーザーの現在地の市区町村コードなど
) -> List[UnifiedEventData]:
    """
    イベントリストをユーザーの現在地に基づいてフィルタリングする。

    Args:
        events: 正規化されたイベントデータのリスト。
        current_location: ユーザーの現在地。
        radius_km: フィルタリング半径 (km)。イベントの位置情報がこの半径内なら関連ありとみなす。
        target_area_codes: ユーザーの現在地が含まれる市区町村コードのリスト。
                           イベントの area_codes と比較する。

    Returns:
        フィルタリングされたイベントデータのリスト。
    """
    if not events:
        return []
    if not current_location:
        logger.warning("Current location not provided for filtering. Returning all events.")
        return events # 現在地がなければフィルタリング不可（または全件返すか、空を返すか要件による）

    filtered_events: List[UnifiedEventData] = []
    user_loc_tuple = (current_location.latitude, current_location.longitude)

    for event in events:
        is_relevant = False

        # 1. イベントに直接的な位置情報 (緯度経度) がある場合、距離で判定
        event_loc = get_event_location(event)
        if event_loc:
            event_loc_tuple = (event_loc.latitude, event_loc.longitude)
            try:
                distance = geodesic(user_loc_tuple, event_loc_tuple).km
                if distance <= radius_km:
                    is_relevant = True
            except Exception as e:
                logger.error(f"Error calculating distance for event '{event.event_id}': {e}")

        # 2. イベントに地域コードがあり、ユーザーの地域コードと一致する場合
        # (距離判定で既に関連ありとされていなければ評価)
        if not is_relevant and target_area_codes and event.area_codes:
            if any(code in target_area_codes for code in event.area_codes):
                is_relevant = True
        # 3. イベントに地域コードも直接的な位置情報もないが、area_description がある場合
        # (これは曖昧なので、より高度なジオコーディングや自然言語処理が必要になる場合がある)
        # ここでは単純なロジックは含めず、上記1, 2で判定する。
        # もし、event_type が広域災害 (例: 台風の進路予報全体) の場合は、
        # ユーザーの地域が含まれる可能性があれば関連ありとすることも検討できる。
        # (例: event.area_description にユーザーの都道府県名が含まれるかなど)

        # 4. 特定のイベントタイプは広域情報として扱う (フィルタリングしない、または緩い基準)
        # 例: "shelter_static_data_updated" は直接的な位置関連性が薄いので、ここでは除外しない
        #     (ただし、提案生成時にユーザーの地域と関連付けるかは別問題)
        if event.event_type == "shelter_static_data_updated":
            # is_relevant = True # 更新通知は常に表示する、などのポリシーも考えられる
            pass # この例では、距離やエリアコードでのフィルタリング対象とする

        if is_relevant:
            filtered_events.append(event)

    logger.info(f"Filtered {len(events)} events down to {len(filtered_events)} relevant events for location ({current_location.latitude}, {current_location.longitude}).")
    return filtered_events


# このフィルタリングロジックを呼び出す処理フローの例
# (通常は agent_suggestions.py や、Pub/Subメッセージを処理するフロー内で呼び出される)
async def example_usage_event_filter(
    all_normalized_events: List[UnifiedEventData], # DBなどから取得した全正規化イベント
    user_current_location: LocationModel,
    user_area_codes: Optional[List[str]] = None # ユーザーの現在地の市区町村コード
):
    relevant_events = filter_events_by_location(
        all_normalized_events,
        user_current_location,
        target_area_codes=user_area_codes
    )

    # relevant_events を使って提案を生成する
    # (safety_beacon_agent.py の invoke_proactive_agent に渡すなど)
    logger.info(f"Example: Found {len(relevant_events)} relevant events for the user.")
    for rev_event in relevant_events:
        logger.info(f"  - Relevant Event ID: {rev_event.event_id}, Type: {rev_event.event_type}, Headline: {rev_event.headline}")

    return relevant_events


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # ダミーデータでテスト
    user_loc = LocationModel(latitude=35.681236, longitude=139.767125) # 東京駅
    user_codes = ["13101"] # 千代田区

    sample_events = [
        UnifiedEventData(event_id="ev1", event_type="earthquake", source_name="JMA", headline="東京で震度3", reported_at=datetime.now(), fetched_at=datetime.now(), location=LocationModel(latitude=35.68, longitude=139.76)),
        UnifiedEventData(event_id="ev2", event_type="weather_alert", source_name="JMA", headline="神奈川に大雨警報", reported_at=datetime.now(), fetched_at=datetime.now(), area_codes=["14100"]), # 横浜市
        UnifiedEventData(event_id="ev3", event_type="shelter_status_update", source_name="GuideAPI", headline="千代田区の避難所A 開設", reported_at=datetime.now(), fetched_at=datetime.now(), location=LocationModel(latitude=35.69, longitude=139.75), area_codes=["13101"]),
        UnifiedEventData(event_id="ev4", event_type="flood_info", source_name="Suiboumap", headline="沖縄の浸水予測", reported_at=datetime.now(), fetched_at=datetime.now(), location=LocationModel(latitude=26.21, longitude=127.68)), # 那覇
        UnifiedEventData(event_id="ev5", event_type="weather_alert", source_name="JMA", headline="東京23区に大雨注意報", reported_at=datetime.now(), fetched_at=datetime.now(), area_codes=["13101", "13102", "13103"]), # 千代田区、中央区、港区
    ]

    async def run_example():
        await example_usage_event_filter(sample_events, user_loc, user_codes)

    asyncio.run(run_example())
