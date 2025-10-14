"""
ElixirMind Action Feedback System
Validates and tracks the success of executed actions.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum

from config import Config


class FeedbackType(Enum):
    """Types of feedback validation."""
    VISUAL_CONFIRMATION = "visual"
    TIMING_BASED = "timing"
    STATE_CHANGE = "state_change"
    COMBINATION = "combination"


@dataclass
class ActionFeedback:
    """Represents feedback about an executed action."""
    action_id: str
    success: bool
    confidence: float
    feedback_type: FeedbackType
    details: Dict[str, Any]
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class ActionValidator:
    """Validates if actions were successfully executed."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Feedback history
        self.feedback_history = []

        # Validation settings
        self.validation_timeout = 2.0  # Max time to wait for validation
        self.confidence_threshold = 0.7

    async def validate_card_placement(self, action_params: Dict[str, Any],
                                      before_state: Any, after_state: Any) -> ActionFeedback:
        """Validate if card placement was successful."""
        try:
            action_id = f"place_card_{int(time.time() * 1000)}"

            # Check elixir change
            elixir_feedback = await self._validate_elixir_change(before_state, after_state)

            # Check for new troop appearance
            troop_feedback = await self._validate_troop_appearance(
                action_params.get('target_position'), after_state
            )

            # Combine feedback
            success = elixir_feedback['success'] and troop_feedback['success']
            confidence = min(
                elixir_feedback['confidence'], troop_feedback['confidence'])

            feedback = ActionFeedback(
                action_id=action_id,
                success=success,
                confidence=confidence,
                feedback_type=FeedbackType.COMBINATION,
                details={
                    'elixir_feedback': elixir_feedback,
                    'troop_feedback': troop_feedback,
                    'target_position': action_params.get('target_position')
                }
            )

            self.feedback_history.append(feedback)
            return feedback

        except Exception as e:
            self.logger.error(f"Card placement validation failed: {e}")
            return ActionFeedback(
                action_id="error",
                success=False,
                confidence=0.0,
                feedback_type=FeedbackType.VISUAL_CONFIRMATION,
                details={'error': str(e)}
            )

    async def _validate_elixir_change(self, before_state: Any, after_state: Any) -> Dict[str, Any]:
        """Validate that elixir decreased appropriately."""
        try:
            before_elixir = getattr(before_state, 'current_elixir', 0)
            after_elixir = getattr(after_state, 'current_elixir', 0)

            # Expected elixir decrease (varies by card, using 3-5 as typical)
            expected_decrease = 4  # Average card cost
            tolerance = 2

            actual_decrease = before_elixir - after_elixir

            # Check if decrease is reasonable
            if abs(actual_decrease - expected_decrease) <= tolerance and actual_decrease > 0:
                return {
                    'success': True,
                    'confidence': 0.8,
                    'before_elixir': before_elixir,
                    'after_elixir': after_elixir,
                    'decrease': actual_decrease
                }
            else:
                return {
                    'success': False,
                    'confidence': 0.3,
                    'before_elixir': before_elixir,
                    'after_elixir': after_elixir,
                    'decrease': actual_decrease
                }

        except Exception as e:
            self.logger.error(f"Elixir validation failed: {e}")
            return {'success': False, 'confidence': 0.0}

    async def _validate_troop_appearance(self, target_position: Tuple[int, int],
                                         after_state: Any) -> Dict[str, Any]:
        """Validate that a troop appeared near the target position."""
        try:
            if not target_position:
                return {'success': False, 'confidence': 0.0}

            target_x, target_y = target_position
            friendly_troops = getattr(after_state, 'friendly_troops', [])

            # Look for troops near target position
            detection_radius = 100  # pixels

            nearby_troops = []
            for troop in friendly_troops:
                troop_pos = troop.get('center', [0, 0])
                if len(troop_pos) >= 2:
                    troop_x, troop_y = troop_pos[:2]
                    distance = np.sqrt((troop_x - target_x)
                                       ** 2 + (troop_y - target_y) ** 2)

                    if distance <= detection_radius:
                        nearby_troops.append({
                            'troop': troop,
                            'distance': distance
                        })

            if nearby_troops:
                # Found troops near target
                closest = min(nearby_troops, key=lambda x: x['distance'])
                confidence = max(
                    0.5, 1.0 - (closest['distance'] / detection_radius))

                return {
                    'success': True,
                    'confidence': confidence,
                    'nearby_troops': len(nearby_troops),
                    'closest_distance': closest['distance']
                }
            else:
                return {
                    'success': False,
                    'confidence': 0.2,
                    'nearby_troops': 0
                }

        except Exception as e:
            self.logger.error(f"Troop appearance validation failed: {e}")
            return {'success': False, 'confidence': 0.0}

    async def validate_click_action(self, click_position: Tuple[int, int],
                                    before_state: Any, after_state: Any) -> ActionFeedback:
        """Validate click action success."""
        try:
            action_id = f"click_{int(time.time() * 1000)}"

            # Simple validation - check for any state change
            state_changed = await self._detect_state_change(before_state, after_state)

            feedback = ActionFeedback(
                action_id=action_id,
                success=state_changed,
                confidence=0.6 if state_changed else 0.3,
                feedback_type=FeedbackType.STATE_CHANGE,
                details={
                    'click_position': click_position,
                    'state_changed': state_changed
                }
            )

            self.feedback_history.append(feedback)
            return feedback

        except Exception as e:
            self.logger.error(f"Click validation failed: {e}")
            return ActionFeedback(
                action_id="error",
                success=False,
                confidence=0.0,
                feedback_type=FeedbackType.STATE_CHANGE,
                details={'error': str(e)}
            )

    async def _detect_state_change(self, before_state: Any, after_state: Any) -> bool:
        """Detect if game state changed between before and after."""
        try:
            # Compare key state attributes
            comparisons = []

            # Check elixir change
            before_elixir = getattr(before_state, 'current_elixir', 0)
            after_elixir = getattr(after_state, 'current_elixir', 0)
            comparisons.append(before_elixir != after_elixir)

            # Check troops count change
            before_troops = len(getattr(before_state, 'friendly_troops', []))
            after_troops = len(getattr(after_state, 'friendly_troops', []))
            comparisons.append(before_troops != after_troops)

            # Check enemy troops change
            before_enemy = len(getattr(before_state, 'enemy_troops', []))
            after_enemy = len(getattr(after_state, 'enemy_troops', []))
            comparisons.append(before_enemy != after_enemy)

            # Return true if any significant change detected
            return any(comparisons)

        except Exception as e:
            self.logger.error(f"State change detection failed: {e}")
            return False

    async def validate_timing_based(self, expected_duration: float,
                                    actual_duration: float) -> ActionFeedback:
        """Validate action based on timing expectations."""
        try:
            action_id = f"timing_{int(time.time() * 1000)}"

            # Check if timing is within acceptable range
            tolerance = 0.5  # 500ms tolerance
            timing_ok = abs(actual_duration - expected_duration) <= tolerance

            confidence = 1.0 - \
                min(1.0, abs(actual_duration - expected_duration) / expected_duration)

            feedback = ActionFeedback(
                action_id=action_id,
                success=timing_ok,
                confidence=confidence,
                feedback_type=FeedbackType.TIMING_BASED,
                details={
                    'expected_duration': expected_duration,
                    'actual_duration': actual_duration,
                    'tolerance': tolerance
                }
            )

            self.feedback_history.append(feedback)
            return feedback

        except Exception as e:
            self.logger.error(f"Timing validation failed: {e}")
            return ActionFeedback(
                action_id="error",
                success=False,
                confidence=0.0,
                feedback_type=FeedbackType.TIMING_BASED,
                details={'error': str(e)}
            )

    def get_success_rate(self, timeframe_minutes: int = 5) -> float:
        """Get success rate for recent actions."""
        try:
            if not self.feedback_history:
                return 0.0

            cutoff_time = time.time() - (timeframe_minutes * 60)
            recent_feedback = [
                f for f in self.feedback_history if f.timestamp > cutoff_time]

            if not recent_feedback:
                return 0.0

            successful = sum(1 for f in recent_feedback if f.success)
            return successful / len(recent_feedback)

        except Exception as e:
            self.logger.error(f"Success rate calculation failed: {e}")
            return 0.0

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get comprehensive feedback statistics."""
        try:
            if not self.feedback_history:
                return {
                    'total_actions': 0,
                    'success_rate': 0.0,
                    'average_confidence': 0.0,
                    'feedback_types': {}
                }

            # Overall stats
            total_actions = len(self.feedback_history)
            successful = sum(1 for f in self.feedback_history if f.success)
            success_rate = successful / total_actions

            # Average confidence
            confidences = [f.confidence for f in self.feedback_history]
            avg_confidence = sum(confidences) / \
                len(confidences) if confidences else 0.0

            # Feedback type breakdown
            type_stats = {}
            for feedback_type in FeedbackType:
                type_feedback = [
                    f for f in self.feedback_history if f.feedback_type == feedback_type]
                if type_feedback:
                    type_success = sum(1 for f in type_feedback if f.success)
                    type_stats[feedback_type.value] = {
                        'count': len(type_feedback),
                        'success_rate': type_success / len(type_feedback),
                        'avg_confidence': sum(f.confidence for f in type_feedback) / len(type_feedback)
                    }

            return {
                'total_actions': total_actions,
                'success_rate': success_rate,
                'average_confidence': avg_confidence,
                'feedback_types': type_stats,
                # Last 10 actions
                'recent_feedback': self.feedback_history[-10:]
            }

        except Exception as e:
            self.logger.error(f"Feedback stats calculation failed: {e}")
            return {}

    async def adaptive_feedback_adjustment(self):
        """Adjust validation parameters based on historical performance."""
        try:
            recent_feedback = self.feedback_history[-50:]  # Last 50 actions

            if len(recent_feedback) < 10:
                return  # Not enough data

            # Analyze confidence vs actual success correlation
            high_conf_actions = [
                f for f in recent_feedback if f.confidence > 0.8]
            low_conf_actions = [
                f for f in recent_feedback if f.confidence < 0.5]

            if high_conf_actions:
                high_conf_success = sum(
                    1 for f in high_conf_actions if f.success) / len(high_conf_actions)

                # Adjust confidence threshold if high confidence actions are failing
                if high_conf_success < 0.7:
                    self.confidence_threshold = min(
                        0.9, self.confidence_threshold + 0.05)
                    self.logger.info(
                        f"Increased confidence threshold to {self.confidence_threshold}")

            if low_conf_actions:
                low_conf_success = sum(
                    1 for f in low_conf_actions if f.success) / len(low_conf_actions)

                # Decrease threshold if low confidence actions are actually succeeding
                if low_conf_success > 0.6:
                    self.confidence_threshold = max(
                        0.5, self.confidence_threshold - 0.05)
                    self.logger.info(
                        f"Decreased confidence threshold to {self.confidence_threshold}")

        except Exception as e:
            self.logger.error(f"Adaptive adjustment failed: {e}")

    def cleanup(self):
        """Cleanup feedback system resources."""
        try:
            # Save feedback history if needed
            self.logger.info(
                f"Feedback system cleaned up. Total feedback records: {len(self.feedback_history)}")

        except Exception as e:
            self.logger.error(f"Feedback cleanup failed: {e}")


class PerformanceTracker:
    """Tracks overall action performance metrics."""

    def __init__(self):
        self.metrics = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'average_execution_time': 0.0,
            'actions_per_minute': 0.0
        }

        self.execution_times = []
        self.last_reset_time = time.time()

    def record_action(self, success: bool, execution_time: float):
        """Record an action result and timing."""
        self.metrics['total_actions'] += 1

        if success:
            self.metrics['successful_actions'] += 1
        else:
            self.metrics['failed_actions'] += 1

        self.execution_times.append(execution_time)

        # Keep only recent execution times
        if len(self.execution_times) > 100:
            self.execution_times = self.execution_times[-50:]

        # Update averages
        if self.execution_times:
            self.metrics['average_execution_time'] = sum(
                self.execution_times) / len(self.execution_times)

        # Calculate actions per minute
        time_elapsed = time.time() - self.last_reset_time
        if time_elapsed > 0:
            self.metrics['actions_per_minute'] = (
                self.metrics['total_actions'] / time_elapsed) * 60

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        success_rate = 0.0
        if self.metrics['total_actions'] > 0:
            success_rate = self.metrics['successful_actions'] / \
                self.metrics['total_actions']

        return {
            **self.metrics,
            'success_rate': success_rate,
            'failure_rate': 1.0 - success_rate
        }

    def reset_metrics(self):
        """Reset all performance metrics."""
        self.metrics = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'average_execution_time': 0.0,
            'actions_per_minute': 0.0
        }
        self.execution_times = []
        self.last_reset_time = time.time()
