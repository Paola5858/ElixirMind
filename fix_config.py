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

# Add missing attributes
new_config_section = config_section.replace(
    '        self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)\n        self.ROI_MY_TOWERS = (0, 400, 1920, 800)',
    '''        self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
        self.ROI_MY_TOWERS = (0, 400, 1920, 800)
        # Add missing attributes for vision pipeline
        self.target_resolution = (1920, 1080)
        self.template_threshold = 0.7
        self.roi_padding = 10'''
)

new_content = content.replace(config_section, new_config_section)

# Write back
with open('screen_capture.py', 'w') as f:
    f.write(new_content)

print("Config class updated with missing attributes")
