"""
Auto Calibrator: Automatic calibration of ROIs.
"""

import cv2
import numpy as np
import logging
from ..pipeline.roi_extractor import ROIExtractor

logger = logging.getLogger(__name__)

class AutoCalibrator:
    def __init__(self, config):
        self.config = config
        self.roi_extractor = ROIExtractor(config)
        self.calibration_templates = {}

    def calibrate_roi(self, image, template_name, search_region=None):
        """Automatically calibrate ROI by finding template in image."""
        if template_name not in self.calibration_templates:
            logger.warning(f"Template {template_name} not loaded")
            return None

        template = self.calibration_templates[template_name]

        # Define search region
        if search_region is None:
            h, w = image.shape[:2]
            search_region = (0, 0, w, h)

        x, y, w, h = search_region

        # Extract search region
        search_img = image[y:y+h, x:x+w]

        # Template matching
        result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > 0.8:  # Good match threshold
            # Calculate ROI around the match
            template_h, template_w = template.shape[:2]
            center_x = x + max_loc[0] + template_w // 2
            center_y = y + max_loc[1] + template_h // 2

            # Create ROI with some padding
            padding = 20
            roi = {
                'x': max(0, center_x - template_w // 2 - padding),
                'y': max(0, center_y - template_h // 2 - padding),
                'width': template_w + 2 * padding,
                'height': template_h + 2 * padding
            }

            logger.info(f"Auto-calibrated ROI for {template_name}: {roi}")
            return roi

        logger.warning(f"Could not find good match for {template_name} (max_val: {max_val})")
        return None

    def load_calibration_template(self, name, image_path):
        """Load template image for calibration."""
        try:
            template = cv2.imread(image_path)
            if template is not None:
                self.calibration_templates[name] = template
                logger.info(f"Loaded calibration template: {name}")
            else:
                logger.error(f"Could not load template: {image_path}")
        except Exception as e:
            logger.error(f"Error loading template {name}: {e}")

    def calibrate_all_rois(self, image):
        """Calibrate all ROIs automatically."""
        calibrated_rois = {}
        for template_name in self.calibration_templates.keys():
            roi = self.calibrate_roi(image, template_name)
            if roi:
                calibrated_rois[template_name] = roi

        return calibrated_rois
