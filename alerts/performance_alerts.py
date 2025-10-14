"""
Performance Alerts: Specialized alerts for performance monitoring.
"""

import logging
from typing import Dict, List
from .alert_manager import AlertManager, AlertType, AlertSeverity

logger = logging.getLogger(__name__)

class PerformanceAlerts:
    """
    Specialized alert system for performance monitoring.
    Integrates with monitoring components to generate alerts.
    """

    def __init__(self, alert_manager: AlertManager, config: Dict = None):
        self.alert_manager = alert_manager
        self.config = config or {}

        # Alert thresholds
        self.cpu_threshold = self.config.get('cpu_threshold', 80.0)
        self.memory_threshold = self.config.get('memory_threshold', 85.0)
        self.fps_threshold = self.config.get('fps_threshold', 20.0)
        self.latency_threshold_ms = self.config.get('latency_threshold_ms', 100.0)

        # Cooldown periods (seconds) to prevent alert spam
        self.alert_cooldowns = {
            'cpu_high': 300,      # 5 minutes
            'memory_high': 300,   # 5 minutes
            'fps_low': 60,        # 1 minute
            'latency_high': 120,  # 2 minutes
            'bottleneck': 600     # 10 minutes
        }

        self.last_alert_times = {}

        logger.info("Performance Alerts initialized")

    def check_performance_alerts(self, performance_data: Dict):
        """
        Check performance metrics and generate alerts if needed.

        Args:
            performance_data: Dict with performance metrics from monitoring components
        """
        current_time = performance_data.get('timestamp', 0)

        # CPU alerts
        if 'cpu_percent' in performance_data:
            self._check_cpu_alert(performance_data['cpu_percent'], current_time)

        # Memory alerts
        if 'memory_percent' in performance_data:
            self._check_memory_alert(performance_data['memory_percent'], current_time)

        # FPS alerts
        if 'fps' in performance_data:
            self._check_fps_alert(performance_data['fps'], current_time)

        # Latency alerts
        if 'latency_ms' in performance_data:
            self._check_latency_alert(performance_data['latency_ms'], current_time)

    def check_bottleneck_alerts(self, bottlenecks: List[Dict]):
        """
        Check for bottleneck alerts.

        Args:
            bottlenecks: List of bottleneck information
        """
        current_time = 0  # Would be passed in real implementation

        for bottleneck in bottlenecks:
            severity = bottleneck.get('severity', 'LOW')
            score = bottleneck.get('bottleneck_score', 0.0)

            if severity in ['HIGH', 'CRITICAL'] or score > 0.8:
                self._create_bottleneck_alert(bottleneck, current_time)

    def _check_cpu_alert(self, cpu_percent: float, current_time: float):
        """Check CPU usage and create alert if needed."""
        if cpu_percent > self.cpu_threshold:
            if self._can_alert('cpu_high', current_time):
                self.alert_manager.create_alert(
                    AlertType.PERFORMANCE,
                    AlertSeverity.HIGH,
                    "High CPU Usage Detected",
                    f"CPU usage is at {cpu_percent:.1f}%, exceeding threshold of {self.cpu_threshold}%",
                    source="performance_monitor",
                    metadata={
                        'cpu_percent': cpu_percent,
                        'threshold': self.cpu_threshold,
                        'recommendation': 'Check for CPU-intensive processes or optimize algorithms'
                    },
                    auto_resolve=True
                )
                self.last_alert_times['cpu_high'] = current_time

    def _check_memory_alert(self, memory_percent: float, current_time: float):
        """Check memory usage and create alert if needed."""
        if memory_percent > self.memory_threshold:
            if self._can_alert('memory_high', current_time):
                severity = AlertSeverity.CRITICAL if memory_percent > 95 else AlertSeverity.HIGH

                self.alert_manager.create_alert(
                    AlertType.PERFORMANCE,
                    severity,
                    "High Memory Usage Detected",
                    f"Memory usage is at {memory_percent:.1f}%, exceeding threshold of {self.memory_threshold}%",
                    source="performance_monitor",
                    metadata={
                        'memory_percent': memory_percent,
                        'threshold': self.memory_threshold,
                        'recommendation': 'Check for memory leaks or reduce memory-intensive operations'
                    },
                    auto_resolve=True
                )
                self.last_alert_times['memory_high'] = current_time

    def _check_fps_alert(self, fps: float, current_time: float):
        """Check FPS and create alert if needed."""
        if fps < self.fps_threshold:
            if self._can_alert('fps_low', current_time):
                severity = AlertSeverity.CRITICAL if fps < 10 else AlertSeverity.HIGH

                self.alert_manager.create_alert(
                    AlertType.PERFORMANCE,
                    severity,
                    "Low FPS Detected",
                    f"FPS dropped to {fps:.1f}, below threshold of {self.fps_threshold}",
                    source="fps_monitor",
                    metadata={
                        'fps': fps,
                        'threshold': self.fps_threshold,
                        'recommendation': 'Check vision processing pipeline or reduce image resolution'
                    },
                    auto_resolve=True
                )
                self.last_alert_times['fps_low'] = current_time

    def _check_latency_alert(self, latency_ms: float, current_time: float):
        """Check latency and create alert if needed."""
        if latency_ms > self.latency_threshold_ms:
            if self._can_alert('latency_high', current_time):
                severity = AlertSeverity.HIGH if latency_ms > 200 else AlertSeverity.MEDIUM

                self.alert_manager.create_alert(
                    AlertType.PERFORMANCE,
                    severity,
                    "High Latency Detected",
                    f"Operation latency is {latency_ms:.1f}ms, exceeding threshold of {self.latency_threshold_ms}ms",
                    source="latency_tracker",
                    metadata={
                        'latency_ms': latency_ms,
                        'threshold': self.latency_threshold_ms,
                        'recommendation': 'Profile code execution or optimize slow operations'
                    },
                    auto_resolve=True
                )
                self.last_alert_times['latency_high'] = current_time

    def _create_bottleneck_alert(self, bottleneck: Dict, current_time: float):
        """Create bottleneck alert."""
        if not self._can_alert('bottleneck', current_time):
            return

        component = bottleneck.get('component', 'unknown')
        score = bottleneck.get('bottleneck_score', 0.0)
        severity_str = bottleneck.get('severity', 'LOW')

        severity_map = {
            'CRITICAL': AlertSeverity.CRITICAL,
            'HIGH': AlertSeverity.HIGH,
            'MEDIUM': AlertSeverity.MEDIUM,
            'LOW': AlertSeverity.LOW
        }
        severity = severity_map.get(severity_str, AlertSeverity.MEDIUM)

        recommendations = bottleneck.get('recommendations', [])

        self.alert_manager.create_alert(
            AlertType.PERFORMANCE,
            severity,
            f"Performance Bottleneck: {component}",
            f"Bottleneck detected in {component} with score {score:.3f}",
            source="bottleneck_detector",
            metadata={
                'component': component,
                'bottleneck_score': score,
                'severity': severity_str,
                'recommendations': '; '.join(recommendations)
            },
            auto_resolve=False  # Bottlenecks need manual resolution
        )
        self.last_alert_times['bottleneck'] = current_time

    def _can_alert(self, alert_type: str, current_time: float) -> bool:
        """
        Check if enough time has passed since last alert of this type.

        Args:
            alert_type: Type of alert
            current_time: Current timestamp

        Returns:
            True if alert can be sent
        """
        if alert_type not in self.last_alert_times:
            return True

        cooldown = self.alert_cooldowns.get(alert_type, 60)
        time_since_last = current_time - self.last_alert_times[alert_type]

        return time_since_last >= cooldown

    def update_thresholds(self, new_thresholds: Dict):
        """
        Update alert thresholds.

        Args:
            new_thresholds: Dict with new threshold values
        """
        self.cpu_threshold = new_thresholds.get('cpu_threshold', self.cpu_threshold)
        self.memory_threshold = new_thresholds.get('memory_threshold', self.memory_threshold)
        self.fps_threshold = new_thresholds.get('fps_threshold', self.fps_threshold)
        self.latency_threshold_ms = new_thresholds.get('latency_threshold_ms', self.latency_threshold_ms)

        logger.info("Performance alert thresholds updated")

    def get_alert_status(self) -> Dict:
        """
        Get current alert status and cooldowns.

        Returns:
            Dict with alert status information
        """
        return {
            'thresholds': {
                'cpu_threshold': self.cpu_threshold,
                'memory_threshold': self.memory_threshold,
                'fps_threshold': self.fps_threshold,
                'latency_threshold_ms': self.latency_threshold_ms
            },
            'last_alert_times': self.last_alert_times.copy(),
            'cooldowns': self.alert_cooldowns.copy()
        }
