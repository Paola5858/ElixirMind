"""
State Encoder for Clash Royale RL Environment.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

class StateEncoder:
    """
    Encodes game state into numerical representation for RL agents.
    """
    def __init__(self, config):
        self.config = config
        self.state_size = 128  # Fixed state size

        # Define state components
        self.state_components = {
            'player_health': 2,  # King tower + princess towers
            'opponent_health': 2,
            'elixir': 1,
            'cards_ready': 8,  # 8 card slots
            'card_types': 8,    # Card type encoding
            'board_state': 64,  # Simplified board representation
            'game_phase': 3,    # Early, mid, late game
            'time_remaining': 1,
            'damage_dealt': 1,
            'damage_taken': 1
        }

    def get_state_size(self):
        """Return the size of the encoded state."""
        return self.state_size

    def encode_initial_state(self):
        """Encode the initial game state."""
        state = np.zeros(self.state_size, dtype=np.float32)
        # Initialize with default values
        state[self._get_component_index('elixir')] = 5.0  # Starting elixir
        state[self._get_component_index('game_phase')] = 0.0  # Early game
        return state

    def encode_state(self):
        """
        Encode the current game state from screen/vision data.

        Returns:
            np.array: Encoded state vector
        """
        state = np.zeros(self.state_size, dtype=np.float32)

        try:
            # Encode player health
            player_health = self._get_player_health()
            state[self._get_component_slice('player_health')] = player_health

            # Encode opponent health
            opponent_health = self._get_opponent_health()
            state[self._get_component_slice('opponent_health')] = opponent_health

            # Encode elixir
            elixir = self._get_elixir()
            state[self._get_component_index('elixir')] = elixir

            # Encode cards
            cards_ready = self._get_cards_ready()
            state[self._get_component_slice('cards_ready')] = cards_ready

            card_types = self._get_card_types()
            state[self._get_component_slice('card_types')] = card_types

            # Encode board state
            board_state = self._encode_board_state()
            state[self._get_component_slice('board_state')] = board_state

            # Encode game phase
            game_phase = self._get_game_phase()
            state[self._get_component_slice('game_phase')] = game_phase

            # Encode time and damage
            time_remaining = self._get_time_remaining()
            state[self._get_component_index('time_remaining')] = time_remaining

            damage_stats = self._get_damage_stats()
            state[self._get_component_index('damage_dealt')] = damage_stats['dealt']
            state[self._get_component_index('damage_taken')] = damage_stats['taken']

        except Exception as e:
            logger.error(f"Error encoding state: {e}")
            # Return zero state on error
            return np.zeros(self.state_size, dtype=np.float32)

        return state

    def _get_component_index(self, component):
        """Get the starting index for a component."""
        index = 0
        for comp, size in self.state_components.items():
            if comp == component:
                return index
            index += size
        raise ValueError(f"Component {component} not found")

    def _get_component_slice(self, component):
        """Get the slice for a component."""
        start = self._get_component_index(component)
        size = self.state_components[component]
        return slice(start, start + size)

    def _get_player_health(self):
        """Get player tower health (placeholder)."""
        return np.array([3.0, 3.0])  # King + princess towers

    def _get_opponent_health(self):
        """Get opponent tower health (placeholder)."""
        return np.array([3.0, 3.0])

    def _get_elixir(self):
        """Get current elixir (placeholder)."""
        return 5.0

    def _get_cards_ready(self):
        """Get which cards are ready (placeholder)."""
        return np.ones(8)  # All cards ready

    def _get_card_types(self):
        """Get card type encodings (placeholder)."""
        return np.random.rand(8)  # Random for now

    def _encode_board_state(self):
        """Encode the board state (placeholder)."""
        return np.random.rand(64)  # Simplified board

    def _get_game_phase(self):
        """Get game phase encoding (placeholder)."""
        return np.array([1.0, 0.0, 0.0])  # Early game

    def _get_time_remaining(self):
        """Get time remaining (placeholder)."""
        return 180.0  # 3 minutes

    def _get_damage_stats(self):
        """Get damage statistics (placeholder)."""
        return {'dealt': 0.0, 'taken': 0.0}
