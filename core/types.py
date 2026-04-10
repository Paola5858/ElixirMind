"""
Central domain types for ElixirMind.

All inter-module contracts are defined here. No module should exchange
raw dicts across the core boundary — use these types instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    PLAY_CARD    = "play_card"
    USE_SPELL    = "use_spell"
    UPGRADE_CARD = "upgrade_card"
    WAIT         = "wait"


class BotState(str, Enum):
    IDLE     = "idle"
    BATTLE   = "battle"
    SHUTDOWN = "shutdown"


# ---------------------------------------------------------------------------
# Action / ActionResult
# ---------------------------------------------------------------------------

@dataclass
class Action:
    """A single bot action to be executed by the Controller."""
    type: ActionType
    card_index: int = 0
    position: Optional[Tuple[int, int]] = None
    duration: float = 0.0


@dataclass
class ActionResult:
    """Outcome of a single executed action."""
    action: Action
    success: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Battle frame / state
# ---------------------------------------------------------------------------

@dataclass
class BattleFrame:
    """Raw data captured from a single screen frame."""
    screen: np.ndarray
    elixir: float = 0.0
    battle_active: bool = False
    timestamp: float = 0.0


@dataclass
class GameState:
    """Derived game state used by Strategy to make decisions."""
    elixir: float = 0.0
    enemy_towers: int = 3
    my_towers: int = 3
    enemy_king_tower: bool = True
    my_king_tower: bool = True
    time_remaining: int = 180
    cards_in_hand: list = field(default_factory=list)
