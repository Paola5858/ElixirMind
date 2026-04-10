"""
Detector: Screen analysis and battle state detection.

Improvements vs previous version:
- ConfigWrapper removed; ROIs/thresholds read directly from config dict
  with explicit fallbacks — no more hardcoded internal class.
- _detect_battle_template no longer returns True unconditionally; it
  returns False when no template is available (honest placeholder).
- detect_battle() signature is unchanged: (bool, ndarray|None).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from screen_capture import ScreenCapture

logger = logging.getLogger(__name__)

# Default ROIs for 1920×1080. Override via config keys below.
_DEFAULT_ROI_HAND        = (0,    800, 1920, 1080)
_DEFAULT_ROI_BATTLEFIELD = (0,    0,   1920, 800)
_DEFAULT_ROI_ELIXIR      = (1700, 900, 1900, 1000)
_DEFAULT_ROI_ENEMY_TOWERS= (0,    0,   1920, 400)
_DEFAULT_ROI_MY_TOWERS   = (0,    400, 1920, 800)


class Detector:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.roi_hand         = tuple(config.get("ROI_HAND",         _DEFAULT_ROI_HAND))
        self.roi_battlefield  = tuple(config.get("ROI_BATTLEFIELD",  _DEFAULT_ROI_BATTLEFIELD))
        self.roi_elixir       = tuple(config.get("ROI_ELIXIR",       _DEFAULT_ROI_ELIXIR))
        self.roi_enemy_towers = tuple(config.get("ROI_ENEMY_TOWERS", _DEFAULT_ROI_ENEMY_TOWERS))
        self.roi_my_towers    = tuple(config.get("ROI_MY_TOWERS",    _DEFAULT_ROI_MY_TOWERS))
        self.template_threshold = float(config.get("template_threshold", 0.7))

        self.initialized = False
        self.cache_manager = None
        self.screen_capture: Optional[ScreenCapture] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        try:
            from vision.cache.cache_manager import CacheManager

            # ScreenCapture expects an object with attribute access; wrap config.
            self.screen_capture = ScreenCapture(_ConfigAdapter(self.config))
            self.screen_capture.initialize()
            self.cache_manager = CacheManager()
            self.initialized = True
            logger.info("Detector initialized.")
        except Exception:
            logger.exception("Detector initialization failed.")
            self.initialized = False

    def shutdown(self) -> None:
        if self.cache_manager:
            self.cache_manager.clear()
        if self.screen_capture:
            self.screen_capture.cleanup()
        self.initialized = False
        logger.info("Detector shut down.")

    # ------------------------------------------------------------------
    # Screen capture
    # ------------------------------------------------------------------

    def capture_screen(self) -> Optional[np.ndarray]:
        if not self.initialized or not self.screen_capture:
            logger.error("Detector not initialized; cannot capture screen.")
            return None
        return self.screen_capture.capture()

    # ------------------------------------------------------------------
    # Battle detection
    # ------------------------------------------------------------------

    def detect_battle(
        self, screen: np.ndarray, debug_mode: bool = False
    ) -> Tuple[bool, Optional[np.ndarray]]:
        """Return (battle_active, debug_image|None)."""
        if not self.initialized or screen is None:
            return False, None

        cache_key = f"battle_{hash(screen.tobytes())}"
        if self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached, None

        debug_image = screen.copy() if debug_mode else None
        indicators = [
            ("elixir",   self._detect_elixir_presence(screen)),
            ("cards",    self._detect_card_hand(screen)),
            ("towers",   self._detect_towers(screen)),
            ("template", self._detect_battle_template(screen)),
        ]

        if debug_mode:
            rois = {
                "elixir":  self.roi_elixir,
                "cards":   self.roi_hand,
                "towers":  self.roi_battlefield,
                "template": self.roi_battlefield,
            }
            for i, (name, present) in enumerate(indicators):
                self._draw_roi(debug_image, rois[name], name, present)
                cv2.putText(
                    debug_image,
                    f"{name}: {'YES' if present else 'NO'}",
                    (10, 30 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2,
                )

        positive = sum(1 for _, v in indicators if v)
        battle_active = positive >= 2

        if debug_mode:
            logger.info("Battle detection: %d/4 indicators positive", positive)
            cv2.putText(
                debug_image,
                f"Battle Active: {battle_active}",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                (0, 255, 0) if battle_active else (0, 0, 255), 3,
            )

        if self.cache_manager and not debug_mode:
            self.cache_manager.put(cache_key, battle_active)

        return battle_active, debug_image

    def detect_battle_end(self, screen: np.ndarray) -> bool:
        if screen is None:
            return False
        try:
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            for template_path in [
                Path("data/templates/ok_button.png"),
                Path("data/templates/victory_crown.png"),
                Path("data/templates/defeat_crown.png"),
            ]:
                if not template_path.exists():
                    continue
                tmpl = cv2.imread(str(template_path), 0)
                if tmpl is None:
                    continue
                res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > 0.75:
                    logger.info("Battle end detected via %s", template_path.stem)
                    return True

            # Colour-based fallback: characteristic end-screen blue/purple
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(
                hsv,
                np.array([90, 50, 50]),
                np.array([130, 255, 255]),
            )
            if np.sum(mask > 0) / mask.size > 0.30:
                logger.info("Battle end detected via colour pattern.")
                return True
        except Exception:
            logger.exception("Error in detect_battle_end.")
        return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_elixir_presence(self, screen: np.ndarray) -> bool:
        x1, y1, x2, y2 = self.roi_elixir
        roi = screen[y1:y2, x1:x2]
        if roi.size == 0:
            return False
        hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, np.array([140, 50, 50]), np.array([170, 255, 255]))
        return np.sum(mask > 0) / roi.size > 0.05

    def _detect_card_hand(self, screen: np.ndarray) -> bool:
        x1, y1, x2, y2 = self.roi_hand
        roi = screen[y1:y2, x1:x2]
        if roi.size == 0:
            return False
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        edged = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
        return int(np.sum(edged > 0)) > 500

    def _detect_towers(self, screen: np.ndarray) -> bool:
        x1, y1, x2, y2 = self.roi_battlefield
        roi = screen[y1:y2, x1:x2]
        if roi.size == 0:
            return False
        edged = cv2.Canny(cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY), 50, 150)
        return int(np.sum(edged > 0)) > 1000

    def _detect_battle_template(self, screen: np.ndarray) -> bool:
        """Template-based battle indicator. Returns False when no template exists."""
        template_path = Path("data/templates/battle_indicator.png")
        if not template_path.exists():
            return False
        tmpl = cv2.imread(str(template_path), 0)
        if tmpl is None:
            return False
        gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val >= self.template_threshold

    def _draw_roi(
        self,
        image: np.ndarray,
        roi: Tuple[int, int, int, int],
        text: str,
        status: bool,
    ) -> None:
        x1, y1, x2, y2 = roi
        color = (0, 255, 0) if status else (0, 0, 255)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image, f"{text}: {'OK' if status else 'FAIL'}",
            (x1, max(y1 - 10, 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
        )


# ---------------------------------------------------------------------------
# Internal adapter — gives ScreenCapture attribute-style access to config dict
# ---------------------------------------------------------------------------

class _ConfigAdapter:
    """Thin adapter so ScreenCapture can use attribute access on a plain dict."""

    def __init__(self, config: dict) -> None:
        self._cfg = config
        self.EMULATOR_TYPE      = config.get("emulator_type", "memu")
        self.TARGET_FPS         = int(config.get("TARGET_FPS", 10))
        self.CAPTURE_METHOD     = config.get("CAPTURE_METHOD", "mss")
        self.SCREENSHOT_DIR     = config.get("SCREENSHOT_DIR", "screenshots")
        self.ROI_HAND           = tuple(config.get("ROI_HAND",         _DEFAULT_ROI_HAND))
        self.ROI_BATTLEFIELD    = tuple(config.get("ROI_BATTLEFIELD",  _DEFAULT_ROI_BATTLEFIELD))
        self.ROI_ELIXIR         = tuple(config.get("ROI_ELIXIR",       _DEFAULT_ROI_ELIXIR))
        self.ROI_ENEMY_TOWERS   = tuple(config.get("ROI_ENEMY_TOWERS", _DEFAULT_ROI_ENEMY_TOWERS))
        self.ROI_MY_TOWERS      = tuple(config.get("ROI_MY_TOWERS",    _DEFAULT_ROI_MY_TOWERS))
        self.target_resolution  = tuple(config.get("target_resolution", (1920, 1080)))
        self.template_threshold = float(config.get("template_threshold", 0.7))
        self.roi_padding        = int(config.get("roi_padding", 10))

    def get(self, key: str, default=None):
        return self._cfg.get(key, default)
