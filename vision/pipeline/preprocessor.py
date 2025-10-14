"""
Preprocessor: Handles image preprocessing (resize, normalize, enhance).
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Preprocessor:
    def __init__(self, config):
        self.config = config
        self.target_size = config.get('target_resolution', (1920, 1080))

    def preprocess(self, image):
        """Apply preprocessing pipeline to image."""
        if image is None:
            return None

        # Convert to numpy array if needed
        if not isinstance(image, np.ndarray):
            image = np.array(image)

        # Resize to target resolution
        image = self.resize_image(image)

        # Normalize
        image = self.normalize_image(image)

        # Enhance contrast
        image = self.enhance_contrast(image)

        return image

    def resize_image(self, image):
        """Resize image to target resolution."""
        if image.shape[:2] != self.target_size:
            image = cv2.resize(image, self.target_size, interpolation=cv2.INTER_LINEAR)
        return image

    def normalize_image(self, image):
        """Normalize image pixel values."""
        if image.dtype != np.uint8:
            image = cv2.convertScaleAbs(image, alpha=255.0)
        return image

    def enhance_contrast(self, image):
        """Enhance image contrast using CLAHE."""
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            image = clahe.apply(image)

        return image
