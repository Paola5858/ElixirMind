"""
Bottleneck Detector: Identifies performance bottlenecks in the system.
"""

import time
import logging
from typing import Dict, List, Tuple, Optional
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class BottleneckDetector:
    """
    Detects and analyzes performance bottlenecks in the bot system.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.analysis_window = self.config.get('analysis_window_seconds', 60)
        self.bottleneck_threshold = self.config.get('bottleneck_threshold', 0.8)

        # Component performance tracking
        self.component_times = defaultdict(list)
        self.component_locks = defaultdict(threading.Lock)

        # Bottleneck history
        self.bottleneck_history = []

        # Performance baselines
        self.baselines = {}

        logger.info("Bottleneck Detector initialized")

    def track_component(self, component_name: str, execution_time: float, metadata: Dict = None):
        """
        Track execution time for a component.

        Args:
            component_name: Name of the component
            execution_time: Time taken in seconds
            metadata: Additional metadata about the execution
        """
        with self.component_locks[component_name]:
            timestamp = time.time()
            entry = {
                'timestamp': timestamp,
                'execution_time': execution_time,
                'metadata': metadata or {}
            }
            self.component_times[component_name].append(entry)

            # Keep only recent entries
            cutoff_time = timestamp - self.analysis_window
            self.component_times[component_name] = [
                e for e in self.component_times[component_name]
                if e['timestamp'] > cutoff_time
            ]

    def analyze_bottlenecks(self) -> List[Dict]:
        """
        Analyze current bottlenecks in the system.

        Returns:
            List of bottleneck information dicts
        """
        bottlenecks = []
        current_time = time.time()

        for component, times in self.component_times.items():
            if not times:
                continue

            # Calculate metrics
            execution_times = [t['execution_time'] for t in times]
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            total_time = sum(execution_times)
            frequency = len(times) / self.analysis_window

            # Calculate bottleneck score (0-1, higher = more bottleneck)
            bottleneck_score = self._calculate_bottleneck_score(component, execution_times)

            if bottleneck_score >= self.bottleneck_threshold:
                bottleneck_info = {
                    'component': component,
                    'bottleneck_score': bottleneck_score,
                    'avg_execution_time': avg_time,
                    'max_execution_time': max_time,
                    'total_time_window': total_time,
                    'call_frequency': frequency,
                    'call_count': len(times),
                    'severity': self._classify_severity(bottleneck_score),
                    'recommendations': self._generate_recommendations(component, bottleneck_score)
                }
                bottlenecks.append(bottleneck_info)

        # Sort by bottleneck score
        bottlenecks.sort(key=lambda x: x['bottleneck_score'], reverse=True)

        # Record in history
        if bottlenecks:
            self.bottleneck_history.append({
                'timestamp': current_time,
                'bottlenecks': bottlenecks
            })

        return bottlenecks

    def get_component_performance(self, component_name: str) -> Dict:
        """
        Get detailed performance metrics for a component.

        Args:
            component_name: Name of the component

        Returns:
            Dict with performance metrics
        """
        with self.component_locks[component_name]:
            times = self.component_times[component_name]

            if not times:
                return {
                    'component': component_name,
                    'call_count': 0,
                    'avg_time': 0.0,
                    'max_time': 0.0,
                    'min_time': 0.0,
                    'total_time': 0.0
                }

            execution_times = [t['execution_time'] for t in times]

            return {
                'component': component_name,
                'call_count': len(times),
                'avg_time': sum(execution_times) / len(execution_times),
                'max_time': max(execution_times),
                'min_time': min(execution_times),
                'total_time': sum(execution_times),
                'frequency_hz': len(times) / self.analysis_window
            }

    def set_baseline(self, component_name: str, baseline_time: float):
        """
        Set performance baseline for a component.

        Args:
            component_name: Name of the component
            baseline_time: Expected execution time in seconds
        """
        self.baselines[component_name] = baseline_time
        logger.info(f"Set baseline for {component_name}: {baseline_time:.4f}s")

    def get_bottleneck_report(self) -> str:
        """
        Generate a comprehensive bottleneck report.

        Returns:
            Formatted bottleneck report
        """
        bottlenecks = self.analyze_bottlenecks()

        report_lines = ["Bottleneck Analysis Report", "=" * 50]

        if not bottlenecks:
            report_lines.append("No significant bottlenecks detected")
            return "\n".join(report_lines)

        report_lines.append(f"Found {len(bottlenecks)} bottleneck(s):")
        report_lines.append("")

        for i, bottleneck in enumerate(bottlenecks, 1):
            report_lines.append(f"{i}. {bottleneck['component']}")
            report_lines.append(f"   Severity: {bottleneck['severity']}")
            report_lines.append(f"   Bottleneck Score: {bottleneck['bottleneck_score']:.3f}")
            report_lines.append(f"   Avg Time: {bottleneck['avg_execution_time']:.4f}s")
            report_lines.append(f"   Max Time: {bottleneck['max_execution_time']:.4f}s")
            report_lines.append(f"   Frequency: {bottleneck['call_frequency']:.2f} Hz")
            report_lines.append(f"   Recommendations:")
            for rec in bottleneck['recommendations']:
                report_lines.append(f"     - {rec}")
            report_lines.append("")

        return "\n".join(report_lines)

    def reset_component(self, component_name: str):
        """
        Reset tracking data for a component.

        Args:
            component_name: Name of the component
        """
        with self.component_locks[component_name]:
            self.component_times[component_name].clear()
        logger.info(f"Reset bottleneck tracking for component: {component_name}")

    def reset_all(self):
        """Reset all bottleneck tracking data."""
        for lock in self.component_locks.values():
            with lock:
                pass
        self.component_times.clear()
        self.bottleneck_history.clear()
        logger.info("Reset all bottleneck tracking data")

    def _calculate_bottleneck_score(self, component: str, execution_times: List[float]) -> float:
        """
        Calculate bottleneck score for a component.

        Returns:
            Score between 0 and 1 (higher = more bottleneck)
        """
        if not execution_times:
            return 0.0

        avg_time = sum(execution_times) / len(execution_times)

        # Factor 1: Execution time relative to baseline
        baseline_score = 0.0
        if component in self.baselines:
            baseline = self.baselines[component]
            if avg_time > baseline:
                baseline_score = min(1.0, (avg_time - baseline) / baseline)
        else:
            # Use statistical approach if no baseline
            sorted_times = sorted(execution_times)
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            baseline_score = min(1.0, p95 / 0.1)  # Assume 100ms is baseline

        # Factor 2: Variability (high variance indicates instability)
        if len(execution_times) > 1:
            mean = sum(execution_times) / len(execution_times)
            variance = sum((x - mean) ** 2 for x in execution_times) / len(execution_times)
            std_dev = variance ** 0.5
            variability_score = min(1.0, std_dev / mean) if mean > 0 else 0.0
        else:
            variability_score = 0.0

        # Factor 3: Frequency (high frequency calls are more critical)
        frequency = len(execution_times) / self.analysis_window
        frequency_score = min(1.0, frequency / 10.0)  # 10 Hz as high frequency

        # Combine factors (weighted average)
        bottleneck_score = (
            baseline_score * 0.5 +      # 50% weight on execution time
            variability_score * 0.3 +   # 30% weight on stability
            frequency_score * 0.2       # 20% weight on frequency
        )

        return bottleneck_score

    def _classify_severity(self, score: float) -> str:
        """Classify bottleneck severity."""
        if score >= 0.9:
            return "CRITICAL"
        elif score >= 0.7:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        elif score >= 0.3:
            return "LOW"
        else:
            return "MINOR"

    def _generate_recommendations(self, component: str, score: float) -> List[str]:
        """Generate recommendations for bottleneck mitigation."""
        recommendations = []

        if score >= 0.8:
            recommendations.append("Consider optimizing algorithm or reducing complexity")
            recommendations.append("Evaluate if component can be parallelized")
            recommendations.append("Consider caching results if applicable")

        if score >= 0.6:
            recommendations.append("Profile component execution in detail")
            recommendations.append("Check for memory leaks or inefficient data structures")

        if score >= 0.4:
            recommendations.append("Monitor component performance trends")
            recommendations.append("Consider load balancing if multiple instances")

        recommendations.append("Review recent code changes for performance regressions")

        return recommendations
