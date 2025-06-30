import math
from typing import Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees).

    Args:
        lat1: Latitude of point 1 in degrees
        lon1: Longitude of point 1 in degrees
        lat2: Latitude of point 2 in degrees
        lon2: Longitude of point 2 in degrees

    Returns:
        Distance between points in kilometers
    """
    # Convert decimal degrees to radians
    lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def is_point_in_radius(
    point_lat: float,
    point_lon: float,
    center_lat: float,
    center_lon: float,
    radius_km: float
) -> bool:
    """Check if a point is within a given radius of a center point.

    Args:
        point_lat: Latitude of point to check
        point_lon: Longitude of point to check
        center_lat: Latitude of center point
        center_lon: Longitude of center point
        radius_km: Radius in kilometers

    Returns:
        True if point is within radius, False otherwise
    """
    distance = haversine_distance(point_lat, point_lon, center_lat, center_lon)
    return distance <= radius_km

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Alias for haversine_distance to maintain backward compatibility.
    
    Args:
        lat1: Latitude of point 1 in degrees
        lon1: Longitude of point 1 in degrees
        lat2: Latitude of point 2 in degrees
        lon2: Longitude of point 2 in degrees

    Returns:
        Distance between points in kilometers
    """
    return haversine_distance(lat1, lon1, lat2, lon2)

def get_location_string(location) -> str:
    """Convert a location object to a string representation.
    
    Args:
        location: Location object with latitude and longitude attributes
        
    Returns:
        String representation of the location
    """
    if hasattr(location, 'latitude') and hasattr(location, 'longitude'):
        return f"{location.latitude:.4f},{location.longitude:.4f}"
    elif isinstance(location, dict):
        lat = location.get('latitude', 0)
        lon = location.get('longitude', 0)
        return f"{lat:.4f},{lon:.4f}"
    else:
        return str(location)
