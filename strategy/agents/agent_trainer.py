"""
Agent Trainer for RL training pipeline.
"""

import logging
import numpy as np
from .ppo_agent import PPOAgent
from .dqn_agent import DQNAgent
from ..environments.clash_env import ClashEnv

logger = logging.getLogger(__name__)

class AgentTrainer:
    """
    Training pipeline for RL agents.
    """
    def __init__(self, config, agent_type='ppo'):
        self.config = config
        self.agent_type = agent_type

        # Training parameters
        self.num_episodes = config.get('training_episodes', 1000)
        self.max_steps = config.get('max_steps_per_episode', 100)
        self.save_freq = config.get('save_frequency', 100)
        self.eval_freq = config.get('eval_frequency', 50)

        # Create environment and agent
        self.env = ClashEnv(config)
        if agent_type == 'ppo':
            self.agent = PPOAgent(config)
        elif agent_type == 'dqn':
            self.agent = DQNAgent(config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Training stats
        self.episode_rewards = []
        self.episode_lengths = []

    def train(self):
        """Train the agent."""
        logger.info(f"Starting training with {self.agent_type.upper()} agent...")

        for episode in range(self.num_episodes):
            episode_reward = 0
            episode_steps = 0
            done = False

            state = self.env.reset()
            trajectory = []

            while not done and episode_steps < self.max_steps:
                # Select action
                action = self.agent.select_action(state)

                # Execute action
                next_state, reward, done, info = self.env.step(action)

                # Store transition
                trajectory.append({
                    'state': state,
                    'action': action,
                    'reward': reward,
                    'next_state': next_state,
                    'done': done,
                    'log_prob': self._get_log_prob(state, action) if self.agent_type == 'ppo' else 0
                })

                state = next_state
                episode_reward += reward
                episode_steps += 1

            # Update agent
            if self.agent_type == 'ppo':
                self.agent.update(trajectory)
            elif self.agent_type == 'dqn':
                for transition in trajectory:
                    self.agent.remember(
                        transition['state'], transition['action'], transition['reward'],
                        transition['next_state'], transition['done']
                    )
                self.agent.update()

            # Record stats
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_steps)

            # Logging
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                logger.info(f"Episode {episode + 1}/{self.num_episodes}, "
                          f"Avg Reward: {avg_reward:.2f}, Steps: {episode_steps}")

            # Save model
            if (episode + 1) % self.save_freq == 0:
                self.save_model(f"models/{self.agent_type}_episode_{episode + 1}.pth")

            # Evaluate
            if (episode + 1) % self.eval_freq == 0:
                eval_reward = self.evaluate(num_episodes=5)
                logger.info(f"Evaluation at episode {episode + 1}: {eval_reward:.2f}")

        logger.info("Training completed!")

    def evaluate(self, num_episodes=10):
        """Evaluate the agent."""
        total_reward = 0

        for _ in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0
            done = False
            steps = 0

            while not done and steps < self.max_steps:
                action = self.agent.select_action(state)
                next_state, reward, done, _ = self.env.step(action)
                episode_reward += reward
                state = next_state
                steps += 1

            total_reward += episode_reward

        return total_reward / num_episodes

    def _get_log_prob(self, state, action):
        """Get log probability for PPO (placeholder)."""
        # This would need to be implemented properly in PPO agent
        return 0.0

    def save_model(self, path):
        """Save the trained model."""
        self.agent.save_model(path)

    def load_model(self, path):
        """Load a trained model."""
        self.agent.load_model(path)

    def get_training_stats(self):
        """Get training statistics."""
        return {
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'average_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0,
            'max_reward': max(self.episode_rewards) if self.episode_rewards else 0
        }
