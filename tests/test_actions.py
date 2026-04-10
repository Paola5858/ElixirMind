"""
Actions Controller tests — written against the actual current API.

Previous version tested a legacy async ActionController that no longer exists.
"""

from unittest.mock import MagicMock, patch

import pytest

from actions.controller import Controller
from core.types import Action, ActionResult, ActionType


@pytest.fixture
def controller():
    return Controller({})


@pytest.fixture
def controller_custom_positions():
    positions = [(100, 900), (200, 900), (300, 900), (400, 900)]
    return Controller({"card_positions": positions})


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_controller_initializes_without_error(controller):
    controller.initialize()  # must not raise


def test_controller_uses_default_card_positions(controller):
    assert len(controller.card_positions) == 4


def test_controller_uses_config_card_positions(controller_custom_positions):
    assert controller_custom_positions.card_positions[0] == (100, 900)


# ---------------------------------------------------------------------------
# execute_actions return type
# ---------------------------------------------------------------------------

def test_execute_actions_returns_list(controller):
    with patch("pyautogui.moveTo"), patch("pyautogui.dragTo"):
        results = controller.execute_actions([
            Action(type=ActionType.PLAY_CARD, card_index=0, position=(500, 500))
        ])
    assert isinstance(results, list)
    assert len(results) == 1


def test_execute_actions_returns_action_result_instances(controller):
    with patch("pyautogui.moveTo"), patch("pyautogui.dragTo"):
        results = controller.execute_actions([
            Action(type=ActionType.PLAY_CARD, card_index=0, position=(500, 500))
        ])
    assert isinstance(results[0], ActionResult)


def test_execute_actions_empty_list_returns_empty(controller):
    results = controller.execute_actions([])
    assert results == []


# ---------------------------------------------------------------------------
# play_card / use_spell
# ---------------------------------------------------------------------------

def test_play_card_success(controller):
    with patch("pyautogui.moveTo") as mock_move, \
         patch("pyautogui.dragTo") as mock_drag:
        results = controller.execute_actions([
            Action(type=ActionType.PLAY_CARD, card_index=1, position=(960, 400))
        ])
    assert results[0].success is True
    mock_move.assert_called_once()
    mock_drag.assert_called_once()


def test_use_spell_success(controller):
    with patch("pyautogui.moveTo"), patch("pyautogui.dragTo"):
        results = controller.execute_actions([
            Action(type=ActionType.USE_SPELL, card_index=2, position=(800, 300))
        ])
    assert results[0].success is True


def test_play_card_invalid_index_returns_failure(controller):
    results = controller.execute_actions([
        Action(type=ActionType.PLAY_CARD, card_index=99, position=(500, 500))
    ])
    assert results[0].success is False
    assert results[0].error is not None


def test_play_card_missing_position_returns_failure(controller):
    results = controller.execute_actions([
        Action(type=ActionType.PLAY_CARD, card_index=0, position=None)
    ])
    assert results[0].success is False


# ---------------------------------------------------------------------------
# upgrade_card
# ---------------------------------------------------------------------------

def test_upgrade_card_success(controller):
    with patch("pyautogui.moveTo"), patch("pyautogui.doubleClick"):
        results = controller.execute_actions([
            Action(type=ActionType.UPGRADE_CARD, card_index=0)
        ])
    assert results[0].success is True


def test_upgrade_card_invalid_index_returns_failure(controller):
    results = controller.execute_actions([
        Action(type=ActionType.UPGRADE_CARD, card_index=10)
    ])
    assert results[0].success is False


# ---------------------------------------------------------------------------
# wait
# ---------------------------------------------------------------------------

def test_wait_action_success(controller):
    with patch("time.sleep") as mock_sleep:
        results = controller.execute_actions([
            Action(type=ActionType.WAIT, duration=0.5)
        ])
    assert results[0].success is True
    mock_sleep.assert_called_once_with(0.5)


def test_wait_zero_duration_does_not_raise(controller):
    with patch("time.sleep"):
        results = controller.execute_actions([
            Action(type=ActionType.WAIT, duration=0.0)
        ])
    assert results[0].success is True


# ---------------------------------------------------------------------------
# Multiple actions
# ---------------------------------------------------------------------------

def test_multiple_actions_all_tracked(controller):
    actions = [
        Action(type=ActionType.PLAY_CARD, card_index=0, position=(500, 500)),
        Action(type=ActionType.WAIT, duration=0.0),
        Action(type=ActionType.PLAY_CARD, card_index=1, position=(700, 400)),
    ]
    with patch("pyautogui.moveTo"), patch("pyautogui.dragTo"), patch("time.sleep"):
        results = controller.execute_actions(actions)
    assert len(results) == 3


def test_one_failure_does_not_abort_remaining_actions(controller):
    """A bad action must not prevent subsequent actions from executing."""
    actions = [
        Action(type=ActionType.PLAY_CARD, card_index=99, position=(500, 500)),  # bad
        Action(type=ActionType.WAIT, duration=0.0),                              # good
    ]
    with patch("time.sleep"):
        results = controller.execute_actions(actions)
    assert results[0].success is False
    assert results[1].success is True
