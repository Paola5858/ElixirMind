"""
PPO Agent for Clash Royale.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.distributions import Categorical
import logging

logger = logging.getLogger(__name__)

class PPOAgent:
    """
    Proximal Policy Optimization agent for card selection.
    """
    def __init__(self, config, state_size=128, action_size=8):
        self.config = config
        self.state_size = state_size
        self.action_size = action_size

        # PPO hyperparameters
        self.lr = config.get('ppo_lr', 3e-4)
        self.gamma = config.get('ppo_gamma', 0.99)
        self.gae_lambda = config.get('ppo_gae_lambda', 0.95)
        self.clip_epsilon = config.get('ppo_clip_epsilon', 0.2)
        self.value_coeff = config.get('ppo_value_coeff', 0.5)
        self.entropy_coeff = config.get('ppo_entropy_coeff', 0.01)
        self.ppo_epochs = config.get('ppo_epochs', 10)
        self.batch_size = config.get('ppo_batch_size', 64)

        # Neural network
        self.policy_net = PolicyNetwork(state_size, action_size)
        self.value_net = ValueNetwork(state_size)
        self.optimizer = optim.Adam([
            {'params': self.policy_net.parameters()},
            {'params': self.value_net.parameters()}
        ], lr=self.lr)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net.to(self.device)
        self.value_net.to(self.device)

    def select_action(self, state):
        """
        Select an action given the current state.

        Args:
            state: Current state vector

        Returns:
            int: Selected action
        """
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            action_probs = self.policy_net(state)
            dist = Categorical(action_probs)
            action = dist.sample()

        return action.item()

    def update(self, trajectories):
        """
        Update the agent using PPO.

        Args:
            trajectories: List of trajectory dictionaries
        """
        # Convert trajectories to tensors
        states = torch.FloatTensor(np.array([t['state'] for t in trajectories])).to(self.device)
        actions = torch.LongTensor(np.array([t['action'] for t in trajectories])).to(self.device)
        rewards = torch.FloatTensor(np.array([t['reward'] for t in trajectories])).to(self.device)
        next_states = torch.FloatTensor(np.array([t['next_state'] for t in trajectories])).to(self.device)
        dones = torch.FloatTensor(np.array([t['done'] for t in trajectories])).to(self.device)
        old_log_probs = torch.FloatTensor(np.array([t['log_prob'] for t in trajectories])).to(self.device)

        # Compute advantages and returns
        with torch.no_grad():
            values = self.value_net(states).squeeze()
            next_values = self.value_net(next_states).squeeze()
            advantages, returns = self._compute_gae(rewards, values, next_values, dones)

        # PPO update
        for _ in range(self.ppo_epochs):
            # Create mini-batches
            indices = np.random.permutation(len(trajectories))
            for start in range(0, len(trajectories), self.batch_size):
                end = start + self.batch_size
                batch_indices = indices[start:end]

                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]

                # Get current policy outputs
                action_probs = self.policy_net(batch_states)
                dist = Categorical(action_probs)
                new_log_probs = dist.log_prob(batch_actions)
                values = self.value_net(batch_states).squeeze()

                # Compute ratios and losses
                ratios = torch.exp(new_log_probs - batch_old_log_probs)
                surr1 = ratios * batch_advantages
                surr2 = torch.clamp(ratios, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages

                policy_loss = -torch.min(surr1, surr2).mean()
                value_loss = nn.MSELoss()(values, batch_returns)
                entropy_loss = -dist.entropy().mean()

                total_loss = policy_loss + self.value_coeff * value_loss - self.entropy_coeff * entropy_loss

                # Update networks
                self.optimizer.zero_grad()
                total_loss.backward()
                self.optimizer.step()

    def _compute_gae(self, rewards, values, next_values, dones):
        """Compute Generalized Advantage Estimation."""
        advantages = []
        gae = 0

        for step in reversed(range(len(rewards))):
            if step == len(rewards) - 1:
                next_value = next_values[step]
            else:
                next_value = values[step + 1]

            delta = rewards[step] + self.gamma * next_value * (1 - dones[step]) - values[step]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[step]) * gae
            advantages.insert(0, gae)

        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = advantages + values

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return advantages, returns

    def save_model(self, path):
        """Save the model."""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'value_net': self.value_net.state_dict(),
            'optimizer': self.optimizer.state_dict()
        }, path)

    def load_model(self, path):
        """Load the model."""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.value_net.load_state_dict(checkpoint['value_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])


class PolicyNetwork(nn.Module):
    """Policy network for PPO."""
    def __init__(self, state_size, action_size):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, action_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.softmax(self.fc3(x), dim=-1)
        return x


class ValueNetwork(nn.Module):
    """Value network for PPO."""
    def __init__(self, state_size):
        super(ValueNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
