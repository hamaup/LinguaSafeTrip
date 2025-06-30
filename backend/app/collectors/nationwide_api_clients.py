"""
Nationwide API Clients
全国自治体API連携クライアント

This module provides API clients for various municipal and government
data sources across Japan for comprehensive shelter and disaster data collection.
"""

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from ..utils.http_client import fetch_json
from ..schemas.api_schemas import DataSourceType
from ..schemas.shelter import ShelterBase as ShelterData
from ..config.app_settings import app_settings

logger = logging.getLogger(__name__)


class MunicipalAPIClient(ABC):
    """Base class for municipal API clients"""
    
    def __init__(self, region_name: str, api_config: dict):
        self.region_name = region_name
        self.api_config = api_config
        self.gov_config = app_settings.government_api
        self.enabled = api_config.get('enabled', False)
        self.base_url = api_config.get('base_url', '')
        self.endpoints = api_config.get('endpoints', {})
        self.rate_limit = api_config.get('rate_limit', 30)
        self.timeout = api_config.get('timeout', 15)
    
    @abstractmethod
    async def fetch_shelter_data(self) -> List[ShelterData]:
        """Fetch shelter data from municipal API"""
        pass


class GenericMunicipalAPIClient(MunicipalAPIClient):
    """汎用自治体API client"""
    
    async def fetch_shelter_data(self) -> List[ShelterData]:
        """自治体の避難所データを取得"""
        if not self.enabled:
            logger.debug(f"{self.region_name} API is not enabled yet")
            return []
        
        try:
            shelters = []
            
            # 複数のエンドポイントから避難所データを取得
            for endpoint_name, endpoint_path in self.endpoints.items():
                if 'shelter' in endpoint_name.lower() or 'evacuation' in endpoint_name.lower():
                    url = f"{self.base_url}{endpoint_path}"
                    
                    logger.debug(f"Fetching {self.region_name} shelter data from: {url}")
                    
                    response = await fetch_json(
                        url=url,
                        timeout=self.timeout
                    )
                    
                    if response:
                        parsed_shelters = self._parse_generic_shelters(response, endpoint_name)
                        shelters.extend(parsed_shelters)
            
            logger.info(f"Collected {len(shelters)} shelters from {self.region_name}")
            return shelters
            
        except Exception as e:
            logger.error(f"Failed to fetch {self.region_name} shelter data: {e}")
            return []
    
    def _parse_generic_shelters(self, data: Any, endpoint_name: str) -> List[ShelterData]:
        """汎用的な避難所データパース"""
        shelters = []
        
        try:
            # データ形式に応じて解析
            if isinstance(data, dict):
                # ルートがオブジェクトの場合、データ配列を探す
                items = data.get('data', data.get('items', data.get('shelters', [])))
            elif isinstance(data, list):
                items = data
            else:
                logger.warning(f"Unexpected data format from {self.region_name}: {type(data)}")
                return []
            
            for i, item in enumerate(items[:100]):  # 最大100件まで
                try:
                    shelter = self._parse_shelter_item(item, i)
                    if shelter:
                        shelters.append(shelter)
                except Exception as e:
                    logger.debug(f"Failed to parse shelter item {i} from {self.region_name}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to parse {self.region_name} shelter data: {e}")
        
        return shelters
    
    def _parse_shelter_item(self, item: dict, index: int) -> Optional[ShelterData]:
        """個別の避難所アイテムをパース"""
        try:
            # 一般的な避難所データフィールドを推測してマッピング
            name_fields = ['name', 'facility_name', 'shelter_name', '施設名', '名称']
            address_fields = ['address', 'location', 'address_text', '住所', '所在地']
            lat_fields = ['latitude', 'lat', 'y', '緯度']
            lon_fields = ['longitude', 'lng', 'lon', 'x', '経度']
            
            # 名前を取得
            name = None
            for field in name_fields:
                if field in item and item[field]:
                    name = str(item[field])
                    break
            
            if not name:
                name = f"{self.region_name}_shelter_{index + 1}"
            
            # 住所を取得
            address = None
            for field in address_fields:
                if field in item and item[field]:
                    address = str(item[field])
                    break
            
            # 座標を取得
            latitude = None
            longitude = None
            
            for field in lat_fields:
                if field in item and item[field]:
                    try:
                        latitude = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            for field in lon_fields:
                if field in item and item[field]:
                    try:
                        longitude = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # 座標がない場合はスキップ
            if latitude is None or longitude is None:
                logger.debug(f"Skipping {name} - no valid coordinates")
                return None
            
            # ShelterDataオブジェクトを作成
            shelter = ShelterData(
                id=f"{self.region_name}_{index + 1}",
                name=name,
                address=address or "",
                latitude=latitude,
                longitude=longitude,
                shelter_type="evacuation_shelter",
                capacity=item.get('capacity', 0),
                facilities=self._extract_facilities(item),
                contact=item.get('contact', item.get('phone', "")),
                status="active",
                source=f"{self.region_name}_api"
            )
            
            return shelter
            
        except Exception as e:
            logger.debug(f"Failed to parse shelter item: {e}")
            return None
    
    def _extract_facilities(self, item: dict) -> List[str]:
        """施設情報を抽出"""
        facilities = []
        
        # 一般的な施設情報フィールド
        facility_fields = ['facilities', 'amenities', 'equipment', '設備', '施設']
        
        for field in facility_fields:
            if field in item:
                value = item[field]
                if isinstance(value, list):
                    facilities.extend([str(f) for f in value])
                elif isinstance(value, str) and value:
                    facilities.append(value)
        
        # デフォルト施設
        if not facilities:
            facilities = ["shelter"]
        
        return facilities




class NationwideDataCollector:
    """全国データ収集統合クラス"""
    
    def __init__(self):
        self.municipal_clients: Dict[str, MunicipalAPIClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """自治体APIクライアントを初期化"""
        # 設定ファイルから自治体API設定を読み込み
        municipal_apis = app_settings.government_api.get_municipal_apis()
        
        for region_name, api_config in municipal_apis.items():
            if region_name != 'prefecture_apis':  # 県庁所在地APIは別途処理
                self.municipal_clients[region_name] = GenericMunicipalAPIClient(
                    region_name, api_config
                )
        
        # 県庁所在地API設定も追加
        prefecture_apis = municipal_apis.get('prefecture_apis', {})
        for region_name, api_config in prefecture_apis.items():
            self.municipal_clients[f"pref_{region_name}"] = GenericMunicipalAPIClient(
                f"pref_{region_name}", api_config
            )
        
        logger.info(f"Initialized {len(self.municipal_clients)} municipal API clients")
    
    async def fetch_nationwide_shelter_data(self, target_regions: List[str]) -> Dict[str, List[ShelterData]]:
        """全国の避難所データを取得"""
        results = {}
        
        for region in target_regions:
            try:
                shelters = await self._fetch_region_shelters(region)
                if shelters:
                    results[region] = shelters
                    logger.info(f"Collected {len(shelters)} shelters from {region}")
                else:
                    logger.debug(f"No shelter data available for {region}")
                    
            except Exception as e:
                logger.error(f"Failed to collect shelter data for {region}: {e}")
                results[region] = []
        
        total_shelters = sum(len(shelters) for shelters in results.values())
        logger.info(f"Total nationwide shelters collected: {total_shelters}")
        
        return results
    
    async def _fetch_region_shelters(self, region: str) -> List[ShelterData]:
        """地域別の避難所データ取得"""
        
        # 東京都は既存のTokyoOpenDataClientを使用
        if region == "tokyo":
            # This will be handled by the existing Tokyo API integration
            return []
        
        # 直接の地域名でクライアントを検索
        client = self.municipal_clients.get(region)
        if client:
            return await client.fetch_shelter_data()
        
        # 県庁所在地APIクライアントも検索
        pref_client = self.municipal_clients.get(f"pref_{region}")
        if pref_client:
            return await pref_client.fetch_shelter_data()
        
        # その他の地域は今後実装予定
        # 現在はGSI（国土地理院）のデータを使用する可能性もある
        return await self._fetch_gsi_shelter_data(region)
    
    async def _fetch_gsi_shelter_data(self, region: str) -> List[ShelterData]:
        """GSI（国土地理院）から避難所データを取得（フォールバック）"""
        try:
            # GSI避難所データAPI（仮想）
            # 実際のGSI APIの仕様に合わせて実装
            logger.debug(f"Attempting to fetch GSI shelter data for {region}")
            
            # 現在は実装されていないため、空のリストを返す
            # 将来的にはGSIのタイル形式データまたはGeoJSONを取得・解析
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch GSI shelter data for {region}: {e}")
            return []
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """API統計情報を取得"""
        total_clients = len(self.municipal_clients)
        enabled_clients = sum(1 for client in self.municipal_clients.values() if client.enabled)
        
        return {
            "total_api_clients": total_clients,
            "enabled_api_clients": enabled_clients,
            "disabled_api_clients": total_clients - enabled_clients,
            "enabled_regions": [name for name, client in self.municipal_clients.items() if client.enabled],
            "planned_regions": [name for name, client in self.municipal_clients.items() if not client.enabled]
        }
    
    def get_supported_regions(self) -> List[str]:
        """サポート済み地域のリスト取得"""
        supported = ["tokyo"]  # 東京都は既存実装でサポート済み
        
        for region, client in self.municipal_clients.items():
            if client.enabled:
                supported.append(region)
        
        return supported
    
    def get_planned_regions(self) -> List[str]:
        """実装予定地域のリスト取得"""
        return [region for region, client in self.municipal_clients.items() 
                if not client.enabled]


# Global instance
nationwide_data_collector = NationwideDataCollector()