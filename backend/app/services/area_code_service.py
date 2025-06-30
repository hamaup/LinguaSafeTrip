"""
地域コードマッピングサービス
位置情報から JMA 地域コードを判定
"""

import json
import logging
from typing import Optional, Dict, Tuple
from pathlib import Path

from app.schemas.hazard import Location

logger = logging.getLogger(__name__)


class AreaCodeService:
    """地域コードマッピングサービス"""
    
    def __init__(self):
        """サービスの初期化"""
        self.area_codes = self._load_area_codes()
    
    def _load_area_codes(self) -> Dict:
        """地域コードマッピングデータを読み込み"""
        try:
            json_path = Path(__file__).parent.parent / "resources" / "jma_area_codes.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load area codes: {e}")
            return {"prefectures": {}}
    
    def get_area_code_from_location(self, location: Location) -> Optional[str]:
        """
        位置情報から地域コードを取得
        
        Returns:
            地域コード（市区町村レベル）。見つからない場合は都道府県レベル、それでも見つからない場合はNone
        """
        lat = location.latitude
        lon = location.longitude
        
        # まず都道府県を特定
        prefecture_code = None
        for pref_code, pref_data in self.area_codes.get("prefectures", {}).items():
            bounds = pref_data.get("bounds", {})
            if self._is_in_bounds(lat, lon, bounds):
                prefecture_code = pref_code
                
                # 市区町村を特定
                for city_code, city_data in pref_data.get("cities", {}).items():
                    city_bounds = city_data.get("bounds", {})
                    if self._is_in_bounds(lat, lon, city_bounds):
                        logger.info(f"Found area code {city_code} ({city_data['name']}) for location {lat}, {lon}")
                        return city_code
                
                # 市区町村が見つからなければ都道府県コードを返す
                logger.info(f"Found prefecture code {prefecture_code} ({pref_data['name']}) for location {lat}, {lon}")
                return prefecture_code
        
        logger.warning(f"No area code found for location {lat}, {lon}")
        return None
    
    def _is_in_bounds(self, lat: float, lon: float, bounds: Dict) -> bool:
        """位置が境界内にあるかチェック"""
        return (bounds.get("min_lat", -90) <= lat <= bounds.get("max_lat", 90) and
                bounds.get("min_lon", -180) <= lon <= bounds.get("max_lon", 180))
    
    def get_area_name(self, area_code: str) -> Optional[str]:
        """地域コードから地域名を取得"""
        # 都道府県レベル
        for pref_code, pref_data in self.area_codes.get("prefectures", {}).items():
            if pref_code == area_code:
                return pref_data.get("name")
            
            # 市区町村レベル
            for city_code, city_data in pref_data.get("cities", {}).items():
                if city_code == area_code:
                    return f"{pref_data.get('name')} {city_data.get('name')}"
        
        return None
    
    def get_nearby_area_codes(self, location: Location, radius_km: float = 10.0) -> list[str]:
        """
        指定位置の周辺地域コードを取得
        
        Args:
            location: 中心位置
            radius_km: 検索半径（km）
            
        Returns:
            周辺地域コードのリスト
        """
        nearby_codes = []
        lat = location.latitude
        lon = location.longitude
        
        # 緯度1度 ≈ 111km として概算
        lat_range = radius_km / 111.0
        lon_range = radius_km / (111.0 * abs(cos(radians(lat))))
        
        expanded_bounds = {
            "min_lat": lat - lat_range,
            "max_lat": lat + lat_range,
            "min_lon": lon - lon_range,
            "max_lon": lon + lon_range
        }
        
        # 境界が重なる地域を検索
        for pref_code, pref_data in self.area_codes.get("prefectures", {}).items():
            pref_bounds = pref_data.get("bounds", {})
            if self._bounds_overlap(expanded_bounds, pref_bounds):
                # 市区町村レベルでチェック
                has_city_match = False
                for city_code, city_data in pref_data.get("cities", {}).items():
                    city_bounds = city_data.get("bounds", {})
                    if self._bounds_overlap(expanded_bounds, city_bounds):
                        nearby_codes.append(city_code)
                        has_city_match = True
                
                # 市区町村が見つからなければ都道府県コードを追加
                if not has_city_match:
                    nearby_codes.append(pref_code)
        
        return nearby_codes
    
    def _bounds_overlap(self, bounds1: Dict, bounds2: Dict) -> bool:
        """2つの境界が重なっているかチェック"""
        return not (bounds1["max_lat"] < bounds2["min_lat"] or
                   bounds1["min_lat"] > bounds2["max_lat"] or
                   bounds1["max_lon"] < bounds2["min_lon"] or
                   bounds1["min_lon"] > bounds2["max_lon"])


# グローバルインスタンス
area_code_service = AreaCodeService()


# 数学関数のインポート
from math import cos, radians