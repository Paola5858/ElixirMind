"""
Strategy Selector for Dynamic Strategy Selection.
Selects optimal strategy based on opponent profile and game state.
"""

import logging
from .deck_analyzer import DeckAnalyzer
from .opponent_profiler import OpponentProfiler

logger = logging.getLogger(__name__)

class StrategySelector:
    """
    Dynamically selects optimal strategy based on meta-analysis.
    """
    def __init__(self, config):
        self.config = config
        self.deck_analyzer = DeckAnalyzer(config)
        self.opponent_profiler = OpponentProfiler(config)

        # Available strategies
        self.strategies = {
            'aggressive': self._aggressive_strategy,
            'defensive': self._defensive_strategy,
            'control': self._control_strategy,
            'fast_attack': self._fast_attack_strategy,
            'beat_down': self._beat_down_strategy,
            'balanced': self._balanced_strategy
        }

        # Strategy selection weights
        self.strategy_weights = {
            'aggressive': 1.0,
            'defensive': 1.0,
            'control': 1.0,
            'fast_attack': 1.0,
            'beat_down': 1.0,
            'balanced': 1.0
        }

    def select_strategy(self, game_state, opponent_profile=None):
        """
        Select the optimal strategy for the current situation.

        Args:
            game_state: Current game state
            opponent_profile: Opponent profile data

        Returns:
            str: Selected strategy name
        """
        if opponent_profile:
            self.opponent_profiler.update_profile(opponent_profile)

        # Analyze current situation
        situation_analysis = self._analyze_situation(game_state)

        # Get strategy scores
        strategy_scores = {}
        for strategy_name, strategy_func in self.strategies.items():
            score = self._evaluate_strategy(strategy_name, situation_analysis)
            strategy_scores[strategy_name] = score

        # Select best strategy
        best_strategy = max(strategy_scores, key=strategy_scores.get)

        logger.info(f"Selected strategy: {best_strategy} "
                   f"(score: {strategy_scores[best_strategy]:.2f})")

        return best_strategy

    def get_strategy_actions(self, strategy_name, game_state):
        """
        Get recommended actions for the selected strategy.

        Args:
            strategy_name: Name of the strategy
            game_state: Current game state

        Returns:
            list: Recommended actions
        """
        if strategy_name not in self.strategies:
            strategy_name = 'balanced'

        strategy_func = self.strategies[strategy_name]
        return strategy_func(game_state)

    def update_strategy_weights(self, strategy_name, performance):
        """
        Update strategy weights based on performance.

        Args:
            strategy_name: Strategy that was used
            performance: Performance score (win=1, loss=-1, draw=0)
        """
        # Simple reinforcement learning for strategy selection
        learning_rate = 0.1

        if performance > 0:
            self.strategy_weights[strategy_name] *= (1 + learning_rate)
        elif performance < 0:
            self.strategy_weights[strategy_name] *= (1 - learning_rate)

        # Normalize weights
        total_weight = sum(self.strategy_weights.values())
        for strategy in self.strategy_weights:
            self.strategy_weights[strategy] /= total_weight

    def _analyze_situation(self, game_state):
        """Analyze the current game situation."""
        analysis = {
            'elixir_advantage': game_state.get('elixir_advantage', 0),
            'tower_damage': game_state.get('tower_damage', 0),
            'opponent_strategy': self.opponent_profiler.predict_strategy(),
            'game_phase': self._determine_game_phase(game_state),
            'card_advantage': game_state.get('card_advantage', 0)
        }

        return analysis

    def _evaluate_strategy(self, strategy_name, situation):
        """Evaluate how suitable a strategy is for the current situation."""
        score = self.strategy_weights[strategy_name]

        # Adjust score based on situation
        if strategy_name == 'aggressive':
            if situation['elixir_advantage'] > 0:
                score += 0.3
            if situation['opponent_strategy'] == 'defensive':
                score += 0.2

        elif strategy_name == 'defensive':
            if situation['elixir_advantage'] < 0:
                score += 0.3
            if situation['opponent_strategy'] == 'aggressive':
                score += 0.2

        elif strategy_name == 'control':
            if situation['game_phase'] == 'mid':
                score += 0.2
            if situation['tower_damage'] > 0:
                score += 0.1

        elif strategy_name == 'fast_attack':
            if situation['game_phase'] == 'early':
                score += 0.3
            if situation['card_advantage'] > 0:
                score += 0.2

        elif strategy_name == 'beat_down':
            if situation['elixir_advantage'] > 1:
                score += 0.3
            if situation['game_phase'] == 'late':
                score += 0.2

        return score

    def _determine_game_phase(self, game_state):
        """Determine the current game phase."""
        time_elapsed = game_state.get('time_elapsed', 0)

        if time_elapsed < 60:
            return 'early'
        elif time_elapsed < 150:
            return 'mid'
        else:
            return 'late'

    def _aggressive_strategy(self, game_state):
        """Aggressive strategy: Push hard, take risks."""
        actions = []

        # Prioritize offensive cards
        if game_state.get('elixir', 0) >= 3:
            actions.append('deploy_offensive_unit')

        # Use spells to support attacks
        if game_state.get('elixir', 0) >= 2:
            actions.append('use_damage_spell')

        return actions

    def _defensive_strategy(self, game_state):
        """Defensive strategy: Focus on defense and counter-play."""
        actions = []

        # Prioritize defensive buildings
        if game_state.get('elixir', 0) >= 3:
            actions.append('deploy_defensive_building')

        # Use spells defensively
        if game_state.get('elixir', 0) >= 1:
            actions.append('use_defensive_spell')

        return actions

    def _control_strategy(self, game_state):
        """Control strategy: Control the board, wear down opponent."""
        actions = []

        # Deploy control units
        if game_state.get('elixir', 0) >= 4:
            actions.append('deploy_control_unit')

        # Use area damage spells
        if game_state.get('elixir', 0) >= 3:
            actions.append('use_area_spell')

        return actions

    def _fast_attack_strategy(self, game_state):
        """Fast attack strategy: Quick, cheap units."""
        actions = []

        # Deploy fast, cheap units
        if game_state.get('elixir', 0) >= 2:
            actions.append('deploy_fast_unit')

        # Use cheap spells
        if game_state.get('elixir', 0) >= 1:
            actions.append('use_cheap_spell')

        return actions

    def _beat_down_strategy(self, game_state):
        """Beat down strategy: Big, powerful units."""
        actions = []

        # Deploy heavy hitters when elixir allows
        if game_state.get('elixir', 0) >= 5:
            actions.append('deploy_heavy_unit')

        # Support with spells
        if game_state.get('elixir', 0) >= 3:
            actions.append('use_support_spell')

        return actions

    def _balanced_strategy(self, game_state):
        """Balanced strategy: Mix of offense and defense."""
        actions = []

        # Balanced approach
        elixir = game_state.get('elixir', 0)

        if elixir >= 4:
            actions.append('deploy_balanced_unit')
        elif elixir >= 2:
            actions.append('deploy_cheap_unit')

        if elixir >= 2:
            actions.append('use_utility_spell')

        return actions
