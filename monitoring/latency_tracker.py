"""
Latency Tracker: Monitors decision-making and action execution latency.
"""

import time
import logging
from typing import Dict, List, Optional, Callable
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class LatencyTracker:
    """
    Tracks latency for various operations in the bot system.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_samples = self.config.get('max_latency_samples', 1000)
        self.alert_threshold_ms = self.config.get('alert_threshold_ms', 100.0)

        # Latency storage: operation -> list of latencies
        self.latencies = defaultdict(lambda: deque(maxlen=self.max_samples))

        # Active operations: operation -> start_time
        self.active_operations = {}

        # Statistics
        self.operation_stats = {}

        logger.info("Latency Tracker initialized")

    def start_operation(self, operation_name: str):
        """
        Start timing an operation.

        Args:
            operation_name: Name of the operation to track
        """
        self.active_operations[operation_name] = time.time()

    def end_operation(self, operation_name: str) -> Optional[float]:
        """
        End timing an operation and record latency.

        Args:
            operation_name: Name of the operation

        Returns:
            Latency in milliseconds, or None if operation wasn't started
        """
        if operation_name not in self.active_operations:
            logger.warning(f"Operation '{operation_name}' ended without being started")
            return None

        start_time = self.active_operations.pop(operation_name)
        latency_ms = (time.time() - start_time) * 1000

        # Record latency
        self.latencies[operation_name].append(latency_ms)

        # Update statistics
        self._update_stats(operation_name)

        return latency_ms

    def measure_operation(self, operation_name: str, func: Callable, *args, **kwargs):
        """
        Measure the latency of a function call.

        Args:
            operation_name: Name of the operation
            func: Function to measure
            *args, **kwargs: Arguments for the function

        Returns:
            Result of the function call
        """
        self.start_operation(operation_name)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            self.end_operation(operation_name)

    def get_operation_stats(self, operation_name: str) -> Dict:
        """
        Get statistics for a specific operation.

        Args:
            operation_name: Name of the operation

        Returns:
            Dict with latency statistics
        """
        if operation_name not in self.operation_stats:
            return {
                'count': 0,
                'mean': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p95': 0.0,
                'p99': 0.0
            }

        return self.operation_stats[operation_name].copy()

    def get_all_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all operations.

        Returns:
            Dict of operation -> stats
        """
        return {op: self.get_operation_stats(op) for op in self.latencies.keys()}

    def check_latency_alerts(self) -> List[str]:
        """
        Check for operations exceeding latency thresholds.

        Returns:
            List of alert messages
        """
        alerts = []

        for operation, stats in self.operation_stats.items():
            if stats['p95'] > self.alert_threshold_ms:
                alerts.append(
                    f"High latency alert: {operation} "
                    f"P95={stats['p95']:.1f}ms > {self.alert_threshold_ms}ms"
                )

        return alerts

    def get_slowest_operations(self, limit: int = 5) -> List[Dict]:
        """
        Get the operations with highest average latency.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of dicts with operation info
        """
        operations = []
        for op, stats in self.operation_stats.items():
            operations.append({
                'operation': op,
                'mean_latency': stats['mean'],
                'p95_latency': stats['p95'],
                'count': stats['count']
            })

        # Sort by mean latency descending
        operations.sort(key=lambda x: x['mean_latency'], reverse=True)

        return operations[:limit]

    def reset_operation(self, operation_name: str):
        """
        Reset latency data for a specific operation.

        Args:
            operation_name: Name of the operation
        """
        if operation_name in self.latencies:
            self.latencies[operation_name].clear()
        if operation_name in self.operation_stats:
            del self.operation_stats[operation_name]
        if operation_name in self.active_operations:
            del self.active_operations[operation_name]

        logger.info(f"Reset latency tracking for operation: {operation_name}")

    def reset_all(self):
        """Reset all latency tracking data."""
        self.latencies.clear()
        self.operation_stats.clear()
        self.active_operations.clear()
        logger.info("Reset all latency tracking data")

    def _update_stats(self, operation_name: str):
        """Update statistics for an operation."""
        latencies = list(self.latencies[operation_name])

        if not latencies:
            return

        try:
            self.operation_stats[operation_name] = {
                'count': len(latencies),
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'min': min(latencies),
                'max': max(latencies),
                'p95': statistics.quantiles(latencies, n=20)[18],  # 95th percentile
                'p99': statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            }
        except statistics.StatisticsError:
            # Fallback for insufficient data
            self.operation_stats[operation_name] = {
                'count': len(latencies),
                'mean': sum(latencies) / len(latencies),
                'median': sorted(latencies)[len(latencies) // 2],
                'min': min(latencies),
                'max': max(latencies),
                'p95': max(latencies),
                'p99': max(latencies)
            }

    def get_latency_report(self) -> str:
        """
        Generate a comprehensive latency report.

        Returns:
            Formatted latency report
        """
        report_lines = ["Latency Report:", "=" * 50]

        all_stats = self.get_all_stats()
        if not all_stats:
            report_lines.append("No latency data available")
            return "\n".join(report_lines)

        # Sort by mean latency
        sorted_ops = sorted(all_stats.items(), key=lambda x: x[1]['mean'], reverse=True)

        for op, stats in sorted_ops:
            report_lines.append(f"\n{op}:")
            report_lines.append(f"  Count: {stats['count']}")
            report_lines.append(f"  Mean: {stats['mean']:.2f}ms")
            report_lines.append(f"  Median: {stats['median']:.2f}ms")
            report_lines.append(f"  P95: {stats['p95']:.2f}ms")
            report_lines.append(f"  P99: {stats['p99']:.2f}ms")
            report_lines.append(f"  Range: {stats['min']:.2f}ms - {stats['max']:.2f}ms")

        # Add alerts
        alerts = self.check_latency_alerts()
        if alerts:
            report_lines.append(f"\n⚠️  ALERTS ({len(alerts)}):")
            for alert in alerts:
                report_lines.append(f"  {alert}")

        return "\n".join(report_lines)
