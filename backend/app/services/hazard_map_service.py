"""Hazard map service for fetching and analyzing GSI hazard data."""

import asyncio
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import httpx
import ssl
from PIL import Image
import io
import logging

from app.schemas.hazard import (
    HazardType, HazardLevel, HazardDetail, HazardInfo, Location
)
from app.db.firestore_client import get_db
from app.config import app_settings

logger = logging.getLogger(__name__)


class HazardMapService:
    """Service for fetching and analyzing hazard map data from GSI."""
    
    BASE_URL = "https://disaportaldata.gsi.go.jp/raster"
    
    # Dataset codes for different hazard types
    DATASET_CODES = {
        HazardType.TSUNAMI: "04_tsunami_newlegend_data",
        HazardType.FLOOD: "01_flood_l2_shinsuishin_kuni_data",
        HazardType.HIGH_TIDE: "03_hightide_l2_shinsuishin_data",
        HazardType.LANDSLIDE: "05_dosekiryukiki",
    }
    
    # Color to depth mapping for tsunami (in meters)
    TSUNAMI_DEPTH_COLORS = {
        (220, 122, 220): 0.3,   # Light purple: < 0.3m
        (255, 145, 255): 1.0,   # Pink: 0.3-1.0m
        (255, 183, 255): 2.0,   # Light pink: 1.0-2.0m
        (255, 216, 192): 3.0,   # Light orange: 2.0-3.0m
        (255, 183, 0): 5.0,     # Orange: 3.0-5.0m
        (255, 145, 0): 10.0,    # Dark orange: 5.0-10.0m
        (255, 0, 0): 20.0       # Red: > 10.0m
    }
    
    # Color to depth mapping for flood (in meters)
    FLOOD_DEPTH_COLORS = {
        (247, 245, 169): 0.5,   # Light yellow: < 0.5m
        (255, 216, 192): 1.0,   # Light orange: 0.5-1.0m
        (255, 183, 183): 3.0,   # Light red: 1.0-3.0m
        (255, 145, 145): 5.0,   # Pink: 3.0-5.0m
        (255, 0, 0): 10.0,      # Red: 5.0-10.0m
        (220, 122, 220): 20.0   # Purple: > 10.0m
    }
    
    def __init__(self):
        """Initialize the hazard map service."""
        # Create SSL context for GSI connections
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
        # Use safer SSL option for compatibility
        try:
            ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        except AttributeError:
            # Fallback for newer Python versions where this option is removed
            pass
        
        self.client = httpx.AsyncClient(timeout=30.0, verify=ssl_context)
        self.firestore_db = get_db()
        self.cache_collection = self.firestore_db.collection("hazard_cache")
        
    def _lon_to_tile_x(self, lon: float, zoom: int) -> int:
        """Convert longitude to tile X coordinate."""
        return int((lon + 180.0) / 360.0 * (2 ** zoom))
    
    def _lat_to_tile_y(self, lat: float, zoom: int) -> int:
        """Convert latitude to tile Y coordinate."""
        lat_rad = math.radians(lat)
        return int((1.0 - math.log(math.tan(lat_rad) + 
                   1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * (2 ** zoom))
    
    def _tile_to_pixel(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to pixel coordinates within a tile."""
        tile_x = self._lon_to_tile_x(lon, zoom)
        tile_y = self._lat_to_tile_y(lat, zoom)
        
        # Calculate position within tile (0-255)
        x_in_tile = ((lon + 180.0) / 360.0 * (2 ** zoom) - tile_x) * 256
        y_in_tile = ((1.0 - math.log(math.tan(math.radians(lat)) + 
                     1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * 
                     (2 ** zoom) - tile_y) * 256
        
        return int(x_in_tile), int(y_in_tile)
    
    def _get_closest_color(self, rgb: Tuple[int, int, int], 
                          color_map: Dict) -> Tuple[Optional[Tuple[int, int, int]], float]:
        """Find the closest matching color from the color map."""
        min_distance = float('inf')
        closest_color = None
        
        for color in color_map.keys():
            # Calculate Euclidean distance in RGB space
            distance = sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, color)) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_color = color
        
        # Threshold for color matching (adjust as needed)
        if min_distance > 50:
            return None, 0.0
            
        return closest_color, color_map[closest_color]
    
    def _depth_to_hazard_level(self, depth: float, hazard_type: HazardType) -> HazardLevel:
        """Convert depth to hazard level."""
        if hazard_type == HazardType.TSUNAMI:
            if depth >= 10.0:
                return HazardLevel.EXTREME
            elif depth >= 5.0:
                return HazardLevel.HIGH
            elif depth >= 2.0:
                return HazardLevel.MEDIUM
            elif depth >= 0.3:
                return HazardLevel.LOW
            else:
                return HazardLevel.NONE
        else:  # FLOOD and others
            if depth >= 5.0:
                return HazardLevel.EXTREME
            elif depth >= 3.0:
                return HazardLevel.HIGH
            elif depth >= 1.0:
                return HazardLevel.MEDIUM
            elif depth >= 0.5:
                return HazardLevel.LOW
            else:
                return HazardLevel.NONE
    
    def _generate_cache_key(self, location: Location, zoom: int) -> str:
        """Generate cache key for the location."""
        # Round to 3 decimal places (approximately 100m precision)
        lat = round(location.latitude, 3)
        lon = round(location.longitude, 3)
        return f"hazard_{lat}_{lon}_{zoom}"
    
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get cached hazard data."""
        try:
            doc = self.cache_collection.document(cache_key).get()
            if doc.exists:
                data = doc.to_dict()
                # Check if cache is still valid (30 days)
                if 'expires_at' in data:
                    expires_at = data['expires_at']
                    if expires_at > datetime.now(timezone.utc):
                        return data
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    async def _save_to_cache(self, cache_key: str, data: Dict):
        """Save hazard data to cache."""
        try:
            data['expires_at'] = datetime.now(timezone.utc) + timedelta(days=30)
            data['created_at'] = datetime.now(timezone.utc)
            self.cache_collection.document(cache_key).set(data)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    async def _fetch_tile(self, hazard_type: HazardType, zoom: int, 
                         x: int, y: int) -> Optional[bytes]:
        """Fetch a hazard map tile."""
        dataset = self.DATASET_CODES.get(hazard_type)
        if not dataset:
            return None
            
        url = f"{self.BASE_URL}/{dataset}/{zoom}/{x}/{y}.png"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"Tile fetch failed: {url} - {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching tile: {e}")
            return None
    
    async def _analyze_tile(self, tile_data: bytes, pixel_x: int, pixel_y: int, 
                           hazard_type: HazardType) -> Optional[HazardDetail]:
        """Analyze a specific pixel in the tile."""
        try:
            image = Image.open(io.BytesIO(tile_data))
            
            # Ensure we're within bounds
            if pixel_x >= image.width or pixel_y >= image.height:
                return None
            
            # Get pixel color (RGBA)
            pixel = image.getpixel((pixel_x, pixel_y))
            
            # Check for transparency or white (no hazard)
            if len(pixel) == 4 and pixel[3] == 0:  # Transparent
                return None
            if pixel[:3] == (255, 255, 255):  # White
                return None
            
            # Get appropriate color map
            if hazard_type == HazardType.TSUNAMI:
                color_map = self.TSUNAMI_DEPTH_COLORS
            elif hazard_type == HazardType.FLOOD:
                color_map = self.FLOOD_DEPTH_COLORS
            else:
                # For other hazard types, use a simple presence check
                return HazardDetail(
                    hazard_type=hazard_type,
                    level=HazardLevel.MEDIUM,
                    depth=None,
                    description=f"{hazard_type.value} hazard detected",
                    source="GSI Hazard Map",
                    updated_at=datetime.now(timezone.utc)
                )
            
            # Find closest matching color
            matched_color, depth = self._get_closest_color(pixel[:3], color_map)
            
            if matched_color is None:
                return None
            
            # Create hazard detail
            level = self._depth_to_hazard_level(depth, hazard_type)
            
            return HazardDetail(
                hazard_type=hazard_type,
                level=level,
                depth=depth,
                description=self._generate_description(hazard_type, depth),
                source="GSI Hazard Map",
                updated_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing tile: {e}")
            return None
    
    def _generate_description(self, hazard_type: HazardType, depth: float) -> str:
        """Generate human-readable description."""
        if hazard_type == HazardType.TSUNAMI:
            if depth >= 10.0:
                return f"Extreme tsunami risk - expected depth over {depth}m"
            elif depth >= 5.0:
                return f"High tsunami risk - expected depth {depth}m"
            elif depth >= 2.0:
                return f"Moderate tsunami risk - expected depth {depth}m"
            else:
                return f"Low tsunami risk - expected depth {depth}m"
        elif hazard_type == HazardType.FLOOD:
            if depth >= 5.0:
                return f"Extreme flood risk - expected depth over {depth}m"
            elif depth >= 3.0:
                return f"High flood risk - expected depth {depth}m"
            elif depth >= 1.0:
                return f"Moderate flood risk - expected depth {depth}m"
            else:
                return f"Low flood risk - expected depth {depth}m"
        else:
            return f"{hazard_type.value} hazard detected"
    
    def _calculate_overall_risk(self, hazards: List[HazardDetail]) -> HazardLevel:
        """Calculate overall risk level from multiple hazards."""
        if not hazards:
            return HazardLevel.NONE
            
        # Take the highest risk level
        max_level = HazardLevel.NONE
        for hazard in hazards:
            if hazard.level.value > max_level.value:
                max_level = hazard.level
                
        return max_level
    
    async def get_hazard_info(self, location: Location, 
                             hazard_types: Optional[List[HazardType]] = None,
                             zoom_level: int = 16) -> HazardInfo:
        """Get hazard information for a specific location."""
        # Default to checking tsunami and flood
        if hazard_types is None:
            hazard_types = [HazardType.TSUNAMI, HazardType.FLOOD]
        
        # Check cache first
        cache_key = self._generate_cache_key(location, zoom_level)
        cached = await self._get_cached_data(cache_key)
        if cached:
            # Convert cached data back to HazardInfo
            return HazardInfo(
                location=location,
                hazards=[HazardDetail(**h) for h in cached['hazards']],
                overall_risk_level=HazardLevel(cached['overall_risk_level']),
                tile_coordinates=cached['tile_coordinates'],  # Already Dict[str, Any]
                analyzed_at=cached['analyzed_at'],
                cache_key=cache_key
            )
        
        # Calculate tile coordinates
        tile_x = self._lon_to_tile_x(location.longitude, zoom_level)
        tile_y = self._lat_to_tile_y(location.latitude, zoom_level)
        pixel_x, pixel_y = self._tile_to_pixel(
            location.latitude, location.longitude, zoom_level
        )
        
        # Fetch and analyze tiles for each hazard type
        hazards = []
        tile_coords = {
            "zoom": zoom_level,
            "x": tile_x,
            "y": tile_y,
            "pixel_x": pixel_x,
            "pixel_y": pixel_y
        }
        
        # Process hazard types in parallel
        tasks = []
        for hazard_type in hazard_types:
            tasks.append(self._process_hazard_type(
                hazard_type, zoom_level, tile_x, tile_y, pixel_x, pixel_y
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, HazardDetail):
                hazards.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error processing hazard: {result}")
        
        # Create hazard info
        hazard_info = HazardInfo(
            location=location,
            hazards=hazards,
            overall_risk_level=self._calculate_overall_risk(hazards),
            tile_coordinates=tile_coords,  # This is Dict[str, Any] as expected
            analyzed_at=datetime.now(timezone.utc),
            cache_key=cache_key
        )
        
        # Save to cache
        cache_data = {
            'hazards': [h.dict() for h in hazards],
            'overall_risk_level': hazard_info.overall_risk_level.value,
            'tile_coordinates': tile_coords,
            'analyzed_at': hazard_info.analyzed_at
        }
        await self._save_to_cache(cache_key, cache_data)
        
        return hazard_info
    
    async def _process_hazard_type(self, hazard_type: HazardType, zoom: int,
                                  tile_x: int, tile_y: int, 
                                  pixel_x: int, pixel_y: int) -> Optional[HazardDetail]:
        """Process a single hazard type."""
        tile_data = await self._fetch_tile(hazard_type, zoom, tile_x, tile_y)
        if tile_data:
            return await self._analyze_tile(tile_data, pixel_x, pixel_y, hazard_type)
        return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()