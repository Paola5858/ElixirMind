"""
Base Strategy: Decision engine for the bot.

Improvements vs previous version:
- decide_actions() returns List[Action] (typed), not List[Dict].
- GameState is imported from core.types — single source of truth.
- Strategy is a concrete default implementation; subclasses override
  decide_actions() for custom behaviour (heuristic, RL, etc.).
- Elixir simulation is clearly marked as a placeholder.
"""

from __future__ import annotations

import logging
import random
from typing import Any, List, Optional

import numpy as np

from core.types import Action, ActionType, GameState

logger = logging.getLogger(__name__)


class Strategy:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config: dict[str, Any] = config
        self.game_state = GameState()
        self._last_elixir: float = 0.0
        self._action_history: List[Action] = []

    def initialize(self) -> None:
        logger.info("Strategy initialized.")

    def shutdown(self) -> None:
        logger.info("Strategy shut down.")

    def decide_actions(
        self, screen: np.ndarray, detector: Any = None
    ) -> List[Action]:
        """Return a list of Actions for the current frame."""
        self._update_game_state(screen, detector)

        actions: List[Action] = []
        actions.extend(self._phase_actions())
        actions.extend(self._tactical_actions())

        # Keep a short history for future context-aware decisions
        self._action_history = (self._action_history + actions)[-10:]
        return actions

    # ------------------------------------------------------------------
    # Game-state update
    # ------------------------------------------------------------------

    def _update_game_state(self, screen: np.ndarray, detector: Any) -> None:
        """Update internal GameState from screen. Elixir is simulated until
        real OCR is wired in."""
        try:
            # Placeholder: increment elixir by 0.5 per tick, cap at 10
            self.game_state.elixir = min(10.0, self._last_elixir + 0.5)
            self._last_elixir = self.game_state.elixir
            self.game_state.time_remaining = max(
                0, self.game_state.time_remaining - 1
            )
        except Exception:
            logger.exception("Error updating game state.")

    # ------------------------------------------------------------------
    # Phase-based strategy
    # ------------------------------------------------------------------

    def _phase_actions(self) -> List[Action]:
        t = self.game_state.time_remaining
        if t > 150:
            return self._early_game()
        if t > 60:
            return self._mid_game()
        return self._late_game()

    def _early_game(self) -> List[Action]:
        if self.game_state.elixir >= 4 and self._should_defend():
            return [self._defensive_action()]
        return []

    def _mid_game(self) -> List[Action]:
        if self.game_state.elixir >= 5 and self._should_attack():
            return [self._offensive_action()]
        return []

    def _late_game(self) -> List[Action]:
        if self.game_state.elixir >= 3:
            return [self._aggressive_action()]
        return []

    # ------------------------------------------------------------------
    # Tactical layer
    # ------------------------------------------------------------------

    def _tactical_actions(self) -> List[Action]:
        if self.game_state.elixir < 4:
            return []
        card_index = self._choose_card()
        position   = self._choose_position()
        if card_index is None or position is None:
            return []
        self.game_state.elixir -= 4  # simplified cost
        return [Action(type=ActionType.PLAY_CARD, card_index=card_index, position=position)]

    # ------------------------------------------------------------------
    # Decision helpers
    # ------------------------------------------------------------------

    def _should_defend(self) -> bool:
        return self.game_state.enemy_towers > self.game_state.my_towers

    def _should_attack(self) -> bool:
        return self.game_state.elixir > 5 or self.game_state.time_remaining < 90

    def _defensive_action(self) -> Action:
        return Action(
            type=ActionType.PLAY_CARD,
            card_index=random.randint(0, 3),
            position=(random.randint(200, 800), random.randint(600, 800)),
        )

    def _offensive_action(self) -> Action:
        return Action(
            type=ActionType.PLAY_CARD,
            card_index=random.randint(0, 3),
            position=(random.randint(400, 1520), random.randint(200, 500)),
        )

    def _aggressive_action(self) -> Action:
        return Action(
            type=ActionType.PLAY_CARD,
            card_index=random.randint(0, 3),
            position=(random.randint(600, 1320), random.randint(100, 300)),
        )

    def _choose_card(self) -> Optional[int]:
        return random.randint(0, 3)

    def _choose_position(self) -> Optional[tuple]:
        t = self.game_state.time_remaining
        if t > 150:
            return (random.randint(200, 800),  random.randint(600, 800))
        if t > 60:
            return (random.randint(400, 1520), random.randint(300, 600))
        return     (random.randint(600, 1320), random.randint(100, 400))
