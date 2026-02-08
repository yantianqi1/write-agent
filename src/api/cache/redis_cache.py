"""
Redis Cache Implementation

Provides Redis-based caching with async support for better performance
in production environments.
"""

import json
import logging
from typing import Optional, Any, TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    import redis.asyncio as aioredis
else:
    try:
        import redis.asyncio as aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        aioredis = None

logger = logging.getLogger(__name__)


class RedisCacheBackend:
    """
    Redis cache backend implementation.

    Provides async caching with Redis for distributed scenarios
    and better persistence compared to in-memory caching.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        password: Optional[str] = None,
        db: int = 0,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
    ):
        """
        Initialize Redis cache backend.

        Args:
            url: Redis connection URL (redis://[password@]host:port/db)
            password: Redis password (if not in URL)
            db: Database number
            max_connections: Maximum connection pool size
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis is required for RedisCache. "
                "Install it with: pip install redis>=5.0.0"
            )

        self.url = url
        self.password = password
        self.db = db
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout

        self._pool: Any = None
        self._client: Any = None
        self._enabled = True

    async def _get_pool(self) -> Any:
        """Get or create connection pool."""
        if self._pool is None:
            # Parse URL to extract components
            parsed = urlparse(self.url)

            # Build connection kwargs
            kwargs = {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 6379,
                "db": self.db,
                "max_connections": self.max_connections,
                "socket_timeout": self.socket_timeout,
                "socket_connect_timeout": self.socket_connect_timeout,
                "retry_on_timeout": self.retry_on_timeout,
                "decode_responses": True,
            }

            # Use password from URL if available
            if parsed.password:
                kwargs["password"] = parsed.password
            elif self.password:
                kwargs["password"] = self.password

            self._pool = aioredis.ConnectionPool(**kwargs)

        return self._pool

    async def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is None:
            pool = await self._get_pool()
            self._client = aioredis.Redis(connection_pool=pool)
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._enabled:
            return None

        try:
            client = await self._get_client()
            value = await client.get(key)

            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return None

        except Exception as e:
            logger.warning(f"Redis get failed for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None for no expiry)

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            return False

        try:
            client = await self._get_client()

            # Serialize value
            serialized = json.dumps(value, ensure_ascii=False)

            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)

            return True

        except Exception as e:
            logger.warning(f"Redis set failed for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0

        except Exception as e:
            logger.warning(f"Redis delete failed for key '{key}': {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "session:*")

        Returns:
            Number of keys deleted
        """
        if not self._enabled:
            return 0

        try:
            client = await self._get_client()
            keys = []

            # Use scan for better performance with many keys
            async for key in client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await client.delete(*keys)

            return 0

        except Exception as e:
            logger.warning(f"Redis invalidate pattern failed for '{pattern}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            result = await client.exists(key)
            return result > 0

        except Exception as e:
            logger.warning(f"Redis exists check failed for key '{key}': {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            result = await client.expire(key, ttl)
            return result > 0

        except Exception as e:
            logger.warning(f"Redis expire failed for key '{key}': {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None if failed
        """
        if not self._enabled:
            return None

        try:
            client = await self._get_client()
            return await client.incrby(key, amount)

        except Exception as e:
            logger.warning(f"Redis increment failed for key '{key}': {e}")
            return None

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs for found keys
        """
        if not self._enabled or not keys:
            return {}

        try:
            client = await self._get_client()
            values = await client.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value

            return result

        except Exception as e:
            logger.warning(f"Redis get_many failed: {e}")
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds (None for no expiry)

        Returns:
            True if all successful, False otherwise
        """
        if not self._enabled or not mapping:
            return False

        try:
            client = await self._get_client()

            # Serialize all values
            serialized = {
                k: json.dumps(v, ensure_ascii=False)
                for k, v in mapping.items()
            }

            await client.mset(serialized)

            # Set TTL if provided
            if ttl:
                for key in mapping.keys():
                    await client.expire(key, ttl)

            return True

        except Exception as e:
            logger.warning(f"Redis set_many failed: {e}")
            return False

    def disable(self) -> None:
        """Disable caching."""
        self._enabled = False

    def enable(self) -> None:
        """Enable caching."""
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled

    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
            self._client = None

        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    async def ping(self) -> bool:
        """
        Check Redis connection.

        Returns:
            True if Redis is responsive, False otherwise
        """
        try:
            client = await self._get_client()
            result = await client.ping()
            return result
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False

    async def info(self) -> dict[str, Any]:
        """
        Get Redis server information.

        Returns:
            Dictionary with Redis info
        """
        try:
            client = await self._get_client()
            info = await client.info()
            return {
                "connected": True,
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace": info.get("db0", ""),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }


class FallbackCache:
    """
    Fallback in-memory cache when Redis is unavailable.
    """

    def __init__(self, ttl: int = 3600):
        """Initialize fallback cache."""
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl
        self._enabled = True

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._enabled:
            return None

        import time
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                return value
            else:
                del self._cache[key]

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self._enabled:
            return False

        import time
        cache_ttl = ttl or self._ttl
        self._cache[key] = (value, time.time() + cache_ttl)
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        import fnmatch
        to_delete = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
        for key in to_delete:
            del self._cache[key]
        return len(to_delete)

    def disable(self) -> None:
        """Disable caching."""
        self._enabled = False

    def enable(self) -> None:
        """Enable caching."""
        self._enabled = True

    async def close(self) -> None:
        """Close cache (no-op for in-memory)."""
        pass


__all__ = [
    "RedisCacheBackend",
    "FallbackCache",
    "REDIS_AVAILABLE",
]
