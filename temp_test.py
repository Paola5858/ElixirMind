import sys
sys.path.insert(0, r'C:\Users\Usuario\AppData\Local\Programs\Python\Python310\Lib\site-packages')

print('Creating Config class...')
from config import load_config

class Config:
    pass

c = Config()
c.config = load_config()
c.EMULATOR_TYPE = c.config.get('emulator_type', 'memu')
c.TARGET_FPS = 10
c.CAPTURE_METHOD = 'mss'
c.SCREENSHOT_DIR = 'screenshots'
c.ROI_HAND = (0, 800, 1920, 1080)
c.ROI_BATTLEFIELD = (0, 0, 1920, 800)
c.ROI_ELIXIR = (1700, 900, 1900, 1000)
c.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
c.ROI_MY_TOWERS = (0, 400, 1920, 800)

print('Config class created')
print('EMULATOR_TYPE:', c.EMULATOR_TYPE)

# Now test screen_capture import
try:
    from screen_capture import ScreenCapture
    print('ScreenCapture imported successfully')

    sc = ScreenCapture(c)
    success = sc.initialize()
    print('Screen capture init:', success)

    if success:
        frame = sc.capture()
        print('Capture result:', frame is not None)
        if frame is not None:
            print('Frame shape:', frame.shape)
        sc.cleanup()

except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()
