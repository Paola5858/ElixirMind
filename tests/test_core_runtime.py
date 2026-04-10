"""Runtime tests for the ElixirMind core."""

from unittest.mock import MagicMock, patch

import pytest

from config import build_config
from core.bot_manager import BotManager
from core.orchestrator import Orchestrator
from core.types import Action, ActionResult, ActionType


# ---------------------------------------------------------------------------
# config.py
# ---------------------------------------------------------------------------

def test_build_config_applies_defaults_when_file_is_missing():
    config = build_config("tests/fixtures/does-not-exist.json")
    assert config.emulator_type == "memu"
    assert config.instance_id == 0
    assert config.poll_interval_seconds > 0
    assert config.log_level == "INFO"


def test_build_config_rejects_invalid_emulator_type(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text('{"emulator_type": "invalid"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported emulator_type"):
        build_config(str(cfg))


# ---------------------------------------------------------------------------
# BotManager
# ---------------------------------------------------------------------------

def test_bot_manager_rejects_zero_poll_interval():
    """BotManager must raise ValueError when poll_interval_seconds <= 0."""
    with pytest.raises(ValueError, match="poll_interval_seconds"):
        BotManager({"poll_interval_seconds": 0})


def test_bot_manager_rejects_negative_poll_interval():
    with pytest.raises(ValueError, match="poll_interval_seconds"):
        BotManager({"poll_interval_seconds": -1})


def test_bot_manager_stop_is_idempotent():
    manager = BotManager({"poll_interval_seconds": 0.01})
    manager.orchestrator = MagicMock()
    manager._running = True

    manager.stop()
    manager.stop()

    manager.orchestrator.shutdown.assert_called_once()


def test_bot_manager_shutdown_state_exits_loop():
    """When state machine returns 'shutdown', run() must exit cleanly."""
    manager = BotManager({"poll_interval_seconds": 0.01})
    manager.orchestrator = MagicMock()
    manager.state_machine = MagicMock()
    manager._running = True
    manager.state_machine.get_state.side_effect = ["shutdown"]

    manager.run()

    manager.orchestrator.shutdown.assert_called_once()


# ---------------------------------------------------------------------------
# Orchestrator — check_for_battle
# ---------------------------------------------------------------------------

def test_check_for_battle_transitions_to_battle_on_detection():
    """detect_battle returns (True, None) — state must become 'battle'."""
    orch = Orchestrator({})
    orch.detector      = MagicMock()
    orch.state_machine = MagicMock()

    orch.detector.capture_screen.return_value = MagicMock()
    # Correct return type: tuple (bool, image|None)
    orch.detector.detect_battle.return_value = (True, None)

    orch.check_for_battle()

    orch.state_machine.set_state.assert_called_once_with("battle")


def test_check_for_battle_does_not_transition_when_no_battle():
    orch = Orchestrator({})
    orch.detector      = MagicMock()
    orch.state_machine = MagicMock()

    orch.detector.capture_screen.return_value = MagicMock()
    orch.detector.detect_battle.return_value = (False, None)

    orch.check_for_battle()

    orch.state_machine.set_state.assert_not_called()


def test_check_for_battle_skips_when_screen_is_none():
    orch = Orchestrator({})
    orch.detector      = MagicMock()
    orch.state_machine = MagicMock()

    orch.detector.capture_screen.return_value = None

    orch.check_for_battle()

    orch.detector.detect_battle.assert_not_called()
    orch.state_machine.set_state.assert_not_called()


# ---------------------------------------------------------------------------
# Orchestrator — handle_battle
# ---------------------------------------------------------------------------

def test_handle_battle_executes_actions_and_tracks_results():
    orch = Orchestrator({})
    orch.detector      = MagicMock()
    orch.controller    = MagicMock()
    orch.strategy      = MagicMock()
    orch.stats_tracker = MagicMock()
    orch.state_machine = MagicMock()

    screen = MagicMock()
    orch.detector.capture_screen.return_value = screen
    orch.detector.detect_battle_end.return_value = False

    action = Action(type=ActionType.PLAY_CARD, card_index=0, position=(100, 200))
    result = ActionResult(action=action, success=True)
    orch.strategy.decide_actions.return_value = [action]
    orch.controller.execute_actions.return_value = [result]

    orch.handle_battle()

    orch.strategy.decide_actions.assert_called_once_with(screen, detector=orch.detector)
    orch.controller.execute_actions.assert_called_once_with([action])
    orch.stats_tracker.update_stats.assert_called_once_with([result])
    orch.state_machine.set_state.assert_not_called()


def test_handle_battle_transitions_to_idle_on_battle_end():
    orch = Orchestrator({})
    orch.detector      = MagicMock()
    orch.controller    = MagicMock()
    orch.strategy      = MagicMock()
    orch.stats_tracker = MagicMock()
    orch.state_machine = MagicMock()

    orch.detector.capture_screen.return_value = MagicMock()
    orch.detector.detect_battle_end.return_value = True
    orch.strategy.decide_actions.return_value = []
    orch.controller.execute_actions.return_value = []

    orch.handle_battle()

    orch.state_machine.set_state.assert_called_once_with("idle")
