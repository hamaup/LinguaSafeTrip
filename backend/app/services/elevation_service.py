"""Elevation data service for fetching altitude information from GSI."""

import asyncio
import logging
import math
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import httpx
import ssl
from asyncio import Semaphore

from app.schemas.hazard import Location
from app.db.firestore_client import get_db
from app.config import app_settings

logger = logging.getLogger(__name__)


class ElevationService:
    """Service for fetching elevation data from GSI (Geospatial Information Authority of Japan)."""
    
    ELEVATION_API_URL = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
    
    def __init__(self):
        """Initialize the elevation service."""
        # Create SSL context for GSI connections
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
        # Use safer SSL option for compatibility
        try:
            ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        except AttributeError:
            # Fallback for newer Python versions where this option is removed
            pass
        
        self.client = httpx.AsyncClient(timeout=10.0, verify=ssl_context)
        self.firestore_db = get_db()
        self.cache_collection = self.firestore_db.collection("elevation_cache")
        # Rate limiter: 1 request per second as per GSI API requirements
        self.rate_limiter = Semaphore(1)
        self._last_request_time = 0
        
    def _generate_cache_key(self, location: Location) -> str:
        """Generate cache key for elevation data."""
        # Round to 4 decimal places (approximately 10m precision)
        lat = round(location.latitude, 4)
        lon = round(location.longitude, 4)
        return f"elevation_{lat}_{lon}"
    
    async def _get_cached_elevation(self, location: Location) -> Optional[float]:
        """Get cached elevation data."""
        try:
            cache_key = self._generate_cache_key(location)
            doc = self.cache_collection.document(cache_key).get()
            
            if doc.exists:
                data = doc.to_dict()
                # Elevation data doesn't change, so we use a long cache period (30 days)
                if 'expires_at' in data and data['expires_at'] > datetime.now(timezone.utc):
                    return data.get('elevation')
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    async def _save_to_cache(self, location: Location, elevation: float):
        """Save elevation data to cache."""
        try:
            cache_key = self._generate_cache_key(location)
            data = {
                'elevation': elevation,
                'location': {
                    'latitude': location.latitude,
                    'longitude': location.longitude
                },
                'created_at': datetime.now(timezone.utc),
                'expires_at': datetime.now(timezone.utc) + timedelta(days=30)
            }
            self.cache_collection.document(cache_key).set(data)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    async def _call_elevation_api(self, location: Location) -> float:
        """Call the GSI elevation API with rate limiting."""
        async with self.rate_limiter:
            # Ensure at least 1 second between requests
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < 1.0:
                await asyncio.sleep(1.0 - time_since_last)
            
            try:
                params = {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'outtype': 'JSON'
                }
                
                response = await self.client.get(self.ELEVATION_API_URL, params=params)
                self._last_request_time = asyncio.get_event_loop().time()
                
                if response.status_code == 200:
                    data = response.json()
                    # GSI API returns elevation in 'elevation' field
                    elevation = data.get('elevation')
                    
                    if elevation is None or elevation == "-----":
                        # No data available for this location (e.g., ocean)
                        return 0.0
                    
                    return float(elevation)
                else:
                    logger.error(f"Elevation API error: {response.status_code}")
                    raise Exception(f"API returned status {response.status_code}")
                    
            except httpx.RequestError as e:
                logger.error(f"Request error calling elevation API: {e}")
                raise
            except Exception as e:
                logger.error(f"Error parsing elevation data: {e}")
                raise
    
    async def get_elevation(self, location: Location) -> float:
        """
        Get elevation for a specific location.
        
        Args:
            location: Location object with latitude and longitude
            
        Returns:
            Elevation in meters above sea level
        """
        # Check cache first
        cached_elevation = await self._get_cached_elevation(location)
        if cached_elevation is not None:
            return cached_elevation
        
        # Call API if not in cache
        try:
            elevation = await self._call_elevation_api(location)
            
            # Save to cache
            await self._save_to_cache(location, elevation)
            
            return elevation
            
        except Exception as e:
            logger.error(f"Failed to get elevation for {location.latitude}, {location.longitude}: {e}")
            # Return a default value instead of failing completely
            return 0.0
    
    async def get_elevations_batch(self, locations: list[Location]) -> Dict[str, float]:
        """
        Get elevations for multiple locations with rate limiting.
        
        Args:
            locations: List of Location objects
            
        Returns:
            Dictionary mapping location string to elevation
        """
        results = {}
        
        for location in locations:
            try:
                elevation = await self.get_elevation(location)
                location_key = f"{location.latitude},{location.longitude}"
                results[location_key] = elevation
            except Exception as e:
                logger.error(f"Failed to get elevation for location: {e}")
                location_key = f"{location.latitude},{location.longitude}"
                results[location_key] = 0.0
        
        return results
    
    async def get_grid_elevations(self, center: Location, grid_size_km: float = 1.0, 
                                 grid_points: int = 5) -> Dict[str, float]:
        """
        Get elevations for a grid around a center point.
        Useful for pre-caching elevation data for an area.
        
        Args:
            center: Center location
            grid_size_km: Distance between grid points in kilometers
            grid_points: Number of points in each direction (total = grid_points^2)
            
        Returns:
            Dictionary of elevations for the grid
        """
        # Approximate degrees per kilometer
        km_per_degree_lat = 111.0
        km_per_degree_lon = 111.0 * abs(math.cos(math.radians(center.latitude)))
        
        # Calculate grid
        locations = []
        half_grid = grid_points // 2
        
        for i in range(-half_grid, half_grid + 1):
            for j in range(-half_grid, half_grid + 1):
                lat_offset = (i * grid_size_km) / km_per_degree_lat
                lon_offset = (j * grid_size_km) / km_per_degree_lon
                
                grid_location = Location(
                    latitude=center.latitude + lat_offset,
                    longitude=center.longitude + lon_offset
                )
                locations.append(grid_location)
        
        return await self.get_elevations_batch(locations)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()