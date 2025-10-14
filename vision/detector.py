import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from pathlib import Path

# Importa as classes necessárias para a captura de tela
from screen_capture import ScreenCapture
from config import load_config

logger = logging.getLogger(__name__)

class Detector:
    def __init__(self, config):
        # Wrap config dict in a class with attribute access
        class ConfigWrapper:
            def __init__(self, config_dict):
                self.config_dict = config_dict
                # Set default attributes
                self.EMULATOR_TYPE = config_dict.get('emulator_type', 'memu')
                self.TARGET_FPS = 10
                self.CAPTURE_METHOD = "mss"
                self.SCREENSHOT_DIR = "screenshots"
                self.ROI_HAND = (0, 800, 1920, 1080)
                self.ROI_BATTLEFIELD = (0, 0, 1920, 800)
                self.ROI_ELIXIR = (1700, 900, 1900, 1000)
                self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
                self.ROI_MY_TOWERS = (0, 400, 1920, 800)
                self.target_resolution = (1920, 1080)
                self.template_threshold = 0.7
                self.roi_padding = 10

            def get(self, key, default=None):
                return self.config_dict.get(key, default)

        self.config = ConfigWrapper(config)
        self.initialized = False
        self.cache_manager = None  # Will be set during initialization
        self.screen_capture = None  # Instância do capturador de tela

    def initialize(self):
        """Initialize the detector with necessary components."""
        try:
            # Import here to avoid circular imports
            from vision.cache.cache_manager import CacheManager

            # Inicializa o sistema de captura de tela
            self.screen_capture = ScreenCapture(self.config)
            self.screen_capture.initialize()

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
        if self.screen_capture:
            self.screen_capture.cleanup()
        self.initialized = False
        logger.info("Detector shutdown")

    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Capture screen using the screen capture system.
        This method acts as a bridge to the ScreenCapture module.
        """
        if not self.initialized or not self.screen_capture:
            logger.error(
                "Detector or ScreenCapture not initialized. Cannot capture screen.")
            return None

        return self.screen_capture.capture()

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

    def detect_battle_end(self, screen: np.ndarray) -> bool:
        """
        Detects if the battle has ended by looking for an 'OK' button or victory/defeat indicators.
        """
        if screen is None:
            return False

        try:
            # Convert to grayscale for template matching
            gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            # Look for "OK" button template
            ok_template_path = Path('data/templates/ok_button.png')
            if ok_template_path.exists():
                ok_template = cv2.imread(str(ok_template_path), 0)
                if ok_template is not None:
                    res = cv2.matchTemplate(gray_screen, ok_template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(res)
                    if max_val > 0.8:
                        logger.info("Battle end detected: OK button found")
                        return True

            # Alternative: Look for victory/defeat text or crown indicators
            # Check for crown icons (victory/defeat indicators)
            victory_template_path = Path('data/templates/victory_crown.png')
            defeat_template_path = Path('data/templates/defeat_crown.png')

            for template_path in [victory_template_path, defeat_template_path]:
                if template_path.exists():
                    template = cv2.imread(str(template_path), 0)
                    if template is not None:
                        res = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        if max_val > 0.7:
                            logger.info(f"Battle end detected: {template_path.stem} found")
                            return True

            # Fallback: Check for specific color patterns in battle end screen
            # Look for the characteristic blue/purple background of battle end screens
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

            # Battle end screens often have specific color ranges
            lower_end_screen = np.array([90, 50, 50])
            upper_end_screen = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_end_screen, upper_end_screen)

            # If significant portion of screen matches end screen colors
            color_ratio = np.sum(mask > 0) / (screen.shape[0] * screen.shape[1])
            if color_ratio > 0.3:  # 30% of screen
                logger.info("Battle end detected: End screen color pattern found")
                return True

        except Exception as e:
            logger.error(f"Error in battle end detection: {e}")

        return False

    def _detect_elixir_presence(self, screen: np.ndarray) -> bool:
        """Check for the presence of elixir color in its ROI."""
        x1, y1, x2, y2 = self.config.ROI_ELIXIR
        roi = screen[y1:y2, x1:x2]
        hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)

        # Pink/purple range for elixir
        lower_purple = np.array([140, 50, 50])
        upper_purple = np.array([170, 255, 255])
        mask = cv2.inRange(hsv, lower_purple, upper_purple)

        # If more than 5% of the ROI has the elixir color, we consider it present
        return np.sum(mask > 0) / (roi.shape[0] * roi.shape[1]) > 0.05

    def _detect_card_hand(self, screen: np.ndarray) -> bool:
        """Check for the presence of cards in the hand ROI."""
        x1, y1, x2, y2 = self.config.ROI_HAND
        roi = screen[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)

        # If there are significant edges, assume cards are present
        return np.sum(edged > 0) > 500

    def _detect_towers(self, screen: np.ndarray) -> bool:
        """Check for the presence of towers in the battlefield ROI."""
        x1, y1, x2, y2 = self.config.ROI_BATTLEFIELD
        roi = screen[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        edged = cv2.Canny(gray, 50, 150)

        # A simple check for vertical lines, common in towers
        return np.sum(edged > 0) > 1000

    def _detect_battle_template(self, screen: np.ndarray) -> bool:
        """Check for a battle-specific template."""
        # This is a placeholder. It would require loading a template image.
        # e.g., cv2.imread('data/templates/battle_indicator.png')
        return True  # Assume true for now to make battle detection easier

    def _draw_roi(self, image: np.ndarray, roi: Tuple[int, int, int, int], text: str, status: bool):
        """Draw a rectangle for the ROI and its status on the debug image."""
        x1, y1, x2, y2 = roi
        color = (0, 255, 0) if status else (0, 0, 255)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

        label = f"{text}: {'OK' if status else 'FAIL'}"
        cv2.putText(image, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
