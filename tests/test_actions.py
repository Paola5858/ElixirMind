"""
ElixirMind Actions Tests  
Unit tests for action controller and feedback systems.
"""

from config import Config
from actions.feedback import ActionValidator, ActionFeedback, FeedbackType
from actions.controller import ActionController, GameAction, ActionType
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


class TestActionController:
    """Tests for ActionController class."""

    @pytest.fixture
    def config(self):
        config = Config()
        config.SAFE_MODE = True
        config.CLICK_DELAY = 0.01  # Fast for testing
        return config

    @pytest.fixture
    def controller(self, config):
        return ActionController(config)

    def test_controller_initialization(self, controller):
        """Test controller initializes correctly."""
        assert controller is not None
        assert controller.config is not None
        assert controller.safety_enabled is True

    @pytest.mark.asyncio
    async def test_execute_place_card_action(self, controller):
        """Test place card action execution."""
        action = GameAction(
            action_type=ActionType.PLACE_CARD,
            parameters={
                'card_position': (240, 940),
                'target_position': (960, 500)
            }
        )

        # Mock PyAutoGUI to avoid actual mouse movements
        with patch('pyautogui.moveTo'), \
                patch('pyautogui.dragTo'):
            result = await controller.execute_action(action)

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_execute_click_action(self, controller):
        """Test click action execution."""
        action = GameAction(
            action_type=ActionType.CLICK,
            parameters={'position': (960, 500)}
        )

        with patch('pyautogui.click'):
            result = await controller.execute_action(action)

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_execute_wait_action(self, controller):
        """Test wait action execution."""
        action = GameAction(
            action_type=ActionType.WAIT,
            parameters={'duration': 0.1}
        )

        result = await controller.execute_action(action)
        assert result is True

    def test_safety_checks(self, controller):
        """Test safety check functionality."""
        # Test safe position
        safe_pos = (960, 500)
        assert controller._is_position_safe(safe_pos) is True

        # Test unsafe positions
        unsafe_positions = [
            (-10, 500),    # Negative X
            (2000, 500),   # Too large X
            (500, -10),    # Negative Y
            (500, 2000)    # Too large Y
        ]

        for pos in unsafe_positions:
            assert controller._is_position_safe(pos) is False

    def test_performance_stats(self, controller):
        """Test performance statistics tracking."""
        stats = controller.get_performance_stats()

        assert 'total_actions' in stats
        assert 'success_rate' in stats
        assert 'actions_per_minute' in stats

    def test_create_place_card_action(self, controller):
        """Test helper method for creating place card actions."""
        action = controller.create_place_card_action(0, 960, 500)

        assert action is not None
        assert action.action_type == ActionType.PLACE_CARD
        assert 'card_position' in action.parameters
        assert 'target_position' in action.parameters


class TestActionValidator:
    """Tests for ActionValidator class."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def validator(self, config):
        return ActionValidator(config)

    @pytest.mark.asyncio
    async def test_validate_card_placement(self, validator):
        """Test card placement validation."""
        # Mock game states
        before_state = Mock()
        before_state.current_elixir = 8
        before_state.friendly_troops = []

        after_state = Mock()
        after_state.current_elixir = 4  # Elixir decreased
        after_state.friendly_troops = [
            {'center': [960, 500]}]  # New troop appeared

        action_params = {
            'target_position': (960, 500),
            'card_position': (240, 940)
        }

        feedback = await validator.validate_card_placement(
            action_params, before_state, after_state
        )

        assert isinstance(feedback, ActionFeedback)
        assert feedback.feedback_type == FeedbackType.COMBINATION

    @pytest.mark.asyncio
    async def test_validate_click_action(self, validator):
        """Test click action validation."""
        before_state = Mock()
        after_state = Mock()

        # Mock different states to indicate change
        before_state.current_elixir = 5
        after_state.current_elixir = 5
        before_state.friendly_troops = []
        after_state.friendly_troops = []

        feedback = await validator.validate_click_action(
            (960, 500), before_state, after_state
        )

        assert isinstance(feedback, ActionFeedback)
        assert feedback.feedback_type == FeedbackType.STATE_CHANGE

    def test_success_rate_calculation(self, validator):
        """Test success rate calculation."""
        # Add some mock feedback
        validator.feedback_history = [
            ActionFeedback(
                "1", True, 0.8, FeedbackType.VISUAL_CONFIRMATION, {}),
            ActionFeedback("2", False, 0.3,
                           FeedbackType.VISUAL_CONFIRMATION, {}),
            ActionFeedback(
                "3", True, 0.9, FeedbackType.VISUAL_CONFIRMATION, {})
        ]

        success_rate = validator.get_success_rate(60)  # Last hour
        assert 0.0 <= success_rate <= 1.0

    def test_feedback_stats(self, validator):
        """Test comprehensive feedback statistics."""
        # Add mock feedback
        validator.feedback_history = [
            ActionFeedback(
                "1", True, 0.8, FeedbackType.VISUAL_CONFIRMATION, {}),
            ActionFeedback("2", True, 0.7, FeedbackType.TIMING_BASED, {})
        ]

        stats = validator.get_feedback_stats()

        assert 'total_actions' in stats
        assert 'success_rate' in stats
        assert 'average_confidence' in stats
        assert 'feedback_types' in stats


class TestActionIntegration:
    """Integration tests for action system."""

    @pytest.fixture
    def config(self):
        config = Config()
        config.SAFE_MODE = True
        return config

    @pytest.mark.asyncio
    async def test_action_execution_with_validation(self, config):
        """Test complete action execution with validation."""
        controller = ActionController(config)
        validator = ActionValidator(config)

        # Create test action
        action = GameAction(
            action_type=ActionType.PLACE_CARD,
            parameters={
                'card_position': (240, 940),
                'target_position': (960, 500)
            }
        )

        # Mock execution
        with patch('pyautogui.moveTo'), \
                patch('pyautogui.dragTo'):
            success = await controller.execute_action(action)

        # Mock validation
        before_state = Mock()
        after_state = Mock()

        feedback = await validator.validate_card_placement(
            action.parameters, before_state, after_state
        )

        assert isinstance(success, bool)
        assert isinstance(feedback, ActionFeedback)

    @pytest.mark.asyncio
    async def test_combo_execution(self, config):
        """Test combo action execution."""
        controller = ActionController(config)

        # Create combo actions
        actions = [
            GameAction(ActionType.PLACE_CARD, {
                'card_position': (240, 940), 'target_position': (700, 500)
            }),
            GameAction(ActionType.WAIT, {'duration': 0.1}),
            GameAction(ActionType.PLACE_CARD, {
                'card_position': (480, 940), 'target_position': (1220, 500)
            })
        ]

        with patch('pyautogui.moveTo'), \
                patch('pyautogui.dragTo'):
            results = await controller.execute_combo(actions)

        assert len(results) == len(actions)
        assert all(isinstance(result, bool) for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
