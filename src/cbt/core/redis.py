"""
Redis connection and caching utilities for CBT system.
"""

import json
import pickle
from typing import Any, Optional, Union, List
import redis.asyncio as redis
from datetime import timedelta
import logging

from .config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection and caching management."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
    
    async def connect(self):
        """Establish Redis connection."""
        try:
            self.connection_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        logger.info("Redis connection closed")
    
    async def health_check(self) -> dict:
        """
        Perform Redis health check.
        
        Returns:
            dict: Health check results
        """
        try:
            if not self.redis_client:
                return {"status": "disconnected", "error": "No Redis connection"}
            
            # Test basic operations
            await self.redis_client.ping()
            
            # Test set/get operations
            test_key = "health_check_test"
            await self.redis_client.setex(test_key, 10, "test_value")
            test_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            is_healthy = test_value == "test_value"
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": settings.redis_host
            }


class CacheManager:
    """High-level caching operations using Redis."""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.default_ttl = 3600  # 1 hour
        
    @property
    def redis(self):
        return self.redis_manager.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            if not self.redis:
                return None
            
            cached_data = await self.redis.get(key)
            if cached_data is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(cached_data)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(cached_data.encode())
                except (pickle.PickleError, TypeError):
                    return cached_data
                    
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.redis:
                return False
            
            # Serialize value
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value).decode()
            
            cache_ttl = ttl or self.default_ttl
            await self.redis.setex(key, cache_ttl, serialized_value)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.redis:
                return False
            
            result = await self.redis.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists
        """
        try:
            if not self.redis:
                return False
            
            result = await self.redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache exists check error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration for existing key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.redis:
                return False
            
            result = await self.redis.expire(key, ttl)
            return result
            
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for key.
        
        Args:
            key: Cache key
            
        Returns:
            int: TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            if not self.redis:
                return -2
            
            return await self.redis.ttl(key)
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value.
        
        Args:
            key: Cache key
            amount: Increment amount
            
        Returns:
            New value or None
        """
        try:
            if not self.redis:
                return None
            
            return await self.redis.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrement numeric value.
        
        Args:
            key: Cache key
            amount: Decrement amount
            
        Returns:
            New value or None
        """
        try:
            if not self.redis:
                return None
            
            return await self.redis.decrby(key, amount)
            
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return None
    
    async def get_multiple(self, keys: List[str]) -> dict:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            dict: Key-value pairs
        """
        try:
            if not self.redis:
                return {}
            
            values = await self.redis.mget(keys)
            result = {}
            
            for i, key in enumerate(keys):
                if values[i] is not None:
                    try:
                        result[key] = json.loads(values[i])
                    except (json.JSONDecodeError, TypeError):
                        try:
                            result[key] = pickle.loads(values[i].encode())
                        except (pickle.PickleError, TypeError):
                            result[key] = values[i]
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get multiple error: {e}")
            return {}
    
    async def set_multiple(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.redis:
                return False
            
            cache_ttl = ttl or self.default_ttl
            
            # Serialize values
            serialized_mapping = {}
            for key, value in mapping.items():
                try:
                    serialized_mapping[key] = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    serialized_mapping[key] = pickle.dumps(value).decode()
            
            # Use pipeline for atomic operation
            pipe = self.redis.pipeline()
            for key, value in serialized_mapping.items():
                pipe.setex(key, cache_ttl, value)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Cache set multiple error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "user:*")
            
        Returns:
            int: Number of keys deleted
        """
        try:
            if not self.redis:
                return 0
            
            keys = await self.redis.keys(pattern)
            if not keys:
                return 0
            
            return await self.redis.delete(*keys)
            
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0


class SessionManager:
    """Session management using Redis."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
    
    async def create_session(self, session_id: str, session_data: dict, ttl: int = 7200) -> bool:
        """
        Create session in Redis.
        
        Args:
            session_id: Session identifier
            session_data: Session data
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        key = f"{self.session_prefix}{session_id}"
        return await self.cache.set(key, session_data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        key = f"{self.session_prefix}{session_id}"
        return await self.cache.get(key)
    
    async def update_session(self, session_id: str, session_data: dict) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            session_data: Updated session data
            
        Returns:
            bool: True if successful
        """
        key = f"{self.session_prefix}{session_id}"
        return await self.cache.set(key, session_data)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if successful
        """
        key = f"{self.session_prefix}{session_id}"
        return await self.cache.delete(key)
    
    async def add_user_session(self, user_id: str, session_id: str) -> bool:
        """
        Add session to user's session list.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            bool: True if successful
        """
        key = f"{self.user_sessions_prefix}{user_id}"
        return await self.cache.redis.sadd(key, session_id)
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all sessions for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session IDs
        """
        key = f"{self.user_sessions_prefix}{user_id}"
        sessions = await self.cache.redis.smembers(key)
        return list(sessions) if sessions else []
    
    async def remove_user_session(self, user_id: str, session_id: str) -> bool:
        """
        Remove session from user's session list.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            bool: True if successful
        """
        key = f"{self.user_sessions_prefix}{user_id}"
        return await self.cache.redis.srem(key, session_id)
    
    async def clear_user_sessions(self, user_id: str) -> int:
        """
        Clear all sessions for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions cleared
        """
        sessions = await self.get_user_sessions(user_id)
        count = 0
        
        for session_id in sessions:
            if await self.delete_session(session_id):
                count += 1
        
        # Clear user session set
        key = f"{self.user_sessions_prefix}{user_id}"
        await self.cache.redis.delete(key)
        
        return count


# Global instances
redis_manager = RedisManager()
cache_manager = CacheManager(redis_manager)
session_manager = SessionManager(cache_manager)
