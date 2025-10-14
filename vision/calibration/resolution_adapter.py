"""
Resolution Adapter: Adapts ROIs for different screen resolutions.
"""

import logging

logger = logging.getLogger(__name__)

class ResolutionAdapter:
    def __init__(self, base_resolution=(1920, 1080)):
        self.base_resolution = base_resolution
        self.current_resolution = base_resolution

    def set_resolution(self, width, height):
        """Set current screen resolution."""
        self.current_resolution = (width, height)
        logger.info(f"Resolution set to: {width}x{height}")

    def adapt_roi(self, roi, target_resolution=None):
        """Adapt ROI coordinates for current resolution."""
        if target_resolution is None:
            target_resolution = self.current_resolution

        base_w, base_h = self.base_resolution
        target_w, target_h = target_resolution

        if base_w == target_w and base_h == target_h:
            return roi.copy()

        # Scale factors
        scale_x = target_w / base_w
        scale_y = target_h / base_h

        adapted_roi = roi.copy()
        adapted_roi['x'] = int(roi['x'] * scale_x)
        adapted_roi['y'] = int(roi['y'] * scale_y)
        adapted_roi['width'] = int(roi['width'] * scale_x)
        adapted_roi['height'] = int(roi['height'] * scale_y)

        return adapted_roi

    def adapt_multiple_rois(self, rois, target_resolution=None):
        """Adapt multiple ROIs."""
        adapted = {}
        for name, roi in rois.items():
            adapted[name] = self.adapt_roi(roi, target_resolution)
        return adapted

    def get_scaling_factors(self, target_resolution=None):
        """Get scaling factors for current/target resolution."""
        if target_resolution is None:
            target_resolution = self.current_resolution

        base_w, base_h = self.base_resolution
        target_w, target_h = target_resolution

        return target_w / base_w, target_h / base_h
