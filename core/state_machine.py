"""
State Machine: Manages bot lifecycle states with validated transitions.
"""

import logging
from typing import FrozenSet, Dict

from .types import BotState

logger = logging.getLogger(__name__)

# Valid transitions: state -> set of reachable states
_TRANSITIONS: Dict[BotState, FrozenSet[BotState]] = {
    BotState.IDLE:     frozenset({BotState.BATTLE, BotState.SHUTDOWN}),
    BotState.BATTLE:   frozenset({BotState.IDLE, BotState.SHUTDOWN}),
    BotState.SHUTDOWN: frozenset(),
}


class StateMachine:
    def __init__(self) -> None:
        self._state = BotState.IDLE

    def set_state(self, state: str | BotState) -> None:
        target = BotState(state) if isinstance(state, str) else state
        allowed = _TRANSITIONS.get(self._state, frozenset())
        if target not in allowed:
            logger.warning(
                "Invalid transition %s -> %s (allowed: %s)",
                self._state, target, {s.value for s in allowed},
            )
            return
        logger.info("State: %s -> %s", self._state.value, target.value)
        self._state = target

    def get_state(self) -> str:
        return self._state.value

    def is_idle(self) -> bool:
        return self._state is BotState.IDLE

    def is_battle(self) -> bool:
        return self._state is BotState.BATTLE

    def is_shutdown(self) -> bool:
        return self._state is BotState.SHUTDOWN
