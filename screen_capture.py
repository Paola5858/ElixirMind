"""
ElixirMind Screen Capture System
High-performance screen capture using MSS for real-time game analysis.
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image
import mss
import cv2

# Config class defined inline to avoid import issues


class Config:
    def __init__(self):
        from config import load_config
        self.config = load_config()
        self.EMULATOR_TYPE = self.config.get("emulator_type", "memu")
        self.TARGET_FPS = 10
        self.CAPTURE_METHOD = "mss"
        self.SCREENSHOT_DIR = "screenshots"
        self.ROI_HAND = (0, 800, 1920, 1080)
        self.ROI_BATTLEFIELD = (0, 0, 1920, 800)
        self.ROI_ELIXIR = (1700, 900, 1900, 1000)
        self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
        self.ROI_MY_TOWERS = (0, 400, 1920, 800)
        # Add missing attributes for vision pipeline
        self.target_resolution = (1920, 1080)
        self.template_threshold = 0.7
        self.roi_padding = 10

    def get(self, key, default=None):
        """Get configuration value with fallback to attributes."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.config.get(key, default)


class ScreenCapture:
    """High-performance screen capture for game analysis."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.sct = None
        self.monitor = None
        self.last_capture_time = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0

        # Cache for performance
        self._region_cache = {}

    def initialize(self) -> bool:
        """Initialize screen capture system."""
        try:
            self.sct = mss.mss()

            # Get monitor information
            self.monitor = self._find_game_window()
            if not self.monitor:
                self.logger.error("Could not find game window")
                return False

            self.logger.info(f"Screen capture initialized: {self.monitor}")
            return True

        except Exception as e:
            self.logger.error(f"Screen capture initialization failed: {e}")
            return False

    def _find_game_window(self) -> Optional[Dict[str, int]]:
        """Find the game window or use primary monitor."""
        try:
            # Try to find emulator window first
            window_region = self._detect_emulator_window()
            if window_region:
                return window_region

            # Fallback to primary monitor
            monitor = self.sct.monitors[1]  # Primary monitor

            # Adjust for common emulator window sizes
            if self.config.EMULATOR_TYPE.lower() == "memu":
                # MEmu typical window size and position
                return {
                    "top": monitor["top"] + 100,
                    "left": monitor["left"] + 100,
                    "width": 1080,
                    "height": 1920,
                    "monitor": 1
                }
            elif self.config.EMULATOR_TYPE.lower() == "ldplayer":
                # LDPlayer typical window size and position (1920x1080 resolution)
                return {
                    "top": monitor["top"] + 50,
                    "left": monitor["left"] + 50,
                    "width": 1920,
                    "height": 1080,
                    "monitor": 1
                }

            return monitor

        except Exception as e:
            self.logger.error(f"Window detection failed: {e}")
            return None

    def _detect_emulator_window(self) -> Optional[Dict[str, int]]:
        """Detect emulator window using multiple methods."""
        try:
            import platform
            if platform.system() == 'Windows':
                return self._detect_windows_emulator_window()
            else:
                # For other platforms, fallback to monitor detection
                return None
        except ImportError:
            self.logger.warning(
                "Window detection not available, using monitor fallback")
            return None

    def _detect_windows_emulator_window(self) -> Optional[Dict[str, int]]:
        """Detect emulator window on Windows."""
        try:
            import win32gui
            import win32con

            emulator_titles = {
                'ldplayer': ['LDPlayer', 'dnplayer'],
                'memu': ['MEmu', 'MEmu Player'],
                'bluestacks': ['BlueStacks', 'HD-Player']
            }

            target_titles = emulator_titles.get(
                self.config.EMULATOR_TYPE.lower(), [])

            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)

                    # Check title and class name
                    for target in target_titles:
                        if target.lower() in title.lower() or target.lower() in class_name.lower():
                            left, top, right, bottom = win32gui.GetWindowRect(
                                hwnd)
                            width = right - left
                            height = bottom - top

                            # Filter reasonable window sizes (emulator windows)
                            if 800 <= width <= 2560 and 600 <= height <= 1600:
                                windows.append({
                                    'hwnd': hwnd,
                                    'title': title,
                                    'class': class_name,
                                    'left': left,
                                    'top': top,
                                    'width': width,
                                    'height': height
                                })

            windows = []
            win32gui.EnumWindows(callback, windows)

            if windows:
                # Use first found window
                window = windows[0]
                self.logger.info(
                    f"Detected emulator window: {window['title']} ({window['width']}x{window['height']})")

                return {
                    "top": window['top'],
                    "left": window['left'],
                    "width": window['width'],
                    "height": window['height'],
                    "monitor": 1
                }

        except ImportError:
            self.logger.warning("win32gui not available for window detection")
        except Exception as e:
            self.logger.error(f"Window detection error: {e}")

        return None

    def capture(self) -> Optional[np.ndarray]:
        """Capture current screen frame."""
        try:
            # Throttle capture rate
            current_time = time.time()
            time_diff = current_time - self.last_capture_time
            min_interval = 1.0 / self.config.TARGET_FPS

            if time_diff < min_interval:
                return None

            # Try MSS capture first
            try:
                screenshot = self.sct.grab(self.monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            except Exception as mss_error:
                self.logger.warning(
                    f"MSS capture failed: {mss_error}, trying fallback methods")

                # Fallback to pyautogui
                try:
                    import pyautogui
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    # pyautogui is RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    self.logger.info(
                        "Using pyautogui fallback for screen capture")
                except Exception as pg_error:
                    self.logger.error(
                        f"All capture methods failed. MSS: {mss_error}, PyAutoGUI: {pg_error}")
                    return None

            # Update timing
            self.last_capture_time = current_time
            self._update_fps_counter()

            return frame

        except Exception as e:
            self.logger.error(f"Screen capture failed: {e}")
            return None

    def capture_region(self, region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """Capture specific region of the screen."""
        try:
            x1, y1, x2, y2 = region

            # Create region dict for mss
            region_dict = {
                "top": self.monitor["top"] + y1,
                "left": self.monitor["left"] + x1,
                "width": x2 - x1,
                "height": y2 - y1
            }

            # Capture region
            screenshot = self.sct.grab(region_dict)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

            return frame

        except Exception as e:
            self.logger.error(f"Region capture failed: {e}")
            return None

    def get_hand_region(self) -> Optional[np.ndarray]:
        """Capture the hand/cards region."""
        return self.capture_region(self.config.ROI_HAND)

    def get_battlefield_region(self) -> Optional[np.ndarray]:
        """Capture the battlefield region."""
        return self.capture_region(self.config.ROI_BATTLEFIELD)

    def get_elixir_region(self) -> Optional[np.ndarray]:
        """Capture the elixir counter region."""
        return self.capture_region(self.config.ROI_ELIXIR)

    def save_screenshot(self, frame: np.ndarray, filename: str = None) -> str:
        """Save screenshot to file."""
        try:
            if filename is None:
                timestamp = int(time.time() * 1000)
                filename = f"screenshot_{timestamp}.png"

            filepath = self.config.SCREENSHOT_DIR + "/" + filename

            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filepath, frame_bgr)

            return filepath

        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return ""

    def _update_fps_counter(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()

        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time

    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps

    def resize_frame(self, frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Resize frame maintaining aspect ratio."""
        try:
            height, width = frame.shape[:2]
            target_width, target_height = target_size

            # Calculate scaling factor
            scale = min(target_width / width, target_height / height)

            # Calculate new dimensions
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Resize
            resized = cv2.resize(
                frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

            return resized

        except Exception as e:
            self.logger.error(f"Frame resize failed: {e}")
            return frame

    def preprocess_for_detection(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for object detection."""
        try:
            # Resize to YOLO input size (640x640)
            processed = self.resize_frame(frame, (640, 640))

            # Normalize
            processed = processed.astype(np.float32) / 255.0

            return processed

        except Exception as e:
            self.logger.error(f"Preprocessing failed: {e}")
            return frame

    def extract_roi_coordinates(self, roi_name: str) -> Tuple[int, int, int, int]:
        """Get ROI coordinates by name."""
        roi_map = {
            "hand": self.config.ROI_HAND,
            "battlefield": self.config.ROI_BATTLEFIELD,
            "elixir": self.config.ROI_ELIXIR,
            "enemy_towers": self.config.ROI_ENEMY_TOWERS,
            "my_towers": self.config.ROI_MY_TOWERS
        }

        return roi_map.get(roi_name, (0, 0, 1920, 1080))

    def get_monitor_info(self) -> Dict[str, Any]:
        """Get current monitor information."""
        return {
            "monitor": self.monitor,
            "fps": self.current_fps,
            "target_fps": self.config.TARGET_FPS,
            "capture_method": self.config.CAPTURE_METHOD
        }

    def cleanup(self):
        """Cleanup screen capture resources."""
        if self.sct:
            self.sct.close()
        self.logger.info("Screen capture cleaned up")


class RegionOfInterest:
    """Helper class for managing ROI operations."""

    def __init__(self, name: str, coords: Tuple[int, int, int, int]):
        self.name = name
        self.x1, self.y1, self.x2, self.y2 = coords
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within ROI."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def get_relative_coords(self, x: int, y: int) -> Tuple[int, int]:
        """Convert absolute coordinates to relative within ROI."""
        return (x - self.x1, y - self.y1)

    def get_absolute_coords(self, rel_x: int, rel_y: int) -> Tuple[int, int]:
        """Convert relative coordinates to absolute."""
        return (self.x1 + rel_x, self.y1 + rel_y)

    def __repr__(self):
        return f"ROI({self.name}: {self.x1},{self.y1},{self.x2},{self.y2})"
