"""
API Manager Service
政府・自治体API管理サービス

This service manages the lifecycle of government API integrations,
including health monitoring, rate limiting, and data collection scheduling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager

from ..collectors.government_api_integration import (
    GovernmentAPIIntegrator, DataSourceType, APIStatus
)
from ..schemas.api_schemas import (
    APIHealthCheck, APIUsageStats, DataCollectionJob, 
    DataCollectionResult, APIConfiguration, ShelterDataRequest,
    BatchShelterResponse, EnhancedShelterData, DataQualityMetrics
)
from ..schemas.shelter import ShelterBase as ShelterData
from ..utils.ttl_cache import TTLCache
from ..config.app_settings import app_settings

logger = logging.getLogger(__name__)
settings = app_settings


class RateLimiter:
    """Rate limiting for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests: List[datetime] = []
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        async with self._lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            if len(self.requests) >= self.requests_per_minute:
                # Calculate wait time until oldest request expires
                oldest_request = min(self.requests)
                wait_until = oldest_request + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"Rate limit reached, waiting {wait_seconds:.2f} seconds")
                    await asyncio.sleep(wait_seconds)
            
            self.requests.append(now)


class APIManagerService:
    """Service for managing government API integrations"""
    
    def __init__(self):
        self.integrator: Optional[GovernmentAPIIntegrator] = None
        self.health_cache = TTLCache(name="api_health", default_ttl_seconds=300)  # 5 minutes
        self.usage_stats: Dict[DataSourceType, APIUsageStats] = {}
        self.rate_limiters: Dict[DataSourceType, RateLimiter] = {}
        self.collection_jobs: Dict[str, DataCollectionJob] = {}
        self.quality_metrics: Dict[DataSourceType, DataQualityMetrics] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Initialize rate limiters
        self._initialize_rate_limiters()
        
        # Initialize usage stats
        self._initialize_usage_stats()
    
    def _initialize_rate_limiters(self):
        """Initialize rate limiters for each data source"""
        rate_limits = {
            DataSourceType.GSI_SHELTER_GEOJSON: 60,  # 60 requests per minute
            DataSourceType.GSI_ELEVATION: 60,
            DataSourceType.GSI_HAZARD: 30,
            DataSourceType.CABINET_OFFICE: 30,
            DataSourceType.FDMA: 30
        }
        
        for source, limit in rate_limits.items():
            self.rate_limiters[source] = RateLimiter(limit)
    
    def _initialize_usage_stats(self):
        """Initialize usage statistics tracking"""
        for source in DataSourceType:
            self.usage_stats[source] = APIUsageStats(
                source=source,
                requests_today=0,
                requests_this_hour=0,
                success_rate=1.0,
                average_response_time=0.0
            )
    
    async def start(self):
        """Start the API manager service"""
        if self._running:
            return
        
        logger.info("Starting API Manager Service")
        self._running = True
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("API Manager Service started successfully")
    
    async def stop(self):
        """Stop the API manager service"""
        if not self._running:
            return
        
        logger.info("Stopping API Manager Service")
        self._running = False
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Close integrator if open
        if self.integrator:
            await self.integrator.__aexit__(None, None, None)
        
        logger.info("API Manager Service stopped")
    
    @asynccontextmanager
    async def get_integrator(self):
        """Get API integrator with proper lifecycle management"""
        if not self.integrator:
            self.integrator = GovernmentAPIIntegrator()
            await self.integrator.__aenter__()
        
        try:
            yield self.integrator
        finally:
            # Keep integrator alive for reuse
            pass
    
    async def fetch_enhanced_shelter_data(self, request: ShelterDataRequest) -> BatchShelterResponse:
        """Fetch enhanced shelter data from multiple sources"""
        start_time = datetime.now()
        
        # Apply rate limiting
        for source in DataSourceType:
            if source in self.rate_limiters:
                await self.rate_limiters[source].wait_if_needed()
        
        async with self.get_integrator() as integrator:
            try:
                # Fetch basic shelter data
                shelters = await integrator.fetch_shelter_data(request.region)
                
                # Enhance with elevation data if requested
                if request.include_elevation and shelters:
                    coordinates = [(s.longitude, s.latitude) for s in shelters]
                    elevation_data = await integrator.fetch_elevation_data(coordinates)
                    
                    for shelter in shelters:
                        coord_key = (shelter.longitude, shelter.latitude)
                        if coord_key in elevation_data:
                            shelter.elevation_data = elevation_data[coord_key]
                
                # Enhance with hazard information if requested
                if request.include_hazard_info and shelters:
                    hazard_data = await integrator.fetch_hazard_data(
                        request.region, "flood"  # Default to flood hazard
                    )
                    
                    for shelter in shelters:
                        if hazard_data:
                            shelter.hazard_info = [hazard_data]
                
                # Convert to enhanced shelter data
                enhanced_shelters = []
                for shelter in shelters:
                    enhanced = EnhancedShelterData(
                        **shelter.dict(),
                        data_sources=[DataSourceType.GSI_SHELTER_GEOJSON],
                        last_verified=datetime.now(),
                        confidence_score=self._calculate_confidence_score(shelter)
                    )
                    enhanced_shelters.append(enhanced)
                
                # Get health status
                health_status = await integrator.health_check_all()
                
                # Update usage statistics
                self._update_usage_stats(DataSourceType.GSI_SHELTER_GEOJSON, True, 
                                       (datetime.now() - start_time).total_seconds())
                
                return BatchShelterResponse(
                    shelters=enhanced_shelters,
                    total_count=len(enhanced_shelters),
                    data_sources_used=[DataSourceType.GSI_SHELTER_GEOJSON],
                    collection_time=datetime.now(),
                    cache_status={},
                    health_status=health_status
                )
            
            except Exception as e:
                logger.error(f"Error fetching enhanced shelter data: {e}")
                
                # Update usage statistics for failure
                self._update_usage_stats(DataSourceType.GSI_SHELTER_GEOJSON, False, 
                                       (datetime.now() - start_time).total_seconds())
                
                # Return empty response with error info
                return BatchShelterResponse(
                    shelters=[],
                    total_count=0,
                    data_sources_used=[],
                    collection_time=datetime.now(),
                    cache_status={},
                    health_status={DataSourceType.GSI_SHELTER_GEOJSON: APIStatus.UNHEALTHY}
                )
    
    async def get_api_health_status(self, force_refresh: bool = False) -> Dict[DataSourceType, APIHealthCheck]:
        """Get health status of all APIs"""
        cache_key = "api_health_status"
        
        if not force_refresh:
            cached_status = self.health_cache.get(cache_key)
            if cached_status:
                return cached_status
        
        health_checks = {}
        
        async with self.get_integrator() as integrator:
            health_status = await integrator.health_check_all()
            
            for source, status in health_status.items():
                health_checks[source] = APIHealthCheck(
                    source=source,
                    status=status,
                    last_check=datetime.now(),
                    endpoints_tested=[f"{source.value}_api"]
                )
        
        # Cache the results
        self.health_cache.set(cache_key, health_checks)
        
        return health_checks
    
    async def get_usage_statistics(self) -> Dict[DataSourceType, APIUsageStats]:
        """Get API usage statistics"""
        return self.usage_stats.copy()
    
    async def get_data_quality_metrics(self) -> Dict[DataSourceType, DataQualityMetrics]:
        """Get data quality metrics"""
        return self.quality_metrics.copy()
    
    def add_collection_job(self, job: DataCollectionJob):
        """Add a data collection job"""
        self.collection_jobs[job.job_id] = job
        logger.info(f"Added collection job: {job.job_id}")
    
    def remove_collection_job(self, job_id: str) -> bool:
        """Remove a data collection job"""
        if job_id in self.collection_jobs:
            del self.collection_jobs[job_id]
            logger.info(f"Removed collection job: {job_id}")
            return True
        return False
    
    def get_collection_jobs(self) -> List[DataCollectionJob]:
        """Get all collection jobs"""
        return list(self.collection_jobs.values())
    
    async def _health_check_loop(self):
        """Background task for periodic health checks"""
        while self._running:
            try:
                await self.get_api_health_status(force_refresh=True)
                logger.debug("Health check completed")
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            
            # Wait 5 minutes between health checks
            await asyncio.sleep(300)
    
    async def _scheduler_loop(self):
        """Background task for scheduled data collection"""
        while self._running:
            try:
                current_time = datetime.now()
                
                for job in self.collection_jobs.values():
                    if not job.enabled:
                        continue
                    
                    if self._should_run_job(job, current_time):
                        asyncio.create_task(self._execute_collection_job(job))
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            # Check every minute
            await asyncio.sleep(60)
    
    def _should_run_job(self, job: DataCollectionJob, current_time: datetime) -> bool:
        """Check if a job should be run"""
        # Simple implementation - could be enhanced with proper cron parsing
        if job.next_run is None:
            return True
        
        return current_time >= job.next_run
    
    async def _execute_collection_job(self, job: DataCollectionJob):
        """Execute a data collection job"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing collection job: {job.job_id}")
            
            # Update job status
            job.last_run = start_time
            job.next_run = self._calculate_next_run(job, start_time)
            
            results = []
            
            for source in job.sources:
                result = await self._collect_data_from_source(source, job)
                results.append(result)
            
            # Update success count
            job.success_count += 1
            
            logger.info(f"Collection job completed: {job.job_id}")
            
        except Exception as e:
            job.failure_count += 1
            logger.error(f"Collection job failed: {job.job_id}, error: {e}")
    
    async def _collect_data_from_source(self, source: DataSourceType, job: DataCollectionJob) -> DataCollectionResult:
        """Collect data from a specific source"""
        start_time = datetime.now()
        
        try:
            # Apply rate limiting
            if source in self.rate_limiters:
                await self.rate_limiters[source].wait_if_needed()
            
            records_collected = 0
            records_updated = 0
            
            # Implementation depends on the job type
            if job.job_type == "shelter_data":
                async with self.get_integrator() as integrator:
                    shelters = await integrator.fetch_shelter_data("tokyo")
                    records_collected = len(shelters)
                    # Here you would typically save to database
                    records_updated = records_collected
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update usage statistics
            self._update_usage_stats(source, True, duration)
            
            return DataCollectionResult(
                job_id=job.job_id,
                source=source,
                status="success",
                records_collected=records_collected,
                records_updated=records_updated,
                records_failed=0,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration
            )
        
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update usage statistics for failure
            self._update_usage_stats(source, False, duration)
            
            return DataCollectionResult(
                job_id=job.job_id,
                source=source,
                status="failed",
                records_collected=0,
                records_updated=0,
                records_failed=1,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                error_details=[str(e)]
            )
    
    def _calculate_next_run(self, job: DataCollectionJob, current_time: datetime) -> datetime:
        """Calculate next run time for a job"""
        # Simple implementation - add 1 hour
        # In a real implementation, you'd parse the cron schedule
        return current_time + timedelta(hours=1)
    
    def _update_usage_stats(self, source: DataSourceType, success: bool, response_time: float):
        """Update usage statistics"""
        if source not in self.usage_stats:
            return
        
        stats = self.usage_stats[source]
        now = datetime.now()
        
        # Reset counters if needed
        if now.date() > stats.last_reset.date():
            stats.requests_today = 0
        
        if now.hour != stats.last_reset.hour:
            stats.requests_this_hour = 0
        
        # Update counters
        stats.requests_today += 1
        stats.requests_this_hour += 1
        
        # Update success rate (simple moving average)
        current_success_rate = 1.0 if success else 0.0
        stats.success_rate = (stats.success_rate * 0.9) + (current_success_rate * 0.1)
        
        # Update average response time
        stats.average_response_time = (stats.average_response_time * 0.9) + (response_time * 0.1)
        
        stats.last_reset = now
    
    def _calculate_confidence_score(self, shelter: ShelterData) -> float:
        """Calculate confidence score for shelter data"""
        score = 1.0
        
        # Reduce score based on missing information
        if not shelter.address:
            score -= 0.1
        if not shelter.facilities:
            score -= 0.1
        if not shelter.contact:
            score -= 0.1
        if not shelter.capacity:
            score -= 0.1
        
        return max(0.0, score)


# Global service instance
api_manager_service = APIManagerService()