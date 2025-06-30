# backend/app/services/geocoding_service.py
"""
逆ジオコーディングサービス
GPS座標から都道府県・市区町村を取得
"""

import logging
import asyncio
import aiohttp
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import os
import json

logger = logging.getLogger(__name__)

# OPTIMIZATION: Enhanced caching with multiple precision levels
_geocoding_cache: Dict[Tuple[float, float], Dict[str, str]] = {}
_cache_expiry: Dict[Tuple[float, float], datetime] = {}
_regional_cache: Dict[str, Dict[str, str]] = {}  # Cache by region for nearby lookups
CACHE_DURATION = timedelta(days=7)  # 1週間キャッシュ
MAX_CACHE_SIZE = 10000  # Increased cache size

# OPTIMIZATION: Circuit breaker for external API calls
_api_failure_count = 0
_last_failure_time: Optional[datetime] = None
FAILURE_THRESHOLD = 3  # Number of failures before circuit opens
CIRCUIT_TIMEOUT = timedelta(minutes=5)  # How long to wait before trying again
MAX_API_TIMEOUT = 3.0  # Reduced from 5 seconds to 3 seconds

def _is_circuit_open() -> bool:
    """Check if circuit breaker is open (API calls should be skipped)"""
    global _api_failure_count, _last_failure_time
    
    if _api_failure_count < FAILURE_THRESHOLD:
        return False
    
    if _last_failure_time and datetime.utcnow() - _last_failure_time > CIRCUIT_TIMEOUT:
        # Reset circuit breaker after timeout
        _api_failure_count = 0
        _last_failure_time = None
        logger.info("Geocoding circuit breaker reset")
        return False
    
    return True

def _record_api_failure():
    """Record an API failure for circuit breaker"""
    global _api_failure_count, _last_failure_time
    _api_failure_count += 1
    _last_failure_time = datetime.utcnow()
    logger.warning(f"Geocoding API failure #{_api_failure_count}")

def _record_api_success():
    """Record an API success (reset failure count)"""
    global _api_failure_count, _last_failure_time
    if _api_failure_count > 0:
        logger.info("Geocoding API recovered")
        _api_failure_count = 0
        _last_failure_time = None


async def reverse_geocode(latitude: float, longitude: float) -> Dict[str, Optional[str]]:
    """
    GPS座標から都道府県・市区町村を取得
    
    Args:
        latitude: 緯度
        longitude: 経度
        
    Returns:
        {"prefecture": "東京都", "city": "港区", "address": "東京都港区..."}
    """
    try:
        # OPTIMIZATION: Enhanced cache check with multiple precision levels
        cache_key = (round(latitude, 4), round(longitude, 4))  # 小数点4桁で丸める
        if cache_key in _geocoding_cache:
            if cache_key in _cache_expiry and _cache_expiry[cache_key] > datetime.utcnow():
                return _geocoding_cache[cache_key]
        
        # Try regional cache for nearby locations (less precise but faster)
        regional_key = f"{round(latitude, 2)},{round(longitude, 2)}"
        if regional_key in _regional_cache:
            return _regional_cache[regional_key]
        
        # OPTIMIZATION: Check circuit breaker before API call
        if _is_circuit_open():
            logger.warning("Geocoding circuit breaker is open, using fallback")
            result = _estimate_prefecture(latitude, longitude)
        else:
            # Yahoo!ジオコーダAPIを使用
            result = await _geocode_with_yahoo(latitude, longitude)
        
        if not result:
            # フォールバックとして簡易的な都道府県判定
            result = _estimate_prefecture(latitude, longitude)
        
        # OPTIMIZATION: Enhanced caching with size limits
        if result and result.get("prefecture"):
            # Cleanup cache if too large
            if len(_geocoding_cache) > MAX_CACHE_SIZE:
                # Remove oldest entries
                oldest_keys = sorted(_cache_expiry.items(), key=lambda x: x[1])[:MAX_CACHE_SIZE // 10]
                for key, _ in oldest_keys:
                    _geocoding_cache.pop(key, None)
                    _cache_expiry.pop(key, None)
            
            _geocoding_cache[cache_key] = result
            _cache_expiry[cache_key] = datetime.utcnow() + CACHE_DURATION
            
            # Also cache in regional cache for faster nearby lookups
            regional_key = f"{round(latitude, 2)},{round(longitude, 2)}"
            _regional_cache[regional_key] = result
            
        return result
        
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        # エラー時は簡易判定を返す
        return _estimate_prefecture(latitude, longitude)


async def _geocode_with_yahoo(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """Yahoo!ジオコーダAPIで逆ジオコーディング"""
    try:
        # Yahoo!リバースジオコーダAPI
        url = "https://map.yahooapis.jp/geoapi/V1/reverseGeoCoder"
        
        # APIキーが必要な場合は環境変数から取得
        appid = os.getenv("YAHOO_API_KEY", "")
        if not appid:
            # APIキーがない場合はNominatimを使用
            return await _geocode_with_nominatim(latitude, longitude)
        
        params = {
            "appid": appid,
            "lat": latitude,
            "lon": longitude,
            "output": "json"
        }
        
        async with aiohttp.ClientSession() as session:
            # OPTIMIZATION: Use shorter timeout
            async with session.get(url, params=params, timeout=MAX_API_TIMEOUT) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "Feature" in data and data["Feature"]:
                        feature = data["Feature"][0]
                        property = feature.get("Property", {})
                        
                        # 住所情報を解析
                        address = property.get("Address", "")
                        country = property.get("Country", {})
                        
                        # 都道府県と市区町村を分離
                        address_detail = property.get("AddressElement", [])
                        prefecture = ""
                        city = ""
                        
                        for element in address_detail:
                            level = element.get("Level")
                            name = element.get("Name", "")
                            
                            if level == "prefecture":
                                prefecture = name
                            elif level == "city":
                                city = name
                        
                        result = {
                            "prefecture": prefecture,
                            "city": city,
                            "address": address
                        }
                        
                        # OPTIMIZATION: Record success for circuit breaker
                        _record_api_success()
                        return result
                else:
                    # OPTIMIZATION: Record failure for non-200 responses
                    _record_api_failure()
                        
        return None
        
    except Exception as e:
        # OPTIMIZATION: Record failure for circuit breaker
        _record_api_failure()
        logger.warning(f"Yahoo API error: {e}")
        return None


async def _geocode_with_nominatim(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """OpenStreetMap Nominatimで逆ジオコーディング（無料・オープン）"""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "lat": latitude,
            "lon": longitude,
            "zoom": 10,  # 市区町村レベル
            "accept-language": "ja"
        }
        
        headers = {
            "User-Agent": "LinguaSafeTrip/1.0"  # User-Agentは必須
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "address" in data:
                        address = data["address"]
                        
                        # 日本の住所階層を抽出
                        prefecture = ""
                        city = ""
                        
                        # 都道府県レベル
                        if "state" in address:
                            prefecture = address["state"]
                        elif "province" in address:
                            prefecture = address["province"]
                        elif "region" in address:
                            prefecture = address["region"]
                        
                        # 市区町村レベル
                        if "city" in address:
                            city = address["city"]
                        elif "town" in address:
                            city = address["town"]
                        elif "village" in address:
                            city = address["village"]
                        elif "suburb" in address:
                            city = address["suburb"]
                        elif "city_district" in address:
                            city = address["city_district"]
                        
                        # 東京都の特殊処理
                        if not prefecture and city in ["港区", "千代田区", "中央区", "新宿区", "渋谷区", "品川区", "目黒区", "世田谷区", "大田区"]:
                            prefecture = "東京都"
                        
                        # display_nameから詳細住所
                        display_name = data.get("display_name", "")
                        
                        return {
                            "prefecture": prefecture,
                            "city": city,
                            "address": display_name
                        }
                        
        return None
        
    except Exception as e:
        logger.warning(f"Nominatim API error: {e}")
        return None


async def _geocode_with_gsi(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """国土地理院APIで逆ジオコーディング"""
    try:
        # 逆ジオコーダAPIのエンドポイント
        url = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress"
        params = {
            "lon": longitude,
            "lat": latitude
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # APIレスポンスの構造を確認
                    if "results" in data:
                        result = data["results"]
                        
                        # GSI APIのレスポンス構造に基づいて抽出
                        # muniCd: 市区町村コード
                        # lv01Nm: 都道府県名
                        # lv02Nm: 市区町村名
                        # lv03Nm: 大字・町名
                        # lv04Nm: 字・丁目
                        
                        prefecture = ""
                        city = ""
                        address_parts = []
                        
                        # 都道府県を特定（コードから推定）
                        muni_code = result.get("muniCd", "")
                        if muni_code:
                            # 市区町村コードの先頭2桁から都道府県を推定
                            pref_code = muni_code[:2]
                            prefecture = _get_prefecture_by_code(pref_code)
                        
                        # 市区町村名
                        if result.get("lv01Nm"):
                            city = result["lv01Nm"]
                            address_parts.append(result["lv01Nm"])
                        
                        # より詳細な住所
                        for key in ["lv02Nm", "lv03Nm", "lv04Nm"]:
                            if result.get(key):
                                address_parts.append(result[key])
                        
                        # もし都道府県が取得できなかった場合、住所から推定
                        if not prefecture and address_parts:
                            prefecture = _estimate_prefecture_from_address(address_parts[0])
                        
                        return {
                            "prefecture": prefecture or "日本",
                            "city": city,
                            "address": prefecture + "".join(address_parts) if prefecture else "".join(address_parts)
                        }
                        
        return None
        
    except Exception as e:
        logger.warning(f"GSI API error: {e}")
        return None


def _get_prefecture_by_code(code: str) -> str:
    """都道府県コードから都道府県名を取得"""
    prefecture_codes = {
        "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県",
        "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
        "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
        "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
        "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
        "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
        "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
        "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
        "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
        "46": "鹿児島県", "47": "沖縄県"
    }
    return prefecture_codes.get(code, "")


def _estimate_prefecture_from_address(address: str) -> str:
    """住所文字列から都道府県を推定"""
    # 主要都市名から都道府県を推定
    city_to_prefecture = {
        "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県",
        "千葉市": "千葉県", "港区": "東京都", "中央区": "東京都", "千代田区": "東京都",
        "横浜市": "神奈川県", "川崎市": "神奈川県", "新潟市": "新潟県",
        "静岡市": "静岡県", "浜松市": "静岡県", "名古屋市": "愛知県",
        "京都市": "京都府", "大阪市": "大阪府", "堺市": "大阪府",
        "神戸市": "兵庫県", "岡山市": "岡山県", "広島市": "広島県",
        "北九州市": "福岡県", "福岡市": "福岡県", "熊本市": "熊本県",
        "那覇市": "沖縄県", "稚内市": "北海道"
    }
    
    for city, prefecture in city_to_prefecture.items():
        if city in address:
            return prefecture
    
    return ""


def _estimate_prefecture(latitude: float, longitude: float) -> Dict[str, Optional[str]]:
    """GPS座標から簡易的に都道府県を推定（フォールバック用）"""
    # 主要都道府県の大まかな範囲
    prefecture_ranges = [
        # (min_lat, max_lat, min_lon, max_lon, prefecture, city)
        (35.5, 35.9, 139.4, 140.0, "東京都", "中央区"),
        (34.5, 34.8, 135.3, 135.6, "大阪府", "大阪市"),
        (35.0, 35.3, 136.8, 137.1, "愛知県", "名古屋市"),
        (43.0, 43.2, 141.2, 141.5, "北海道", "札幌市"),
        (33.8, 34.0, 130.8, 131.0, "福岡県", "福岡市"),
        (38.2, 38.4, 140.8, 141.0, "宮城県", "仙台市"),
        # 必要に応じて追加
    ]
    
    for min_lat, max_lat, min_lon, max_lon, prefecture, city in prefecture_ranges:
        if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
            return {
                "prefecture": prefecture,
                "city": city,
                "address": f"{prefecture}{city}"
            }
    
    # デフォルト（日本国内と仮定）
    return {
        "prefecture": "日本",
        "city": None,
        "address": None
    }


async def batch_reverse_geocode(locations: list[Tuple[float, float]]) -> list[Dict[str, Optional[str]]]:
    """複数の座標を一括で逆ジオコーディング"""
    tasks = [reverse_geocode(lat, lon) for lat, lon in locations]
    return await asyncio.gather(*tasks)