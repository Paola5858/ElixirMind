"""
ROI Extractor: Extracts Regions of Interest from images.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ROIExtractor:
    def __init__(self, config):
        self.config = config
        self.rois = config.get('rois', {})

    def extract_rois(self, image, roi_names=None):
        """Extract specified ROIs from image."""
        if image is None:
            return {}

        if roi_names is None:
            roi_names = self.rois.keys()

        extracted_rois = {}
        for roi_name in roi_names:
            if roi_name in self.rois:
                roi_config = self.rois[roi_name]
                roi_image = self.extract_single_roi(image, roi_config)
                if roi_image is not None:
                    extracted_rois[roi_name] = roi_image

        return extracted_rois

    def extract_single_roi(self, image, roi_config):
        """Extract a single ROI based on config."""
        try:
            x = roi_config.get('x', 0)
            y = roi_config.get('y', 0)
            width = roi_config.get('width', 100)
            height = roi_config.get('height', 100)

            # Ensure coordinates are within image bounds
            h, w = image.shape[:2]
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            width = min(width, w - x)
            height = min(height, h - y)

            if width <= 0 or height <= 0:
                logger.warning(f"Invalid ROI dimensions: {width}x{height}")
                return None

            roi = image[y:y+height, x:x+width]
            return roi

        except Exception as e:
            logger.error(f"Error extracting ROI: {e}")
            return None

    def update_roi(self, roi_name, new_config):
        """Update ROI configuration."""
        self.rois[roi_name] = new_config
        logger.info(f"Updated ROI {roi_name}: {new_config}")
