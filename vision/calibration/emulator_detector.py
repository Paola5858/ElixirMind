"""
Emulator Detector: Detects the type of emulator being used.
"""

import cv2
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

class EmulatorDetector:
    def __init__(self):
        self.emulator_signatures = {
            'memu': {
                'templates': ['memu_border.png', 'memu_controls.png'],
                'window_title_keywords': ['mumu', 'memu'],
                'process_names': ['MEmu.exe', 'MEmuConsole.exe']
            },
            'bluestacks': {
                'templates': ['bluestacks_home.png', 'bluestacks_settings.png'],
                'window_title_keywords': ['bluestacks', 'blue'],
                'process_names': ['Bluestacks.exe', 'HD-Player.exe']
            },
            'ldplayer': {
                'templates': ['ldplayer_border.png', 'ldplayer_controls.png'],
                'window_title_keywords': ['ldplayer'],
                'process_names': ['LdVBoxHeadless.exe', 'LdBox.exe']
            }
        }
        self.templates = {}

    def detect_emulator(self, screen_image=None, window_title=None, process_list=None):
        """Detect emulator type using multiple methods."""
        detections = {}

        # Method 1: Template matching on screen
        if screen_image is not None:
            detections.update(self.detect_by_templates(screen_image))

        # Method 2: Window title analysis
        if window_title:
            detections.update(self.detect_by_window_title(window_title))

        # Method 3: Process analysis
        if process_list:
            detections.update(self.detect_by_processes(process_list))

        # Determine most likely emulator
        if detections:
            emulator_type = max(detections, key=detections.get)
            confidence = detections[emulator_type]
            logger.info(f"Detected emulator: {emulator_type} (confidence: {confidence})")
            return emulator_type, confidence

        logger.warning("Could not detect emulator type")
        return None, 0.0

    def detect_by_templates(self, image):
        """Detect by matching templates."""
        detections = {}
        for emulator, config in self.emulator_signatures.items():
            confidence = 0.0
            template_count = 0

            for template_name in config['templates']:
                template = self.load_template(template_name)
                if template is not None:
                    match_conf = self.match_template(image, template)
                    confidence += match_conf
                    template_count += 1

            if template_count > 0:
                detections[emulator] = confidence / template_count

        return detections

    def detect_by_window_title(self, title):
        """Detect by analyzing window title."""
        detections = {}
        title_lower = title.lower()

        for emulator, config in self.emulator_signatures.items():
            confidence = 0.0
            keyword_count = 0

            for keyword in config['window_title_keywords']:
                if keyword in title_lower:
                    confidence += 1.0
                    keyword_count += 1

            if keyword_count > 0:
                detections[emulator] = min(1.0, confidence / keyword_count)

        return detections

    def detect_by_processes(self, process_list):
        """Detect by checking running processes."""
        detections = {}
        process_names = [p.lower() for p in process_list]

        for emulator, config in self.emulator_signatures.items():
            for process in config['process_names']:
                if process.lower() in process_names:
                    detections[emulator] = 1.0
                    break

        return detections

    def load_template(self, template_name):
        """Load template image."""
        if template_name in self.templates:
            return self.templates[template_name]

        # Assume templates are in data/templates/
        template_path = os.path.join('data', 'templates', template_name)
        if os.path.exists(template_path):
            template = cv2.imread(template_path)
            if template is not None:
                self.templates[template_name] = template
                return template

        return None

    def match_template(self, image, template):
        """Match template in image."""
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val
