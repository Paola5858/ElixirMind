"""
Query Optimizer: Optimizes database queries for better performance.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import Select
import psutil

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """
    Optimizes database queries and provides performance monitoring.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Optimization settings
        self.enable_caching = self.config.get('enable_caching', True)
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5 minutes
        self.slow_query_threshold = self.config.get('slow_query_threshold', 1.0)  # seconds

        # Query cache
        self.query_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

        # Performance monitoring
        self.query_stats = []
        self.max_stats_history = 1000

        logger.info("Query Optimizer initialized")

    def optimize_query(self, query: Query, context: Dict = None) -> Query:
        """
        Optimize a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            context: Query context information

        Returns:
            Optimized query
        """
        context = context or {}

        # Apply various optimizations
        query = self._add_selective_filtering(query, context)
        query = self._add_index_hints(query, context)
        query = self._optimize_joins(query, context)
        query = self._add_query_limits(query, context)

        return query

    def execute_with_monitoring(self, session: Session, query: Query,
                               description: str = "") -> Any:
        """
        Execute query with performance monitoring.

        Args:
            session: Database session
            query: Query to execute
            description: Query description

        Returns:
            Query results
        """
        start_time = time.time()
        query_hash = self._hash_query(query)

        # Check cache first
        if self.enable_caching and query_hash in self.query_cache:
            cache_entry = self.query_cache[query_hash]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                self.cache_stats['hits'] += 1
                logger.debug(f"Query cache hit: {description}")
                return cache_entry['result']
            else:
                # Cache expired
                del self.query_cache[query_hash]
                self.cache_stats['evictions'] += 1

        self.cache_stats['misses'] += 1

        try:
            # Execute query
            result = session.execute(query)

            # Convert to list for caching (consumes the result)
            result_list = result.fetchall() if hasattr(result, 'fetchall') else result

            execution_time = time.time() - start_time

            # Cache result if appropriate
            if self._should_cache_query(query, execution_time):
                self.query_cache[query_hash] = {
                    'result': result_list,
                    'timestamp': time.time(),
                    'execution_time': execution_time
                }

            # Record statistics
            self._record_query_stats(query_hash, execution_time, description, success=True)

            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {description} ({execution_time:.2f}s)")

            return result_list

        except Exception as e:
            execution_time = time.time() - start_time
            self._record_query_stats(query_hash, execution_time, description, success=False, error=str(e))
            logger.error(f"Query execution failed: {description} - {e}")
            raise

    def get_performance_report(self) -> Dict:
        """
        Get query performance report.

        Returns:
            Dict with performance statistics
        """
        if not self.query_stats:
            return {'message': 'No query statistics available'}

        total_queries = len(self.query_stats)
        successful_queries = len([s for s in self.query_stats if s['success']])
        failed_queries = total_queries - successful_queries

        execution_times = [s['execution_time'] for s in self.query_stats if s['success']]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        max_execution_time = max(execution_times) if execution_times else 0
        min_execution_time = min(execution_times) if execution_times else 0

        slow_queries = len([s for s in self.query_stats
                          if s['success'] and s['execution_time'] > self.slow_query_threshold])

        report = {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'success_rate': successful_queries / total_queries if total_queries > 0 else 0,
            'avg_execution_time': avg_execution_time,
            'max_execution_time': max_execution_time,
            'min_execution_time': min_execution_time,
            'slow_queries': slow_queries,
            'cache_stats': self.cache_stats.copy(),
            'cache_hit_rate': self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses'])
                           if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0
        }

        return report

    def clear_cache(self, pattern: str = None):
        """
        Clear query cache.

        Args:
            pattern: Pattern to match for selective clearing (optional)
        """
        if pattern:
            keys_to_remove = [k for k in self.query_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.query_cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
        else:
            cache_size = len(self.query_cache)
            self.query_cache.clear()
            logger.info(f"Cleared all {cache_size} cache entries")

    def analyze_query_plan(self, session: Session, query: Query) -> Dict:
        """
        Analyze query execution plan.

        Args:
            session: Database session
            query: Query to analyze

        Returns:
            Dict with query plan analysis
        """
        try:
            # Get EXPLAIN output
            explain_query = text(f"EXPLAIN QUERY PLAN {str(query)}")
            result = session.execute(explain_query)
            plan = result.fetchall()

            analysis = {
                'query_plan': [dict(row) for row in plan],
                'estimated_cost': self._estimate_query_cost(plan),
                'uses_indexes': self._check_index_usage(plan),
                'recommendations': self._generate_query_recommendations(plan)
            }

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze query plan: {e}")
            return {'error': str(e)}

    def _add_selective_filtering(self, query: Query, context: Dict) -> Query:
        """Add selective filtering to reduce data scanned."""
        # Add date range filters if context provides them
        if 'date_from' in context and 'date_to' in context:
            date_column = getattr(query.column_descriptions[0]['entity'], 'timestamp', None)
            if date_column is not None:
                query = query.filter(
                    and_(
                        date_column >= context['date_from'],
                        date_column <= context['date_to']
                    )
                )

        # Add limit for large result sets
        if 'max_results' in context:
            query = query.limit(context['max_results'])

        return query

    def _add_index_hints(self, query: Query, context: Dict) -> Query:
        """Add index hints for better query performance."""
        # This is database-specific and would need implementation
        # for the specific database being used
        return query

    def _optimize_joins(self, query: Query, context: Dict) -> Query:
        """Optimize join operations."""
        # Add join hints or reorder joins for better performance
        return query

    def _add_query_limits(self, query: Query, context: Dict) -> Query:
        """Add reasonable limits to prevent excessive resource usage."""
        # Add default limit if not specified and no aggregation
        if not hasattr(query, '_limit') and not context.get('no_limit', False):
            default_limit = context.get('default_limit', 1000)
            query = query.limit(default_limit)

        return query

    def _hash_query(self, query: Query) -> str:
        """Generate hash for query caching."""
        query_str = str(query)
        return str(hash(query_str))

    def _should_cache_query(self, query: Query, execution_time: float) -> bool:
        """Determine if query result should be cached."""
        if not self.enable_caching:
            return False

        # Cache expensive queries
        if execution_time > 0.1:  # More than 100ms
            return True

        # Cache aggregate queries
        query_str = str(query).upper()
        if any(keyword in query_str for keyword in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']):
            return True

        return False

    def _record_query_stats(self, query_hash: str, execution_time: float,
                          description: str, success: bool, error: str = None):
        """Record query execution statistics."""
        stat_entry = {
            'timestamp': time.time(),
            'query_hash': query_hash,
            'execution_time': execution_time,
            'description': description,
            'success': success,
            'error': error
        }

        self.query_stats.append(stat_entry)

        # Maintain history limit
        if len(self.query_stats) > self.max_stats_history:
            self.query_stats = self.query_stats[-self.max_stats_history:]

    def _estimate_query_cost(self, query_plan: List) -> float:
        """Estimate query execution cost from plan."""
        # Simple cost estimation based on plan
        cost = 0.0
        for step in query_plan:
            if 'SCAN' in str(step).upper():
                cost += 10.0  # Table scan is expensive
            elif 'SEARCH' in str(step).upper():
                cost += 1.0   # Index search is cheaper
        return cost

    def _check_index_usage(self, query_plan: List) -> bool:
        """Check if query uses indexes effectively."""
        for step in query_plan:
            if 'INDEX' in str(step).upper():
                return True
        return False

    def _generate_query_recommendations(self, query_plan: List) -> List[str]:
        """Generate query optimization recommendations."""
        recommendations = []

        plan_text = str(query_plan).upper()

        if 'SCAN TABLE' in plan_text and 'INDEX' not in plan_text:
            recommendations.append("Consider adding indexes on frequently queried columns")

        if 'MULTIPLE SCANS' in plan_text:
            recommendations.append("Query might benefit from query restructuring")

        return recommendations

class QueryBuilder:
    """
    Helper class for building optimized queries.
    """

    def __init__(self, session: Session, optimizer: QueryOptimizer = None):
        self.session = session
        self.optimizer = optimizer or QueryOptimizer()

    def build_match_query(self, filters: Dict = None) -> Query:
        """
        Build optimized match query.

        Args:
            filters: Query filters

        Returns:
            Optimized query
        """
        from storage.models import Match

        query = self.session.query(Match)

        if filters:
            if 'result' in filters:
                query = query.filter(Match.result == filters['result'])
            if 'deck_id' in filters:
                query = query.filter(Match.deck_id == filters['deck_id'])
            if 'date_from' in filters:
                query = query.filter(Match.timestamp >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(Match.timestamp <= filters['date_to'])

        # Apply optimizations
        context = {'query_type': 'match_analysis'}
        query = self.optimizer.optimize_query(query, context)

        return query

    def build_performance_query(self, metric_type: str = None,
                               time_range: tuple = None) -> Query:
        """
        Build optimized performance metrics query.

        Args:
            metric_type: Type of metric to query
            time_range: (start_time, end_time) tuple

        Returns:
            Optimized query
        """
        from storage.models import PerformanceMetrics

        query = self.session.query(
            PerformanceMetrics.metric_type,
            func.avg(PerformanceMetrics.value).label('avg_value'),
            func.max(PerformanceMetrics.value).label('max_value'),
            func.min(PerformanceMetrics.value).label('min_value'),
            func.count(PerformanceMetrics.id).label('count')
        )

        if metric_type:
            query = query.filter(PerformanceMetrics.metric_type == metric_type)

        if time_range:
            start_time, end_time = time_range
            query = query.filter(
                and_(
                    PerformanceMetrics.timestamp >= start_time,
                    PerformanceMetrics.timestamp <= end_time
                )
            )

        query = query.group_by(PerformanceMetrics.metric_type)

        # Apply optimizations
        context = {'query_type': 'performance_aggregation'}
        query = self.optimizer.optimize_query(query, context)

        return query
