print('Manual edit test')
import os
content = open('screen_capture.py').read()
new_content = content.replace('from config import Config', '''# Config class defined inline to avoid import issues
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
        self.ROI_MY_TOWERS = (0, 400, 1920, 800)''')
open('screen_capture.py', 'w').write(new_content)
print('File modified')
