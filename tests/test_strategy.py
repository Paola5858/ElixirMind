"""
Strategy tests — written against the actual current API.

Previous version tested a legacy async interface that no longer exists.
All tests here use the real synchronous Strategy class and core.types.
"""

import numpy as np
import pytest

from core.types import Action, ActionType, GameState
from strategy.base import Strategy


@pytest.fixture
def strategy():
    return Strategy({})


@pytest.fixture
def blank_screen():
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Initialization / shutdown
# ---------------------------------------------------------------------------

def test_strategy_initializes_without_error(strategy):
    strategy.initialize()  # must not raise


def test_strategy_shuts_down_without_error(strategy):
    strategy.initialize()
    strategy.shutdown()  # must not raise


# ---------------------------------------------------------------------------
# decide_actions return type
# ---------------------------------------------------------------------------

def test_decide_actions_returns_list(strategy, blank_screen):
    result = strategy.decide_actions(blank_screen)
    assert isinstance(result, list)


def test_decide_actions_returns_action_instances(strategy, blank_screen):
    # Force elixir high enough to guarantee at least one action
    strategy.game_state.elixir = 10.0
    strategy._last_elixir = 10.0
    result = strategy.decide_actions(blank_screen)
    for item in result:
        assert isinstance(item, Action), f"Expected Action, got {type(item)}"


def test_decide_actions_action_has_valid_type(strategy, blank_screen):
    strategy.game_state.elixir = 10.0
    strategy._last_elixir = 10.0
    result = strategy.decide_actions(blank_screen)
    for action in result:
        assert action.type in ActionType


def test_decide_actions_play_card_has_position(strategy, blank_screen):
    strategy.game_state.elixir = 10.0
    strategy._last_elixir = 10.0
    result = strategy.decide_actions(blank_screen)
    for action in result:
        if action.type == ActionType.PLAY_CARD:
            assert action.position is not None
            assert len(action.position) == 2


# ---------------------------------------------------------------------------
# Elixir gating
# ---------------------------------------------------------------------------

def test_no_actions_when_elixir_is_zero(strategy, blank_screen):
    strategy.game_state.elixir = 0.0
    strategy._last_elixir = 0.0
    # Override _update_game_state to keep elixir at 0
    strategy._update_game_state = lambda *_: None
    result = strategy.decide_actions(blank_screen)
    assert result == []


# ---------------------------------------------------------------------------
# Phase routing
# ---------------------------------------------------------------------------

def test_early_game_phase_is_selected_at_high_time(strategy, blank_screen):
    strategy.game_state.time_remaining = 180
    strategy.game_state.elixir = 10.0
    strategy._last_elixir = 10.0
    strategy._update_game_state = lambda *_: None
    # Should not raise; phase routing must handle time=180
    strategy.decide_actions(blank_screen)


def test_late_game_phase_is_selected_at_low_time(strategy, blank_screen):
    strategy.game_state.time_remaining = 10
    strategy.game_state.elixir = 10.0
    strategy._last_elixir = 10.0
    strategy._update_game_state = lambda *_: None
    result = strategy.decide_actions(blank_screen)
    # Late game with elixir >= 3 must produce at least one action
    assert len(result) >= 1


# ---------------------------------------------------------------------------
# Action history
# ---------------------------------------------------------------------------

def test_action_history_is_bounded(strategy, blank_screen):
    strategy.game_state.elixir = 10.0
    strategy._last_elixir = 10.0
    for _ in range(20):
        strategy.decide_actions(blank_screen)
    assert len(strategy._action_history) <= 10


# ---------------------------------------------------------------------------
# GameState integration
# ---------------------------------------------------------------------------

def test_game_state_is_gamestate_instance(strategy):
    assert isinstance(strategy.game_state, GameState)


def test_time_remaining_decrements(strategy, blank_screen):
    strategy.game_state.time_remaining = 100
    strategy.decide_actions(blank_screen)
    assert strategy.game_state.time_remaining < 100
