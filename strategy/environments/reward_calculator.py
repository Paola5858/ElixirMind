"""
Reward Calculator for Clash Royale RL Environment.
"""

import logging

logger = logging.getLogger(__name__)

class RewardCalculator:
    """
    Calculates rewards based on game actions and state changes.
    """
    def __init__(self, config):
        self.config = config
        self.reward_weights = {
            'damage_dealt': 1.0,
            'damage_taken': -0.8,
            'card_played': 0.1,
            'tower_damage': 2.0,
            'win': 10.0,
            'loss': -5.0,
            'draw': 0.0
        }

    def calculate_reward(self, action, current_state):
        """
        Calculate reward for the given action and state.

        Args:
            action: The action taken (card index)
            current_state: Current game state

        Returns:
            float: Calculated reward
        """
        reward = 0.0

        # Base reward for playing a card
        reward += self.reward_weights['card_played']

        # Calculate damage-based rewards
        damage_reward = self._calculate_damage_reward(current_state)
        reward += damage_reward

        # Calculate strategic rewards
        strategic_reward = self._calculate_strategic_reward(action, current_state)
        reward += strategic_reward

        # Battle outcome rewards
        outcome_reward = self._calculate_outcome_reward(current_state)
        reward += outcome_reward

        return reward

    def _calculate_damage_reward(self, state):
        """Calculate reward based on damage dealt/taken."""
        reward = 0.0

        if 'damage_dealt' in state:
            reward += state['damage_dealt'] * self.reward_weights['damage_dealt']

        if 'damage_taken' in state:
            reward += state['damage_taken'] * self.reward_weights['damage_taken']

        if 'tower_damage' in state:
            reward += state['tower_damage'] * self.reward_weights['tower_damage']

        return reward

    def _calculate_strategic_reward(self, action, state):
        """Calculate reward based on strategic value of action."""
        reward = 0.0

        # Reward for playing high-value cards at appropriate times
        if 'card_values' in state and action < len(state['card_values']):
            card_value = state['card_values'][action]
            reward += card_value * 0.5

        # Reward for counter-play
        if self._is_counter_play(action, state):
            reward += 1.0

        return reward

    def _calculate_outcome_reward(self, state):
        """Calculate reward based on battle outcome."""
        reward = 0.0

        if 'battle_result' in state:
            result = state['battle_result']
            if result == 'win':
                reward += self.reward_weights['win']
            elif result == 'loss':
                reward += self.reward_weights['loss']
            elif result == 'draw':
                reward += self.reward_weights['draw']

        return reward

    def _is_counter_play(self, action, state):
        """Check if the action is a counter-play."""
        # Implement counter-play detection logic
        return False  # Placeholder
