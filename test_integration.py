#!/usr/bin/env python3
"""
Test integration of screen capture with vision detector.
"""

import sys
sys.path.insert(0, r'C:\Users\Usuario\AppData\Local\Programs\Python\Python310\Lib\site-packages')

from config import load_config

class Config:
    """Configuration class for screen capture."""
    def __init__(self):
        self.config = load_config()
        # Set default attributes that screen_capture expects
        self.EMULATOR_TYPE = self.config.get('emulator_type', 'memu')
        self.TARGET_FPS = 10
        self.CAPTURE_METHOD = 'mss'
        self.SCREENSHOT_DIR = 'screenshots'
        # Add ROI definitions (placeholders)
        self.ROI_HAND = (0, 800, 1920, 1080)
        self.ROI_BATTLEFIELD = (0, 0, 1920, 800)
        self.ROI_ELIXIR = (1700, 900, 1900, 1000)
        self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
        self.ROI_MY_TOWERS = (0, 400, 1920, 800)
        # Add missing attributes for vision components
        self.target_resolution = (1920, 1080)
        self.template_threshold = 0.7
        self.roi_padding = 10

    def get(self, key, default=None):
        """Dict-like get method for compatibility."""
        return getattr(self, key, default)

def test_screen_capture():
    """Test screen capture integration."""
    print("Testing screen capture integration...")

    try:
        from screen_capture import ScreenCapture

        config = Config()
        sc = ScreenCapture(config)

        success = sc.initialize()
        if not success:
            print("❌ Screen capture initialization failed")
            return False

        print("✅ Screen capture initialized")

        # Test capture
        frame = sc.capture()
        if frame is None:
            print("❌ Screen capture failed")
            return False

        print(f"✅ Screen capture successful: {frame.shape}")

        # Test vision detector integration
        from vision.detector import Detector

        detector = Detector(config)
        detector.initialize()

        # Test capture_screen method
        captured_frame = detector.capture_screen()
        if captured_frame is None:
            print("❌ Vision detector capture failed")
            return False

        print(f"✅ Vision detector capture successful: {captured_frame.shape}")

        detector.shutdown()
        sc.cleanup()

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_screen_capture()
    print(f"\nIntegration test: {'PASSED' if success else 'FAILED'}")
