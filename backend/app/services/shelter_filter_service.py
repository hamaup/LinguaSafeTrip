"""Service for filtering shelters based on hazard data and safety criteria."""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.schemas.hazard import (
    HazardInfo, HazardType, HazardLevel, Location,
    SafeShelter, Shelter
)
from app.services.elevation_service import ElevationService

logger = logging.getLogger(__name__)


class ShelterFilterService:
    """Service for filtering and evaluating shelter safety based on hazard data."""
    
    # Safety margins for different hazard types (in meters)
    SAFETY_MARGINS = {
        HazardType.TSUNAMI: 5.0,      # 5m above expected tsunami height
        HazardType.FLOOD: 2.0,        # 2m above expected flood level
        HazardType.HIGH_TIDE: 3.0,    # 3m above high tide level
    }
    
    # Minimum safety scores for different disaster types
    MIN_SAFETY_SCORES = {
        HazardType.TSUNAMI: 0.6,      # Higher threshold for tsunami
        HazardType.FLOOD: 0.4,        # Moderate threshold for flood
        HazardType.HIGH_TIDE: 0.4,    # Moderate threshold for high tide
    }
    
    def __init__(self, elevation_service: Optional[ElevationService] = None):
        """Initialize the shelter filter service."""
        self.elevation_service = elevation_service or ElevationService()
    
    def _calculate_safety_score(self, elevation: float, hazard_data: HazardInfo,
                               disaster_type: HazardType) -> float:
        """
        Calculate safety score based on elevation and hazard data.
        Score ranges from 0.0 (unsafe) to 1.0 (very safe).
        """
        # Find the relevant hazard for the disaster type
        relevant_hazard = None
        for hazard in hazard_data.hazards:
            if hazard.hazard_type == disaster_type:
                relevant_hazard = hazard
                break
        
        # If no hazard of this type, location is safe
        if not relevant_hazard or relevant_hazard.level == HazardLevel.NONE:
            return 1.0
        
        # If no depth information, use level-based scoring
        if relevant_hazard.depth is None:
            level_scores = {
                HazardLevel.LOW: 0.7,
                HazardLevel.MEDIUM: 0.5,
                HazardLevel.HIGH: 0.3,
                HazardLevel.EXTREME: 0.1
            }
            return level_scores.get(relevant_hazard.level, 0.5)
        
        # Calculate score based on elevation margin
        required_margin = self.SAFETY_MARGINS.get(disaster_type, 2.0)
        actual_margin = elevation - relevant_hazard.depth
        
        if actual_margin < 0:
            # Below hazard level - very unsafe
            return 0.0
        elif actual_margin < required_margin:
            # Below safety margin - partially safe
            return actual_margin / required_margin * 0.5
        else:
            # Above safety margin - safe
            # Score increases with additional margin, capped at 1.0
            extra_margin = actual_margin - required_margin
            return min(1.0, 0.5 + (extra_margin / (required_margin * 2)))
    
    def _evaluate_safety(self, elevation: float, hazard_data: HazardInfo,
                        disaster_type: HazardType) -> bool:
        """Determine if a shelter is safe based on strict criteria."""
        score = self._calculate_safety_score(elevation, hazard_data, disaster_type)
        min_score = self.MIN_SAFETY_SCORES.get(disaster_type, 0.5)
        return score >= min_score
    
    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations in kilometers using Haversine formula."""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _estimate_travel_time(self, distance_km: float, is_emergency: bool = True) -> int:
        """
        Estimate travel time in minutes based on distance.
        Assumes walking speed of 4 km/h normally, 3 km/h in emergency.
        """
        walking_speed = 3.0 if is_emergency else 4.0  # km/h
        time_hours = distance_km / walking_speed
        return int(time_hours * 60)  # Convert to minutes
    
    async def filter_safe_shelters(self, shelters: List[Shelter],
                                  hazard_data: HazardInfo,
                                  disaster_type: HazardType,
                                  user_location: Optional[Location] = None,
                                  max_results: int = 20) -> List[SafeShelter]:
        """
        Filter shelters based on safety criteria.
        
        Args:
            shelters: List of available shelters
            hazard_data: Hazard information for the area
            disaster_type: Type of disaster to evaluate for
            user_location: User's current location (for distance calculation)
            max_results: Maximum number of results to return
            
        Returns:
            List of safe shelters sorted by safety score
        """
        safe_shelters = []
        
        # Process shelters in parallel for better performance
        tasks = []
        for shelter in shelters:
            tasks.append(self._evaluate_shelter(
                shelter, hazard_data, disaster_type, user_location
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, SafeShelter) and result.is_safe:
                safe_shelters.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error evaluating shelter: {result}")
        
        # Sort by safety score (descending) and distance (ascending)
        safe_shelters.sort(key=lambda s: (-s.safety_score, s.distance))
        
        # Return top results
        return safe_shelters[:max_results]
    
    async def _evaluate_shelter(self, shelter: Shelter,
                               hazard_data: HazardInfo,
                               disaster_type: HazardType,
                               user_location: Optional[Location]) -> SafeShelter:
        """Evaluate a single shelter for safety."""
        # Get elevation
        elevation = await self.elevation_service.get_elevation(shelter.location)
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(elevation, hazard_data, disaster_type)
        
        # Determine if safe
        is_safe = self._evaluate_safety(elevation, hazard_data, disaster_type)
        
        # Calculate distance and travel time if user location provided
        distance = 0.0
        estimated_time = 0
        if user_location:
            distance = self._calculate_distance(user_location, shelter.location)
            estimated_time = self._estimate_travel_time(distance, is_emergency=True)
        
        # Determine specific safety for tsunami
        is_tsunami_safe = False
        if disaster_type == HazardType.TSUNAMI:
            tsunami_hazard = next(
                (h for h in hazard_data.hazards if h.hazard_type == HazardType.TSUNAMI),
                None
            )
            if tsunami_hazard and tsunami_hazard.depth:
                margin = elevation - tsunami_hazard.depth
                is_tsunami_safe = margin >= self.SAFETY_MARGINS[HazardType.TSUNAMI]
            else:
                is_tsunami_safe = True  # No tsunami hazard
        
        return SafeShelter(
            id=shelter.id,
            name=shelter.name,
            location=shelter.location,
            elevation=elevation,
            building_floors=getattr(shelter, 'building_floors', None),
            capacity=shelter.capacity,
            distance=distance,
            estimated_time=estimated_time,
            is_tsunami_safe=is_tsunami_safe,
            is_safe=is_safe,
            safety_score=safety_score,
            hazard_info=self._get_shelter_hazard_summary(hazard_data, elevation, disaster_type)
        )
    
    def _get_shelter_hazard_summary(self, hazard_data: HazardInfo, 
                                   elevation: float,
                                   disaster_type: HazardType) -> Dict[str, any]:
        """Generate a summary of hazard information relevant to the shelter."""
        summary = {
            'elevation': elevation,
            'disaster_type': disaster_type.value,
            'hazards': []
        }
        
        for hazard in hazard_data.hazards:
            hazard_summary = {
                'type': hazard.hazard_type.value,
                'level': hazard.level.value,
                'depth': hazard.depth
            }
            
            if hazard.depth:
                margin = elevation - hazard.depth
                hazard_summary['elevation_margin'] = margin
                hazard_summary['is_above'] = margin > 0
                
            summary['hazards'].append(hazard_summary)
        
        return summary
    
    def get_filter_criteria(self, disaster_type: HazardType) -> Dict[str, any]:
        """Get the filtering criteria used for the specified disaster type."""
        return {
            'disaster_type': disaster_type.value,
            'safety_margin': self.SAFETY_MARGINS.get(disaster_type, 2.0),
            'min_safety_score': self.MIN_SAFETY_SCORES.get(disaster_type, 0.5),
            'evaluation_method': 'elevation_based',
            'considers_building_floors': True
        }
    
    async def evaluate_route_safety(self, route_points: List[Location],
                                   hazard_data_list: List[HazardInfo]) -> Dict[str, any]:
        """
        Evaluate the safety of a route based on hazard data along the path.
        
        Args:
            route_points: List of locations along the route
            hazard_data_list: Hazard data for each point
            
        Returns:
            Route safety evaluation
        """
        if len(route_points) != len(hazard_data_list):
            raise ValueError("Route points and hazard data must have same length")
        
        route_hazards = []
        max_risk_level = HazardLevel.NONE
        
        for i, (point, hazard_data) in enumerate(zip(route_points, hazard_data_list)):
            elevation = await self.elevation_service.get_elevation(point)
            
            point_info = {
                'index': i,
                'location': point.dict(),
                'elevation': elevation,
                'risk_level': hazard_data.overall_risk_level.value,
                'hazards': []
            }
            
            for hazard in hazard_data.hazards:
                if hazard.level != HazardLevel.NONE:
                    hazard_info = {
                        'type': hazard.hazard_type.value,
                        'level': hazard.level.value,
                        'depth': hazard.depth
                    }
                    if hazard.depth:
                        hazard_info['is_safe'] = elevation > hazard.depth + \
                                                self.SAFETY_MARGINS.get(hazard.hazard_type, 2.0)
                    point_info['hazards'].append(hazard_info)
            
            route_hazards.append(point_info)
            
            if hazard_data.overall_risk_level.value > max_risk_level.value:
                max_risk_level = hazard_data.overall_risk_level
        
        # Determine overall route safety
        is_route_safe = max_risk_level.value <= HazardLevel.MEDIUM.value
        
        return {
            'is_safe': is_route_safe,
            'max_risk_level': max_risk_level.value,
            'total_points': len(route_points),
            'hazard_points': len([p for p in route_hazards if p['risk_level'] != 'none']),
            'route_details': route_hazards,
            'recommendation': self._get_route_recommendation(max_risk_level, route_hazards)
        }
    
    def _get_route_recommendation(self, max_risk_level: HazardLevel,
                                 route_hazards: List[Dict]) -> str:
        """Generate route safety recommendation."""
        if max_risk_level == HazardLevel.EXTREME:
            return "This route passes through extreme hazard areas. Find an alternative route immediately."
        elif max_risk_level == HazardLevel.HIGH:
            return "This route has high-risk areas. Consider an alternative route if possible."
        elif max_risk_level == HazardLevel.MEDIUM:
            return "This route has moderate hazards. Proceed with caution and stay alert."
        elif max_risk_level == HazardLevel.LOW:
            return "This route has low hazard risk. Normal precautions recommended."
        else:
            return "This route appears safe based on current hazard data."