"""
Pattern Randomizer: Randomizes bot behavior patterns to avoid detection.
"""

import random
import logging
from typing import Dict, List, Any, Optional, Callable
import time

logger = logging.getLogger(__name__)

class PatternRandomizer:
    """
    Randomizes various bot behavior patterns to make them less predictable
    and harder to detect.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Randomization parameters
        self.randomization_strength = self.config.get('randomization_strength', 0.5)
        self.pattern_memory = self.config.get('pattern_memory', 10)

        # Pattern tracking
        self.action_patterns = []
        self.timing_patterns = []
        self.movement_patterns = []

        # Randomization rules
        self.rules = {
            'action_sequence': self._randomize_action_sequence,
            'timing_delays': self._randomize_timing_delays,
            'movement_paths': self._randomize_movement_paths,
            'decision_order': self._randomize_decision_order,
            'resource_usage': self._randomize_resource_usage
        }

        # Pattern history for analysis
        self.pattern_history = []

        logger.info("Pattern Randomizer initialized")

    def randomize_action(self, action: Dict) -> Dict:
        """
        Apply randomization to a bot action.

        Args:
            action: Original action dictionary

        Returns:
            Randomized action dictionary
        """
        randomized_action = action.copy()

        # Apply various randomization techniques
        randomized_action = self._apply_timing_randomization(randomized_action)
        randomized_action = self._apply_parameter_randomization(randomized_action)
        randomized_action = self._apply_sequence_randomization(randomized_action)

        # Track pattern
        self._track_pattern('action', action, randomized_action)

        return randomized_action

    def randomize_timing(self, base_delay: float, context: str = 'general') -> float:
        """
        Randomize timing delays to avoid predictable patterns.

        Args:
            base_delay: Base delay time
            context: Context for the timing (affects randomization)

        Returns:
            Randomized delay time
        """
        # Context-based randomization
        context_multiplier = self._get_context_multiplier(context)

        # Apply randomization
        variation_range = base_delay * self.randomization_strength * context_multiplier
        variation = random.uniform(-variation_range, variation_range)

        randomized_delay = base_delay + variation

        # Ensure minimum delay
        randomized_delay = max(0.01, randomized_delay)

        # Track timing pattern
        self._track_timing_pattern(base_delay, randomized_delay, context)

        return randomized_delay

    def randomize_movement(self, start_pos: tuple, end_pos: tuple,
                          movement_type: str = 'cursor') -> List[tuple]:
        """
        Randomize movement patterns.

        Args:
            start_pos: Starting position
            end_pos: Ending position
            movement_type: Type of movement

        Returns:
            List of positions for randomized movement path
        """
        # Base straight line
        path = [start_pos, end_pos]

        # Apply randomization based on movement type
        if movement_type == 'cursor':
            path = self._randomize_cursor_movement(start_pos, end_pos)
        elif movement_type == 'scroll':
            path = self._randomize_scroll_movement(start_pos, end_pos)
        elif movement_type == 'drag':
            path = self._randomize_drag_movement(start_pos, end_pos)

        # Track movement pattern
        self._track_movement_pattern(start_pos, end_pos, path, movement_type)

        return path

    def randomize_decision(self, options: List[Any], weights: Optional[List[float]] = None) -> Any:
        """
        Randomize decision making to avoid predictable choices.

        Args:
            options: List of decision options
            weights: Optional weights for options

        Returns:
            Selected option
        """
        if not options:
            return None

        # Apply randomization to weights
        if weights is None:
            weights = [1.0] * len(options)

        # Add randomness to weights
        randomized_weights = []
        for weight in weights:
            variation = weight * self.randomization_strength * random.uniform(-0.5, 0.5)
            randomized_weight = max(0.1, weight + variation)
            randomized_weights.append(randomized_weight)

        # Select option
        total_weight = sum(randomized_weights)
        normalized_weights = [w / total_weight for w in randomized_weights]

        choice = random.choices(options, weights=normalized_weights, k=1)[0]

        # Track decision pattern
        self._track_decision_pattern(options, weights, choice)

        return choice

    def inject_random_events(self, probability: float = 0.1) -> Optional[Dict]:
        """
        Occasionally inject random events to break patterns.

        Args:
            probability: Probability of injecting a random event

        Returns:
            Random event action or None
        """
        if random.random() < probability:
            events = [
                {'type': 'pause', 'duration': random.uniform(0.5, 3.0)},
                {'type': 'micro_movement', 'distance': random.randint(1, 5)},
                {'type': 'focus_change', 'target': 'random_window'},
                {'type': 'scroll_check', 'direction': random.choice(['up', 'down'])}
            ]

            event = random.choice(events)
            logger.debug(f"Injected random event: {event}")
            return event

        return None

    def analyze_patterns(self) -> Dict:
        """
        Analyze current randomization patterns for effectiveness.

        Returns:
            Analysis of pattern distribution and randomness
        """
        analysis = {
            'total_patterns': len(self.pattern_history),
            'pattern_distribution': {},
            'randomness_score': 0.0,
            'detection_risk': 'low'
        }

        if not self.pattern_history:
            return analysis

        # Analyze pattern distribution
        pattern_types = {}
        for pattern in self.pattern_history[-100:]:  # Last 100 patterns
            p_type = pattern.get('type', 'unknown')
            pattern_types[p_type] = pattern_types.get(p_type, 0) + 1

        analysis['pattern_distribution'] = pattern_types

        # Calculate randomness score (0-1, higher is more random)
        total_patterns = sum(pattern_types.values())
        if total_patterns > 0:
            max_expected = total_patterns / len(pattern_types)
            variance = sum((count - max_expected) ** 2 for count in pattern_types.values())
            randomness_score = 1.0 - (variance / (total_patterns ** 2))
            analysis['randomness_score'] = max(0.0, min(1.0, randomness_score))

        # Assess detection risk
        if analysis['randomness_score'] < 0.3:
            analysis['detection_risk'] = 'high'
        elif analysis['randomness_score'] < 0.6:
            analysis['detection_risk'] = 'medium'
        else:
            analysis['detection_risk'] = 'low'

        return analysis

    def _apply_timing_randomization(self, action: Dict) -> Dict:
        """Apply timing randomization to action."""
        if 'delay' in action:
            original_delay = action['delay']
            randomized_delay = self.randomize_timing(original_delay, 'action_timing')
            action['delay'] = randomized_delay

        return action

    def _apply_parameter_randomization(self, action: Dict) -> Dict:
        """Apply parameter randomization to action."""
        # Randomize numeric parameters slightly
        for key, value in action.items():
            if isinstance(value, (int, float)) and key not in ['delay', 'timestamp']:
                # Small randomization for parameters
                variation = value * self.randomization_strength * 0.1
                action[key] = value + random.uniform(-variation, variation)

        return action

    def _apply_sequence_randomization(self, action: Dict) -> Dict:
        """Apply sequence randomization to break repetitive patterns."""
        # Occasionally modify action sequence
        if random.random() < self.randomization_strength * 0.2:
            # Could add micro-pauses or reorder sub-actions
            action['sequence_randomized'] = True

        return action

    def _randomize_cursor_movement(self, start: tuple, end: tuple) -> List[tuple]:
        """Randomize cursor movement path."""
        # Add intermediate points for natural movement
        points = [start]

        # Add 1-3 intermediate points
        num_points = random.randint(1, 3)
        for i in range(num_points):
            t = (i + 1) / (num_points + 1)
            # Add some deviation from straight line
            deviation = random.randint(-20, 20)
            if random.random() < 0.5:  # X or Y deviation
                mid_x = start[0] + (end[0] - start[0]) * t + deviation
                mid_y = start[1] + (end[1] - start[1]) * t
            else:
                mid_x = start[0] + (end[0] - start[0]) * t
                mid_y = start[1] + (end[1] - start[1]) * t + deviation

            points.append((int(mid_x), int(mid_y)))

        points.append(end)
        return points

    def _randomize_scroll_movement(self, start: tuple, end: tuple) -> List[tuple]:
        """Randomize scroll movement."""
        # Scroll movements are more direct but with slight variations
        points = [start]

        # Add small intermediate point
        mid_x = (start[0] + end[0]) / 2 + random.randint(-5, 5)
        mid_y = (start[1] + end[1]) / 2 + random.randint(-5, 5)
        points.append((int(mid_x), int(mid_y)))

        points.append(end)
        return points

    def _randomize_drag_movement(self, start: tuple, end: tuple) -> List[tuple]:
        """Randomize drag movement (more deliberate)."""
        # Drag movements should be more precise but still human-like
        points = [start]

        # Add multiple points for smooth dragging
        steps = random.randint(3, 6)
        for i in range(1, steps):
            t = i / steps
            x = start[0] + (end[0] - start[0]) * t + random.randint(-3, 3)
            y = start[1] + (end[1] - start[1]) * t + random.randint(-3, 3)
            points.append((int(x), int(y)))

        points.append(end)
        return points

    def _get_context_multiplier(self, context: str) -> float:
        """Get randomization multiplier based on context."""
        multipliers = {
            'combat': 0.7,  # Less randomization in combat (needs to be responsive)
            'menu_navigation': 1.2,  # More randomization in menus
            'waiting': 1.5,  # More randomization during waits
            'general': 1.0
        }
        return multipliers.get(context, 1.0)

    def _track_pattern(self, pattern_type: str, original: Any, randomized: Any):
        """Track pattern for analysis."""
        pattern_entry = {
            'timestamp': time.time(),
            'type': pattern_type,
            'original': str(original)[:100],  # Truncate for storage
            'randomized': str(randomized)[:100],
            'randomization_applied': original != randomized
        }

        self.pattern_history.append(pattern_entry)

        # Keep history manageable
        if len(self.pattern_history) > 1000:
            self.pattern_history = self.pattern_history[-500:]

    def _track_timing_pattern(self, original: float, randomized: float, context: str):
        """Track timing pattern."""
        self._track_pattern('timing', {'delay': original, 'context': context},
                          {'delay': randomized, 'context': context})

    def _track_movement_pattern(self, start: tuple, end: tuple, path: List[tuple], movement_type: str):
        """Track movement pattern."""
        self._track_pattern('movement', {'start': start, 'end': end, 'type': movement_type},
                          {'path_length': len(path), 'type': movement_type})

    def _track_decision_pattern(self, options: List[Any], weights: Optional[List[float]], choice: Any):
        """Track decision pattern."""
        self._track_pattern('decision', {'options_count': len(options), 'weights': weights},
                          {'choice_index': options.index(choice) if choice in options else -1})
