"""災害コンテキスト管理モジュール - 災害モード判断と緊急度評価"""
import os
import logging
import re
import json # jsonをインポート
import math
from typing import Dict, Any, Optional, List, Tuple, Union
from app.schemas.agent_state import LocationState
from datetime import datetime, timedelta
from google.cloud import firestore

# LLMクライアントをインポート  
from app.agents.safety_beacon_agent.core.llm_singleton import log_llm_prompt, log_llm_response, ainvoke_llm

logger = logging.getLogger(__name__)


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    ハーバサイン公式を使用して2点間の距離を計算（km）
    """
    # Validate inputs
    if not all(isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
        logger.warning(f"Invalid coordinates for distance calculation: {lat1}, {lon1}, {lat2}, {lon2}")
        return float('inf')  # Return large distance if invalid
    
    # Validate coordinate ranges
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        logger.warning(f"Invalid latitude values: {lat1}, {lat2}")
        return float('inf')
    
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        logger.warning(f"Invalid longitude values: {lon1}, {lon2}")
        return float('inf')
    
    # 地球の半径（km）
    R = 6371.0
    
    # 度をラジアンに変換
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 差を計算
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # ハーバサイン公式
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # 距離を計算
    distance = R * c
    return distance

# ユーティリティ関数
def get_state_value(state: Union[Dict[str, Any], Any], key: str, default: Any = None) -> Any:
    """状態から値を取得（辞書/オブジェクト両対応）"""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)

def update_state_value(state: Union[Dict[str, Any], Any], key: str, value: Any) -> None:
    """状態の値を更新（辞書/オブジェクト両対応）"""
    if isinstance(state, dict):
        state[key] = value
    else:
        setattr(state, key, value)

# Firestoreクライアント初期化
try:
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    if not gcp_project_id:
        if os.getenv("ENVIRONMENT") in ["development", "test"]:
            gcp_project_id = "safetybee-development"
            logger.warning(f"Using development fallback GCP_PROJECT_ID: {gcp_project_id}")
        else:
            raise ValueError("GCP_PROJECT_ID environment variable is required in production")

    db = firestore.AsyncClient(project=gcp_project_id)
    logger.info("Firestore client initialized for disaster context manager")
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {e}")
    raise

async def collect_disaster_data(location: Optional[Dict[str, float]] = None, time_range_hours: int = 24) -> List[Dict[str, Any]]:
    """災害データを収集（データ収集係）"""
    try:
        # 時間範囲を設定（デフォルト24時間）
        time_threshold = datetime.now() - timedelta(hours=time_range_hours)
        
        # 基本クエリ
        query = db.collection("jma_events")\
                 .where(filter=firestore.FieldFilter("timestamp", ">", time_threshold))\
                 .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                 .limit(50)

        docs = await query.get()
        
        disaster_data = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            disaster_data.append(data)
        
        logger.info(f"Collected {len(disaster_data)} disaster events from last {time_range_hours} hours")
        return disaster_data

    except Exception as e:
        logger.error(f"Error collecting disaster data: {e}")
        return []

def preprocess_disaster_data(raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """災害データを前処理（前処理係）"""
    processed_data = {
        "active_alerts": [],      # 現在有効な警報
        "recent_earthquakes": [], # 最近の地震
        "weather_warnings": [],   # 気象警報
        "tsunami_alerts": [],     # 津波情報
        "evacuation_orders": [],  # 避難指示
        "other_events": []        # その他
    }
    
    for event in raw_data:
        # イベントタイプで分類
        event_type = event.get("event_type", "").lower()
        severity = event.get("severity", "")
        
        # アクティブな警報かチェック
        if severity in ["警告", "緊急", "warning", "emergency"]:
            processed_data["active_alerts"].append(event)
        
        # タイプ別に分類
        if "earthquake" in event_type or "地震" in event.get("title", ""):
            processed_data["recent_earthquakes"].append(event)
        elif "tsunami" in event_type or "津波" in event.get("title", ""):
            processed_data["tsunami_alerts"].append(event)
        elif "weather" in event_type or "気象" in event.get("title", ""):
            processed_data["weather_warnings"].append(event)
        elif "避難" in event.get("title", ""):
            processed_data["evacuation_orders"].append(event)
        else:
            processed_data["other_events"].append(event)
    
    logger.info(f"Preprocessed disaster data: {len(processed_data['active_alerts'])} active alerts")
    return processed_data

def filter_by_location(disaster_data: Dict[str, List[Dict[str, Any]]], 
                       user_location: Optional[Union[Dict[str, Any], Any]],
                       user_prefecture: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """位置情報に基づいてフィルタリング（フィルタ係）"""
    # Handle different location data types
    lat = None
    lon = None
    
    if user_location:
        # Handle dict type
        if isinstance(user_location, dict):
            lat = user_location.get("latitude")
            lon = user_location.get("longitude")
        # Handle Pydantic model or object with attributes
        elif hasattr(user_location, "latitude") and hasattr(user_location, "longitude"):
            lat = user_location.latitude
            lon = user_location.longitude
        # Handle other potential formats
        else:
            logger.warning(f"Unknown location format: {type(user_location)}")
    
    if not lat and not lon and not user_prefecture:
        # 位置情報がない場合は全データを返す
        return disaster_data
    
    filtered_data = {}
    
    for category, events in disaster_data.items():
        filtered_events = []
        
        for event in events:
            # イベントの影響地域を取得
            affected_areas = event.get("area_name", "").split("、")
            
            # ユーザーの都道府県と照合
            if user_prefecture:
                for area in affected_areas:
                    if user_prefecture in area or area in user_prefecture:
                        filtered_events.append(event)
                        break
            else:
                # 位置情報がある場合は距離計算でフィルタリング
                if lat is not None and lon is not None:
                    # イベントに位置情報がある場合のみ距離計算
                    event_lat = event.get("latitude")
                    event_lon = event.get("longitude")
                    
                    if event_lat and event_lon:
                        # 距離計算（ハーバサイン公式）
                        distance_km = _calculate_distance(
                            lat, lon,
                            event_lat, event_lon
                        )
                        
                        # 50km以内のイベントのみを含める
                        if distance_km <= 50.0:
                            filtered_events.append(event)
                    else:
                        # イベントに位置情報がない場合は地域名での照合を試みる
                        # ユーザーの都道府県と照合（既に上で試みているが、ここでも再度チェック）
                        if user_prefecture and affected_areas:
                            for area in affected_areas:
                                if user_prefecture in area or area in user_prefecture:
                                    filtered_events.append(event)
                                    break
                        # 位置情報も地域名も一致しない場合は除外（バグ修正）
                        # 以前は無条件で含めていたが、これは無関係なアラートを送る原因
        
        filtered_data[category] = filtered_events
    
    total_filtered = sum(len(events) for events in filtered_data.values())
    logger.info(f"Filtered disaster data: {total_filtered} relevant events")
    return filtered_data

def filter_by_user_query(disaster_data: Dict[str, List[Dict[str, Any]]],
                        user_input: str,
                        primary_intent: str) -> Dict[str, List[Dict[str, Any]]]:
    """ユーザーの質問内容に基づいてフィルタリング"""
    filtered_data = {}
    
    # インテントに基づいて関連カテゴリを選択
    if primary_intent == "evacuation":
        filtered_data["evacuation_orders"] = disaster_data.get("evacuation_orders", [])
        filtered_data["active_alerts"] = disaster_data.get("active_alerts", [])
    elif primary_intent == "disaster_info":
        # 全カテゴリから関連情報を収集
        for category, events in disaster_data.items():
            if events:  # 空でないカテゴリのみ
                filtered_data[category] = events[:5]  # 各カテゴリから最大5件
    elif "earthquake" in primary_intent or "地震" in user_input:
        filtered_data["recent_earthquakes"] = disaster_data.get("recent_earthquakes", [])
    elif "tsunami" in primary_intent or "津波" in user_input:
        filtered_data["tsunami_alerts"] = disaster_data.get("tsunami_alerts", [])
    else:
        # デフォルト：アクティブアラートのみ
        filtered_data["active_alerts"] = disaster_data.get("active_alerts", [])
    
    return filtered_data

async def evaluate_emergency_mode(state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    緊急モードかどうかを判定
    Returns: (is_emergency_mode, mode_details)
    """
    mode_details = {
        "mode": "normal",
        "reason": None,
        "severity": 0,
        "expires_at": None
    }
    
    # 0. 既存の緊急モード設定を優先（フロントエンドからの指定など）
    existing_disaster_mode = get_state_value(state, "is_disaster_mode", False)
    if existing_disaster_mode:
        mode_details.update({
            "mode": "emergency",
            "reason": "existing_disaster_mode_active",
            "severity": 3,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        })
        return True, mode_details
    
    # 1. 外部アラート（FCM）の確認
    external_alerts = get_state_value(state, "external_alerts", [])
    if external_alerts:
        # アクティブな外部アラートがある場合は緊急モード
        mode_details.update({
            "mode": "emergency",
            "reason": "external_alert_active",
            "severity": 3,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        })
        return True, mode_details
    
    # 2. 災害データの収集と評価
    raw_disaster_data = await collect_disaster_data(time_range_hours=24)
    processed_data = preprocess_disaster_data(raw_disaster_data)
    
    # 3. 位置ベースの評価
    user_location = get_state_value(state, "user_location")
    if user_location:
        location_filtered = filter_by_location(processed_data, user_location)
        
        # アクティブアラートの確認
        active_alerts = location_filtered.get("active_alerts", [])
        if active_alerts:
            # 50km圏内にアクティブアラートがある
            mode_details.update({
                "mode": "emergency",
                "reason": "nearby_active_alert",
                "severity": 2,
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(),
                "alert_count": len(active_alerts)
            })
            return True, mode_details
        
        # 大規模地震の確認（震度5以上）
        earthquakes = location_filtered.get("recent_earthquakes", [])
        for eq in earthquakes:
            magnitude = eq.get("magnitude", 0)
            if magnitude >= 5.0:
                mode_details.update({
                    "mode": "emergency",
                    "reason": "major_earthquake",
                    "severity": 3,
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                    "magnitude": magnitude
                })
                return True, mode_details
        
        # 津波警報・注意報の確認
        tsunami_alerts = location_filtered.get("tsunami_alerts", [])
        if tsunami_alerts:
            mode_details.update({
                "mode": "emergency",
                "reason": "tsunami_alert",
                "severity": 3,
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat()
            })
            return True, mode_details
    
    # 4. 時間経過による自動解除チェック
    # 最後の緊急モード設定時刻を確認（stateに保存されている場合）
    last_emergency_timestamp = get_state_value(state, "last_emergency_timestamp")
    if last_emergency_timestamp:
        last_emergency = datetime.fromisoformat(last_emergency_timestamp)
        time_since_emergency = datetime.now() - last_emergency
        
        if time_since_emergency < timedelta(hours=24):
            # 24時間以内は緊急モードを維持する可能性
            # ただし、他の条件が全てクリアされていれば解除
            pass
    
    # 通常モードと判定
    mode_details["reason"] = "no_active_threats"
    return False, mode_details

async def prepare_disaster_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    次のハンドラーのために災害コンテキストを準備
    1. データ収集
    2. 前処理
    3. フィルタリング
    """
    # 緊急モード判定
    is_emergency_mode, mode_details = await evaluate_emergency_mode(state)
    
    if not is_emergency_mode:
        # 通常モードの場合は最小限のコンテキストを返す
        return {
            "active_alerts": [],
            "relevant_info": {},
            "shelters": [],
            "evacuation_routes": [],
            "mode_details": mode_details
        }
    
    # 1. データ収集
    raw_disaster_data = await collect_disaster_data(time_range_hours=48)
    
    # 避難所情報も収集（将来的に実装）
    shelter_data = []  # TODO: collect_shelter_data()
    
    # 2. 前処理
    processed_data = preprocess_disaster_data(raw_disaster_data)
    
    # 3. フィルタリング
    # 位置情報によるフィルタ - user_location フィールドを使用
    user_location = get_state_value(state, "user_location")
    
    # Extract prefecture from address if available
    user_prefecture = None
    if user_location:
        # Try to get prefecture from address field
        if isinstance(user_location, dict) and "address" in user_location:
            address = user_location.get("address", "")
            # Simple prefecture extraction from address
            prefectures = ["東京都", "大阪府", "京都府", "北海道"] + [f"{p}県" for p in ["青森", "岩手", "宮城", "秋田", "山形", "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "神奈川", "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "滋賀", "兵庫", "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口", "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "沖縄"]]
            for pref in prefectures:
                if pref in address:
                    user_prefecture = pref
                    break
        elif hasattr(user_location, "address"):
            address = getattr(user_location, "address", "")
            # Same prefecture extraction logic
            prefectures = ["東京都", "大阪府", "京都府", "北海道"] + [f"{p}県" for p in ["青森", "岩手", "宮城", "秋田", "山形", "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "神奈川", "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "滋賀", "兵庫", "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口", "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "沖縄"]]
            for pref in prefectures:
                if pref in address:
                    user_prefecture = pref
                    break
    
    location_filtered = filter_by_location(processed_data, user_location, user_prefecture)
    
    # ユーザーの質問内容によるフィルタ
    user_input = get_state_value(state, "user_input", "")
    primary_intent = get_state_value(state, "primary_intent", "unknown")
    
    final_filtered = filter_by_user_query(location_filtered, user_input, primary_intent)
    
    # ハンドラーが使いやすい形式に整形
    disaster_context = {
        "active_alerts": final_filtered.get("active_alerts", []),
        "relevant_info": final_filtered,
        "shelters": shelter_data,
        "evacuation_routes": [],  # TODO: 避難経路情報
        "user_location": user_location,
        "collected_at": datetime.now().isoformat(),
        "mode_details": mode_details,
        "is_emergency_mode": is_emergency_mode
    }
    
    logger.info(f"Prepared disaster context with {len(disaster_context['active_alerts'])} active alerts")
    return disaster_context

async def update_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """災害コンテキストを更新"""
    # 災害コンテキストを準備
    disaster_context = await prepare_disaster_context(state)
    
    # 災害コンテキストから緊急モード判定結果を取得
    is_disaster_mode = disaster_context.get("is_emergency_mode", False)
    
    # 緊急モードに変更があった場合はログ出力
    current_mode = get_state_value(state, "is_disaster_mode", False)
    if current_mode != is_disaster_mode:
        mode_details = disaster_context.get("mode_details", {})
    # 状態更新 (StateGraphでは辞書形式、main_orchestratorではオブジェクト形式)
    if isinstance(state, dict):
        # LangGraph StateGraph用: 辞書として更新
        state.update({
            "is_disaster_mode": is_disaster_mode,
            "disaster_context": disaster_context,
            "disaster_context_evaluation": {
                "is_disaster_related": get_state_value(state, "is_disaster_related", False),
                "primary_intent": get_state_value(state, "primary_intent", "unknown"),
                "required_action": "monitor"
            }
        })
    else:
        # main_orchestrator用: AgentStateModelオブジェクトとして更新
        state.is_disaster_mode = is_disaster_mode
        state.disaster_context = disaster_context
        state.disaster_context_evaluation = {
            "is_disaster_related": getattr(state, "is_disaster_related", False),
            "primary_intent": getattr(state, "primary_intent", "unknown"),
            "required_action": "monitor"
        }

    return state
# DisasterContextManagerNode class has been removed.
# Use enhanced_task_router instead, which combines context analysis and routing.