import os

# Read the detector file
with open('vision/detector.py', 'r') as f:
    content = f.read()

# Replace the capture_screen method
old_method = '''    def capture_screen(self):
        """Capture screen using emulator."""
        # This would integrate with emulator capture
        # For now, return placeholder
        return None'''

new_method = '''    def capture_screen(self):
        """Capture screen using screen capture system."""
        try:
            from screen_capture import ScreenCapture, Config
            if not hasattr(self, 'screen_capture'):
                config = Config()
                self.screen_capture = ScreenCapture(config)
                self.screen_capture.initialize()

            frame = self.screen_capture.capture()
            return frame
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None'''

new_content = content.replace(old_method, new_method)

# Write back
with open('vision/detector.py', 'w') as f:
    f.write(new_content)

print("Detector updated successfully")
