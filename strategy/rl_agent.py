"""
ElixirMind Reinforcement Learning Agent
Advanced RL-based strategy using PPO from Stable Baselines3.
"""

import asyncio
import logging
import time
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import pickle
import os
from pathlib import Path

try:
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.vec_env import DummyVecEnv
    import gymnasium as gym
    from gymnasium import spaces
    STABLE_BASELINES_AVAILABLE = True
except ImportError:
    STABLE_BASELINES_AVAILABLE = False
    print("Stable Baselines3 not available. RL agent will use fallback heuristics.")

from .base import BaseStrategy, StrategyDecision
from .heuristic import HeuristicStrategy
from actions.controller import GameAction, ActionType
from config import Config


class ClashRoyaleEnv(gym.Env):
    """Gymnasium environment for Clash Royale bot training."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        # Action space: [card_to_play (0-3), target_x (0-1920), target_y (200-800)]
        # Simplified to discrete actions for easier training
        # 4 cards * 9 x positions * 6 y positions
        self.action_space = spaces.Discrete(4 * 9 * 6)

        # Observation space: [elixir, enemy_troops_count, friendly_troops_count, tower_healths, card_availability]
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(15,), dtype=np.float32
        )

        # Game state tracking
        self.current_game_state = None
        self.last_action_time = 0
        self.episode_reward = 0
        self.episode_length = 0
        self.max_episode_length = 300  # 5 minutes max

        # Reward tracking
        self.last_elixir = 0
        self.last_enemy_troops = 0
        self.last_friendly_troops = 0
        self.last_tower_damage = 0

    def reset(self, seed=None, options=None):
        """Reset environment for new episode."""
        super().reset(seed=seed)

        self.episode_reward = 0
        self.episode_length = 0
        self.last_action_time = time.time()

        # Return initial observation
        observation = np.zeros(15, dtype=np.float32)
        info = {}

        return observation, info

    def step(self, action):
        """Execute action and return new state, reward, done, info."""
        try:
            # Decode action
            card_index, target_pos = self._decode_action(action)

            # Create game action
            game_action = self._create_game_action(card_index, target_pos)

            # Calculate reward
            reward = self._calculate_reward(game_action)

            # Update episode tracking
            self.episode_length += 1
            self.episode_reward += reward

            # Check if episode is done
            done = self.episode_length >= self.max_episode_length

            # Get new observation
            observation = self._get_observation()

            info = {
                'episode_reward': self.episode_reward,
                'episode_length': self.episode_length,
                'action_executed': game_action is not None
            }

            return observation, reward, done, False, info  # terminated, truncated

        except Exception as e:
            logging.error(f"Environment step failed: {e}")
            return np.zeros(15, dtype=np.float32), -1.0, True, False, {}

    def _decode_action(self, action: int) -> Tuple[int, Tuple[int, int]]:
        """Decode discrete action to card index and position."""
        try:
            # Decode action space: 4 cards * 9 x positions * 6 y positions = 216 actions
            cards_count = 4
            x_positions = 9
            y_positions = 6

            card_index = action // (x_positions * y_positions)
            remaining = action % (x_positions * y_positions)
            x_index = remaining // y_positions
            y_index = remaining % y_positions

            # Map indices to actual coordinates
            x_coords = [480, 640, 800, 960, 1120,
                        1280, 1440, 1600, 1760]  # 9 positions
            y_coords = [300, 400, 500, 600, 700, 800]  # 6 positions

            target_x = x_coords[min(x_index, len(x_coords) - 1)]
            target_y = y_coords[min(y_index, len(y_coords) - 1)]

            return card_index, (target_x, target_y)

        except Exception as e:
            logging.error(f"Action decoding failed: {e}")
            return 0, (960, 500)

    def _create_game_action(self, card_index: int, target_pos: Tuple[int, int]) -> Optional[GameAction]:
        """Create GameAction from decoded action."""
        try:
            if not (0 <= card_index < 4):
                return None

            # Check if we have game state and cards available
            if not self.current_game_state:
                return None

            cards_in_hand = getattr(
                self.current_game_state, 'cards_in_hand', [])
            if card_index >= len(cards_in_hand):
                return None

            card = cards_in_hand[card_index]
            if not card.get('available', False):
                return None

            # Create place card action
            card_position = card.get('coordinates', (0, 0))

            return GameAction(
                action_type=ActionType.PLACE_CARD,
                parameters={
                    'card_position': card_position,
                    'target_position': target_pos,
                    'card_index': card_index
                }
            )

        except Exception as e:
            logging.error(f"Game action creation failed: {e}")
            return None

    def _calculate_reward(self, game_action: Optional[GameAction]) -> float:
        """Calculate reward for the action taken."""
        try:
            if not self.current_game_state:
                return 0.0

            reward = 0.0

            # Reward for successful actions
            if game_action:
                reward += 0.1  # Small reward for taking valid action
            else:
                reward -= 0.05  # Small penalty for invalid action

            # Elixir management rewards
            current_elixir = self.current_game_state.current_elixir
            if current_elixir < 10:  # Good elixir usage
                reward += 0.02 * (10 - current_elixir) / 10

            # Combat effectiveness rewards
            enemy_troops = len(
                getattr(self.current_game_state, 'enemy_troops', []))
            friendly_troops = len(
                getattr(self.current_game_state, 'friendly_troops', []))

            # Reward for maintaining board presence
            if friendly_troops > enemy_troops:
                reward += 0.05
            elif enemy_troops > friendly_troops + 2:
                reward -= 0.03  # Penalty for being overwhelmed

            # Tower damage rewards (would need to track tower health changes)
            # This is simplified - in practice you'd track actual damage dealt/taken

            # Time-based penalties to encourage action
            time_since_last = time.time() - self.last_action_time
            if time_since_last > 5:  # Encourage timely actions
                reward -= 0.01

            return reward

        except Exception as e:
            logging.error(f"Reward calculation failed: {e}")
            return 0.0

    def _get_observation(self) -> np.ndarray:
        """Get current observation from game state."""
        try:
            obs = np.zeros(15, dtype=np.float32)

            if not self.current_game_state:
                return obs

            # Normalize elixir (0-10 -> 0-1)
            obs[0] = self.current_game_state.current_elixir / 10.0

            # Enemy and friendly troop counts (normalized by max expected)
            enemy_troops = len(
                getattr(self.current_game_state, 'enemy_troops', []))
            friendly_troops = len(
                getattr(self.current_game_state, 'friendly_troops', []))
            obs[1] = min(enemy_troops / 10.0, 1.0)
            obs[2] = min(friendly_troops / 10.0, 1.0)

            # Tower health (normalized) - simplified as we don't track actual health
            obs[3] = 1.0  # Enemy king tower health
            obs[4] = 1.0  # Enemy left tower health
            obs[5] = 1.0  # Enemy right tower health
            obs[6] = 1.0  # Our king tower health
            obs[7] = 1.0  # Our left tower health
            obs[8] = 1.0  # Our right tower health

            # Card availability (4 cards, 0 or 1)
            cards_in_hand = getattr(
                self.current_game_state, 'cards_in_hand', [])
            for i in range(4):
                if i < len(cards_in_hand):
                    obs[9 +
                        i] = 1.0 if cards_in_hand[i].get('available', False) else 0.0
                else:
                    obs[9 + i] = 0.0

            # Battle phase indicator
            obs[13] = 0.5  # Simplified battle phase

            # Threat level
            threat_levels = {'low': 0.25, 'medium': 0.5,
                             'high': 0.75, 'critical': 1.0}
            obs[14] = threat_levels.get('medium', 0.5)  # Simplified

            return obs

        except Exception as e:
            logging.error(f"Observation generation failed: {e}")
            return np.zeros(15, dtype=np.float32)

    def update_game_state(self, game_state):
        """Update environment with new game state."""
        self.current_game_state = game_state


class RLAgent(BaseStrategy):
    """Reinforcement Learning strategy using PPO."""

    def __init__(self, config: Config):
        super().__init__(config)

        # Fallback strategy
        self.fallback_strategy = HeuristicStrategy(config)

        # RL components
        self.model = None
        self.env = None
        self.use_rl = STABLE_BASELINES_AVAILABLE and config.USE_RL_STRATEGY

        # Training parameters
        self.training_mode = False
        self.experience_buffer = []
        self.buffer_size = 10000

        # Performance tracking
        self.rl_decisions = 0
        self.fallback_decisions = 0

    async def initialize(self) -> bool:
        """Initialize RL agent."""
        try:
            self.logger.info("Initializing RL agent")

            # Initialize fallback strategy
            await self.fallback_strategy.initialize()

            if not self.use_rl:
                self.logger.warning(
                    "Using fallback heuristic strategy (RL not available)")
                return True

            # Initialize environment
            self.env = ClashRoyaleEnv(self.config)

            # Load or create model
            if not await self._load_model():
                await self._create_new_model()

            self.logger.info("RL agent initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"RL agent initialization failed: {e}")
            return False

    async def _load_model(self) -> bool:
        """Load existing RL model."""
        try:
            model_path = Path(self.config.RL_MODEL_PATH)

            if not model_path.exists():
                self.logger.info("No existing RL model found")
                return False

            self.model = PPO.load(str(model_path))
            self.logger.info(f"Loaded RL model from {model_path}")
            return True

        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            return False

    async def _create_new_model(self):
        """Create new RL model."""
        try:
            # Create vectorized environment
            vec_env = DummyVecEnv([lambda: self.env])

            # Create PPO model
            self.model = PPO(
                "MlpPolicy",
                vec_env,
                verbose=1,
                learning_rate=3e-4,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01
            )

            self.logger.info("Created new RL model")

        except Exception as e:
            self.logger.error(f"Model creation failed: {e}")
            raise

    async def decide_action(self, game_state) -> Optional[GameAction]:
        """Make strategic decision using RL or fallback."""
        try:
            if not self.should_make_decision():
                return None

            # Update environment with current state
            if self.env:
                self.env.update_game_state(game_state)

            # Try RL decision first
            if self.use_rl and self.model and random.random() < 0.8:  # 80% RL, 20% exploration
                action = await self._make_rl_decision(game_state)
                if action:
                    self.rl_decisions += 1
                    self.last_decision_time = time.time()
                    return action

            # Fallback to heuristic
            action = await self.fallback_strategy.decide_action(game_state)
            if action:
                self.fallback_decisions += 1

            return action

        except Exception as e:
            self.logger.error(f"RL decision making failed: {e}")
            return await self.fallback_strategy.decide_action(game_state)

    async def _make_rl_decision(self, game_state) -> Optional[GameAction]:
        """Make decision using RL model."""
        try:
            if not self.model or not self.env:
                return None

            # Get observation
            obs = self.env._get_observation()

            # Predict action
            action, _ = self.model.predict(obs, deterministic=False)

            # Decode action
            card_index, target_pos = self.env._decode_action(int(action))

            # Create game action
            return self.env._create_game_action(card_index, target_pos)

        except Exception as e:
            self.logger.error(f"RL decision failed: {e}")
            return None

    async def update_from_feedback(self, action: GameAction, success: bool):
        """Update RL model based on feedback."""
        try:
            # Update fallback strategy
            await self.fallback_strategy.update_from_feedback(action, success)

            if success:
                self.successful_decisions += 1

            # Store experience for RL training
            if self.training_mode and self.env:
                experience = {
                    'action': action,
                    'success': success,
                    'timestamp': time.time(),
                    'game_state': self.env.current_game_state
                }

                self.experience_buffer.append(experience)

                # Keep buffer size manageable
                if len(self.experience_buffer) > self.buffer_size:
                    self.experience_buffer = self.experience_buffer[-self.buffer_size//2:]

        except Exception as e:
            self.logger.error(f"RL feedback update failed: {e}")

    async def train_model(self, timesteps: int = 10000):
        """Train the RL model."""
        try:
            if not self.use_rl or not self.model:
                self.logger.warning("Cannot train: RL not available")
                return

            self.logger.info(f"Starting RL training for {timesteps} timesteps")
            self.training_mode = True

            # Train the model
            self.model.learn(total_timesteps=timesteps)

            # Save trained model
            await self._save_model()

            self.training_mode = False
            self.logger.info("RL training completed")

        except Exception as e:
            self.logger.error(f"RL training failed: {e}")
            self.training_mode = False

    async def _save_model(self):
        """Save RL model to disk."""
        try:
            if not self.model:
                return

            model_path = Path(self.config.RL_MODEL_PATH)
            model_path.parent.mkdir(parents=True, exist_ok=True)

            self.model.save(str(model_path))
            self.logger.info(f"Saved RL model to {model_path}")

        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get RL-specific performance metrics."""
        try:
            base_metrics = super().get_performance_metrics()

            rl_metrics = {
                'rl_decisions': self.rl_decisions,
                'fallback_decisions': self.fallback_decisions,
                'rl_usage_ratio': 0.0,
                'training_mode': self.training_mode,
                'experience_buffer_size': len(self.experience_buffer),
                'model_loaded': self.model is not None
            }

            total_decisions = self.rl_decisions + self.fallback_decisions
            if total_decisions > 0:
                rl_metrics['rl_usage_ratio'] = self.rl_decisions / \
                    total_decisions

            return {**base_metrics, **rl_metrics}

        except Exception as e:
            self.logger.error(f"RL metrics calculation failed: {e}")
            return super().get_performance_metrics()


# Fallback imports for when Stable Baselines3 is not available
if not STABLE_BASELINES_AVAILABLE:
    import random

    class RLAgent(BaseStrategy):
        """Fallback RL agent that uses heuristic strategy."""

        def __init__(self, config: Config):
            super().__init__(config)
            self.fallback_strategy = HeuristicStrategy(config)

        async def initialize(self) -> bool:
            self.logger.warning(
                "Using fallback heuristic strategy (Stable Baselines3 not available)")
            return await self.fallback_strategy.initialize()

        async def decide_action(self, game_state) -> Optional[GameAction]:
            return await self.fallback_strategy.decide_action(game_state)

        async def update_from_feedback(self, action: GameAction, success: bool):
            await self.fallback_strategy.update_from_feedback(action, success)
