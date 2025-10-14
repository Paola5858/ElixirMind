"""
Humanizer: Simulates human behavior patterns to avoid detection.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Callable
import math

logger = logging.getLogger(__name__)

class Humanizer:
    """
    Simulates human behavior patterns including reaction times,
    decision delays, and natural movement patterns.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Reaction time parameters (in seconds)
        self.min_reaction_time = self.config.get('min_reaction_time', 0.2)
        self.max_reaction_time = self.config.get('max_reaction_time', 1.5)
        self.avg_reaction_time = self.config.get('avg_reaction_time', 0.6)

        # Decision delay parameters
        self.min_decision_delay = self.config.get('min_decision_delay', 0.1)
        self.max_decision_delay = self.config.get('max_decision_delay', 2.0)

        # Movement patterns
        self.movement_smoothness = self.config.get('movement_smoothness', 0.8)
        self.cursor_speed_variation = self.config.get('cursor_speed_variation', 0.3)

        # Fatigue simulation
        self.fatigue_level = 0.0
        self.fatigue_increase_rate = self.config.get('fatigue_increase_rate', 0.001)

        # Behavior patterns
        self.behavior_patterns = {
            'focused': {'reaction_multiplier': 0.8, 'delay_multiplier': 0.7},
            'distracted': {'reaction_multiplier': 1.5, 'delay_multiplier': 1.8},
            'tired': {'reaction_multiplier': 2.0, 'delay_multiplier': 2.5},
            'aggressive': {'reaction_multiplier': 0.5, 'delay_multiplier': 0.4}
        }

        self.current_behavior = 'focused'

        logger.info("Humanizer initialized with human-like behavior simulation")

    def simulate_reaction_time(self, urgency: float = 1.0) -> float:
        """
        Simulate human reaction time based on urgency and current behavior.

        Args:
            urgency: Urgency factor (0.0 = very urgent, 1.0 = normal)

        Returns:
            Reaction time in seconds
        """
        # Base reaction time with normal distribution
        base_time = self._normal_distribution(
            self.avg_reaction_time,
            (self.max_reaction_time - self.min_reaction_time) / 6
        )

        # Apply behavior modifier
        behavior_mod = self.behavior_patterns[self.current_behavior]['reaction_multiplier']
        base_time *= behavior_mod

        # Apply urgency modifier (faster for urgent situations)
        urgency_mod = max(0.3, 1.0 - urgency * 0.7)
        base_time *= urgency_mod

        # Apply fatigue
        fatigue_mod = 1.0 + self.fatigue_level * 0.5
        base_time *= fatigue_mod

        # Ensure within bounds
        reaction_time = max(self.min_reaction_time, min(self.max_reaction_time, base_time))

        # Increase fatigue slightly
        self.fatigue_level = min(1.0, self.fatigue_level + self.fatigue_increase_rate)

        return reaction_time

    def simulate_decision_delay(self, complexity: float = 1.0) -> float:
        """
        Simulate decision-making delay based on complexity.

        Args:
            complexity: Decision complexity (0.0 = simple, 1.0 = complex)

        Returns:
            Decision delay in seconds
        """
        # Base delay increases with complexity
        base_delay = self.min_decision_delay + (
            self.max_decision_delay - self.min_decision_delay
        ) * complexity

        # Add randomness
        variation = (random.random() - 0.5) * 0.4  # ±20% variation
        base_delay *= (1.0 + variation)

        # Apply behavior modifier
        behavior_mod = self.behavior_patterns[self.current_behavior]['delay_multiplier']
        base_delay *= behavior_mod

        # Apply fatigue
        fatigue_mod = 1.0 + self.fatigue_level * 0.8
        base_delay *= fatigue_mod

        return max(self.min_decision_delay, base_delay)

    def simulate_cursor_movement(self, start_pos: tuple, end_pos: tuple,
                               duration: Optional[float] = None) -> List[tuple]:
        """
        Simulate human-like cursor movement with natural curves.

        Args:
            start_pos: Starting position (x, y)
            end_pos: Ending position (x, y)
            duration: Movement duration (auto-calculated if None)

        Returns:
            List of (x, y) positions for smooth movement
        """
        if duration is None:
            distance = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
            duration = distance / 800.0  # pixels per second
            duration = max(0.1, min(2.0, duration))  # Clamp duration

        # Add human-like variations
        control_points = self._generate_control_points(start_pos, end_pos)

        # Generate smooth curve
        points = []
        steps = max(5, int(duration * 60))  # 60 FPS equivalent

        for i in range(steps + 1):
            t = i / steps
            point = self._bezier_curve(t, [start_pos] + control_points + [end_pos])
            points.append(point)

        return points

    def simulate_typing_pattern(self, text: str) -> List[float]:
        """
        Simulate human typing patterns with varying delays.

        Args:
            text: Text to be "typed"

        Returns:
            List of delays between keystrokes
        """
        delays = []
        words = text.split()

        for i, word in enumerate(words):
            # Word-level delay
            if i > 0:
                word_delay = random.uniform(0.1, 0.5)
                delays.append(word_delay)

            # Character-level delays
            for char in word:
                # Faster for common characters, slower for special chars
                base_delay = 0.08 if char.isalnum() else 0.15

                # Add randomness
                delay = base_delay * random.uniform(0.7, 1.4)

                # Occasional longer pauses (thinking)
                if random.random() < 0.05:
                    delay += random.uniform(0.2, 0.8)

                delays.append(delay)

        return delays

    def take_break(self, break_duration: float = 30.0):
        """
        Simulate taking a break to reduce fatigue.

        Args:
            break_duration: Break duration in seconds
        """
        fatigue_reduction = min(self.fatigue_level, break_duration / 300.0)  # Reduce over 5 minutes
        self.fatigue_level -= fatigue_reduction

        logger.info(f"Took break for {break_duration:.1f}s, fatigue reduced by {fatigue_reduction:.3f}")

    def change_behavior(self, behavior: str):
        """
        Change current behavior pattern.

        Args:
            behavior: Behavior pattern name
        """
        if behavior in self.behavior_patterns:
            self.current_behavior = behavior
            logger.info(f"Changed behavior to: {behavior}")
        else:
            logger.warning(f"Unknown behavior pattern: {behavior}")

    def get_status(self) -> Dict:
        """
        Get current humanizer status.

        Returns:
            Dict with current status
        """
        return {
            'current_behavior': self.current_behavior,
            'fatigue_level': self.fatigue_level,
            'reaction_time_range': (self.min_reaction_time, self.max_reaction_time),
            'decision_delay_range': (self.min_decision_delay, self.max_decision_delay)
        }

    def _normal_distribution(self, mean: float, std_dev: float) -> float:
        """Generate a random value from normal distribution."""
        # Box-Muller transform for normal distribution
        u1 = random.random()
        u2 = random.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mean + z0 * std_dev

    def _generate_control_points(self, start: tuple, end: tuple) -> List[tuple]:
        """Generate control points for natural cursor movement."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # Add 1-2 control points for natural curves
        num_points = random.randint(1, 2)
        points = []

        for i in range(num_points):
            # Control point offset from straight line
            offset_factor = random.uniform(0.1, 0.4)
            perpendicular_x = -dy * offset_factor
            perpendicular_y = dx * offset_factor

            # Random position along the path
            t = random.uniform(0.2, 0.8)
            base_x = start[0] + dx * t
            base_y = start[1] + dy * t

            # Add perpendicular offset
            point = (
                base_x + perpendicular_x * (random.random() - 0.5) * 2,
                base_y + perpendicular_y * (random.random() - 0.5) * 2
            )
            points.append(point)

        return points

    def _bezier_curve(self, t: float, points: List[tuple]) -> tuple:
        """Calculate point on Bezier curve."""
        if len(points) == 1:
            return points[0]

        new_points = []
        for i in range(len(points) - 1):
            x = points[i][0] + (points[i+1][0] - points[i][0]) * t
            y = points[i][1] + (points[i+1][1] - points[i][1]) * t
            new_points.append((x, y))

        return self._bezier_curve(t, new_points)
