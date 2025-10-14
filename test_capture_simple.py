#!/usr/bin/env python3
"""
Simple test for screen capture with LDPlayer configuration.
"""

import sys
sys.path.insert(0, r'C:\Users\Usuario\AppData\Local\Programs\Python\Python310\Lib\site-packages')

from config import load_config

class Config:
    def __init__(self):
        self.config = load_config()
        self.EMULATOR_TYPE = 'ldplayer'  # Force LDPlayer for testing
        self.TARGET_FPS = 10
        self.CAPTURE_METHOD = 'mss'
        self.SCREENSHOT_DIR = 'screenshots'
        self.ROI_HAND = (0, 800, 1920, 1080)
        self.ROI_BATTLEFIELD = (0, 0, 1920, 800)
        self.ROI_ELIXIR = (1700, 900, 1900, 1000)
        self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
        self.ROI_MY_TOWERS = (0, 400, 1920, 800)

def test_capture():
    print("Testing screen capture with LDPlayer config...")

    config = Config()
    print(f"Emulator type: {config.EMULATOR_TYPE}")

    try:
        from screen_capture import ScreenCapture

        sc = ScreenCapture(config)
        success = sc.initialize()
        print(f'Screen capture init: {success}')

        if success:
            frame = sc.capture()
            print(f'Capture result: {frame is not None}')
            if frame is not None:
                print(f'Frame shape: {frame.shape}')
                print("✅ Screen capture working!")
            else:
                print("❌ Capture returned None")
        else:
            print("❌ Initialization failed")

        sc.cleanup()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_capture()
