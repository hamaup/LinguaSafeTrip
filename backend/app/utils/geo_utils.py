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

def lon2tile(lon: float, zoom: int) -> int:
    """Convert longitude to tile X coordinate.
    
    Args:
        lon: Longitude in degrees
        zoom: Zoom level
        
    Returns:
        Tile X coordinate
    """
    return int((lon + 180.0) / 360.0 * (2 ** zoom))

def lat2tile(lat: float, zoom: int) -> int:
    """Convert latitude to tile Y coordinate.
    
    Args:
        lat: Latitude in degrees
        zoom: Zoom level
        
    Returns:
        Tile Y coordinate
    """
    lat_rad = math.radians(lat)
    return int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * (2 ** zoom))

def get_tile_coordinates(lat: float, lon: float, zoom: int) -> Tuple[int, int, int]:
    """Get tile coordinates for a given latitude, longitude, and zoom level.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        zoom: Zoom level
        
    Returns:
        Tuple of (zoom, x, y) tile coordinates
    """
    x = lon2tile(lon, zoom)
    y = lat2tile(lat, zoom)
    return (zoom, x, y)

def get_surrounding_tiles(lat: float, lon: float, zoom: int, radius: int = 1) -> list[Tuple[int, int, int]]:
    """Get surrounding tiles for a given location.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        zoom: Zoom level
        radius: Number of tiles to include in each direction (default 1)
        
    Returns:
        List of (zoom, x, y) tile coordinates including center and surrounding tiles
    """
    center_x = lon2tile(lon, zoom)
    center_y = lat2tile(lat, zoom)
    
    tiles = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            tiles.append((zoom, center_x + dx, center_y + dy))
    
    return tiles
