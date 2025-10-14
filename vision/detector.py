import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class Detector:
    def __init__(self, config):
        self.config = config
        self.initialized = False
        self.cache_manager = None  # Will be set during initialization

    def initialize(self):
        """Initialize the detector with necessary components."""
        try:
            # Import here to avoid circular imports
            from vision.cache.cache_manager import CacheManager
            self.cache_manager = CacheManager()
            self.initialized = True
            logger.info("Detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize detector: {e}")
            self.initialized = False

    def shutdown(self):
        """Shutdown the detector and cleanup resources."""
        if self.cache_manager:
            self.cache_manager.clear()
        self.initialized = False
        logger.info("Detector shutdown")

    def detect_battle(self, screen, debug_mode=False) -> tuple[bool, np.ndarray | None]:
        """Detect if battle is active using multiple indicators."""
        if not self.initialized or screen is None:
            return False, None

        # Check cache first
        cache_key = f"battle_detection_{hash(screen.tobytes()) if screen is not None else 'none'}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result, None

        # Multiple battle detection methods
        indicators = []
        debug_image = screen.copy() if debug_mode else None

        # Method 1: Elixir detection
        elixir_present = self._detect_elixir_presence(screen)
        indicators.append(("elixir", elixir_present))
        if debug_mode:
            self._draw_roi(debug_image, self.config.ROI_ELIXIR,
                           "Elixir", elixir_present)

        # Method 2: Card hand detection
        cards_present = self._detect_card_hand(screen)
        indicators.append(("cards", cards_present))
        if debug_mode:
            self._draw_roi(debug_image, self.config.ROI_HAND,
                           "Cards", cards_present)

        # Method 3: Tower detection
        towers_present = self._detect_towers(screen)
        indicators.append(("towers", towers_present))
        if debug_mode:
            self._draw_roi(debug_image, self.config.ROI_BATTLEFIELD,
                           "Towers", towers_present)

        # Method 4: Template matching (if templates available)
        template_match = self._detect_battle_template(screen)
        indicators.append(("template", template_match))

        # Battle is active if at least 2 indicators are positive
        positive_indicators = sum(
            1 for _, is_present in indicators if is_present)
        battle_active = positive_indicators >= 2

        # Debug logging
        if debug_mode:
            logger.info(f"Battle detection: {positive_indicators}/4 indicators positive")
            for i, (name, is_present) in enumerate(indicators):
                status_text = f"{name}: {'YES' if is_present else 'NO'}"
                logger.info(f"  - {status_text}")
                cv2.putText(debug_image, status_text, (10, 30 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            final_status = f"Battle Active: {battle_active}"
            cv2.putText(debug_image, final_status, (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0) if battle_active else (0, 0, 255), 3)

        # Cache result
        if not debug_mode:
            self.cache_manager.put(cache_key, battle_active)

        return battle_active, debug_image
