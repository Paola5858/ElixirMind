"""
ElixirMind Vision Utilities
Helper functions for computer vision and image processing.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import math
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def calculate_iou(box1: List[int], box2: List[int]) -> float:
    """Calculate Intersection over Union (IoU) for two bounding boxes."""
    try:
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # Calculate intersection area
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)

        if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
            return 0.0

        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)

        # Calculate union area
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = area1 + area2 - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    except Exception as e:
        logger.error(f"IoU calculation failed: {e}")
        return 0.0


def non_max_suppression(detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
    """Apply Non-Maximum Suppression to remove overlapping detections."""
    try:
        if not detections:
            return []

        # Sort by confidence
        sorted_detections = sorted(
            detections, key=lambda x: x.get('confidence', 0), reverse=True)

        filtered = []

        for current in sorted_detections:
            current_box = current.get('bbox', [])
            if not current_box:
                continue

            # Check against already filtered detections
            should_keep = True

            for filtered_detection in filtered:
                filtered_box = filtered_detection.get('bbox', [])
                if not filtered_box:
                    continue

                iou = calculate_iou(current_box, filtered_box)
                if iou > iou_threshold:
                    should_keep = False
                    break

            if should_keep:
                filtered.append(current)

        return filtered

    except Exception as e:
        logger.error(f"NMS failed: {e}")
        return detections


def resize_with_padding(image: np.ndarray, target_size: Tuple[int, int],
                        fill_color: Tuple[int, int, int] = (114, 114, 114)) -> np.ndarray:
    """Resize image with padding to maintain aspect ratio."""
    try:
        height, width = image.shape[:2]
        target_width, target_height = target_size

        # Calculate scaling factor
        scale = min(target_width / width, target_height / height)

        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize image
        resized = cv2.resize(image, (new_width, new_height),
                             interpolation=cv2.INTER_LINEAR)

        # Create padded image
        padded = np.full((target_height, target_width, 3),
                         fill_color, dtype=np.uint8)

        # Calculate padding offsets
        y_offset = (target_height - new_height) // 2
        x_offset = (target_width - new_width) // 2

        # Place resized image in center
        padded[y_offset:y_offset + new_height,
               x_offset:x_offset + new_width] = resized

        return padded

    except Exception as e:
        logger.error(f"Resize with padding failed: {e}")
        return image


def extract_color_histogram(image: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
    """Extract color histogram from image region."""
    try:
        # Convert to HSV for better color representation
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Calculate histogram
        hist_h = cv2.calcHist([hsv], [0], mask, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], mask, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], mask, [256], [0, 256])

        # Normalize histograms
        hist_h = cv2.normalize(hist_h, hist_h).flatten()
        hist_s = cv2.normalize(hist_s, hist_s).flatten()
        hist_v = cv2.normalize(hist_v, hist_v).flatten()

        # Combine histograms
        combined_hist = np.concatenate([hist_h, hist_s, hist_v])

        return combined_hist

    except Exception as e:
        logger.error(f"Color histogram extraction failed: {e}")
        return np.array([])


def detect_edges(image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150) -> np.ndarray:
    """Detect edges using Canny edge detection."""
    try:
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, low_threshold, high_threshold)

        return edges

    except Exception as e:
        logger.error(f"Edge detection failed: {e}")
        return np.zeros_like(image[:, :, 0] if len(image.shape) == 3 else image)


def find_template_matches(image: np.ndarray, template: np.ndarray,
                          threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Find all template matches in image."""
    try:
        # Ensure both images are grayscale
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            image_gray = image

        if len(template.shape) == 3:
            template_gray = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        else:
            template_gray = template

        # Template matching
        result = cv2.matchTemplate(
            image_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        # Find locations where matching exceeds threshold
        locations = np.where(result >= threshold)

        matches = []
        h, w = template_gray.shape

        for pt in zip(*locations[::-1]):
            matches.append({
                'bbox': [pt[0], pt[1], pt[0] + w, pt[1] + h],
                'confidence': float(result[pt[1], pt[0]]),
                'center': [pt[0] + w // 2, pt[1] + h // 2]
            })

        # Apply NMS to remove overlapping matches
        return non_max_suppression(matches)

    except Exception as e:
        logger.error(f"Template matching failed: {e}")
        return []


def calculate_color_similarity(color1: np.ndarray, color2: np.ndarray) -> float:
    """Calculate color similarity using Euclidean distance."""
    try:
        if color1.shape != color2.shape:
            return 0.0

        # Calculate Euclidean distance in color space
        distance = np.sqrt(np.sum((color1 - color2) ** 2))

        # Convert to similarity (0-1, where 1 is identical)
        max_distance = np.sqrt(3 * (255 ** 2))  # Maximum possible RGB distance
        similarity = 1.0 - (distance / max_distance)

        return max(0.0, similarity)

    except Exception as e:
        logger.error(f"Color similarity calculation failed: {e}")
        return 0.0


def enhance_image_contrast(image: np.ndarray, alpha: float = 1.2, beta: int = 30) -> np.ndarray:
    """Enhance image contrast and brightness."""
    try:
        # Apply contrast and brightness adjustment
        enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return enhanced

    except Exception as e:
        logger.error(f"Image enhancement failed: {e}")
        return image


def create_circular_mask(shape: Tuple[int, int], center: Tuple[int, int], radius: int) -> np.ndarray:
    """Create circular mask for region extraction."""
    try:
        mask = np.zeros(shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)
        return mask

    except Exception as e:
        logger.error(f"Circular mask creation failed: {e}")
        return np.zeros(shape[:2], dtype=np.uint8)


def extract_roi_safe(image: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
    """Safely extract ROI from image with bounds checking."""
    try:
        if image.size == 0:
            return np.array([])

        height, width = image.shape[:2]
        x1, y1, x2, y2 = roi

        # Clamp coordinates to image bounds
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(x1 + 1, min(x2, width))
        y2 = max(y1 + 1, min(y2, height))

        return image[y1:y2, x1:x2]

    except Exception as e:
        logger.error(f"ROI extraction failed: {e}")
        return np.array([])


def calculate_distance(point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
    """Calculate Euclidean distance between two points."""
    try:
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    except Exception as e:
        logger.error(f"Distance calculation failed: {e}")
        return float('inf')


def filter_detections_by_area(detections: List[Dict], min_area: int = 100,
                              max_area: int = 50000) -> List[Dict]:
    """Filter detections by bounding box area."""
    try:
        filtered = []

        for detection in detections:
            bbox = detection.get('bbox', [])
            if len(bbox) >= 4:
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                area = width * height

                if min_area <= area <= max_area:
                    filtered.append(detection)

        return filtered

    except Exception as e:
        logger.error(f"Area filtering failed: {e}")
        return detections


def draw_detection_results(image: np.ndarray, detections: List[Dict],
                           class_names: Optional[Dict] = None) -> np.ndarray:
    """Draw detection results on image for visualization."""
    try:
        result_image = image.copy()

        for detection in detections:
            bbox = detection.get('bbox', [])
            confidence = detection.get('confidence', 0.0)
            class_id = detection.get('class', 'unknown')

            if len(bbox) >= 4:
                x1, y1, x2, y2 = bbox

                # Draw bounding box
                cv2.rectangle(result_image, (int(x1), int(y1)),
                              (int(x2), int(y2)), (0, 255, 0), 2)

                # Draw label
                label = f"{class_names.get(class_id, class_id) if class_names else class_id}: {confidence:.2f}"
                label_size = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]

                cv2.rectangle(result_image, (int(x1), int(y1) - label_size[1] - 10),
                              (int(x1) + label_size[0], int(y1)), (0, 255, 0), -1)

                cv2.putText(result_image, label, (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return result_image

    except Exception as e:
        logger.error(f"Detection visualization failed: {e}")
        return image


def normalize_coordinates(coords: Tuple[int, int], image_shape: Tuple[int, int]) -> Tuple[float, float]:
    """Normalize coordinates to 0-1 range based on image dimensions."""
    try:
        height, width = image_shape[:2]
        x, y = coords

        norm_x = x / width if width > 0 else 0.0
        norm_y = y / height if height > 0 else 0.0

        return (norm_x, norm_y)

    except Exception as e:
        logger.error(f"Coordinate normalization failed: {e}")
        return (0.0, 0.0)


def denormalize_coordinates(norm_coords: Tuple[float, float],
                            image_shape: Tuple[int, int]) -> Tuple[int, int]:
    """Convert normalized coordinates back to pixel coordinates."""
    try:
        height, width = image_shape[:2]
        norm_x, norm_y = norm_coords

        x = int(norm_x * width)
        y = int(norm_y * height)

        return (x, y)

    except Exception as e:
        logger.error(f"Coordinate denormalization failed: {e}")
        return (0, 0)
