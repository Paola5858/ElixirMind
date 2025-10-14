"""
Base Strategy: Abstract base for all strategies.
"""
import random
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Represents the current game state."""
    elixir: float = 0.0
    enemy_towers: int = 3
    my_towers: int = 3
    enemy_king_tower: bool = True
    my_king_tower: bool = True
    time_remaining: int = 180  # seconds
    cards_in_hand: List[str] = None  # Card names/types

    def __post_init__(self):
        if self.cards_in_hand is None:
            self.cards_in_hand = []

class Strategy:
    def __init__(self, config):
        self.config = config
        self.game_state = GameState()
        self.last_elixir_detection = 0.0
        self.action_history = []  # Track recent actions

    def initialize(self):
        """Initialize the strategy."""
        logger.info("Base Strategy initialized.")

    def shutdown(self):
        """Shutdown the strategy."""
        logger.info("Base Strategy shutdown.")

    def decide_actions(self, screen: np.ndarray, detector: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Decide actions based on the screen and current game state.
        Enhanced strategy with better decision logic.
        """
        actions = []

        # Update game state from screen analysis
        self._update_game_state(screen, detector)

        # Analyze opponent and make strategic decisions
        strategic_actions = self._analyze_game_situation()
        actions.extend(strategic_actions)

        # Add tactical actions based on current state
        tactical_actions = self._decide_tactical_actions()
        actions.extend(tactical_actions)

        # Update action history
        self.action_history.extend(actions)
        self.action_history = self.action_history[-10:]  # Keep last 10 actions

        return actions

    def _update_game_state(self, screen: np.ndarray, detector: Optional[Any]):
        """Update game state from screen analysis."""
        try:
            # Detect elixir level
            if detector and hasattr(detector, '_detect_elixir_presence'):
                # This would need proper OCR/text recognition for actual elixir values
                # For now, use a simple estimation
                self.game_state.elixir = min(
                    10.0, self.last_elixir_detection + 0.5)
                self.last_elixir_detection = self.game_state.elixir

            # Estimate time remaining (simplified)
            self.game_state.time_remaining = max(
                0, self.game_state.time_remaining - 1)

        except Exception as e:
            logger.error(f"Error updating game state: {e}")

    def _analyze_game_situation(self) -> List[Dict[str, Any]]:
        """Analyze the overall game situation and make strategic decisions."""
        actions = []

        # Early game strategy (first 30 seconds)
        if self.game_state.time_remaining > 150:
            actions.extend(self._early_game_strategy())

        # Mid game strategy
        elif self.game_state.time_remaining > 60:
            actions.extend(self._mid_game_strategy())

        # Late game strategy
        else:
            actions.extend(self._late_game_strategy())

        return actions

    def _early_game_strategy(self) -> List[Dict[str, Any]]:
        """Early game: Focus on defense and economy."""
        actions = []

        if self.game_state.elixir >= 4:
            # Prioritize defensive plays early
            if self._should_defend():
                actions.append(self._create_defensive_action())

        return actions

    def _mid_game_strategy(self) -> List[Dict[str, Any]]:
        """Mid game: Balance offense and defense."""
        actions = []

        if self.game_state.elixir >= 5:
            # More aggressive plays
            if self._should_attack():
                actions.append(self._create_offensive_action())

        return actions

    def _late_game_strategy(self) -> List[Dict[str, Any]]:
        """Late game: Go for the win."""
        actions = []

        if self.game_state.elixir >= 3:
            # Desperate measures - use whatever is available
            actions.append(self._create_aggressive_action())

        return actions

    def _decide_tactical_actions(self) -> List[Dict[str, Any]]:
        """Make tactical decisions based on current elixir and situation."""
        actions = []

        # Basic elixir-based decision making
        if self.game_state.elixir >= 4:
            logger.info(
                f"Sufficient elixir ({self.game_state.elixir:.1f}). Deciding to play a card.")

            # Choose card and position based on strategy
            card_index = self._choose_best_card()
            position = self._choose_best_position()

            if card_index is not None and position is not None:
                actions.append({
                    'type': 'play_card',
                    'card_index': card_index,
                    'position': position
                })
                self.game_state.elixir -= 4  # Simplified elixir cost

        return actions

    def _should_defend(self) -> bool:
        """Determine if defensive action is needed."""
        # Simple heuristic: defend if enemy towers are stronger
        return self.game_state.enemy_towers > self.game_state.my_towers

    def _should_attack(self) -> bool:
        """Determine if offensive action is warranted."""
        # Attack if we have elixir advantage or time pressure
        elixir_advantage = self.game_state.elixir > 5
        time_pressure = self.game_state.time_remaining < 90
        return elixir_advantage or time_pressure

    def _create_defensive_action(self) -> Dict[str, Any]:
        """Create a defensive action."""
        # Place defensive units near own towers
        card_index = random.randint(0, 3)
        # Defensive positions near own side
        target_x = random.randint(200, 800)
        target_y = random.randint(600, 800)

        return {
            'type': 'play_card',
            'card_index': card_index,
            'position': (target_x, target_y)
        }

    def _create_offensive_action(self) -> Dict[str, Any]:
        """Create an offensive action."""
        card_index = random.randint(0, 3)
        # Offensive positions on enemy side
        target_x = random.randint(400, 1520)
        target_y = random.randint(200, 500)

        return {
            'type': 'play_card',
            'card_index': card_index,
            'position': (target_x, target_y)
        }

    def _create_aggressive_action(self) -> Dict[str, Any]:
        """Create an aggressive end-game action."""
        card_index = random.randint(0, 3)
        # Target enemy towers directly
        target_x = random.randint(600, 1320)
        target_y = random.randint(100, 300)

        return {
            'type': 'play_card',
            'card_index': card_index,
            'position': (target_x, target_y)
        }

    def _choose_best_card(self) -> Optional[int]:
        """Choose the best card to play based on current situation."""
        # Simple random selection for now
        # In a real implementation, this would consider card synergies, elixir costs, etc.
        return random.randint(0, 3)

    def _choose_best_position(self) -> Optional[tuple]:
        """Choose the best position to play a card."""
        # Position based on current strategy phase
        if self.game_state.time_remaining > 150:  # Early game
            # Defensive positions
            x = random.randint(200, 800)
            y = random.randint(600, 800)
        elif self.game_state.time_remaining > 60:  # Mid game
            # Balanced positions
            x = random.randint(400, 1520)
            y = random.randint(300, 600)
        else:  # Late game
            # Aggressive positions
            x = random.randint(600, 1320)
            y = random.randint(100, 400)

        return (x, y)
