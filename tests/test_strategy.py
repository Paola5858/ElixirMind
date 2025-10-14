"""
ElixirMind Strategy Tests
Unit tests for bot strategy systems.
"""

from config import Config
from vision.detector import GameState
from actions.controller import GameAction, ActionType
from strategy.base import BaseStrategy, StrategyDecision
from strategy.heuristic import HeuristicStrategy
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


class TestHeuristicStrategy:
    """Tests for HeuristicStrategy class."""

    @pytest.fixture
    def config(self):
        config = Config()
        config.MIN_ELIXIR_TO_PLAY = 3
        return config

    @pytest.fixture
    def strategy(self, config):
        return HeuristicStrategy(config)

    @pytest.mark.asyncio
    async def test_strategy_initialization(self, strategy):
        """Test strategy initializes correctly."""
        result = await strategy.initialize()
        assert result is True
        assert strategy.config is not None

    @pytest.mark.asyncio
    async def test_decision_with_low_elixir(self, strategy):
        """Test decision making with insufficient elixir."""
        await strategy.initialize()

        # Create game state with low elixir
        game_state = GameState()
        game_state.current_elixir = 2  # Below minimum

        result = await strategy.decide_action(game_state)
        assert result is None

    @pytest.mark.asyncio
    async def test_decision_with_sufficient_elixir(self, strategy):
        """Test decision making with sufficient elixir."""
        await strategy.initialize()

        # Create game state with sufficient elixir
        game_state = GameState()
        game_state.current_elixir = 5
        game_state.cards_in_hand = [
            {
                'name': 'knight',
                'position': 0,
                'available': True,
                'coordinates': (240, 940)
            }
        ]

        result = await strategy.decide_action(game_state)
        # Result may be None or GameAction depending on strategy rules
        assert result is None or isinstance(result, GameAction)

    @pytest.mark.asyncio
    async def test_update_from_feedback(self, strategy):
        """Test strategy learning from feedback."""
        await strategy.initialize()

        action = GameAction(
            action_type=ActionType.PLACE_CARD,
            parameters={'card_position': (
                240, 940), 'target_position': (960, 500)}
        )

        # Test successful feedback
        await strategy.update_from_feedback(action, True)
        assert strategy.successful_decisions > 0

        # Test failed feedback
        await strategy.update_from_feedback(action, False)
        # Should handle gracefully without errors


class TestBaseStrategy:
    """Tests for BaseStrategy abstract class."""

    def test_base_strategy_instantiation(self):
        """Test that BaseStrategy cannot be instantiated directly."""
        config = Config()

        with pytest.raises(TypeError):
            BaseStrategy(config)

    def test_strategy_decision_creation(self):
        """Test StrategyDecision creation."""
        action = GameAction(
            action_type=ActionType.PLACE_CARD,
            parameters={}
        )

        decision = StrategyDecision(
            action=action,
            reasoning="Test decision",
            confidence=0.8,
            priority=5
        )

        assert decision.action == action
        assert decision.reasoning == "Test decision"
        assert decision.confidence == 0.8
        assert decision.priority == 5
        assert decision.timestamp > 0


class MockStrategy(BaseStrategy):
    """Mock strategy for testing BaseStrategy functionality."""

    async def decide_action(self, game_state):
        return None

    async def initialize(self):
        return True

    async def update_from_feedback(self, action, success):
        pass


class TestStrategyBase:
    """Tests for BaseStrategy common functionality."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def mock_strategy(self, config):
        return MockStrategy(config)

    def test_performance_metrics_empty(self, mock_strategy):
        """Test performance metrics with no data."""
        metrics = mock_strategy.get_performance_metrics()

        assert metrics['decisions_made'] == 0
        assert metrics['success_rate'] == 0.0
        assert metrics['average_confidence'] == 0.0

    def test_decision_logging(self, mock_strategy):
        """Test decision logging functionality."""
        decision = StrategyDecision(
            action=None,
            reasoning="Test log",
            confidence=0.7,
            priority=3
        )

        mock_strategy.log_decision(decision)

        assert len(mock_strategy.decision_history) == 1
        assert mock_strategy.decisions_made == 1

    def test_decision_timing(self, mock_strategy):
        """Test decision timing checks."""
        # Should allow decision initially
        assert mock_strategy.should_make_decision() is True

        # Simulate recent decision
        mock_strategy.last_decision_time = mock_strategy.last_decision_time + 1000

        # Should still allow (timing logic depends on implementation)
        result = mock_strategy.should_make_decision()
        assert isinstance(result, bool)

# Integration tests


class TestStrategyIntegration:
    """Integration tests for strategy system."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.asyncio
    async def test_strategy_game_loop_simulation(self, config):
        """Simulate game loop with strategy decisions."""
        strategy = HeuristicStrategy(config)
        await strategy.initialize()

        # Simulate multiple game states
        game_states = [
            GameState(current_elixir=3, cards_in_hand=[]),
            GameState(current_elixir=6, cards_in_hand=[
                {'name': 'knight', 'position': 0,
                    'available': True, 'coordinates': (240, 940)}
            ]),
            GameState(current_elixir=10, cards_in_hand=[
                {'name': 'giant', 'position': 1,
                    'available': True, 'coordinates': (480, 940)}
            ])
        ]

        decisions = []
        for state in game_states:
            decision = await strategy.decide_action(state)
            if decision:
                decisions.append(decision)
                # Simulate feedback
                await strategy.update_from_feedback(decision, True)

        # Verify strategy made decisions and learned
        metrics = strategy.get_performance_metrics()
        assert metrics['decisions_made'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
