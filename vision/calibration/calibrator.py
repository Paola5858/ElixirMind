"""
Auto Calibrator: Automatic calibration system for ROIs and emulator detection.
Handles resolution detection, ROI calibration, and validation.
"""

import cv2
import numpy as np
import asyncio
import logging
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import json
import time

from .auto_calibrator import AutoCalibrator
from .resolution_adapter import ResolutionAdapter
from .emulator_detector import EmulatorDetector
from ..pipeline.roi_extractor import ROIExtractor

logger = logging.getLogger(__name__)

class Calibrator:
    """
    Comprehensive calibration system for ElixirMind.
    Handles automatic detection and calibration of emulator resolution and ROIs.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.auto_calibrator = AutoCalibrator(config)
        self.resolution_adapter = ResolutionAdapter()
        self.emulator_detector = EmulatorDetector()
        self.roi_extractor = ROIExtractor(config)

        # Calibration state
        self.calibrated_rois = {}
        self.emulator_type = None
        self.detected_resolution = None
        self.calibration_templates = {}
        self.validation_results = {}

        # Calibration data storage
        self.calibration_dir = Path("data/calibration")
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_file = self.calibration_dir / "calibration_data.json"

        # Load existing calibration if available
        self.load_calibration_data()

    async def detect_emulator_resolution(self, screenshot_path: Optional[str] = None) -> Tuple[Optional[str], Tuple[int, int]]:
        """
        Detect emulator type and resolution automatically.

        Args:
            screenshot_path: Path to screenshot for analysis

        Returns:
            Tuple of (emulator_type, resolution)
        """
        logger.info("Starting emulator and resolution detection...")

        try:
            # Take screenshot if not provided
            if screenshot_path is None:
                screenshot_path = await self._take_screenshot()

            # Load screenshot
            image = cv2.imread(screenshot_path)
            if image is None:
                logger.error("Could not load screenshot for detection")
                return None, (0, 0)

            # Detect emulator type
            emulator_type, confidence = self.emulator_detector.detect_emulator(
                screen_image=image
            )

            if emulator_type and confidence > 0.5:
                self.emulator_type = emulator_type
                logger.info(f"Detected emulator: {emulator_type} (confidence: {confidence:.2f})")
            else:
                logger.warning("Could not confidently detect emulator type")
                self.emulator_type = "unknown"

            # Detect resolution
            height, width = image.shape[:2]
            resolution = (width, height)
            self.detected_resolution = resolution
            self.resolution_adapter.set_resolution(width, height)

            logger.info(f"Detected resolution: {width}x{height}")

            return self.emulator_type, resolution

        except Exception as e:
            logger.error(f"Error in emulator resolution detection: {e}")
            return None, (0, 0)

    async def calibrate_rois(self, screenshot_path: Optional[str] = None,
                           force_recalibration: bool = False) -> Dict[str, Dict]:
        """
        Automatically calibrate all ROIs for the current setup.

        Args:
            screenshot_path: Path to screenshot for calibration
            force_recalibration: Force recalibration even if cached

        Returns:
            Dictionary of calibrated ROIs
        """
        logger.info("Starting ROI calibration...")

        # Check if we have cached calibration
        if not force_recalibration and self.calibrated_rois:
            logger.info("Using cached calibration data")
            return self.calibrated_rois

        try:
            # Take screenshot if not provided
            if screenshot_path is None:
                screenshot_path = await self._take_screenshot()

            # Load screenshot
            image = cv2.imread(screenshot_path)
            if image is None:
                logger.error("Could not load screenshot for calibration")
                return {}

            # Load calibration templates
            await self._load_calibration_templates()

            # Perform calibration for each ROI type
            calibrated_rois = {}

            # Define ROI types and their search regions
            roi_definitions = self._get_roi_definitions()

            for roi_name, roi_config in roi_definitions.items():
                logger.info(f"Calibrating ROI: {roi_name}")

                # Get search region for this ROI
                search_region = roi_config.get('search_region')
                template_name = roi_config.get('template')

                if template_name and template_name in self.calibration_templates:
                    # Use template matching calibration
                    roi = self.auto_calibrator.calibrate_roi(
                        image, template_name, search_region
                    )
                else:
                    # Use fallback calibration method
                    roi = await self._fallback_roi_calibration(
                        image, roi_name, roi_config
                    )

                if roi:
                    calibrated_rois[roi_name] = roi
                    logger.info(f"Successfully calibrated {roi_name}: {roi}")
                else:
                    logger.warning(f"Failed to calibrate {roi_name}")

            # Store calibrated ROIs
            self.calibrated_rois = calibrated_rois
            await self.save_calibration_data()

            logger.info(f"Calibration completed. Calibrated {len(calibrated_rois)} ROIs")
            return calibrated_rois

        except Exception as e:
            logger.error(f"Error during ROI calibration: {e}")
            return {}

    async def validate_detection(self, screenshot_path: Optional[str] = None) -> Dict[str, bool]:
        """
        Validate that detection is working correctly with calibrated ROIs.

        Args:
            screenshot_path: Path to screenshot for validation

        Returns:
            Dictionary of validation results
        """
        logger.info("Starting detection validation...")

        validation_results = {}

        try:
            # Take screenshot if not provided
            if screenshot_path is None:
                screenshot_path = await self._take_screenshot()

            # Load screenshot
            image = cv2.imread(screenshot_path)
            if image is None:
                logger.error("Could not load screenshot for validation")
                return {"screenshot_load": False}

            # Validate basic image properties
            validation_results["screenshot_load"] = True
            validation_results["image_dimensions"] = image.shape[:2]

            # Validate calibrated ROIs
            if self.calibrated_rois:
                roi_validation = await self._validate_rois(image)
                validation_results.update(roi_validation)
            else:
                validation_results["roi_calibration"] = False
                logger.warning("No calibrated ROIs available for validation")

            # Validate template matching
            template_validation = self._validate_templates(image)
            validation_results.update(template_validation)

            # Overall validation score
            valid_checks = sum(1 for v in validation_results.values() if isinstance(v, bool) and v)
            total_checks = sum(1 for v in validation_results.values() if isinstance(v, bool))
            validation_results["overall_score"] = valid_checks / total_checks if total_checks > 0 else 0

            self.validation_results = validation_results

            logger.info(f"Validation completed. Score: {validation_results.get('overall_score', 0):.2f}")
            return validation_results

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {"error": str(e)}

    async def _take_screenshot(self) -> str:
        """Take a screenshot for calibration/validation."""
        # Import here to avoid circular imports
        from ..screen_capture import ScreenCapture

        screen_capture = ScreenCapture(self.config)
        screenshot_path = await screen_capture.capture_screen("calibration_screenshot.png")
        return screenshot_path

    async def _load_calibration_templates(self):
        """Load calibration templates from disk."""
        templates_dir = Path("data/templates/calibration")

        if not templates_dir.exists():
            logger.warning("Calibration templates directory not found")
            return

        for template_file in templates_dir.glob("*.png"):
            template_name = template_file.stem
            self.auto_calibrator.load_calibration_template(
                template_name, str(template_file)
            )
            logger.info(f"Loaded calibration template: {template_name}")

    def _get_roi_definitions(self) -> Dict[str, Dict]:
        """Get definitions for ROIs that need calibration."""
        return {
            "player_health": {
                "template": "health_bar",
                "search_region": (0.1, 0.1, 0.3, 0.2),  # Top-left area
                "fallback": "pattern_based"
            },
            "opponent_health": {
                "template": "health_bar",
                "search_region": (0.7, 0.1, 0.3, 0.2),  # Top-right area
                "fallback": "pattern_based"
            },
            "player_cards": {
                "template": "card_slot",
                "search_region": (0.0, 0.7, 1.0, 0.3),  # Bottom area
                "fallback": "grid_based"
            },
            "opponent_cards": {
                "template": "card_slot",
                "search_region": (0.0, 0.0, 1.0, 0.3),  # Top area
                "fallback": "grid_based"
            },
            "mana_bar": {
                "template": "mana_crystal",
                "search_region": (0.4, 0.8, 0.2, 0.1),  # Bottom center
                "fallback": "color_based"
            },
            "battle_timer": {
                "template": "timer_icon",
                "search_region": (0.45, 0.05, 0.1, 0.1),  # Top center
                "fallback": "text_based"
            }
        }

    async def _fallback_roi_calibration(self, image: np.ndarray,
                                      roi_name: str, roi_config: Dict) -> Optional[Dict]:
        """Fallback calibration methods when template matching fails."""
        method = roi_config.get('fallback', 'default')

        if method == 'pattern_based':
            return self._pattern_based_calibration(image, roi_name)
        elif method == 'grid_based':
            return self._grid_based_calibration(image, roi_name)
        elif method == 'color_based':
            return self._color_based_calibration(image, roi_name)
        elif method == 'text_based':
            return self._text_based_calibration(image, roi_name)
        else:
            return self._default_calibration(image, roi_name)

    def _pattern_based_calibration(self, image: np.ndarray, roi_name: str) -> Optional[Dict]:
        """Pattern-based ROI calibration."""
        # Implement pattern recognition for health bars, etc.
        # This is a simplified version
        height, width = image.shape[:2]

        if "health" in roi_name:
            # Look for colored bars
            if "player" in roi_name:
                return {"x": 50, "y": 50, "width": 200, "height": 30}
            else:
                return {"x": width - 250, "y": 50, "width": 200, "height": 30}

        return None

    def _grid_based_calibration(self, image: np.ndarray, roi_name: str) -> Optional[Dict]:
        """Grid-based ROI calibration for card areas."""
        height, width = image.shape[:2]

        if "cards" in roi_name:
            if "player" in roi_name:
                return {"x": 0, "y": int(height * 0.75), "width": width, "height": int(height * 0.25)}
            else:
                return {"x": 0, "y": 0, "width": width, "height": int(height * 0.25)}

        return None

    def _color_based_calibration(self, image: np.ndarray, roi_name: str) -> Optional[Dict]:
        """Color-based ROI calibration."""
        # Look for specific colors (mana crystals are usually blue)
        height, width = image.shape[:2]

        if "mana" in roi_name:
            return {"x": int(width * 0.4), "y": int(height * 0.85),
                   "width": int(width * 0.2), "height": int(height * 0.1)}

        return None

    def _text_based_calibration(self, image: np.ndarray, roi_name: str) -> Optional[Dict]:
        """Text-based ROI calibration."""
        # Use OCR to find text elements
        height, width = image.shape[:2]

        if "timer" in roi_name:
            return {"x": int(width * 0.45), "y": int(height * 0.05),
                   "width": int(width * 0.1), "height": int(height * 0.1)}

        return None

    def _default_calibration(self, image: np.ndarray, roi_name: str) -> Optional[Dict]:
        """Default calibration fallback."""
        # Return a centered ROI as last resort
        height, width = image.shape[:2]
        return {"x": int(width * 0.4), "y": int(height * 0.4),
               "width": int(width * 0.2), "height": int(height * 0.2)}

    async def _validate_rois(self, image: np.ndarray) -> Dict[str, bool]:
        """Validate that calibrated ROIs are reasonable."""
        validation_results = {}

        for roi_name, roi in self.calibrated_rois.items():
            try:
                # Check if ROI is within image bounds
                height, width = image.shape[:2]
                x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']

                within_bounds = (0 <= x < width and 0 <= y < height and
                               x + w <= width and y + h <= height)

                # Check if ROI has reasonable size
                reasonable_size = (w > 10 and h > 10 and w < width and h < height)

                # Check if ROI contains meaningful content (not all black/white)
                roi_img = image[y:y+h, x:x+w]
                if roi_img.size > 0:
                    mean_color = np.mean(roi_img)
                    has_content = 10 < mean_color < 245  # Not too dark or bright
                else:
                    has_content = False

                validation_results[f"{roi_name}_bounds"] = within_bounds
                validation_results[f"{roi_name}_size"] = reasonable_size
                validation_results[f"{roi_name}_content"] = has_content
                validation_results[roi_name] = within_bounds and reasonable_size and has_content

            except Exception as e:
                logger.error(f"Error validating ROI {roi_name}: {e}")
                validation_results[roi_name] = False

        return validation_results

    def _validate_templates(self, image: np.ndarray) -> Dict[str, bool]:
        """Validate template matching capability."""
        validation_results = {}

        if not self.calibration_templates:
            validation_results["templates_loaded"] = False
            return validation_results

        validation_results["templates_loaded"] = True

        # Test template matching on a small region
        test_region = image[100:200, 100:200] if image.shape[0] > 200 and image.shape[1] > 200 else image

        template_found = False
        for template_name, template in self.calibration_templates.items():
            try:
                result = cv2.matchTemplate(test_region, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > 0.3:  # Lower threshold for validation
                    template_found = True
                    break
            except:
                continue

        validation_results["template_matching"] = template_found
        return validation_results

    async def save_calibration_data(self):
        """Save calibration data to disk."""
        try:
            data = {
                "emulator_type": self.emulator_type,
                "detected_resolution": self.detected_resolution,
                "calibrated_rois": self.calibrated_rois,
                "calibration_time": time.time(),
                "validation_results": self.validation_results
            }

            with open(self.calibration_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Calibration data saved to {self.calibration_file}")

        except Exception as e:
            logger.error(f"Error saving calibration data: {e}")

    def load_calibration_data(self):
        """Load calibration data from disk."""
        try:
            if self.calibration_file.exists():
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)

                self.emulator_type = data.get("emulator_type")
                self.detected_resolution = data.get("detected_resolution")
                self.calibrated_rois = data.get("calibrated_rois", {})
                self.validation_results = data.get("validation_results", {})

                if self.detected_resolution:
                    self.resolution_adapter.set_resolution(*self.detected_resolution)

                logger.info(f"Calibration data loaded from {self.calibration_file}")
                return True

        except Exception as e:
            logger.error(f"Error loading calibration data: {e}")

        return False

    def get_calibrated_roi(self, roi_name: str) -> Optional[Dict]:
        """Get a calibrated ROI by name."""
        return self.calibrated_rois.get(roi_name)

    def get_all_calibrated_rois(self) -> Dict[str, Dict]:
        """Get all calibrated ROIs."""
        return self.calibrated_rois.copy()

    def is_calibrated(self) -> bool:
        """Check if system is properly calibrated."""
        return (bool(self.calibrated_rois) and
                self.emulator_type is not None and
                self.detected_resolution is not None)

    def get_calibration_status(self) -> Dict:
        """Get current calibration status."""
        return {
            "is_calibrated": self.is_calibrated(),
            "emulator_type": self.emulator_type,
            "resolution": self.detected_resolution,
            "calibrated_rois_count": len(self.calibrated_rois),
            "validation_score": self.validation_results.get("overall_score", 0)
        }
