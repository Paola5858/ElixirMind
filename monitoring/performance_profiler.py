"""
Performance Profiler: Monitors CPU, memory, and GPU usage.
"""

import psutil
import time
import logging
from typing import Dict, List
import GPUtil

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """
    Monitors system performance metrics including CPU, memory, and GPU.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.history = []
        self.max_history = self.config.get('max_history', 1000)
        self.sample_interval = self.config.get('sample_interval', 1.0)

        # Initialize metrics
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.memory_used = 0
        self.memory_total = 0
        self.gpu_usage = []
        self.gpu_memory = []

        logger.info("Performance Profiler initialized")

    def start_monitoring(self):
        """Start continuous performance monitoring."""
        logger.info("Starting performance monitoring...")
        # This would typically run in a separate thread
        pass

    def stop_monitoring(self):
        """Stop performance monitoring."""
        logger.info("Stopping performance monitoring...")

    def get_current_metrics(self) -> Dict:
        """
        Get current performance metrics.

        Returns:
            Dict containing CPU, memory, and GPU metrics
        """
        # CPU metrics
        self.cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory metrics
        memory = psutil.virtual_memory()
        self.memory_percent = memory.percent
        self.memory_used = memory.used
        self.memory_total = memory.total

        # GPU metrics (if available)
        try:
            gpus = GPUtil.getGPUs()
            self.gpu_usage = [gpu.load * 100 for gpu in gpus]
            self.gpu_memory = [gpu.memoryUsed for gpu in gpus]
        except Exception as e:
            logger.debug(f"GPU monitoring not available: {e}")
            self.gpu_usage = []
            self.gpu_memory = []

        metrics = {
            'timestamp': time.time(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used / (1024 * 1024),
            'memory_total_mb': self.memory_total / (1024 * 1024),
            'gpu_usage': self.gpu_usage,
            'gpu_memory_mb': self.gpu_memory
        }

        # Add to history
        self.history.append(metrics)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return metrics

    def get_average_metrics(self, window_seconds: int = 60) -> Dict:
        """
        Get average metrics over a time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Dict with averaged metrics
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        # Filter metrics within window
        window_metrics = [
            m for m in self.history
            if m['timestamp'] >= window_start
        ]

        if not window_metrics:
            return self.get_current_metrics()

        # Calculate averages
        avg_metrics = {
            'cpu_percent_avg': sum(m['cpu_percent'] for m in window_metrics) / len(window_metrics),
            'memory_percent_avg': sum(m['memory_percent'] for m in window_metrics) / len(window_metrics),
            'memory_used_mb_avg': sum(m['memory_used_mb'] for m in window_metrics) / len(window_metrics),
            'samples': len(window_metrics),
            'window_seconds': window_seconds
        }

        return avg_metrics

    def check_thresholds(self, thresholds: Dict) -> List[str]:
        """
        Check if current metrics exceed thresholds.

        Args:
            thresholds: Dict with threshold values

        Returns:
            List of exceeded threshold messages
        """
        alerts = []
        metrics = self.get_current_metrics()

        # CPU threshold
        if 'cpu_percent' in thresholds and metrics['cpu_percent'] > thresholds['cpu_percent']:
            alerts.append(f"CPU usage {metrics['cpu_percent']:.1f}% exceeds threshold {thresholds['cpu_percent']}%")

        # Memory threshold
        if 'memory_percent' in thresholds and metrics['memory_percent'] > thresholds['memory_percent']:
            alerts.append(f"Memory usage {metrics['memory_percent']:.1f}% exceeds threshold {thresholds['memory_percent']}%")

        # GPU thresholds
        if self.gpu_usage and 'gpu_percent' in thresholds:
            for i, gpu_usage in enumerate(self.gpu_usage):
                if gpu_usage > thresholds['gpu_percent']:
                    alerts.append(f"GPU {i} usage {gpu_usage:.1f}% exceeds threshold {thresholds['gpu_percent']}%")

        return alerts

    def get_system_info(self) -> Dict:
        """
        Get system information.

        Returns:
            Dict with system details
        """
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'gpu_count': len(GPUtil.getGPUs()) if GPUtil.getGPUs() else 0,
            'platform': psutil.platform
        }

    def clear_history(self):
        """Clear metrics history."""
        self.history.clear()
        logger.info("Performance history cleared")
