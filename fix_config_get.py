import os

# Read the Config class in screen_capture.py
with open('screen_capture.py', 'r') as f:
    content = f.read()

# Find the Config class definition
config_start = content.find('class Config:')
config_end = content.find('\n\nclass ScreenCapture:', config_start)
config_section = content[config_start:config_end]

print("Current Config class:")
print(config_section)
print("\n" + "="*50)

# Add get method to Config class
new_config_section = config_section.replace(
    '''        # Add missing attributes for vision pipeline
        self.target_resolution = (1920, 1080)
        self.template_threshold = 0.7
        self.roi_padding = 10''',
    '''        # Add missing attributes for vision pipeline
        self.target_resolution = (1920, 1080)
        self.template_threshold = 0.7
        self.roi_padding = 10

    def get(self, key, default=None):
        """Get configuration value with fallback to attributes."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.config.get(key, default)'''
)

new_content = content.replace(config_section, new_config_section)

# Write back
with open('screen_capture.py', 'w') as f:
    f.write(new_content)

print("Config class updated with get method")
