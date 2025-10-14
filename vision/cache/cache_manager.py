"""
Cache Manager: Manages detection cache for performance optimization.
"""

import time
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, max_size=1000, ttl=300):  # 5 minutes TTL
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key):
        """Get cached item if not expired."""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                self.cache.move_to_end(key)  # LRU
                return item['data']
            else:
                del self.cache[key]
        return None

    def put(self, key, data):
        """Put item in cache."""
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # Remove oldest
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    def clear(self):
        """Clear all cache."""
        self.cache.clear()

    def cleanup_expired(self):
        """Remove expired items."""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item['timestamp'] >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
