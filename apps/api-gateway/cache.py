"""
Redis Cache Layer
Author: Volodymyr Stetsenko (Zero2Auditor)
"""

import os
import json
import redis.asyncio as redis
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default


class RedisCache:
    """Redis cache client"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = await redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info(f"[+] Connected to Redis at {REDIS_URL}")
            return True
        except Exception as e:
            logger.error(f"[!] Failed to connect to Redis: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"[!] Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: CACHE_TTL)
            
        Returns:
            True if successful
        """
        try:
            serialized = json.dumps(value)
            await self.client.set(key, serialized, ex=ttl or CACHE_TTL)
            return True
        except Exception as e:
            logger.error(f"[!] Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"[!] Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"[!] Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter
        
        Args:
            key: Counter key
            amount: Amount to increment
            
        Returns:
            New value or None on error
        """
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"[!] Cache increment error for key {key}: {e}")
            return None
    
    async def set_job_status(self, job_id: str, status: dict, ttl: int = 3600):
        """
        Cache job status
        
        Args:
            job_id: Job identifier
            status: Status data
            ttl: Time to live
        """
        key = f"job:status:{job_id}"
        await self.set(key, status, ttl)
    
    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """
        Get cached job status
        
        Args:
            job_id: Job identifier
            
        Returns:
            Status data or None
        """
        key = f"job:status:{job_id}"
        return await self.get(key)
    
    async def set_contract_analysis(self, contract_hash: str, results: dict, ttl: int = 86400):
        """
        Cache contract analysis results
        
        Args:
            contract_hash: Hash of contract source
            results: Analysis results
            ttl: Time to live (default: 24 hours)
        """
        key = f"contract:analysis:{contract_hash}"
        await self.set(key, results, ttl)
    
    async def get_contract_analysis(self, contract_hash: str) -> Optional[dict]:
        """
        Get cached contract analysis
        
        Args:
            contract_hash: Hash of contract source
            
        Returns:
            Cached results or None
        """
        key = f"contract:analysis:{contract_hash}"
        return await self.get(key)
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("[+] Redis connection closed")


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Get cache instance"""
    if not cache.client:
        await cache.connect()
    return cache

