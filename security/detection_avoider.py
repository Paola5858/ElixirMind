"""
Detection Avoider: Implements various techniques to avoid detection by game anti-cheat systems.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Callable
import hashlib
import os

logger = logging.getLogger(__name__)

class DetectionAvoider:
    """
    Implements various techniques to avoid detection by anti-cheat systems,
    including signature randomization, behavior normalization, and stealth techniques.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Detection avoidance settings
        self.stealth_level = self.config.get('stealth_level', 'medium')  # low, medium, high
        self.signature_rotation_interval = self.config.get('signature_rotation', 300)  # 5 minutes

        # Detection patterns to avoid
        self.known_detection_patterns = {
            'perfect_timing': self._avoid_perfect_timing,
            'repetitive_actions': self._avoid_repetitive_actions,
            'unusual_patterns': self._avoid_unusual_patterns,
            'memory_signatures': self._avoid_memory_signatures,
            'network_signatures': self._avoid_network_signatures
        }

        # Stealth techniques
        self.stealth_techniques = {
            'memory_obfuscation': self._apply_memory_obfuscation,
            'timing_jitter': self._apply_timing_jitter,
            'behavior_mimicry': self._apply_behavior_mimicry,
            'signature_rotation': self._apply_signature_rotation
        }

        # Detection history
        self.detection_history = []
        self.last_signature_rotation = time.time()

        # Risk assessment
        self.current_risk_level = 'low'
        self.risk_factors = {}

        logger.info(f"Detection Avoider initialized with {self.stealth_level} stealth level")

    def process_action(self, action: Dict) -> Dict:
        """
        Process an action through detection avoidance techniques.

        Args:
            action: Bot action to process

        Returns:
            Modified action with detection avoidance applied
        """
        processed_action = action.copy()

        # Apply stealth techniques based on level
        if self.stealth_level == 'high':
            processed_action = self._apply_all_stealth_techniques(processed_action)
        elif self.stealth_level == 'medium':
            processed_action = self._apply_medium_stealth(processed_action)
        else:  # low
            processed_action = self._apply_basic_stealth(processed_action)

        # Check for detection patterns
        self._check_detection_patterns(processed_action)

        # Update risk assessment
        self._update_risk_assessment()

        return processed_action

    def get_risk_assessment(self) -> Dict:
        """
        Get current risk assessment.

        Returns:
            Dict with risk assessment data
        """
        return {
            'current_risk_level': self.current_risk_level,
            'risk_factors': self.risk_factors.copy(),
            'stealth_level': self.stealth_level,
            'last_signature_rotation': self.last_signature_rotation,
            'detection_events': len(self.detection_history)
        }

    def force_signature_rotation(self):
        """Force immediate signature rotation."""
        self._apply_signature_rotation()
        self.last_signature_rotation = time.time()
        logger.info("Forced signature rotation")

    def simulate_human_behavior(self, action: Dict) -> Dict:
        """
        Apply human-like behavior modifications to avoid detection.

        Args:
            action: Original action

        Returns:
            Modified action with human-like behavior
        """
        # Add micro-delays
        if 'delay' not in action:
            action['delay'] = random.uniform(0.01, 0.05)

        # Add slight timing variations
        if 'timing' in action:
            original_timing = action['timing']
            variation = original_timing * 0.05  # 5% variation
            action['timing'] = original_timing + random.uniform(-variation, variation)

        # Add occasional mistakes or corrections
        if random.random() < 0.02:  # 2% chance
            action['human_error'] = True
            action['correction_delay'] = random.uniform(0.1, 0.5)

        return action

    def _apply_all_stealth_techniques(self, action: Dict) -> Dict:
        """Apply all stealth techniques (high stealth level)."""
        for technique_func in self.stealth_techniques.values():
            action = technique_func(action)
        return action

    def _apply_medium_stealth(self, action: Dict) -> Dict:
        """Apply medium level stealth techniques."""
        techniques_to_apply = ['timing_jitter', 'behavior_mimicry']
        for technique in techniques_to_apply:
            if technique in self.stealth_techniques:
                action = self.stealth_techniques[technique](action)
        return action

    def _apply_basic_stealth(self, action: Dict) -> Dict:
        """Apply basic stealth techniques."""
        return self.stealth_techniques['timing_jitter'](action)

    def _apply_memory_obfuscation(self, action: Dict) -> Dict:
        """Apply memory obfuscation techniques."""
        # Add random memory access patterns
        action['memory_noise'] = os.urandom(16).hex()

        # Modify action hash to avoid signature detection
        action_content = str(sorted(action.items()))
        action['signature_hash'] = hashlib.sha256(action_content.encode()).hexdigest()[:16]

        return action

    def _apply_timing_jitter(self, action: Dict) -> Dict:
        """Apply timing jitter to avoid perfect timing detection."""
        if 'delay' in action:
            original_delay = action['delay']
            # Add small random jitter
            jitter = original_delay * 0.1 * random.uniform(-1, 1)
            action['delay'] = max(0.001, original_delay + jitter)

        # Add micro-pauses between actions
        action['micro_pause'] = random.uniform(0.001, 0.01)

        return action

    def _apply_behavior_mimicry(self, action: Dict) -> Dict:
        """Apply human behavior mimicry."""
        # Simulate human decision variability
        if 'confidence' in action:
            original_confidence = action['confidence']
            # Add human-like uncertainty
            uncertainty = random.uniform(-0.1, 0.1)
            action['confidence'] = max(0.0, min(1.0, original_confidence + uncertainty))

        # Add occasional "thinking" delays
        if random.random() < 0.05:
            action['thinking_delay'] = random.uniform(0.2, 1.0)

        return action

    def _apply_signature_rotation(self, action: Dict = None) -> Dict:
        """Apply signature rotation to avoid pattern detection."""
        # Rotate various identifiers and patterns
        rotation_data = {
            'rotation_timestamp': time.time(),
            'rotation_id': random.randint(1000, 9999),
            'pattern_offset': random.uniform(0, 1)
        }

        if action is not None:
            action['signature_rotation'] = rotation_data
            return action
        else:
            # Global rotation
            self.last_signature_rotation = time.time()
            logger.info("Applied global signature rotation")

        return action if action is not None else {}

    def _avoid_perfect_timing(self, action: Dict) -> Dict:
        """Avoid detection based on perfect timing patterns."""
        # Check if timing is too perfect (exact intervals)
        if 'interval' in action:
            interval = action['interval']
            # Add small imperfection to perfect intervals
            if interval % 0.1 == 0:  # Too round
                imperfection = random.uniform(-0.02, 0.02)
                action['interval'] = max(0.01, interval + imperfection)

        return action

    def _avoid_repetitive_actions(self, action: Dict) -> Dict:
        """Avoid detection based on repetitive action patterns."""
        # Track action frequency and add variations
        action_type = action.get('type', 'unknown')

        # Add occasional different actions to break patterns
        if random.random() < 0.03:  # 3% chance
            action['pattern_break'] = True
            action['alternative_action'] = f"variant_{random.randint(1, 5)}"

        return action

    def _avoid_unusual_patterns(self, action: Dict) -> Dict:
        """Avoid unusual patterns that might trigger detection."""
        # Check for unusual parameter combinations
        suspicious_patterns = [
            lambda a: a.get('speed', 1.0) > 10,  # Too fast
            lambda a: a.get('accuracy', 0.5) > 0.99,  # Too accurate
            lambda a: a.get('delay', 1.0) < 0.001,  # Too fast response
        ]

        for pattern_check in suspicious_patterns:
            if pattern_check(action):
                # Normalize suspicious parameters
                if 'speed' in action and action['speed'] > 10:
                    action['speed'] = random.uniform(1.0, 3.0)
                if 'accuracy' in action and action['accuracy'] > 0.99:
                    action['accuracy'] = random.uniform(0.85, 0.95)
                if 'delay' in action and action['delay'] < 0.001:
                    action['delay'] = random.uniform(0.01, 0.1)

                logger.debug("Normalized suspicious action parameters")

        return action

    def _avoid_memory_signatures(self, action: Dict) -> Dict:
        """Avoid memory-based detection signatures."""
        # Add memory noise and obfuscation
        action['memory_fingerprint'] = hashlib.md5(os.urandom(32)).hexdigest()

        # Randomize memory allocation patterns
        if random.random() < 0.1:
            action['memory_allocation'] = random.randint(1024, 10240)  # Random allocation size

        return action

    def _avoid_network_signatures(self, action: Dict) -> Dict:
        """Avoid network-based detection signatures."""
        # Add network traffic randomization
        if 'network_call' in action:
            # Add random headers or parameters
            action['network_noise'] = {
                'user_agent_variation': random.randint(1, 10),
                'request_delay': random.uniform(0.001, 0.01)
            }

        return action

    def _check_detection_patterns(self, action: Dict):
        """Check action against known detection patterns."""
        for pattern_name, pattern_func in self.known_detection_patterns.items():
            try:
                pattern_func(action)
            except Exception as e:
                logger.warning(f"Error checking detection pattern {pattern_name}: {e}")

    def _update_risk_assessment(self):
        """Update overall risk assessment."""
        # Calculate risk based on various factors
        risk_score = 0.0

        # Factor 1: Stealth level
        stealth_multipliers = {'low': 1.5, 'medium': 1.0, 'high': 0.5}
        risk_score += stealth_multipliers.get(self.stealth_level, 1.0)

        # Factor 2: Time since last signature rotation
        time_since_rotation = time.time() - self.last_signature_rotation
        if time_since_rotation > self.signature_rotation_interval * 2:
            risk_score += 0.5  # Increased risk

        # Factor 3: Detection history
        recent_detections = len([
            d for d in self.detection_history
            if time.time() - d['timestamp'] < 3600  # Last hour
        ])
        risk_score += recent_detections * 0.2

        # Determine risk level
        if risk_score > 2.0:
            self.current_risk_level = 'high'
        elif risk_score > 1.0:
            self.current_risk_level = 'medium'
        else:
            self.current_risk_level = 'low'

        # Update risk factors
        self.risk_factors = {
            'stealth_level': self.stealth_level,
            'time_since_rotation': time_since_rotation,
            'recent_detections': recent_detections,
            'calculated_score': risk_score
        }
