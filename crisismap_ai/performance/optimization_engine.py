"""
Advanced Performance Optimization Engine.

This module provides comprehensive performance optimization features including
intelligent caching, database optimization, response time improvements,
auto-scaling, and performance monitoring.
"""

import asyncio
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import gzip
import pickle
from collections import defaultdict, deque
from functools import wraps, lru_cache
import redis
import memcache
from pymongo import MongoClient, IndexModel
from pymongo.collection import Collection
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import psutil
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import aiofiles
import uvloop
import orjson
from aiocache import Cache, cached
from aiocache.serializers import PickleSerializer
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache level priorities."""
    L1_MEMORY = "l1_memory"      # In-memory, fastest
    L2_REDIS = "l2_redis"        # Redis, fast
    L3_MEMCACHED = "l3_memcached"  # Memcached, moderate
    L4_DATABASE = "l4_database"   # Database cache, slow
    L5_FILESYSTEM = "l5_filesystem"  # File cache, slowest


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    ADAPTIVE = "adaptive"


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    cache_hits: int = 0
    cache_misses: int = 0
    db_query_times: deque = field(default_factory=lambda: deque(maxlen=100))
    cpu_usage: deque = field(default_factory=lambda: deque(maxlen=60))
    memory_usage: deque = field(default_factory=lambda: deque(maxlen=60))
    request_count: int = 0
    error_count: int = 0
    active_connections: int = 0
    
    @property
    def avg_response_time(self) -> float:
        """Average response time in milliseconds."""
        return statistics.mean(self.response_times) if self.response_times else 0.0
    
    @property
    def cache_hit_ratio(self) -> float:
        """Cache hit ratio percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    @property
    def avg_db_query_time(self) -> float:
        """Average database query time in milliseconds."""
        return statistics.mean(self.db_query_times) if self.db_query_times else 0.0


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    l1_max_size: int = 1000
    l1_ttl: int = 300  # 5 minutes
    l2_ttl: int = 3600  # 1 hour
    l3_ttl: int = 7200  # 2 hours
    l4_ttl: int = 86400  # 24 hours
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    enable_serialization: bool = True
    warm_up_enabled: bool = True
    adaptive_ttl: bool = True


@dataclass
class DatabaseConfig:
    """Database optimization configuration."""
    connection_pool_size: int = 20
    max_overflow: int = 50
    pool_timeout: int = 30
    pool_recycle: int = 3600
    query_timeout: int = 30
    enable_query_cache: bool = True
    enable_connection_pooling: bool = True
    enable_read_replicas: bool = True
    shard_key: Optional[str] = None


class MultiLevelCache:
    """Advanced multi-level caching system."""
    
    def __init__(self, config: CacheConfig = None):
        """Initialize multi-level cache."""
        self.config = config or CacheConfig()
        self.l1_cache = {}  # In-memory cache
        self.l2_redis = None
        self.l3_memcached = None
        self.metrics = PerformanceMetrics()
        self._initialize_caches()
        
        # Prometheus metrics
        self.cache_requests = Counter('cache_requests_total', 'Total cache requests', ['level'])
        self.cache_hits = Counter('cache_hits_total', 'Total cache hits', ['level'])
        self.cache_misses = Counter('cache_misses_total', 'Total cache misses', ['level'])
        self.cache_response_time = Histogram('cache_response_time_seconds', 'Cache response time')
    
    def _initialize_caches(self):
        """Initialize cache connections."""
        try:
            # Redis L2 cache
            self.l2_redis = redis.Redis(
                host='localhost',
                port=6379,
                db=1,
                decode_responses=False,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            logger.info("✅ Redis L2 cache initialized")
        except Exception as e:
            logger.warning(f"Redis L2 cache not available: {e}")
        
        try:
            # Memcached L3 cache
            self.l3_memcached = memcache.Client(['127.0.0.1:11211'])
            logger.info("✅ Memcached L3 cache initialized")
        except Exception as e:
            logger.warning(f"Memcached L3 cache not available: {e}")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from multi-level cache."""
        start_time = time.time()
        
        try:
            # L1: In-memory cache
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                if entry['expires'] > time.time():
                    self.cache_requests.labels(level='l1').inc()
                    self.cache_hits.labels(level='l1').inc()
                    self.metrics.cache_hits += 1
                    return self._deserialize(entry['data'])
                else:
                    del self.l1_cache[key]
            
            # L2: Redis cache
            if self.l2_redis:
                try:
                    data = self.l2_redis.get(f"cache:{key}")
                    if data:
                        self.cache_requests.labels(level='l2').inc()
                        self.cache_hits.labels(level='l2').inc()
                        self.metrics.cache_hits += 1
                        
                        # Promote to L1
                        await self._set_l1(key, data, self.config.l1_ttl)
                        return self._deserialize(data)
                except Exception as e:
                    logger.warning(f"Redis cache error: {e}")
            
            # L3: Memcached cache
            if self.l3_memcached:
                try:
                    data = self.l3_memcached.get(f"cache:{key}")
                    if data:
                        self.cache_requests.labels(level='l3').inc()
                        self.cache_hits.labels(level='l3').inc()
                        self.metrics.cache_hits += 1
                        
                        # Promote to L2 and L1
                        await self._set_l2(key, data, self.config.l2_ttl)
                        await self._set_l1(key, data, self.config.l1_ttl)
                        return self._deserialize(data)
                except Exception as e:
                    logger.warning(f"Memcached cache error: {e}")
            
            # Cache miss
            self.cache_misses.labels(level='all').inc()
            self.metrics.cache_misses += 1
            return default
            
        finally:
            response_time = (time.time() - start_time) * 1000
            self.cache_response_time.observe(response_time / 1000)
            self.metrics.response_times.append(response_time)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in multi-level cache."""
        if ttl is None:
            ttl = self.config.l1_ttl
        
        serialized_data = self._serialize(value)
        
        # Set in all available cache levels
        await self._set_l1(key, serialized_data, ttl)
        
        if self.l2_redis:
            await self._set_l2(key, serialized_data, ttl or self.config.l2_ttl)
        
        if self.l3_memcached:
            await self._set_l3(key, serialized_data, ttl or self.config.l3_ttl)
        
        return True
    
    async def _set_l1(self, key: str, data: bytes, ttl: int):
        """Set in L1 memory cache."""
        # Implement LRU eviction if cache is full
        if len(self.l1_cache) >= self.config.l1_max_size:
            # Remove oldest entry
            oldest_key = min(self.l1_cache.keys(), 
                           key=lambda k: self.l1_cache[k]['accessed'])
            del self.l1_cache[oldest_key]
        
        self.l1_cache[key] = {
            'data': data,
            'expires': time.time() + ttl,
            'accessed': time.time()
        }
    
    async def _set_l2(self, key: str, data: bytes, ttl: int):
        """Set in L2 Redis cache."""
        try:
            self.l2_redis.setex(f"cache:{key}", ttl, data)
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
    
    async def _set_l3(self, key: str, data: bytes, ttl: int):
        """Set in L3 Memcached cache."""
        try:
            self.l3_memcached.set(f"cache:{key}", data, time=ttl)
        except Exception as e:
            logger.warning(f"Memcached set error: {e}")
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for caching."""
        if self.config.enable_serialization:
            serialized = pickle.dumps(data)
            
            if (self.config.enable_compression and 
                len(serialized) > self.config.compression_threshold):
                return gzip.compress(serialized)
            
            return serialized
        
        return str(data).encode()
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize cached data."""
        if self.config.enable_serialization:
            try:
                # Try decompression first
                if self.config.enable_compression:
                    try:
                        data = gzip.decompress(data)
                    except:
                        pass  # Not compressed
                
                return pickle.loads(data)
            except:
                return data.decode()
        
        return data.decode()
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate cache entry across all levels."""
        # Remove from L1
        if key in self.l1_cache:
            del self.l1_cache[key]
        
        # Remove from L2
        if self.l2_redis:
            try:
                self.l2_redis.delete(f"cache:{key}")
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Remove from L3
        if self.l3_memcached:
            try:
                self.l3_memcached.delete(f"cache:{key}")
            except Exception as e:
                logger.warning(f"Memcached delete error: {e}")
        
        return True
    
    async def warm_up(self, warm_up_data: Dict[str, Any]):
        """Warm up cache with frequently accessed data."""
        if not self.config.warm_up_enabled:
            return
        
        logger.info(f"🔥 Warming up cache with {len(warm_up_data)} entries")
        
        for key, value in warm_up_data.items():
            await self.set(key, value, self.config.l2_ttl)
        
        logger.info("✅ Cache warm-up completed")


class DatabaseOptimizer:
    """Advanced database optimization system."""
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database optimizer."""
        self.config = config or DatabaseConfig()
        self.query_cache = MultiLevelCache()
        self.connection_pools = {}
        self.query_stats = defaultdict(list)
        self.slow_queries = deque(maxlen=100)
        
        # Prometheus metrics
        self.db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')
        self.db_connections_active = Gauge('db_connections_active', 'Active database connections')
        self.db_queries_total = Counter('db_queries_total', 'Total database queries', ['operation'])
        
        self._setup_connection_pools()
    
    def _setup_connection_pools(self):
        """Setup optimized database connection pools."""
        # MongoDB connection pool
        try:
            self.mongo_client = AsyncIOMotorClient(
                'mongodb://localhost:27017',
                maxPoolSize=self.config.connection_pool_size,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                retryWrites=True
            )
            logger.info("✅ MongoDB connection pool initialized")
        except Exception as e:
            logger.warning(f"MongoDB connection error: {e}")
        
        # PostgreSQL connection pool
        try:
            self.pg_engine = create_engine(
                'postgresql://user:password@localhost/crisismap',
                poolclass=QueuePool,
                pool_size=self.config.connection_pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False
            )
            logger.info("✅ PostgreSQL connection pool initialized")
        except Exception as e:
            logger.warning(f"PostgreSQL connection error: {e}")
    
    @lru_cache(maxsize=1000)
    def _generate_query_hash(self, query: str, params: str = "") -> str:
        """Generate hash for query caching."""
        return hashlib.md5(f"{query}{params}".encode()).hexdigest()
    
    async def execute_query(
        self,
        query: str,
        params: Dict = None,
        cache_ttl: int = 300,
        use_cache: bool = True
    ) -> Any:
        """Execute optimized database query with caching."""
        start_time = time.time()
        params = params or {}
        
        try:
            # Generate cache key
            if use_cache:
                cache_key = self._generate_query_hash(query, str(params))
                cached_result = await self.query_cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute query
            if 'SELECT' in query.upper():
                self.db_queries_total.labels(operation='select').inc()
                result = await self._execute_select(query, params)
            elif 'INSERT' in query.upper():
                self.db_queries_total.labels(operation='insert').inc()
                result = await self._execute_insert(query, params)
            elif 'UPDATE' in query.upper():
                self.db_queries_total.labels(operation='update').inc()
                result = await self._execute_update(query, params)
            elif 'DELETE' in query.upper():
                self.db_queries_total.labels(operation='delete').inc()
                result = await self._execute_delete(query, params)
            else:
                self.db_queries_total.labels(operation='other').inc()
                result = await self._execute_other(query, params)
            
            # Cache result if appropriate
            if use_cache and 'SELECT' in query.upper():
                await self.query_cache.set(cache_key, result, cache_ttl)
            
            return result
            
        finally:
            # Record metrics
            query_time = (time.time() - start_time) * 1000
            self.db_query_duration.observe(query_time / 1000)
            self.query_stats[query].append(query_time)
            
            # Track slow queries
            if query_time > 1000:  # > 1 second
                self.slow_queries.append({
                    'query': query[:200],
                    'time': query_time,
                    'timestamp': datetime.now()
                })
    
    async def _execute_select(self, query: str, params: Dict) -> List[Dict]:
        """Execute optimized SELECT query."""
        # Implementation would depend on the specific database
        # This is a placeholder for the actual implementation
        pass
    
    async def _execute_insert(self, query: str, params: Dict) -> Any:
        """Execute optimized INSERT query."""
        pass
    
    async def _execute_update(self, query: str, params: Dict) -> Any:
        """Execute optimized UPDATE query."""
        pass
    
    async def _execute_delete(self, query: str, params: Dict) -> Any:
        """Execute optimized DELETE query."""
        pass
    
    async def _execute_other(self, query: str, params: Dict) -> Any:
        """Execute other database operations."""
        pass
    
    async def optimize_indexes(self, collection_name: str, query_patterns: List[Dict]):
        """Automatically optimize database indexes based on query patterns."""
        try:
            logger.info(f"🔍 Optimizing indexes for {collection_name}")
            
            # Analyze query patterns
            index_recommendations = self._analyze_query_patterns(query_patterns)
            
            # Create optimized indexes
            if hasattr(self, 'mongo_client'):
                collection = self.mongo_client.crisismap[collection_name]
                
                for index_spec in index_recommendations:
                    try:
                        await collection.create_index(
                            index_spec['keys'],
                            background=True,
                            name=index_spec.get('name')
                        )
                        logger.info(f"✅ Created index: {index_spec}")
                    except Exception as e:
                        logger.warning(f"Index creation failed: {e}")
            
        except Exception as e:
            logger.error(f"Index optimization error: {e}")
    
    def _analyze_query_patterns(self, query_patterns: List[Dict]) -> List[Dict]:
        """Analyze query patterns to recommend optimal indexes."""
        index_recommendations = []
        
        # Analyze field usage frequency
        field_usage = defaultdict(int)
        sort_patterns = defaultdict(int)
        
        for pattern in query_patterns:
            # Count field usage in filters
            for field in pattern.get('filter', {}):
                field_usage[field] += pattern.get('frequency', 1)
            
            # Count sort patterns
            for field, direction in pattern.get('sort', {}).items():
                sort_patterns[(field, direction)] += pattern.get('frequency', 1)
        
        # Recommend compound indexes for frequently used combinations
        frequent_fields = [field for field, count in field_usage.items() if count > 10]
        
        if len(frequent_fields) > 1:
            # Create compound index for most frequently used fields
            index_recommendations.append({
                'keys': [(field, 1) for field in frequent_fields[:3]],
                'name': f"compound_{'_'.join(frequent_fields[:3])}"
            })
        
        # Recommend indexes for sort operations
        for (field, direction), count in sort_patterns.items():
            if count > 5:
                index_recommendations.append({
                    'keys': [(field, direction)],
                    'name': f"sort_{field}_{direction}"
                })
        
        return index_recommendations
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate database performance report."""
        return {
            'total_queries': sum(len(queries) for queries in self.query_stats.values()),
            'avg_query_time': statistics.mean([
                time for queries in self.query_stats.values() for time in queries
            ]) if self.query_stats else 0,
            'slow_queries_count': len(self.slow_queries),
            'cache_hit_ratio': self.query_cache.metrics.cache_hit_ratio,
            'active_connections': self.db_connections_active._value._value,
            'top_slow_queries': list(self.slow_queries)[-10:]
        }


class ResponseTimeOptimizer:
    """Advanced response time optimization system."""
    
    def __init__(self):
        """Initialize response time optimizer."""
        self.request_metrics = defaultdict(list)
        self.optimization_strategies = {}
        self.route_optimizations = {}
        
        # Prometheus metrics
        self.request_duration = Histogram('request_duration_seconds', 'Request duration', ['method', 'endpoint'])
        self.response_size = Histogram('response_size_bytes', 'Response size in bytes')
        
    def optimize_response(self, func: Callable) -> Callable:
        """Decorator for response optimization."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute function with optimizations
                result = await func(*args, **kwargs)
                
                # Apply response optimizations
                optimized_result = await self._apply_response_optimizations(result)
                
                return optimized_result
                
            finally:
                # Record metrics
                duration = time.time() - start_time
                self.request_metrics[func.__name__].append(duration * 1000)
                self.request_duration.labels(
                    method='unknown',
                    endpoint=func.__name__
                ).observe(duration)
        
        return wrapper
    
    async def _apply_response_optimizations(self, response: Any) -> Any:
        """Apply various response optimizations."""
        if isinstance(response, dict):
            # JSON optimization
            response = await self._optimize_json_response(response)
        
        # Compression optimization
        response = await self._optimize_compression(response)
        
        return response
    
    async def _optimize_json_response(self, data: Dict) -> Dict:
        """Optimize JSON response structure."""
        # Remove null/empty values to reduce payload size
        def remove_empty(obj):
            if isinstance(obj, dict):
                return {k: remove_empty(v) for k, v in obj.items() 
                       if v is not None and v != "" and v != []}
            elif isinstance(obj, list):
                return [remove_empty(item) for item in obj if item is not None]
            return obj
        
        optimized = remove_empty(data)
        
        # Use faster JSON serialization
        if hasattr(orjson, 'dumps'):
            # orjson is much faster than standard json
            return orjson.loads(orjson.dumps(optimized))
        
        return optimized
    
    async def _optimize_compression(self, data: Any) -> Any:
        """Optimize response compression."""
        # This would typically be handled by middleware
        # but can be applied at the application level for specific responses
        return data
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get response time performance summary."""
        summary = {}
        
        for endpoint, times in self.request_metrics.items():
            if times:
                summary[endpoint] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'p95_time': np.percentile(times, 95),
                    'p99_time': np.percentile(times, 99),
                    'request_count': len(times)
                }
        
        return summary


class AutoScaler:
    """Intelligent auto-scaling system."""
    
    def __init__(self):
        """Initialize auto-scaler."""
        self.metrics_history = deque(maxlen=300)  # 5 minutes of data
        self.scaling_decisions = deque(maxlen=100)
        self.current_capacity = 1.0
        self.min_capacity = 0.5
        self.max_capacity = 10.0
        
        # Prometheus metrics
        self.scaling_events = Counter('scaling_events_total', 'Total scaling events', ['direction'])
        self.current_capacity_gauge = Gauge('current_capacity', 'Current system capacity')
        
    async def collect_metrics(self):
        """Collect system metrics for scaling decisions."""
        metrics = {
            'timestamp': time.time(),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'active_requests': self._get_active_requests(),
            'response_time': self._get_avg_response_time(),
            'error_rate': self._get_error_rate()
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def _get_active_requests(self) -> int:
        """Get current active request count."""
        # Implementation would depend on the web server
        return 0
    
    def _get_avg_response_time(self) -> float:
        """Get average response time."""
        # Implementation would get this from monitoring system
        return 0.0
    
    def _get_error_rate(self) -> float:
        """Get current error rate."""
        # Implementation would calculate from error metrics
        return 0.0
    
    async def make_scaling_decision(self) -> Dict[str, Any]:
        """Make intelligent scaling decision based on metrics."""
        if len(self.metrics_history) < 10:
            return {'action': 'no_change', 'reason': 'insufficient_data'}
        
        recent_metrics = list(self.metrics_history)[-10:]
        
        # Calculate scaling factors
        cpu_factor = statistics.mean([m['cpu_usage'] for m in recent_metrics])
        memory_factor = statistics.mean([m['memory_usage'] for m in recent_metrics])
        response_time_factor = statistics.mean([m['response_time'] for m in recent_metrics])
        
        # Make scaling decision
        if cpu_factor > 80 or memory_factor > 85 or response_time_factor > 2000:
            # Scale up
            if self.current_capacity < self.max_capacity:
                new_capacity = min(self.current_capacity * 1.5, self.max_capacity)
                self.scaling_events.labels(direction='up').inc()
                return {
                    'action': 'scale_up',
                    'new_capacity': new_capacity,
                    'reason': f'High resource usage: CPU={cpu_factor:.1f}%, Mem={memory_factor:.1f}%'
                }
        
        elif cpu_factor < 30 and memory_factor < 40 and response_time_factor < 500:
            # Scale down
            if self.current_capacity > self.min_capacity:
                new_capacity = max(self.current_capacity * 0.8, self.min_capacity)
                self.scaling_events.labels(direction='down').inc()
                return {
                    'action': 'scale_down',
                    'new_capacity': new_capacity,
                    'reason': f'Low resource usage: CPU={cpu_factor:.1f}%, Mem={memory_factor:.1f}%'
                }
        
        return {'action': 'no_change', 'reason': 'metrics_within_thresholds'}
    
    async def apply_scaling(self, decision: Dict[str, Any]):
        """Apply scaling decision."""
        if decision['action'] in ['scale_up', 'scale_down']:
            old_capacity = self.current_capacity
            self.current_capacity = decision['new_capacity']
            self.current_capacity_gauge.set(self.current_capacity)
            
            logger.info(f"🔄 Scaling {decision['action']}: {old_capacity} -> {self.current_capacity}")
            
            # Record scaling decision
            self.scaling_decisions.append({
                'timestamp': time.time(),
                'action': decision['action'],
                'old_capacity': old_capacity,
                'new_capacity': self.current_capacity,
                'reason': decision['reason']
            })


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Advanced performance monitoring middleware."""
    
    def __init__(self, app, optimizer_engine):
        """Initialize performance middleware."""
        super().__init__(app)
        self.optimizer = optimizer_engine
        
        # Prometheus metrics
        self.requests_total = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
        self.request_duration = Histogram('request_duration_seconds', 'Request duration')
        self.response_size_bytes = Histogram('response_size_bytes', 'Response size')
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with performance monitoring."""
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            self.requests_total.labels(method=method, endpoint=path).inc()
            self.request_duration.observe(duration)
            
            # Get response size
            response_size = len(response.body) if hasattr(response, 'body') else 0
            self.response_size_bytes.observe(response_size)
            
            # Update optimizer metrics
            self.optimizer.metrics.response_times.append(duration * 1000)
            self.optimizer.metrics.request_count += 1
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration * 1000:.2f}ms"
            response.headers['X-Cache-Status'] = 'MISS'  # Would be set by cache layer
            
            return response
            
        except Exception as e:
            # Record error
            self.optimizer.metrics.error_count += 1
            raise


class PerformanceOptimizationEngine:
    """Main performance optimization engine."""
    
    def __init__(
        self,
        cache_config: CacheConfig = None,
        db_config: DatabaseConfig = None,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    ):
        """Initialize performance optimization engine."""
        self.strategy = strategy
        self.cache = MultiLevelCache(cache_config)
        self.db_optimizer = DatabaseOptimizer(db_config)
        self.response_optimizer = ResponseTimeOptimizer()
        self.auto_scaler = AutoScaler()
        self.metrics = PerformanceMetrics()
        
        # Background tasks
        self.monitoring_task = None
        self.optimization_task = None
        
        logger.info(f"🚀 Performance Optimization Engine initialized with {strategy.value} strategy")
    
    async def start_optimization(self):
        """Start background optimization tasks."""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.optimization_task = asyncio.create_task(self._optimization_loop())
        
        logger.info("✅ Performance optimization tasks started")
    
    async def stop_optimization(self):
        """Stop background optimization tasks."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.optimization_task:
            self.optimization_task.cancel()
        
        logger.info("🛑 Performance optimization tasks stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                # Collect system metrics
                await self.auto_scaler.collect_metrics()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _optimization_loop(self):
        """Background optimization loop."""
        while True:
            try:
                # Make scaling decisions
                scaling_decision = await self.auto_scaler.make_scaling_decision()
                if scaling_decision['action'] != 'no_change':
                    await self.auto_scaler.apply_scaling(scaling_decision)
                
                # Optimize cache based on usage patterns
                await self._optimize_cache_strategy()
                
                # Optimize database queries
                await self._optimize_database_performance()
                
                await asyncio.sleep(60)  # Optimize every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(60)
    
    def _update_performance_metrics(self):
        """Update system performance metrics."""
        # Update CPU and memory usage
        self.metrics.cpu_usage.append(psutil.cpu_percent())
        self.metrics.memory_usage.append(psutil.virtual_memory().percent)
        
        # Update active connections
        self.metrics.active_connections = len(psutil.net_connections())
    
    async def _optimize_cache_strategy(self):
        """Optimize caching strategy based on usage patterns."""
        hit_ratio = self.cache.metrics.cache_hit_ratio
        
        if hit_ratio < 50:  # Low hit ratio
            # Increase cache TTL for better retention
            self.cache.config.l1_ttl = min(self.cache.config.l1_ttl * 1.2, 1800)
            self.cache.config.l2_ttl = min(self.cache.config.l2_ttl * 1.2, 7200)
        elif hit_ratio > 90:  # Very high hit ratio
            # Decrease cache TTL to save memory
            self.cache.config.l1_ttl = max(self.cache.config.l1_ttl * 0.9, 60)
            self.cache.config.l2_ttl = max(self.cache.config.l2_ttl * 0.9, 600)
    
    async def _optimize_database_performance(self):
        """Optimize database performance based on query patterns."""
        # Analyze slow queries and suggest optimizations
        if self.db_optimizer.slow_queries:
            logger.info(f"⚠️ Detected {len(self.db_optimizer.slow_queries)} slow queries")
            
            # Group similar queries
            similar_queries = self._group_similar_queries(self.db_optimizer.slow_queries)
            
            # Suggest index optimizations
            for query_group in similar_queries:
                await self._suggest_query_optimizations(query_group)
    
    def _group_similar_queries(self, slow_queries: List[Dict]) -> List[List[Dict]]:
        """Group similar slow queries for optimization."""
        # Simple grouping by query pattern (first 50 characters)
        groups = defaultdict(list)
        
        for query in slow_queries:
            pattern = query['query'][:50]
            groups[pattern].append(query)
        
        return list(groups.values())
    
    async def _suggest_query_optimizations(self, query_group: List[Dict]):
        """Suggest optimizations for a group of similar queries."""
        # This would analyze the queries and suggest specific optimizations
        # For now, just log the suggestion
        if len(query_group) > 3:
            avg_time = statistics.mean([q['time'] for q in query_group])
            logger.info(f"💡 Optimization suggestion: Query pattern '{query_group[0]['query'][:50]}...' "
                       f"executed {len(query_group)} times with avg time {avg_time:.2f}ms")
    
    async def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'strategy': self.strategy.value,
            'cache_performance': {
                'hit_ratio': self.cache.metrics.cache_hit_ratio,
                'avg_response_time': self.cache.metrics.avg_response_time,
                'total_requests': self.cache.metrics.cache_hits + self.cache.metrics.cache_misses
            },
            'database_performance': await self.db_optimizer.get_performance_report(),
            'response_times': self.response_optimizer.get_performance_summary(),
            'system_metrics': {
                'avg_cpu_usage': statistics.mean(self.metrics.cpu_usage) if self.metrics.cpu_usage else 0,
                'avg_memory_usage': statistics.mean(self.metrics.memory_usage) if self.metrics.memory_usage else 0,
                'total_requests': self.metrics.request_count,
                'error_rate': (self.metrics.error_count / max(self.metrics.request_count, 1)) * 100
            },
            'scaling_status': {
                'current_capacity': self.auto_scaler.current_capacity,
                'recent_decisions': list(self.auto_scaler.scaling_decisions)[-5:]
            }
        }
    
    def get_middleware(self) -> PerformanceMiddleware:
        """Get performance monitoring middleware."""
        return PerformanceMiddleware(None, self)


# Global optimizer instance
_optimizer_engine = None

def get_performance_optimizer() -> PerformanceOptimizationEngine:
    """Get global performance optimizer instance."""
    global _optimizer_engine
    if _optimizer_engine is None:
        _optimizer_engine = PerformanceOptimizationEngine()
    return _optimizer_engine


# Decorators for easy optimization
def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = await optimizer.cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await optimizer.cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def optimized_response(func: Callable) -> Callable:
    """Decorator for response optimization."""
    optimizer = get_performance_optimizer()
    return optimizer.response_optimizer.optimize_response(func)