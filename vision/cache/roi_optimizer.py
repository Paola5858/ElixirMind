"""
ROI Optimizer: Dynamic optimization of Regions of Interest.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

class ROIOptimizer:
    def __init__(self, config):
        self.config = config
        self.roi_history = {}
        self.performance_stats = {}

    def optimize_roi(self, roi_name, detections, screen_size):
        """Optimize ROI based on detection performance."""
        if roi_name not in self.roi_history:
            self.roi_history[roi_name] = []

        self.roi_history[roi_name].append(detections)

        # Keep only recent history
        if len(self.roi_history[roi_name]) > 10:
            self.roi_history[roi_name].pop(0)

        # Calculate optimal ROI
        if len(self.roi_history[roi_name]) >= 5:
            avg_detections = np.mean(self.roi_history[roi_name])
            if avg_detections < 0.1:  # Low detection rate
                return self.expand_roi(roi_name, screen_size)
            elif avg_detections > 0.8:  # High detection rate
                return self.contract_roi(roi_name)

        return self.config.get(f'roi_{roi_name}', {})

    def expand_roi(self, roi_name, screen_size):
        """Expand ROI for better coverage."""
        current_roi = self.config.get(f'roi_{roi_name}', {})
        expanded = {
            'x': max(0, current_roi.get('x', 0) - 10),
            'y': max(0, current_roi.get('y', 0) - 10),
            'width': min(screen_size[0], current_roi.get('width', 100) + 20),
            'height': min(screen_size[1], current_roi.get('height', 100) + 20)
        }
        logger.info(f"Expanded ROI {roi_name}: {expanded}")
        return expanded

    def contract_roi(self, roi_name):
        """Contract ROI for better precision."""
        current_roi = self.config.get(f'roi_{roi_name}', {})
        contracted = {
            'x': current_roi.get('x', 0) + 5,
            'y': current_roi.get('y', 0) + 5,
            'width': max(50, current_roi.get('width', 100) - 10),
            'height': max(50, current_roi.get('height', 100) - 10)
        }
        logger.info(f"Contracted ROI {roi_name}: {contracted}")
        return contracted

    def reset_stats(self, roi_name):
        """Reset performance stats for ROI."""
        if roi_name in self.roi_history:
            self.roi_history[roi_name].clear()
