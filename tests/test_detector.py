"""
Detector tests — written against the actual current API.

Previous version tested a legacy async GameStateDetector that no longer exists.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from vision.detector import Detector


@pytest.fixture
def detector():
    d = Detector({})
    # Inject a mock cache manager so tests don't need the real one
    d.cache_manager = MagicMock()
    d.cache_manager.get.return_value = None
    d.initialized = True
    return d


@pytest.fixture
def blank_frame():
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def purple_elixir_frame():
    """Frame with purple pixels in the elixir ROI."""
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # ROI_ELIXIR default: (1700, 900, 1900, 1000) — fill with purple (RGB)
    frame[900:1000, 1700:1900] = [200, 0, 200]
    return frame


# ---------------------------------------------------------------------------
# Initialization / shutdown
# ---------------------------------------------------------------------------

def test_detector_initializes_with_mocked_deps():
    d = Detector({})
    with patch("vision.detector.ScreenCapture") as mock_sc, \
         patch("vision.detector.Detector.initialize") as mock_init:
        mock_init.return_value = None
        d.initialize()


def test_detector_shutdown_clears_state(detector):
    detector.screen_capture = MagicMock()
    detector.shutdown()
    assert detector.initialized is False


# ---------------------------------------------------------------------------
# detect_battle return type
# ---------------------------------------------------------------------------

def test_detect_battle_returns_tuple(detector, blank_frame):
    result = detector.detect_battle(blank_frame)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_detect_battle_first_element_is_bool(detector, blank_frame):
    battle_active, _ = detector.detect_battle(blank_frame)
    assert isinstance(battle_active, bool)


def test_detect_battle_returns_false_for_blank_frame(detector, blank_frame):
    battle_active, _ = detector.detect_battle(blank_frame)
    assert battle_active is False


def test_detect_battle_returns_none_debug_image_when_not_debug(detector, blank_frame):
    _, debug_img = detector.detect_battle(blank_frame, debug_mode=False)
    assert debug_img is None


def test_detect_battle_returns_debug_image_when_debug(detector, blank_frame):
    _, debug_img = detector.detect_battle(blank_frame, debug_mode=True)
    assert debug_img is not None
    assert isinstance(debug_img, np.ndarray)


# ---------------------------------------------------------------------------
# detect_battle — cache behaviour
# ---------------------------------------------------------------------------

def test_detect_battle_uses_cache_on_second_call(detector, blank_frame):
    detector.cache_manager.get.return_value = True  # cache hit
    battle_active, _ = detector.detect_battle(blank_frame)
    assert battle_active is True
    # Should not call put again on a cache hit
    detector.cache_manager.put.assert_not_called()


def test_detect_battle_stores_result_in_cache(detector, blank_frame):
    detector.cache_manager.get.return_value = None  # cache miss
    detector.detect_battle(blank_frame)
    detector.cache_manager.put.assert_called_once()


# ---------------------------------------------------------------------------
# detect_battle — None screen
# ---------------------------------------------------------------------------

def test_detect_battle_returns_false_for_none_screen(detector):
    battle_active, debug_img = detector.detect_battle(None)
    assert battle_active is False
    assert debug_img is None


def test_detect_battle_returns_false_when_not_initialized(blank_frame):
    d = Detector({})
    d.initialized = False
    battle_active, _ = d.detect_battle(blank_frame)
    assert battle_active is False


# ---------------------------------------------------------------------------
# detect_battle_end
# ---------------------------------------------------------------------------

def test_detect_battle_end_returns_false_for_blank_frame(detector, blank_frame):
    result = detector.detect_battle_end(blank_frame)
    assert result is False


def test_detect_battle_end_returns_false_for_none(detector):
    assert detector.detect_battle_end(None) is False


def test_detect_battle_end_detects_end_screen_colour(detector):
    """A frame dominated by the end-screen blue/purple should trigger detection."""
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Fill >30% with BGR blue (maps to HSV hue ~120 — within [90,130])
    frame[:, :] = [200, 0, 0]  # BGR blue
    result = detector.detect_battle_end(frame)
    assert result is True


# ---------------------------------------------------------------------------
# ROI configuration
# ---------------------------------------------------------------------------

def test_detector_reads_roi_from_config():
    custom_roi = [10, 20, 100, 200]
    d = Detector({"ROI_ELIXIR": custom_roi})
    assert d.roi_elixir == tuple(custom_roi)


def test_detector_uses_default_roi_when_not_in_config():
    d = Detector({})
    assert d.roi_elixir == (1700, 900, 1900, 1000)


# ---------------------------------------------------------------------------
# capture_screen
# ---------------------------------------------------------------------------

def test_capture_screen_returns_none_when_not_initialized():
    d = Detector({})
    d.initialized = False
    assert d.capture_screen() is None


def test_capture_screen_delegates_to_screen_capture(detector):
    mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    detector.screen_capture = MagicMock()
    detector.screen_capture.capture.return_value = mock_frame
    result = detector.capture_screen()
    assert result is mock_frame
