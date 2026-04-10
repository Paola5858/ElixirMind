"""
Actions Controller: Executes bot actions and returns typed results.

Improvements vs previous version:
- execute_actions() returns List[ActionResult] instead of None.
- Card positions read from config with fallback to 1920×1080 defaults.
- play_card and use_spell share one implementation (_drag_card).
- Each action result carries success/error for StatsTracker.
"""

from __future__ import annotations

import logging
import time
from typing import List

import pyautogui

from core.types import Action, ActionResult, ActionType

logger = logging.getLogger(__name__)

_DEFAULT_CARD_POSITIONS = [
    (780,  920),
    (960,  920),
    (1140, 920),
    (1320, 920),
]


class Controller:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.card_positions: List[tuple] = config.get(
            "card_positions", _DEFAULT_CARD_POSITIONS
        )

    def initialize(self) -> None:
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
        logger.info("Controller initialized.")

    def shutdown(self) -> None:
        logger.info("Controller shut down.")

    def execute_actions(self, actions: List[Action]) -> List[ActionResult]:
        """Execute actions and return one ActionResult per action."""
        results: List[ActionResult] = []
        for action in actions:
            result = self._execute_one(action)
            results.append(result)
            if not result.success:
                logger.warning("Action failed: %s — %s", action, result.error)
        return results

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _execute_one(self, action: Action) -> ActionResult:
        try:
            if action.type in (ActionType.PLAY_CARD, ActionType.USE_SPELL):
                self._drag_card(action)
            elif action.type == ActionType.UPGRADE_CARD:
                self._upgrade_card(action)
            elif action.type == ActionType.WAIT:
                self._wait(action)
            else:
                return ActionResult(action=action, success=False,
                                    error=f"Unknown action type: {action.type}")
            return ActionResult(action=action, success=True)
        except Exception as exc:
            return ActionResult(action=action, success=False, error=str(exc))

    def _drag_card(self, action: Action) -> None:
        idx = action.card_index
        if not (0 <= idx < len(self.card_positions)):
            raise ValueError(f"card_index {idx} out of range")
        if action.position is None:
            raise ValueError("position is required for play_card/use_spell")

        src = self.card_positions[idx]
        dst = action.position
        pyautogui.moveTo(src[0], src[1])
        pyautogui.dragTo(dst[0], dst[1], duration=0.25, tween=pyautogui.easeOutQuad)
        logger.info("Dragged card %d -> %s", idx, dst)

    def _upgrade_card(self, action: Action) -> None:
        idx = action.card_index
        if not (0 <= idx < len(self.card_positions)):
            raise ValueError(f"card_index {idx} out of range")
        pos = self.card_positions[idx]
        pyautogui.moveTo(pos[0], pos[1])
        pyautogui.doubleClick()
        logger.info("Upgraded card %d", idx)

    def _wait(self, action: Action) -> None:
        duration = max(0.0, action.duration)
        time.sleep(duration)
        logger.debug("Waited %.2fs", duration)
