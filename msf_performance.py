#!/usr/bin/env python3

"""
MSF MCP Performance Optimizations
---------------------------------
Caching, connection pooling, result streaming, and performance monitoring.
"""

import asyncio
import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import wraps
import weakref
import gc
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    value: Any
    timestamp: float
    access_count: int = 0
    size_bytes: int = 0

@dataclass
class PerformanceMetrics:
    cache_hits: int = 0
    cache_misses: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    memory_usage_mb: float = 0.0
    active_connections: int = 0
    command_execution_times: List[float] = field(default_factory=list)
    rpc_call_times: List[float] = field(default_factory=list)

class LRUCache:
    """
    High-performance LRU cache with size limits and TTL support.
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.total_size = 0
        self.max_memory_mb = 100  # 100MB cache limit
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check TTL
            if time.time() - entry.timestamp > self.ttl:
                del self.cache[key]
                self.total_size -= entry.size_bytes
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.access_count += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any, size_hint: int = None):
        """Set value in cache."""
        async with self._lock:
            # Calculate size
            if size_hint is None:
                try:
                    size_bytes = len(json.dumps(value, default=str))
                except:
                    size_bytes = 1024  # Default estimate
            else:
                size_bytes = size_hint
            
            # Check memory limit
            if self.total_size + size_bytes > self.max_memory_mb * 1024 * 1024:
                await self._evict_oldest()
            
            # Remove existing entry if present
            if key in self.cache:
                old_entry = self.cache[key]
                self.total_size -= old_entry.size_bytes
            
            # Add new entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                size_bytes=size_bytes
            )
            
            self.cache[key] = entry
            self.total_size += size_bytes
            
            # Enforce max size
            while len(self.cache) > self.max_size:
                await self._evict_oldest()
    
    async def _evict_oldest(self):
        """Evict the oldest entry."""
        if self.cache:
            oldest_key, oldest_entry = self.cache.popitem(last=False)
            self.total_size -= oldest_entry.size_bytes
            logger.debug(f"Evicted cache entry: {oldest_key}")
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            self.total_size = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self.cache),
            "total_size_bytes": self.total_size,
            "total_size_mb": self.total_size / (1024 * 1024),
            "max_size": self.max_size,
            "ttl": self.ttl
        }

class ConnectionPool:
    """
    Connection pool for RPC connections with health checking.
    """
    
    def __init__(self, max_connections: int = 10, health_check_interval: int = 30):
        self.max_connections = max_connections
        self.health_check_interval = health_check_interval
        self.connections: List[Any] = []
        self.available_connections = asyncio.Queue()
        self.connection_count = 0
        self.health_check_task = None
        self._lock = asyncio.Lock()
    
    async def start(self, connection_factory: Callable):
        """Start the connection pool."""
        self.connection_factory = connection_factory
        
        # Pre-populate with initial connections
        for _ in range(min(3, self.max_connections)):
            await self._create_connection()
        
        # Start health checking
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def get_connection(self):
        """Get a connection from the pool."""
        try:
            # Try to get an available connection with timeout
            connection = await asyncio.wait_for(
                self.available_connections.get(),
                timeout=5.0
            )
            return connection
        except asyncio.TimeoutError:
            # Create new connection if under limit
            if self.connection_count < self.max_connections:
                return await self._create_connection()
            else:
                raise RuntimeError("Connection pool exhausted")
    
    async def return_connection(self, connection):
        """Return a connection to the pool."""
        if connection and await self._is_connection_healthy(connection):
            await self.available_connections.put(connection)
        else:
            # Connection is unhealthy, create a new one
            await self._create_connection()
    
    async def _create_connection(self):
        """Create a new connection."""
        async with self._lock:
            if self.connection_count >= self.max_connections:
                return None
            
            try:
                connection = await self.connection_factory()
                self.connections.append(connection)
                self.connection_count += 1
                await self.available_connections.put(connection)
                logger.debug(f"Created new connection, pool size: {self.connection_count}")
                return connection
            except Exception as e:
                logger.error(f"Failed to create connection: {e}")
                return None
    
    async def _is_connection_healthy(self, connection) -> bool:
        """Check if a connection is healthy."""
        try:
            # Implement connection health check
            # This would depend on the specific connection type
            return hasattr(connection, 'is_connected') and connection.is_connected
        except:
            return False
    
    async def _health_check_loop(self):
        """Periodic health check of connections."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Check all connections
                unhealthy_connections = []
                for connection in self.connections:
                    if not await self._is_connection_healthy(connection):
                        unhealthy_connections.append(connection)
                
                # Remove unhealthy connections
                for connection in unhealthy_connections:
                    self.connections.remove(connection)
                    self.connection_count -= 1
                    logger.warning("Removed unhealthy connection from pool")
                
                # Ensure minimum connections
                while self.connection_count < min(3, self.max_connections):
                    await self._create_connection()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection health check: {e}")
    
    async def stop(self):
        """Stop the connection pool."""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection in self.connections:
            try:
                if hasattr(connection, 'close'):
                    await connection.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        
        self.connections.clear()
        self.connection_count = 0

class ResultStreamer:
    """
    Stream large results in chunks to avoid memory issues.
    """
    
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
    
    async def stream_result(self, data: str) -> AsyncGenerator[str, None]:
        """Stream data in chunks."""
        if len(data) <= self.chunk_size:
            yield data
            return
        
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            yield chunk
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.001)
    
    async def stream_json_array(self, items: List[Any]) -> AsyncGenerator[str, None]:
        """Stream JSON array items one by one."""
        yield "["
        
        for i, item in enumerate(items):
            if i > 0:
                yield ","
            
            try:
                yield json.dumps(item)
            except Exception as e:
                logger.error(f"Error serializing item: {e}")
                yield json.dumps({"error": f"Serialization error: {str(e)}"})
            
            # Yield control periodically
            if i % 100 == 0:
                await asyncio.sleep(0.001)
        
        yield "]"

class PerformanceMonitor:
    """
    Monitor and track performance metrics.
    """
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()
        self._lock = asyncio.Lock()
    
    async def record_cache_hit(self):
        """Record a cache hit."""
        async with self._lock:
            self.metrics.cache_hits += 1
    
    async def record_cache_miss(self):
        """Record a cache miss."""
        async with self._lock:
            self.metrics.cache_misses += 1
    
    async def record_request(self, response_time: float):
        """Record a request with response time."""
        async with self._lock:
            self.metrics.total_requests += 1
            
            # Update average response time
            total_time = self.metrics.average_response_time * (self.metrics.total_requests - 1)
            self.metrics.average_response_time = (total_time + response_time) / self.metrics.total_requests
    
    async def record_command_execution(self, execution_time: float):
        """Record command execution time."""
        async with self._lock:
            self.metrics.command_execution_times.append(execution_time)
            
            # Keep only recent times (last 1000)
            if len(self.metrics.command_execution_times) > 1000:
                self.metrics.command_execution_times = self.metrics.command_execution_times[-1000:]
    
    async def record_rpc_call(self, call_time: float):
        """Record RPC call time."""
        async with self._lock:
            self.metrics.rpc_call_times.append(call_time)
            
            # Keep only recent times (last 1000)
            if len(self.metrics.rpc_call_times) > 1000:
                self.metrics.rpc_call_times = self.metrics.rpc_call_times[-1000:]
    
    async def update_memory_usage(self):
        """Update current memory usage."""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            async with self._lock:
                self.metrics.memory_usage_mb = memory_mb
        except Exception as e:
            logger.error(f"Error updating memory usage: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        await self.update_memory_usage()
        
        async with self._lock:
            cache_hit_rate = 0.0
            if self.metrics.cache_hits + self.metrics.cache_misses > 0:
                cache_hit_rate = self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses)
            
            avg_command_time = 0.0
            if self.metrics.command_execution_times:
                avg_command_time = sum(self.metrics.command_execution_times) / len(self.metrics.command_execution_times)
            
            avg_rpc_time = 0.0
            if self.metrics.rpc_call_times:
                avg_rpc_time = sum(self.metrics.rpc_call_times) / len(self.metrics.rpc_call_times)
            
            return {
                "uptime_seconds": time.time() - self.start_time,
                "total_requests": self.metrics.total_requests,
                "average_response_time": self.metrics.average_response_time,
                "cache_hit_rate": cache_hit_rate,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "active_connections": self.metrics.active_connections,
                "average_command_execution_time": avg_command_time,
                "average_rpc_call_time": avg_rpc_time,
                "recent_command_times": self.metrics.command_execution_times[-10:],
                "recent_rpc_times": self.metrics.rpc_call_times[-10:]
            }

class PerformanceOptimizer:
    """
    Main performance optimization coordinator.
    """
    
    def __init__(self, config):
        self.config = config
        self.cache = LRUCache(
            max_size=config.performance.cache_max_size,
            ttl=config.performance.cache_ttl
        ) if config.performance.cache_enabled else None
        
        self.connection_pool = ConnectionPool(
            max_connections=config.performance.connection_pooling and 10 or 1
        ) if config.performance.connection_pooling else None
        
        self.result_streamer = ResultStreamer() if config.performance.result_streaming else None
        self.performance_monitor = PerformanceMonitor()
        
        # Weak reference cleanup
        self._cleanup_task = None
    
    async def start(self, connection_factory: Optional[Callable] = None):
        """Start performance optimization components."""
        if self.connection_pool and connection_factory:
            await self.connection_pool.start(connection_factory)
        
        # Start periodic cleanup
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Performance optimizer started")
    
    async def stop(self):
        """Stop performance optimization components."""
        if self.connection_pool:
            await self.connection_pool.stop()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance optimizer stopped")
    
    def cache_key(self, command: str, context: Dict[str, Any] = None) -> str:
        """Generate cache key for command and context."""
        if not self.cache:
            return ""
        
        # Create hash of command and relevant context
        cache_data = {
            "command": command,
            "workspace": context.get("workspace", "default") if context else "default"
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    async def get_cached_result(self, key: str) -> Optional[Any]:
        """Get result from cache."""
        if not self.cache:
            return None
        
        result = await self.cache.get(key)
        
        if result:
            await self.performance_monitor.record_cache_hit()
        else:
            await self.performance_monitor.record_cache_miss()
        
        return result
    
    async def cache_result(self, key: str, result: Any, size_hint: int = None):
        """Cache a result."""
        if not self.cache:
            return
        
        await self.cache.set(key, result, size_hint)
    
    async def get_connection(self):
        """Get a connection from the pool."""
        if self.connection_pool:
            return await self.connection_pool.get_connection()
        return None
    
    async def return_connection(self, connection):
        """Return a connection to the pool."""
        if self.connection_pool and connection:
            await self.connection_pool.return_connection(connection)
    
    async def stream_large_result(self, data: str) -> AsyncGenerator[str, None]:
        """Stream large results."""
        if self.result_streamer and len(data) > 8192:
            async for chunk in self.result_streamer.stream_result(data):
                yield chunk
        else:
            yield data
    
    async def record_performance(self, operation: str, execution_time: float):
        """Record performance metrics."""
        await self.performance_monitor.record_request(execution_time)
        
        if operation == "command":
            await self.performance_monitor.record_command_execution(execution_time)
        elif operation == "rpc":
            await self.performance_monitor.record_rpc_call(execution_time)
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        metrics = await self.performance_monitor.get_metrics()
        
        if self.cache:
            metrics["cache_stats"] = self.cache.get_stats()
        
        return metrics
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of resources."""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
                # Force garbage collection
                gc.collect()
                
                # Clear old cache entries if memory usage is high
                if self.cache:
                    await self.performance_monitor.update_memory_usage()
                    if self.performance_monitor.metrics.memory_usage_mb > 400:  # > 400MB
                        logger.info("High memory usage, clearing cache")
                        await self.cache.clear()
                
                logger.debug("Periodic cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")


def performance_monitor(operation: str = "request"):
    """
    Decorator to monitor performance of functions.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                # Would need access to global performance monitor
                logger.debug(f"{operation} completed in {execution_time:.3f}s")
        
        return wrapper
    return decorator

# Global performance optimizer
performance_optimizer: Optional[PerformanceOptimizer] = None

def get_performance_optimizer() -> Optional[PerformanceOptimizer]:
    """Get the global performance optimizer."""
    return performance_optimizer

def initialize_performance_optimizer(config):
    """Initialize the global performance optimizer."""
    global performance_optimizer
    performance_optimizer = PerformanceOptimizer(config)