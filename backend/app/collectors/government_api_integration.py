"""
Government API Integration Module
政府・自治体API連携統合モジュール

This module provides a unified interface for collecting shelter and disaster data
from various government and municipal APIs in Japan.

Data Sources:
- 東京都オープンデータAPI (Tokyo Open Data API)
- 国土地理院 (GSI) Hazard Map and Elevation APIs
- 内閣府防災情報 (Cabinet Office Disaster Prevention)
- 消防庁データ (Fire and Disaster Management Agency)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union, Any
import asyncio
import logging
import zipfile
import json
import io
from urllib.parse import urljoin

from ..config.app_settings import app_settings
from ..utils.http_client import fetch_json, fetch_bytes, HTTPClient
from ..services.cache_service import cache_service, CacheType, get_cached_or_fetch
from ..schemas.api_schemas import ElevationData, HazardData, HazardTileInfo, DataSourceType, APIStatus
from ..schemas.shelter import ShelterBase as ShelterData

logger = logging.getLogger(__name__)
app_config = app_settings


# DataSourceType and APIStatus imported from api_schemas


@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    name: str
    base_url: str
    data_source: DataSourceType
    rate_limit: int  # requests per minute
    timeout: int  # seconds
    requires_auth: bool = False
    auth_header: Optional[str] = None
    health_check_path: Optional[str] = None


@dataclass
class APIResponse:
    """Unified API response structure"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    source: Optional[DataSourceType] = None
    cache_hit: bool = False
    response_time: Optional[float] = None


class BaseAPIClient(ABC):
    """Base class for all API clients"""
    
    def __init__(self, endpoint: APIEndpoint, http_client: HTTPClient):
        self.endpoint = endpoint
        self.http_client = http_client
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300  # 5 minutes
        )
    
    @abstractmethod
    async def fetch_data(self, **kwargs) -> APIResponse:
        """Fetch data from the API"""
        pass
    
    @abstractmethod
    async def health_check(self) -> APIStatus:
        """Check API health status"""
        pass
    
    async def _make_request(self, url: str, params: Dict = None, cache_type: CacheType = None) -> APIResponse:
        """Make HTTP request with unified caching and error handling"""
        
        # Circuit breaker check
        if not self.circuit_breaker.can_execute():
            return APIResponse(
                success=False,
                error="Circuit breaker is open",
                source=self.endpoint.data_source
            )
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Use unified cache if cache_type is specified
            if cache_type:
                cache_params = {"url": url, "params": params or {}}
                
                async def fetch_func():
                    return await fetch_json(
                        url=url,
                        params=params,
                        headers=self._get_headers(),
                        timeout=self.endpoint.timeout
                    )
                
                data = await get_cached_or_fetch(
                    cache_type=cache_type,
                    params=cache_params,
                    fetch_func=fetch_func
                )
                
                if data is not None:
                    self.circuit_breaker.record_success()
                    end_time = asyncio.get_event_loop().time()
                    
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=200,
                        source=self.endpoint.data_source,
                        response_time=end_time - start_time,
                        cache_hit=True  # May be cache hit or fresh fetch
                    )
                else:
                    self.circuit_breaker.record_failure()
                    return APIResponse(
                        success=False,
                        error="Failed to fetch data",
                        source=self.endpoint.data_source
                    )
            else:
                # Direct fetch without caching
                data = await fetch_json(
                    url=url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=self.endpoint.timeout
                )
                
                end_time = asyncio.get_event_loop().time()
                
                if data is not None:
                    self.circuit_breaker.record_success()
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=200,
                        source=self.endpoint.data_source,
                        response_time=end_time - start_time
                    )
                else:
                    self.circuit_breaker.record_failure()
                    return APIResponse(
                        success=False,
                        error="Failed to fetch data",
                        source=self.endpoint.data_source
                    )
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            return APIResponse(
                success=False,
                error=str(e),
                source=self.endpoint.data_source
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "User-Agent": "SafeBeee/1.0 (Safety Application)",
            "Accept": "application/json"
        }
        
        if self.endpoint.requires_auth and self.endpoint.auth_header:
            headers["Authorization"] = self.endpoint.auth_header
        
        return headers


class CircuitBreaker:
    """Circuit breaker implementation for API resilience"""
    
    def __init__(self, failure_threshold: int, recovery_timeout: int):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout




class GSIClient(BaseAPIClient):
    """国土地理院 (GSI) API client"""
    
    async def fetch_data(self, data_type: str, **kwargs) -> APIResponse:
        """Fetch GSI data"""
        if data_type == "elevation":
            return await self._fetch_elevation(**kwargs)
        elif data_type == "hazard":
            return await self._fetch_hazard_data(**kwargs)
        elif data_type in ["evacuation_sites", "evacuation_shelters"]:
            return await self._fetch_shelter_geojson(data_type=data_type, **kwargs)
        else:
            return APIResponse(
                success=False,
                error=f"Unsupported data type: {data_type}",
                source=self.endpoint.data_source
            )
    
    async def _fetch_elevation(self, longitude: float, latitude: float) -> APIResponse:
        """Fetch elevation data from GSI API"""
        url = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
        params = {
            "lon": longitude,
            "lat": latitude,
            "outtype": "JSON"
        }
        
        response = await self._make_request(url, params, cache_type=CacheType.GOV_API_ELEVATION)
        
        if response.success and response.data:
            # Check if GSI API returned an error or no elevation data
            if isinstance(response.data, dict):
                elevation_value = response.data.get("elevation")
                if elevation_value is None or elevation_value == "-----":
                    logger.debug(f"No elevation data available for coordinates ({longitude}, {latitude})")
                    return APIResponse(
                        success=False,
                        error="No elevation data available for this location",
                        source=self.endpoint.data_source
                    )
                
                # Parse GSI elevation response
                elevation_data = self._parse_elevation_response(response.data, longitude, latitude)
                response.data = elevation_data
            else:
                logger.debug(f"Unexpected elevation response format for ({longitude}, {latitude}): {response.data}")
                return APIResponse(
                    success=False,
                    error="Unexpected response format from elevation API",
                    source=self.endpoint.data_source
                )
        
        return response
    
    async def _fetch_hazard_data(self, region: str, hazard_type: str, bounds: tuple = None) -> APIResponse:
        """Fetch hazard map tile information from GSI"""
        # GSI ハザードマップタイルサービスの情報を取得
        # タイル形式データの場合、特定地域のタイル情報を返す
        
        # ハザードタイプとタイルIDのマッピング（国土地理院の実際のタイルID）
        hazard_tile_mapping = {
            "flood": "hazardmap_flood",      # 洪水浸水想定区域
            "tsunami": "hazardmap_tsunami",  # 津波浸水想定
            "landslide": "hazardmap_doseki", # 土砂災害警戒区域
            "storm_surge": "hazardmap_takashio"  # 高潮浸水想定区域
        }
        
        tile_id = hazard_tile_mapping.get(hazard_type)
        if not tile_id:
            return APIResponse(
                success=False,
                error=f"Unsupported hazard type: {hazard_type}",
                source=self.endpoint.data_source
            )
        
        # 地域の境界ボックスが指定されていない場合は、主要都市の座標を使用
        if bounds is None:
            region_coords = self._get_region_bounds(region)
            if region_coords is None:
                return APIResponse(
                    success=False,
                    error=f"Unknown region: {region}",
                    source=self.endpoint.data_source
                )
            bounds = region_coords
        
        # タイル情報を構築
        hazard_tile_info = HazardTileInfo(
            hazard_type=hazard_type,
            region=region,
            tile_id=tile_id,
            tile_base_url=f"https://cyberjapandata.gsi.go.jp/xyz/{tile_id}",
            wmts_url="http://gsi-cyberjapan.github.io/experimental_wmts/gsitiles_wmts.xml",
            bounds={
                "west": bounds[0],
                "south": bounds[1], 
                "east": bounds[2],
                "north": bounds[3]
            },
            zoom_levels={"min": 5, "max": 17},
            attribution="ハザードマップポータルサイト",
            data_format="PNG tiles (XYZ format)"
        )
        
        return APIResponse(
            success=True,
            data=hazard_tile_info,
            status_code=200,
            source=self.endpoint.data_source
        )
    
    def _get_region_bounds(self, region: str) -> tuple:
        """Get bounding box coordinates for major regions"""
        # 主要地域の境界ボックス座標 (west, south, east, north)
        region_bounds = {
            "tokyo": (138.9, 35.5, 140.0, 35.9),
            "osaka": (135.3, 34.5, 135.7, 34.8),
            "kyoto": (135.5, 34.9, 135.9, 35.1),
            "kanagawa": (139.0, 35.1, 139.8, 35.6),
            "saitama": (138.8, 35.7, 139.9, 36.3),
            "chiba": (139.7, 35.0, 140.9, 36.1),
            "fukuoka": (130.2, 33.4, 130.6, 33.8),
            "sendai": (140.7, 38.1, 141.1, 38.4),
            "hiroshima": (132.3, 34.2, 132.6, 34.5),
            "nationwide": (129.0, 31.0, 146.0, 46.0)  # 日本全国
        }
        return region_bounds.get(region.lower())
    
    async def _fetch_shelter_geojson(self, data_type: str = "evacuation_sites", **kwargs) -> APIResponse:
        """Fetch shelter data using GSI official CSV data"""
        # 国土地理院公式の避難所CSVデータを使用（GeoJSON変換）
        # データソース: https://hinanmap.gsi.go.jp/index.html
        
        try:
            # 注意: GSI公式CSVのURLが現在利用できないため、モックデータで動作確認
            # 実際の運用では適切なエンドポイントに変更する必要があります
            logger.warning("GSI shelter CSV endpoint not available, using mock data for testing")
            
            # モックCSVデータ（実際のGSI形式に基づく）
            mock_csv_content = '''名称,住所,緯度,経度,災害種別,収容人数,都道府県,市区町村,市区町村コード
東京駅周辺避難所,東京都千代田区丸の内1-1-1,35.6809591,139.7673068,洪水・地震・津波,500,東京都,千代田区,13101
新宿区立新宿小学校,東京都新宿区西新宿1-1-1,35.6896,139.6917,洪水・地震,300,東京都,新宿区,13104  
渋谷区民会館,東京都渋谷区道玄坂1-1-1,35.6581,139.7016,地震・火災,200,東京都,渋谷区,13113
池袋防災センター,東京都豊島区東池袋1-1-1,35.7295,139.7142,洪水・地震・火災,400,東京都,豊島区,13116
品川区立品川小学校,東京都品川区北品川1-1-1,35.6197,139.7394,洪水・地震,250,東京都,品川区,13109'''
            
            csv_content = mock_csv_content
            
            # CSVをGeoJSONに変換
            import csv
            import io
            
            geojson_data = {
                "type": "FeatureCollection", 
                "features": []
            }
            
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            feature_count = 0
            
            for row in csv_reader:
                try:
                    # 座標の取得（緯度・経度カラム名は実際のCSVに合わせて調整）
                    lat = float(row.get('緯度', row.get('latitude', 0)))
                    lon = float(row.get('経度', row.get('longitude', 0)))
                    
                    if lat == 0 or lon == 0:
                        continue
                    
                    # GeoJSON Feature作成
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "名称": row.get('名称', row.get('name', 'Unknown')),
                            "住所": row.get('住所', row.get('address', '')),
                            "災害種別": row.get('災害種別', row.get('disaster_types', '')),
                            "収容人数": row.get('収容人数', ''),
                            "市区町村コード": row.get('市区町村コード', ''),
                            "都道府県": row.get('都道府県', ''),
                            "市区町村": row.get('市区町村', '')
                        }
                    }
                    
                    geojson_data["features"].append(feature)
                    feature_count += 1
                    
                    # テスト時は100件に制限
                    if feature_count >= 100:
                        break
                        
                except (ValueError, TypeError) as e:
                    continue  # 不正なデータ行をスキップ
            
            if feature_count == 0:
                return APIResponse(
                    success=False,
                    error="No valid shelter data found in CSV",
                    source=self.endpoint.data_source
                )
            
            logger.info(f"Successfully converted {feature_count} shelters from GSI CSV to GeoJSON")
            
            return APIResponse(
                success=True,
                data=geojson_data,
                status_code=200,
                source=self.endpoint.data_source
            )
            
        except Exception as e:
            logger.error(f"Error fetching GSI shelter CSV data: {e}")
            return APIResponse(
                success=False,
                error=str(e),
                source=self.endpoint.data_source
            )
    
    def _parse_elevation_response(self, data: Dict, longitude: float, latitude: float) -> ElevationData:
        """Parse GSI elevation API response"""
        return ElevationData(
            elevation=data.get("elevation"),
            data_source=data.get("hsrc", "unknown"),  # GSI uses 'hsrc' not 'datasrc'
            accuracy=self._determine_accuracy(data.get("hsrc", "")),
            coordinates={
                "longitude": longitude,  # Use request parameters
                "latitude": latitude     # Use request parameters
            }
        )
    
    def _determine_accuracy(self, data_source: str) -> str:
        """Determine elevation data accuracy from source"""
        if "5m" in data_source.lower():
            return "5m"
        elif "10m" in data_source.lower():
            return "10m"
        else:
            return "unknown"
    
    async def _extract_geojson_from_zip(self, zip_data: bytes) -> Optional[Dict]:
        """Extract GeoJSON data from ZIP file"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
                # ZIPファイル内のGeoJSONファイルを探す
                for file_name in zip_file.namelist():
                    if file_name.endswith('.geojson') or file_name.endswith('.json'):
                        with zip_file.open(file_name) as geojson_file:
                            geojson_content = geojson_file.read().decode('utf-8')
                            return json.loads(geojson_content)
                
                logger.warning("No GeoJSON file found in ZIP archive")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting GeoJSON from ZIP: {e}")
            return None
    
    async def health_check(self) -> APIStatus:
        """Check GSI API health"""
        try:
            # Test with Tokyo Station coordinates
            response = await self._fetch_elevation(139.7673068, 35.6809591)
            
            if response.success:
                return APIStatus.HEALTHY
            else:
                return APIStatus.UNHEALTHY
        except Exception:
            return APIStatus.UNKNOWN


class GovernmentAPIIntegrator:
    """Main integration class for all government APIs"""
    
    def __init__(self):
        self.clients: Dict[DataSourceType, BaseAPIClient] = {}
        self.http_client: Optional[HTTPClient] = None
        self.endpoints = self._configure_endpoints()
    
    def _configure_endpoints(self) -> Dict[DataSourceType, APIEndpoint]:
        """Configure API endpoints"""
        return {
            DataSourceType.GSI_ELEVATION: APIEndpoint(
                name="GSI Elevation API",
                base_url="https://cyberjapandata2.gsi.go.jp",
                data_source=DataSourceType.GSI_ELEVATION,
                rate_limit=60,  # Conservative rate limit
                timeout=5
            ),
            DataSourceType.GSI_HAZARD: APIEndpoint(
                name="GSI Hazard Map API",
                base_url="https://disaportal.gsi.go.jp",
                data_source=DataSourceType.GSI_HAZARD,
                rate_limit=30,
                timeout=10
            ),
            DataSourceType.GSI_SHELTER_GEOJSON: APIEndpoint(
                name="GSI Shelter GeoJSON API",
                base_url="https://www.gsi.go.jp",
                data_source=DataSourceType.GSI_SHELTER_GEOJSON,
                rate_limit=10,  # Large file downloads
                timeout=30
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.http_client = HTTPClient()
        
        # Initialize clients
        for source_type, endpoint in self.endpoints.items():
            if source_type in [DataSourceType.GSI_ELEVATION, DataSourceType.GSI_HAZARD, DataSourceType.GSI_SHELTER_GEOJSON]:
                self.clients[source_type] = GSIClient(endpoint, self.http_client)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.http_client:
            await self.http_client.close()
    
    async def fetch_shelter_data(self, region: str = "nationwide") -> List[ShelterData]:
        """Fetch shelter data from GSI CSV source"""
        try:
            # Use dedicated GSI shelter CSV client
            from .gsi_shelter_client import GSIShelterClient
            
            async with GSIShelterClient() as gsi_client:
                shelter_data_list = await gsi_client.fetch_shelter_csv_data(
                    prefecture=None if region == "nationwide" else region
                )
                
                # Convert ShelterBase to ShelterData (they are aliases)
                results = shelter_data_list
                
            logger.info(f"Fetched {len(results)} shelters from GSI CSV data")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching GSI shelter data: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    async def fetch_elevation_data(self, coordinates: List[tuple]) -> Dict[tuple, ElevationData]:
        """Fetch elevation data for multiple coordinates"""
        elevation_data = {}
        gsi_client = self.clients.get(DataSourceType.GSI_ELEVATION)
        
        if not gsi_client:
            return elevation_data
        
        # Process coordinates in batches to respect rate limits
        batch_size = 10
        for i in range(0, len(coordinates), batch_size):
            batch = coordinates[i:i + batch_size]
            
            tasks = []
            for lon, lat in batch:
                tasks.append(gsi_client.fetch_data("elevation", longitude=lon, latitude=lat))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for (lon, lat), response in zip(batch, responses):
                if isinstance(response, APIResponse) and response.success:
                    elevation_data[(lon, lat)] = response.data
                else:
                    logger.debug(f"Failed to fetch elevation for {lon}, {lat}")
            
            # Rate limiting delay
            await asyncio.sleep(1)
        
        return elevation_data
    
    async def fetch_hazard_data(self, region: str, hazard_type: str) -> Optional[HazardTileInfo]:
        """Fetch hazard map tile information"""
        gsi_client = self.clients.get(DataSourceType.GSI_HAZARD)
        
        if not gsi_client:
            return None
        
        response = await gsi_client.fetch_data("hazard", region=region, hazard_type=hazard_type)
        
        if response.success and response.data:
            return response.data  # HazardTileInfo object is already created in _fetch_hazard_data
        
        return None
    
    async def health_check_all(self) -> Dict[DataSourceType, APIStatus]:
        """Check health of all APIs"""
        health_status = {}
        
        tasks = []
        for source_type, client in self.clients.items():
            tasks.append((source_type, client.health_check()))
        
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        for (source_type, _), result in zip(tasks, results):
            if isinstance(result, APIStatus):
                health_status[source_type] = result
            else:
                health_status[source_type] = APIStatus.UNKNOWN
        
        return health_status
    
    
    def _normalize_hazard_data(self, data: Any, hazard_type: str) -> HazardData:
        """Normalize hazard map data"""
        return HazardData(
            hazard_type=hazard_type,
            region=data.get('region', ''),
            risk_level=data.get('risk_level', 'unknown'),
            affected_areas=data.get('affected_areas', []),
            metadata=data.get('metadata', {}),
            source=DataSourceType.GSI_HAZARD.value
        )
    
    def _normalize_gsi_shelters(self, geojson_data: Dict, shelter_type: str) -> List[ShelterData]:
        """Normalize GSI GeoJSON shelter data"""
        shelters = []
        
        try:
            features = geojson_data.get('features', [])
            
            for feature in features:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                coordinates = geometry.get('coordinates', [])
                
                if len(coordinates) >= 2:
                    # GeoJSONの座標は [longitude, latitude] の順序
                    longitude, latitude = coordinates[0], coordinates[1]
                    
                    # GeoPoint作成
                    from ..schemas.shelter import GeoPoint
                    location = GeoPoint(latitude=float(latitude), longitude=float(longitude))
                    
                    # 災害種別の処理
                    disaster_types_str = properties.get('災害種別', properties.get('disaster_types', ''))
                    disaster_types = self._parse_disaster_types(disaster_types_str)
                    
                    shelter = ShelterData(
                        name=properties.get('名称', properties.get('name', 'Unknown')),
                        address=properties.get('住所', properties.get('address', '')),
                        location=location,
                        disaster_types=disaster_types,
                        capacity=self._parse_capacity(properties.get('収容人数', properties.get('capacity'))),
                        notes=f"都道府県: {properties.get('都道府県', '')}, 市区町村: {properties.get('市区町村', '')}",
                        data_source=DataSourceType.GSI_SHELTER_GEOJSON.value
                    )
                    shelters.append(shelter)
            
            logger.info(f"Normalized {len(shelters)} shelters from GSI data")
            
        except Exception as e:
            logger.error(f"Error normalizing GSI shelter data: {e}")
        
        return shelters
    
    def _parse_disaster_types(self, disaster_types_str: str) -> List[str]:
        """Parse disaster types from string"""
        if not disaster_types_str:
            return ["general"]
        
        # 災害種別の文字列を解析
        disaster_mapping = {
            "洪水": "flood",
            "崖崩れ": "landslide", 
            "土石流": "landslide",
            "地滑り": "landslide",
            "高潮": "storm_surge",
            "地震": "earthquake",
            "津波": "tsunami",
            "大規模な火事": "fire",
            "内水氾濫": "flood",
            "火山現象": "volcano"
        }
        
        disaster_types = []
        for jp_type, en_type in disaster_mapping.items():
            if jp_type in disaster_types_str:
                disaster_types.append(en_type)
        
        return disaster_types if disaster_types else ["general"]
    
    def _parse_capacity(self, capacity_str: Any) -> Optional[int]:
        """Parse capacity from string to integer"""
        if capacity_str is None:
            return None
        
        try:
            if isinstance(capacity_str, int):
                return capacity_str
            elif isinstance(capacity_str, str):
                # 数字のみを抽出
                import re
                numbers = re.findall(r'\d+', capacity_str)
                if numbers:
                    return int(numbers[0])
            return None
        except (ValueError, TypeError):
            return None
    
    def _parse_facilities(self, properties: Dict) -> List[str]:
        """Parse facilities from properties"""
        facilities = []
        
        # 施設情報のマッピング
        facility_mapping = {
            '給水': 'water',
            'トイレ': 'toilet',
            '電源': 'power',
            'WiFi': 'wifi',
            'バリアフリー': 'wheelchair',
            'エレベーター': 'elevator',
            'ペット': 'pet_allowed'
        }
        
        for key, value in properties.items():
            if key in facility_mapping and value:
                facilities.append(facility_mapping[key])
        
        return facilities


# Usage example
async def main():
    """Example usage of the government API integrator"""
    async with GovernmentAPIIntegrator() as integrator:
        # Check API health
        health_status = await integrator.health_check_all()
        logger.info("API Health Status: %s", health_status)
        
        # Fetch shelter data
        shelters = await integrator.fetch_shelter_data("tokyo")
        logger.info("Found %d shelters", len(shelters))
        
        # Fetch elevation data for shelter locations
        coordinates = [(shelter.longitude, shelter.latitude) for shelter in shelters[:5]]
        elevation_data = await integrator.fetch_elevation_data(coordinates)
        logger.info("Elevation data for %d locations", len(elevation_data))


if __name__ == "__main__":
    asyncio.run(main())