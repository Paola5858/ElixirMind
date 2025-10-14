"""
FPS Monitor: Monitors frames per second for vision processing.
"""

import time
import logging
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)

class FPSMonitor:
    """
    Monitors frames per second for vision processing and other operations.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.window_size = self.config.get('fps_window_size', 30)
        self.target_fps = self.config.get('target_fps', 30.0)

        # FPS tracking
        self.frame_times = deque(maxlen=self.window_size)
        self.current_fps = 0.0
        self.average_fps = 0.0
        self.min_fps = float('inf')
        self.max_fps = 0.0

        # Performance tracking
        self.total_frames = 0
        self.start_time = time.time()

        logger.info(f"FPS Monitor initialized with target {self.target_fps} FPS")

    def tick(self, frame_time: Optional[float] = None) -> float:
        """
        Record a frame/tick and calculate FPS.

        Args:
            frame_time: Time taken for this frame (optional, uses current time if None)

        Returns:
            Current FPS
        """
        current_time = time.time()

        if frame_time is None:
            # Use time since last tick
            if self.frame_times:
                frame_time = current_time - self.frame_times[-1]
            else:
                frame_time = 0.0

        self.frame_times.append(current_time)
        self.total_frames += 1

        # Calculate current FPS
        if len(self.frame_times) >= 2:
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span > 0:
                self.current_fps = (len(self.frame_times) - 1) / time_span
            else:
                self.current_fps = 0.0
        else:
            self.current_fps = 0.0

        # Update average FPS
        total_time = current_time - self.start_time
        if total_time > 0:
            self.average_fps = self.total_frames / total_time

        # Update min/max FPS
        if self.current_fps > 0:
            self.min_fps = min(self.min_fps, self.current_fps)
            self.max_fps = max(self.max_fps, self.current_fps)

        return self.current_fps

    def get_fps_stats(self) -> Dict:
        """
        Get comprehensive FPS statistics.

        Returns:
            Dict with FPS metrics
        """
        current_time = time.time()
        runtime = current_time - self.start_time

        return {
            'current_fps': self.current_fps,
            'average_fps': self.average_fps,
            'min_fps': self.min_fps if self.min_fps != float('inf') else 0.0,
            'max_fps': self.max_fps,
            'total_frames': self.total_frames,
            'runtime_seconds': runtime,
            'target_fps': self.target_fps,
            'fps_stability': self._calculate_stability()
        }

    def is_below_target(self, threshold_percent: float = 10.0) -> bool:
        """
        Check if current FPS is below target by a certain percentage.

        Args:
            threshold_percent: Percentage below target to trigger alert

        Returns:
            True if FPS is below threshold
        """
        if self.target_fps <= 0:
            return False

        threshold_fps = self.target_fps * (1.0 - threshold_percent / 100.0)
        return self.current_fps < threshold_fps

    def reset(self):
        """Reset FPS monitoring."""
        self.frame_times.clear()
        self.current_fps = 0.0
        self.average_fps = 0.0
        self.min_fps = float('inf')
        self.max_fps = 0.0
        self.total_frames = 0
        self.start_time = time.time()
        logger.info("FPS Monitor reset")

    def _calculate_stability(self) -> float:
        """
        Calculate FPS stability (lower variance = more stable).

        Returns:
            Stability score (0.0 to 1.0, higher is more stable)
        """
        if len(self.frame_times) < 3:
            return 1.0

        # Calculate frame time differences
        frame_times_list = list(self.frame_times)
        intervals = []
        for i in range(1, len(frame_times_list)):
            intervals.append(frame_times_list[i] - frame_times_list[i-1])

        if not intervals:
            return 1.0

        # Calculate coefficient of variation
        mean_interval = sum(intervals) / len(intervals)
        if mean_interval == 0:
            return 1.0

        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        cv = std_dev / mean_interval

        # Convert to stability score (lower CV = higher stability)
        stability = max(0.0, 1.0 - cv)
        return stability

    def get_performance_report(self) -> str:
        """
        Generate a performance report string.

        Returns:
            Formatted performance report
        """
        stats = self.get_fps_stats()

        report = ".2f"".2f"".2f"".2f"".2f"".2f"".2f"".2f"f"""
FPS Performance Report:
- Current FPS: {stats['current_fps']:.2f}
- Average FPS: {stats['average_fps']:.2f}
- Min FPS: {stats['min_fps']:.2f}
- Max FPS: {stats['max_fps']:.2f}
- Target FPS: {stats['target_fps']:.2f}
- Stability: {stats['fps_stability']:.2f}
- Total Frames: {stats['total_frames']}
- Runtime: {stats['runtime_seconds']:.1f}s
"""

        if self.is_below_target():
            report += f"⚠️  WARNING: FPS below target by {self.target_fps - self.current_fps:.2f} FPS\n"

        return report
