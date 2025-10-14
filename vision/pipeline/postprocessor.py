"""
Postprocessor: Handles post-processing (NMS, filtering, validation).
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Postprocessor:
    def __init__(self, config):
        self.config = config
        self.nms_threshold = config.get('nms_threshold', 0.3)
        self.confidence_threshold = config.get('confidence_threshold', 0.5)

    def postprocess(self, detections):
        """Apply post-processing to detections."""
        if not detections:
            return []

        # Filter by confidence
        filtered = self.filter_by_confidence(detections)

        # Apply Non-Maximum Suppression
        nms_result = self.apply_nms(filtered)

        # Validate detections
        validated = self.validate_detections(nms_result)

        return validated

    def filter_by_confidence(self, detections):
        """Filter detections by confidence threshold."""
        return [d for d in detections if d.get('confidence', 0) >= self.confidence_threshold]

    def apply_nms(self, detections):
        """Apply Non-Maximum Suppression to reduce overlapping detections."""
        if not detections:
            return []

        # Extract boxes and scores
        boxes = []
        scores = []
        for det in detections:
            bbox = det.get('bbox', [])
            if len(bbox) == 4:
                boxes.append(bbox)
                scores.append(det.get('confidence', 0))

        if not boxes:
            return detections

        # Convert to numpy arrays
        boxes = np.array(boxes)
        scores = np.array(scores)

        # Apply NMS
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_threshold, self.nms_threshold)

        if len(indices) > 0:
            indices = indices.flatten()
            return [detections[i] for i in indices]

        return []

    def validate_detections(self, detections):
        """Validate detections for consistency."""
        validated = []
        for det in detections:
            if self.is_valid_detection(det):
                validated.append(det)
        return validated

    def is_valid_detection(self, detection):
        """Check if detection is valid."""
        required_keys = ['bbox', 'confidence']
        for key in required_keys:
            if key not in detection:
                return False

        bbox = detection['bbox']
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            return False

        # Check bbox coordinates are reasonable
        x, y, w, h = bbox
        if w <= 0 or h <= 0 or x < 0 or y < 0:
            return False

        return True
