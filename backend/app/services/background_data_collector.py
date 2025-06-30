"""
Background Data Collector Service
バックグラウンドデータ収集サービス

This service runs background tasks to periodically collect and cache
government API data for improved response times.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from ..collectors.government_api_integration import GovernmentAPIIntegrator, DataSourceType
from ..services.cache_service import cache_service, CacheType
from ..schemas.api_schemas import ShelterDataRequest, APIStatus
from ..config.app_settings import app_settings

logger = logging.getLogger(__name__)


@dataclass
class CollectionSchedule:
    """Data collection schedule configuration"""
    cache_type: CacheType
    data_source: DataSourceType
    interval_minutes: int
    regions: List[str]
    last_run: Optional[datetime] = None
    enabled: bool = True


class BackgroundDataCollector:
    """Background service for periodic data collection"""
    
    def __init__(self):
        self.running = False
        self.tasks: Set[asyncio.Task] = set()
        self.schedules = self._configure_schedules()
        self.integrator: Optional[GovernmentAPIIntegrator] = None
        
    def _configure_schedules(self) -> List[CollectionSchedule]:
        """Configure data collection schedules from app settings"""
        gov_config = app_settings.government_api
        
        return [
            # 全国避難所データ（GSI GeoJSON） - 設定ファイルから間隔取得
            CollectionSchedule(
                cache_type=CacheType.GOV_API_SHELTER,
                data_source=DataSourceType.GSI_SHELTER_GEOJSON,
                interval_minutes=gov_config.collection_intervals["shelter_data"],
                regions=["nationwide"]  # 全国一括データ
            ),
            
            # GSI標高データ（全国主要地点） - 設定ファイルから間隔取得
            CollectionSchedule(
                cache_type=CacheType.GOV_API_ELEVATION,
                data_source=DataSourceType.GSI_ELEVATION,
                interval_minutes=gov_config.collection_intervals["elevation_data"],
                regions=gov_config.target_regions  # 全国対応
            ),
            
            # GSIハザードマップ（全国） - タイル情報収集に変更
            CollectionSchedule(
                cache_type=CacheType.GOV_API_HAZARD,
                data_source=DataSourceType.GSI_HAZARD,
                interval_minutes=gov_config.collection_intervals["hazard_data"],
                regions=gov_config.target_regions,  # 全国対応
                enabled=True  # タイル情報収集として有効化
            )
            
        ]
    
    async def start(self):
        """Start background data collection"""
        if self.running:
            logger.warning("Background data collector is already running")
            return
            
        self.running = True
        logger.info("Starting background data collector")
        
        # Initialize API integrator
        self.integrator = GovernmentAPIIntegrator()
        await self.integrator.__aenter__()
        
        # Start collection tasks for each schedule
        for schedule in self.schedules:
            if schedule.enabled:
                task = asyncio.create_task(
                    self._collection_loop(schedule),
                    name=f"collect_{schedule.data_source.value}_{schedule.cache_type.value}"
                )
                self.tasks.add(task)
        
        logger.info(f"Started {len(self.tasks)} background collection tasks")
    
    async def stop(self):
        """Stop background data collection"""
        if not self.running:
            return
            
        logger.info("Stopping background data collector")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        
        # Close integrator
        if self.integrator:
            await self.integrator.__aexit__(None, None, None)
            self.integrator = None
        
        logger.info("Background data collector stopped")
    
    async def _collection_loop(self, schedule: CollectionSchedule):
        """Main collection loop for a specific schedule"""
        logger.info(f"Started collection loop for {schedule.data_source.value} (interval: {schedule.interval_minutes} minutes)")
        
        while self.running:
            try:
                # Check if it's time to collect
                if self._should_collect(schedule):
                    await self._collect_data(schedule)
                    schedule.last_run = datetime.now()
                
                # Sleep for collection interval or minimum 1 hour to reduce frequent checks
                sleep_minutes = max(60, schedule.interval_minutes // 10)  # Sleep for 1/10 of interval or minimum 1 hour
                logger.debug(f"Next check for {schedule.data_source.value} in {sleep_minutes} minutes")
                await asyncio.sleep(sleep_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info(f"Collection loop cancelled for {schedule.data_source.value}")
                break
            except Exception as e:
                logger.error(f"Error in collection loop for {schedule.data_source.value}: {e}")
                # Sleep longer on error to avoid spam
                await asyncio.sleep(3600)  # 1 hour on error
    
    def _should_collect(self, schedule: CollectionSchedule) -> bool:
        """Check if data should be collected for this schedule"""
        if not schedule.enabled:
            return False
            
        # 初回実行は起動から1時間後に遅延（API負荷軽減）
        if schedule.last_run is None:
            # 初回は実行しないが、last_runを現在時刻に設定して次回実行の基準とする
            schedule.last_run = datetime.now()
            logger.info(f"First run delayed for {schedule.data_source.value}, next check in {schedule.interval_minutes} minutes")
            return False
            
        time_since_last = datetime.now() - schedule.last_run
        return time_since_last >= timedelta(minutes=schedule.interval_minutes)
    
    async def _collect_data(self, schedule: CollectionSchedule):
        """Collect data for a specific schedule"""
        logger.info(f"Collecting data for {schedule.data_source.value}")
        
        try:
            if schedule.data_source == DataSourceType.GSI_SHELTER_GEOJSON:
                await self._collect_shelter_data(schedule)
            elif schedule.data_source == DataSourceType.GSI_ELEVATION:
                await self._collect_elevation_data(schedule)
            elif schedule.data_source == DataSourceType.GSI_HAZARD:
                await self._collect_hazard_data(schedule)
            
            logger.info(f"Successfully collected data for {schedule.data_source.value}")
            
        except Exception as e:
            logger.error(f"Failed to collect data for {schedule.data_source.value}: {e}")
    
    async def _collect_shelter_data(self, schedule: CollectionSchedule):
        """Collect shelter data from GSI GeoJSON API"""
        if not self.integrator:
            return
            
        try:
            # 全国避難所データを一括取得
            logger.info("Fetching nationwide shelter data from GSI GeoJSON...")
            shelters = await self.integrator.fetch_shelter_data("nationwide")
            
            if shelters:
                # Cache the data
                cache_params = {
                    "data_type": "nationwide_shelters",
                    "source": "gsi_geojson"
                }
                
                await cache_service.set(
                    cache_type=schedule.cache_type,
                    params=cache_params,
                    data=[shelter.dict() for shelter in shelters],
                    custom_ttl_minutes=43200  # 30日
                )
                
                logger.info(f"Cached {len(shelters)} shelters nationwide from GSI GeoJSON")
            else:
                logger.warning("No shelter data received from GSI GeoJSON API")
                
        except Exception as e:
            logger.error(f"Failed to collect nationwide shelter data: {e}")
            
        # レート制限（月1回なので制限緩く）
        await asyncio.sleep(10.0)  # 10秒待機
    
    async def _collect_elevation_data(self, schedule: CollectionSchedule):
        """Collect elevation data for major points nationwide"""
        if not self.integrator:
            return
            
        # Define major points for each region (全国対応)
        major_points = {
            # 関東地方
            "tokyo": [(139.691706, 35.689487), (139.699755, 35.658034), (139.634619, 35.449507)],
            "kanagawa": [(139.638189, 35.447507), (139.621922, 35.466797)],
            "saitama": [(139.623993, 35.861660), (139.656540, 35.852611)],
            "chiba": [(140.113682, 35.605057), (140.060608, 35.570830)],
            "ibaraki": [(140.446793, 36.341793), (140.373506, 36.083468)],
            "tochigi": [(139.883731, 36.565725), (139.698753, 36.371899)],
            "gunma": [(139.060406, 36.391203), (138.990831, 36.322762)],
            
            # 関西地方
            "osaka": [(135.502165, 34.693738), (135.494148, 34.702485)],
            "kyoto": [(135.768029, 35.011636), (135.759033, 35.021247)],
            "hyogo": [(135.183304, 34.691279), (134.690982, 34.919054)],
            "nara": [(135.832748, 34.692088), (135.804993, 34.679359)],
            "wakayama": [(135.167618, 34.226034), (135.209267, 34.225987)],
            "shiga": [(135.868605, 35.004531), (136.016555, 35.217716)],
            
            # 中部地方
            "aichi": [(136.881537, 35.183727), (136.906107, 35.170694)],
            "shizuoka": [(138.383084, 34.976987), (138.382777, 34.977322)],
            "gifu": [(136.722291, 35.391227), (136.757923, 35.423411)],
            "mie": [(136.508588, 34.730539), (136.521739, 34.721276)],
            "nagano": [(138.181239, 36.651295), (138.247095, 36.676431)],
            "yamanashi": [(138.568449, 35.664158), (138.606995, 35.691467)],
            "fukui": [(136.223640, 36.064180), (136.217688, 36.061463)],
            "ishikawa": [(136.625573, 36.594682), (136.637497, 36.571674)],
            "toyama": [(137.211338, 36.695270), (137.213749, 36.696259)],
            "niigata": [(139.023095, 37.916192), (139.036757, 37.902573)],
            
            # 九州地方
            "fukuoka": [(130.418297, 33.606576), (130.401716, 33.589886)],
            "saga": [(130.298822, 33.249442), (130.279437, 33.274607)],
            "nagasaki": [(129.873047, 32.744839), (129.869433, 32.757994)],
            "kumamoto": [(130.741904, 32.789827), (130.708218, 32.776409)],
            "oita": [(131.612619, 33.238172), (131.599861, 33.229694)],
            "miyazaki": [(131.423882, 31.911153), (131.420801, 31.908415)],
            "kagoshima": [(130.557724, 31.596554), (130.543427, 31.582132)],
            
            # 東北地方
            "sendai": [(140.869415, 38.268839), (140.882263, 38.260525)],
            "fukushima": [(140.467551, 37.750299), (140.478363, 37.754742)],
            "yamagata": [(140.363633, 38.240436), (140.331734, 38.253740)],
            "iwate": [(141.152716, 39.703531), (141.134567, 39.701592)],
            "aomori": [(140.740593, 40.824308), (140.775528, 40.813102)],
            "akita": [(140.102387, 39.718614), (140.115776, 39.717625)],
            
            # 北海道・沖縄
            "hokkaido": [(141.354469, 43.064171), (141.347899, 43.068896)],
            "okinawa": [(127.679245, 26.212401), (127.647362, 26.194247)],
            
            # その他主要都市
            "hiroshima": [(132.459622, 34.397844), (132.482147, 34.404615)],
            "okayama": [(133.934414, 34.661751), (133.918743, 34.655150)],
            "yamaguchi": [(131.471649, 34.185956), (131.476410, 34.186569)],
            "tokushima": [(134.559330, 34.075831), (134.543157, 34.077332)],
            "kagawa": [(134.043428, 34.340149), (134.048673, 34.339962)],
            "ehime": [(132.765681, 33.841624), (132.766045, 33.844270)],
            "kochi": [(133.531079, 33.559706), (133.548210, 33.560819)],
        }
        
        for region in schedule.regions:
            if region in major_points:
                coordinates = major_points[region]
                
                try:
                    # Fetch elevation data
                    elevation_data = await self.integrator.fetch_elevation_data(coordinates)
                    
                    if elevation_data:
                        # Cache the data
                        cache_params = {
                            "region": region,
                            "data_type": "elevation",
                            "coordinates": coordinates
                        }
                        
                        await cache_service.set(
                            cache_type=schedule.cache_type,
                            params=cache_params,
                            data=elevation_data
                        )
                        
                        logger.info(f"Cached elevation data for {len(elevation_data)} points in {region}")
                
                except Exception as e:
                    logger.error(f"Failed to collect elevation data for {region}: {e}")
    
    async def _collect_hazard_data(self, schedule: CollectionSchedule):
        """Collect hazard map data"""
        if not self.integrator:
            return
            
        hazard_types = ["flood", "tsunami", "landslide"]
        
        # 全国の主要地域でハザードデータを収集
        for region in schedule.regions:
            for hazard_type in hazard_types:
                try:
                    # Fetch hazard data
                    hazard_data = await self.integrator.fetch_hazard_data(region, hazard_type)
                    
                    if hazard_data:
                        # Cache the data
                        cache_params = {
                            "region": region,
                            "hazard_type": hazard_type,
                            "data_type": "hazard"
                        }
                        
                        await cache_service.set(
                            cache_type=schedule.cache_type,
                            params=cache_params,
                            data=hazard_data.dict()
                        )
                        
                        logger.info(f"Cached {hazard_type} hazard data for {region}")
                
                except Exception as e:
                    logger.error(f"Failed to collect {hazard_type} hazard data for {region}: {e}")
                    
                # 全国対応でレート制限を考慮した待機
                await asyncio.sleep(0.5)  # 0.5秒間隔でリクエスト
    
    async def _collect_health_data(self, schedule: CollectionSchedule):
        """Collect API health status"""
        if not self.integrator:
            return
            
        try:
            # Check health of all APIs
            health_status = await self.integrator.health_check_all()
            
            # Cache the health data
            cache_params = {
                "data_type": "api_health",
                "timestamp": datetime.now().isoformat()
            }
            
            # Convert status to dict for caching
            health_dict = {
                source.value: status.value 
                for source, status in health_status.items()
            }
            
            await cache_service.set(
                cache_type=schedule.cache_type,
                params=cache_params,
                data=health_dict,
                custom_ttl_minutes=5  # Short TTL for health data
            )
            
            logger.info(f"Cached health status for {len(health_status)} APIs")
            
        except Exception as e:
            logger.error(f"Failed to collect API health data: {e}")
    
    async def force_collection(self, data_source: Optional[DataSourceType] = None):
        """Force immediate data collection for specified source or all sources"""
        logger.info(f"Force collecting data for {data_source.value if data_source else 'all sources'}")
        
        schedules_to_run = self.schedules
        if data_source:
            schedules_to_run = [s for s in self.schedules if s.data_source == data_source]
        
        for schedule in schedules_to_run:
            if schedule.enabled:
                await self._collect_data(schedule)
                schedule.last_run = datetime.now()
    
    def get_collection_status(self) -> Dict:
        """Get status of background collection"""
        status = {
            "running": self.running,
            "active_tasks": len(self.tasks),
            "schedules": []
        }
        
        for schedule in self.schedules:
            schedule_status = {
                "data_source": schedule.data_source.value,
                "cache_type": schedule.cache_type.value,
                "interval_minutes": schedule.interval_minutes,
                "enabled": schedule.enabled,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "next_run": None
            }
            
            if schedule.last_run and schedule.enabled:
                next_run = schedule.last_run + timedelta(minutes=schedule.interval_minutes)
                schedule_status["next_run"] = next_run.isoformat()
            
            status["schedules"].append(schedule_status)
        
        return status


# Global service instance
background_data_collector = BackgroundDataCollector()