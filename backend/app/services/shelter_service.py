"""Service for managing shelter data and searches."""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
import math

from app.schemas.hazard import Shelter, Location
from app.schemas.api_schemas import ShelterDataRequest, DataSourceType
from app.db.firestore_client import get_db
from app.services.api_manager_service import api_manager_service
from app.collectors.government_api_integration import GovernmentAPIIntegrator

logger = logging.getLogger(__name__)


class ShelterService:
    """Service for shelter-related operations."""
    
    def __init__(self):
        """Initialize the shelter service."""
        self.firestore_db = get_db()
        self.shelters_collection = self.firestore_db.collection("shelters")
        self._government_data_enabled = True  # Enable government API integration
    
    async def search_nearby_shelters(self, location: Location, 
                                   radius_km: float = 5.0,
                                   limit: int = 50,
                                   include_government_data: bool = True) -> List[Shelter]:
        """
        Search for shelters within a radius of the given location.
        
        Args:
            location: Center location for search
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            include_government_data: Include data from government APIs
            
        Returns:
            List of shelters within the radius
        """
        try:
            nearby_shelters = []
            
            # First, try to get government API data if enabled
            if include_government_data and self._government_data_enabled:
                gov_shelters = await self._fetch_government_shelters(location, radius_km)
                nearby_shelters.extend(gov_shelters)
                logger.info(f"Found {len(gov_shelters)} shelters from government APIs")
            
            # If we don't have enough results, supplement with local data
            if len(nearby_shelters) < limit:
                local_shelters = await self._search_local_shelters(location, radius_km, limit - len(nearby_shelters))
                nearby_shelters.extend(local_shelters)
                logger.info(f"Added {len(local_shelters)} shelters from local data")
            
            # Sort by distance and limit results
            nearby_shelters.sort(key=lambda s: self._calculate_distance(location, s.location))
            return nearby_shelters[:limit]
            
        except Exception as e:
            logger.error(f"Error searching shelters: {e}")
            # Fallback to local data only
            return await self._search_local_shelters(location, radius_km, limit)
    
    async def get_shelter_by_id(self, shelter_id: str) -> Optional[Shelter]:
        """Get a specific shelter by ID."""
        try:
            doc = self.shelters_collection.document(shelter_id).get()
            
            if not doc.exists:
                return None
            
            shelter_data = doc.to_dict()
            return Shelter(
                id=doc.id,
                name=shelter_data.get('name', 'Unknown'),
                location=Location(
                    latitude=shelter_data.get('latitude', 0),
                    longitude=shelter_data.get('longitude', 0)
                ),
                capacity=shelter_data.get('capacity', 0),
                shelter_type=shelter_data.get('type'),
                facilities=shelter_data.get('facilities', [])
            )
            
        except Exception as e:
            logger.error(f"Error getting shelter {shelter_id}: {e}")
            return None
    
    async def _fetch_government_shelters(self, location: Location, radius_km: float) -> List[Shelter]:
        """Fetch shelter data from government APIs."""
        try:
            # Use GSI GeoJSON data for nationwide coverage
            async with GovernmentAPIIntegrator() as integrator:
                shelter_data_list = await integrator.fetch_shelter_data("nationwide")
                
                # Filter shelters within radius
                nearby_shelters = []
                for shelter_data in shelter_data_list:
                    shelter_location = Location(
                        latitude=shelter_data.location.latitude,
                        longitude=shelter_data.location.longitude
                    )
                    
                    distance = self._calculate_distance(location, shelter_location)
                    if distance <= radius_km:
                        shelter = Shelter(
                            id=getattr(shelter_data, 'id', f'gsi_{hash(shelter_data.name + str(shelter_data.location.latitude))}'),
                            name=shelter_data.name,
                            location=shelter_location,
                            capacity=shelter_data.capacity or 0,
                            shelter_type=','.join(shelter_data.disaster_types) if shelter_data.disaster_types else None,
                            facilities=[]  # ShelterBase doesn't have facilities field
                        )
                        nearby_shelters.append(shelter)
                
                return nearby_shelters
            
        except Exception as e:
            logger.warning(f"Failed to fetch government shelter data: {e}")
            # Fallback to API manager service
            try:
                region = self._determine_region(location)
                request = ShelterDataRequest(
                    region=region,
                    coordinates={
                        "longitude": location.longitude,
                        "latitude": location.latitude
                    },
                    radius_km=radius_km,
                    include_elevation=True,
                    include_hazard_info=True
                )
                
                response = await api_manager_service.fetch_enhanced_shelter_data(request)
                
                shelters = []
                for enhanced_shelter in response.shelters:
                    shelter = Shelter(
                        id=f"gov_{enhanced_shelter.id}",
                        name=enhanced_shelter.name,
                        location=Location(
                            latitude=enhanced_shelter.latitude,
                            longitude=enhanced_shelter.longitude
                        ),
                        capacity=enhanced_shelter.capacity or 0,
                        shelter_type=enhanced_shelter.shelter_type,
                        facilities=enhanced_shelter.facilities or []
                    )
                    shelters.append(shelter)
                
                return shelters
                
            except Exception as fallback_error:
                logger.error(f"Both primary and fallback shelter data fetch failed: {fallback_error}")
                return []
    
    async def _search_local_shelters(self, location: Location, radius_km: float, limit: int) -> List[Shelter]:
        """Search local Firestore shelter data."""
        try:
            # Get all shelters (in production, use geohashing for efficiency)
            shelters_ref = self.shelters_collection.limit(200)
            docs = shelters_ref.stream()
            
            nearby_shelters = []
            
            for doc in docs:
                shelter_data = doc.to_dict()
                shelter_location = Location(
                    latitude=shelter_data.get('latitude', 0),
                    longitude=shelter_data.get('longitude', 0)
                )
                
                # Calculate distance
                distance = self._calculate_distance(location, shelter_location)
                
                if distance <= radius_km:
                    shelter = Shelter(
                        id=doc.id,
                        name=shelter_data.get('name', 'Unknown'),
                        location=shelter_location,
                        capacity=shelter_data.get('capacity', 0),
                        shelter_type=shelter_data.get('type'),
                        facilities=shelter_data.get('facilities', [])
                    )
                    nearby_shelters.append(shelter)
                    
                    if len(nearby_shelters) >= limit:
                        break
            
            return nearby_shelters
            
        except Exception as e:
            logger.error(f"Error searching local shelters: {e}")
            return []
    
    def _determine_region(self, location: Location) -> str:
        """Determine region based on location coordinates."""
        # Simplified region detection - in production, use proper geographic lookup
        # Tokyo bounds (approximate)
        if (35.5 <= location.latitude <= 35.9 and 
            139.3 <= location.longitude <= 139.9):
            return "tokyo"
        
        # Default to tokyo for now - could be expanded
        return "tokyo"
    
    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    async def create_mock_shelters(self, center: Location, count: int = 10) -> List[str]:
        """
        Create mock shelter data for testing.
        This should only be used in development/testing.
        """
        created_ids = []
        
        for i in range(count):
            # Generate random position around center
            lat_offset = (i % 5 - 2) * 0.01  # Roughly 1km per 0.01 degree
            lon_offset = ((i // 5) % 3 - 1) * 0.01
            
            shelter_data = {
                'name': f'避難所 {i+1}',
                'name_en': f'Shelter {i+1}',
                'latitude': center.latitude + lat_offset,
                'longitude': center.longitude + lon_offset,
                'capacity': 100 + i * 50,
                'type': 'designated' if i % 2 == 0 else 'tsunami',
                'facilities': ['water', 'toilet'] if i % 3 == 0 else ['water'],
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Add to Firestore
            doc_ref = self.shelters_collection.add(shelter_data)
            created_ids.append(doc_ref[1].id)
            
        logger.info(f"Created {count} mock shelters")
        return created_ids