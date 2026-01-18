"""
Caching service for external API calls (Google Maps, Geocoding, Places).

Provides Redis-based caching to reduce API costs and improve performance.

Key patterns:
- geo:reverse:{lat}:{lng} - TTL 24h
- geo:forward:{address_hash} - TTL 24h
- places:nearby:{lat}:{lng}:{type} - TTL 1h
- places:details:{place_id} - TTL 24h
"""

import hashlib
import logging
from typing import Optional, Any
from .redis_client import RedisCache

logger = logging.getLogger(__name__)

# TTL Configuration (in seconds)
TTL_GEOCODE = 86400  # 24 hours
TTL_PLACES_NEARBY = 3600  # 1 hour (results can change)
TTL_PLACES_DETAILS = 86400  # 24 hours


class GeocodingCache:
    """Cache for geocoding API responses."""

    @staticmethod
    def _round_coords(lat: float, lng: float, precision: int = 6) -> tuple:
        """Round coordinates to reduce key variations."""
        return round(lat, precision), round(lng, precision)

    @staticmethod
    def _hash_address(address: str) -> str:
        """Create a hash of an address string."""
        normalized = address.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    @staticmethod
    async def get_reverse_geocode(lat: float, lng: float) -> Optional[dict]:
        """
        Get cached reverse geocoding result.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Cached result or None
        """
        lat_r, lng_r = GeocodingCache._round_coords(lat, lng)
        key = f"geo:reverse:{lat_r}:{lng_r}"
        return await RedisCache.get_json(key)

    @staticmethod
    async def set_reverse_geocode(lat: float, lng: float, result: dict) -> bool:
        """
        Cache a reverse geocoding result.

        Args:
            lat: Latitude
            lng: Longitude
            result: Geocoding API response

        Returns:
            True if cached successfully
        """
        lat_r, lng_r = GeocodingCache._round_coords(lat, lng)
        key = f"geo:reverse:{lat_r}:{lng_r}"
        success = await RedisCache.set_json(key, result, TTL_GEOCODE)
        if success:
            logger.debug(f"Cached reverse geocode for {lat_r},{lng_r}")
        return success

    @staticmethod
    async def get_forward_geocode(address: str) -> Optional[dict]:
        """
        Get cached forward geocoding result.

        Args:
            address: Address string to geocode

        Returns:
            Cached result or None
        """
        address_hash = GeocodingCache._hash_address(address)
        key = f"geo:forward:{address_hash}"
        return await RedisCache.get_json(key)

    @staticmethod
    async def set_forward_geocode(address: str, result: dict) -> bool:
        """
        Cache a forward geocoding result.

        Args:
            address: Address string
            result: Geocoding API response

        Returns:
            True if cached successfully
        """
        address_hash = GeocodingCache._hash_address(address)
        key = f"geo:forward:{address_hash}"
        success = await RedisCache.set_json(key, result, TTL_GEOCODE)
        if success:
            logger.debug(f"Cached forward geocode for address hash {address_hash}")
        return success


class PlacesCache:
    """Cache for Google Places API responses."""

    @staticmethod
    def _round_coords(lat: float, lng: float, precision: int = 4) -> tuple:
        """Round coordinates (lower precision for places to group nearby requests)."""
        return round(lat, precision), round(lng, precision)

    @staticmethod
    async def get_nearby_places(lat: float, lng: float, place_type: str) -> Optional[dict]:
        """
        Get cached nearby places result.

        Args:
            lat: Latitude
            lng: Longitude
            place_type: Type of place (e.g., 'hospital', 'school')

        Returns:
            Cached result or None
        """
        lat_r, lng_r = PlacesCache._round_coords(lat, lng)
        key = f"places:nearby:{lat_r}:{lng_r}:{place_type}"
        return await RedisCache.get_json(key)

    @staticmethod
    async def set_nearby_places(
        lat: float, lng: float, place_type: str, result: dict
    ) -> bool:
        """
        Cache nearby places result.

        Args:
            lat: Latitude
            lng: Longitude
            place_type: Type of place
            result: Places API response

        Returns:
            True if cached successfully
        """
        lat_r, lng_r = PlacesCache._round_coords(lat, lng)
        key = f"places:nearby:{lat_r}:{lng_r}:{place_type}"
        success = await RedisCache.set_json(key, result, TTL_PLACES_NEARBY)
        if success:
            logger.debug(f"Cached nearby {place_type} for {lat_r},{lng_r}")
        return success

    @staticmethod
    async def get_place_details(place_id: str) -> Optional[dict]:
        """
        Get cached place details.

        Args:
            place_id: Google Place ID

        Returns:
            Cached result or None
        """
        key = f"places:details:{place_id}"
        return await RedisCache.get_json(key)

    @staticmethod
    async def set_place_details(place_id: str, result: dict) -> bool:
        """
        Cache place details.

        Args:
            place_id: Google Place ID
            result: Place Details API response

        Returns:
            True if cached successfully
        """
        key = f"places:details:{place_id}"
        success = await RedisCache.set_json(key, result, TTL_PLACES_DETAILS)
        if success:
            logger.debug(f"Cached place details for {place_id}")
        return success


class DirectionsCache:
    """Cache for Google Directions API responses."""

    @staticmethod
    def _round_coords(lat: float, lng: float, precision: int = 5) -> tuple:
        """Round coordinates for directions caching."""
        return round(lat, precision), round(lng, precision)

    @staticmethod
    def _make_key(
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float
    ) -> str:
        """Generate cache key for directions."""
        o_lat, o_lng = DirectionsCache._round_coords(origin_lat, origin_lng)
        d_lat, d_lng = DirectionsCache._round_coords(dest_lat, dest_lng)
        return f"directions:{o_lat},{o_lng}:{d_lat},{d_lng}"

    @staticmethod
    async def get_directions(
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float
    ) -> Optional[dict]:
        """
        Get cached directions result.

        Args:
            origin_lat, origin_lng: Origin coordinates
            dest_lat, dest_lng: Destination coordinates

        Returns:
            Cached result or None
        """
        key = DirectionsCache._make_key(origin_lat, origin_lng, dest_lat, dest_lng)
        return await RedisCache.get_json(key)

    @staticmethod
    async def set_directions(
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float,
        result: dict
    ) -> bool:
        """
        Cache directions result.

        Args:
            origin_lat, origin_lng: Origin coordinates
            dest_lat, dest_lng: Destination coordinates
            result: Directions API response

        Returns:
            True if cached successfully
        """
        key = DirectionsCache._make_key(origin_lat, origin_lng, dest_lat, dest_lng)
        # Directions cached for 24 hours (routes don't change often)
        success = await RedisCache.set_json(key, result, TTL_GEOCODE)
        if success:
            logger.debug(f"Cached directions from ({origin_lat},{origin_lng}) to ({dest_lat},{dest_lng})")
        return success


class CacheStats:
    """Cache statistics and management."""

    @staticmethod
    async def get_stats() -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        from .redis_client import get_redis_client

        try:
            client = await get_redis_client()
            if not client:
                return {"status": "unavailable", "message": "Redis not connected"}

            # Count keys by pattern
            geo_keys = 0
            places_keys = 0
            directions_keys = 0

            async for key in client.scan_iter(match="geo:*", count=100):
                geo_keys += 1

            async for key in client.scan_iter(match="places:*", count=100):
                places_keys += 1

            async for key in client.scan_iter(match="directions:*", count=100):
                directions_keys += 1

            return {
                "status": "healthy",
                "geocoding_cached": geo_keys,
                "places_cached": places_keys,
                "directions_cached": directions_keys,
                "total_cached": geo_keys + places_keys + directions_keys
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "message": str(e)}


# Export
__all__ = [
    'GeocodingCache',
    'PlacesCache',
    'DirectionsCache',
    'CacheStats'
]
