"""
Vision Detector: Enhanced detector using pipeline and caching.
"""

import logging
from .pipeline.preprocessor import Preprocessor
from .pipeline.roi_extractor import ROIExtractor
from .pipeline.postprocessor import Postprocessor
from .cache.cache_manager import CacheManager
from .cache.template_cache import TemplateCache
from .cache.roi_optimizer import ROIOptimizer
from .calibration.auto_calibrator import AutoCalibrator
from .calibration.resolution_adapter import ResolutionAdapter
from .calibration.emulator_detector import EmulatorDetector

logger = logging.getLogger(__name__)

class Detector:
    def __init__(self, config):
        self.config = config

        # Initialize pipeline components
        self.preprocessor = Preprocessor(config)
        self.roi_extractor = ROIExtractor(config)
        self.postprocessor = Postprocessor(config)

        # Initialize caching system
        self.cache_manager = CacheManager()
        self.template_cache = TemplateCache()
        self.roi_optimizer = ROIOptimizer(config)

        # Initialize calibration system
        self.auto_calibrator = AutoCalibrator(config)
        self.resolution_adapter = ResolutionAdapter()
        self.emulator_detector = EmulatorDetector()

        self.initialized = False

    def initialize(self):
        """Initialize all vision components."""
        if self.initialized:
            return

        logger.info("Initializing vision detector...")

        # Preload templates
        self.template_cache.preload_templates(['battle_start', 'battle_end', 'health_bar'])

        # Detect emulator type
        emulator_type, confidence = self.emulator_detector.detect_emulator()
        if emulator_type:
            logger.info(f"Detected emulator: {emulator_type} (confidence: {confidence})")
            self.config['emulator_type'] = emulator_type

        self.initialized = True
        logger.info("Vision detector initialized.")

    def shutdown(self):
        """Shutdown vision components."""
        logger.info("Shutting down vision detector...")
        self.cache_manager.clear()
        self.template_cache.clear_cache()
        self.initialized = False
        logger.info("Vision detector shut down.")

    def capture_screen(self):
        """Capture screen using emulator."""
        # This would integrate with emulator capture
        # For now, return placeholder
        return None

    def detect_battle(self, screen):
        """Detect if battle is active."""
        if not self.initialized or screen is None:
            return False

        # Check cache first
        cache_key = f"battle_detection_{hash(screen.tobytes()) if screen is not None else 'none'}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Preprocess image
        processed = self.preprocessor.preprocess(screen)

        # Extract battle ROI
        battle_roi = self.roi_optimizer.optimize_roi('battle', 0.5, screen.shape[:2])
        self.roi_extractor.update_roi('battle', battle_roi)
        roi_images = self.roi_extractor.extract_rois(processed, ['battle'])

        # Template matching for battle detection
        battle_template = self.template_cache.load_template('battle_start')
        if battle_template is not None and 'battle' in roi_images:
            # Simple template matching (placeholder for more sophisticated detection)
            result = self.match_template(roi_images['battle'], battle_template)
            confidence = result.get('confidence', 0) if result else 0

            # Cache result
            self.cache_manager.put(cache_key, confidence > 0.7)

            return confidence > 0.7

        return False

    def detect_battle_end(self, screen):
        """Detect if battle has ended."""
        if not self.initialized or screen is None:
            return False

        # Similar to detect_battle but for end condition
        processed = self.preprocessor.preprocess(screen)
        roi_images = self.roi_extractor.extract_rois(processed, ['battle'])

        end_template = self.template_cache.load_template('battle_end')
        if end_template is not None and 'battle' in roi_images:
            result = self.match_template(roi_images['battle'], end_template)
            confidence = result.get('confidence', 0) if result else 0
            return confidence > 0.7

        return False

    def match_template(self, image, template):
        """Simple template matching placeholder."""
        # Placeholder implementation - would use OpenCV template matching
        return {'confidence': 0.5, 'bbox': [0, 0, 100, 100]}
