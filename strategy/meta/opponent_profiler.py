"""
Opponent Profiler for Meta-Learning.
Profiles opponent behavior and deck tendencies.
"""

import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class OpponentProfiler:
    """
    Profiles opponent behavior and predicts strategies.
    """
    def __init__(self, config):
        self.config = config

        # Profile data
        self.opponent_history = []
        self.card_usage_patterns = defaultdict(int)
        self.strategy_patterns = defaultdict(int)
        self.timing_patterns = defaultdict(int)

        # Strategy archetypes
        self.strategy_archetypes = {
            'aggressive': ['Hog Rider', 'Balloon', 'Minion Horde', 'Barbarians'],
            'defensive': ['Cannon', 'Tesla', 'Bomb Tower', 'Inferno Tower'],
            'spell_heavy': ['Fireball', 'Lightning', 'Poison', 'Freeze'],
            'beat_down': ['Giant', 'P.E.K.K.A', 'Royal Giant', 'Golem'],
            'fast_attack': ['Skeleton Army', 'Goblins', 'Archers', 'Minions'],
            'control': ['X-Bow', 'Mortar', 'Wizard', 'Witch']
        }

    def update_profile(self, game_data):
        """
        Update opponent profile with new game data.

        Args:
            game_data: Dictionary containing game information
        """
        self.opponent_history.append(game_data)

        # Update card usage patterns
        if 'opponent_cards' in game_data:
            for card in game_data['opponent_cards']:
                self.card_usage_patterns[card] += 1

        # Update strategy patterns
        if 'opponent_strategy' in game_data:
            strategy = game_data['opponent_strategy']
            self.strategy_patterns[strategy] += 1

        # Update timing patterns
        if 'action_timings' in game_data:
            for timing in game_data['action_timings']:
                self.timing_patterns[timing] += 1

    def predict_strategy(self):
        """
        Predict opponent's likely strategy based on profile.

        Returns:
            str: Predicted strategy
        """
        if not self.opponent_history:
            return 'unknown'

        # Analyze recent games (last 10)
        recent_games = self.opponent_history[-10:]

        # Count strategy frequencies
        strategy_counts = Counter()
        for game in recent_games:
            if 'opponent_strategy' in game:
                strategy_counts[game['opponent_strategy']] += 1

        if strategy_counts:
            return strategy_counts.most_common(1)[0][0]

        # Fallback to card-based prediction
        return self._predict_from_cards()

    def predict_counter_strategy(self):
        """
        Predict best counter strategy based on opponent profile.

        Returns:
            str: Recommended counter strategy
        """
        opponent_strategy = self.predict_strategy()

        counter_strategies = {
            'aggressive': 'defensive',
            'defensive': 'aggressive',
            'spell_heavy': 'troop_heavy',
            'beat_down': 'spell_heavy',
            'fast_attack': 'control',
            'control': 'fast_attack',
            'unknown': 'balanced'
        }

        return counter_strategies.get(opponent_strategy, 'balanced')

    def get_opponent_weaknesses(self):
        """
        Identify opponent weaknesses based on profile.

        Returns:
            list: List of identified weaknesses
        """
        weaknesses = []

        # Analyze card usage patterns
        common_cards = [card for card, count in self.card_usage_patterns.items()
                       if count >= 3]  # Cards used in 3+ games

        # Check for common vulnerabilities
        if any(card in common_cards for card in ['Giant', 'Royal Giant']):
            weaknesses.append('vulnerable_to_lightning')
        if 'Hog Rider' in common_cards:
            weaknesses.append('vulnerable_to_fireball')
        if 'Balloon' in common_cards:
            weaknesses.append('vulnerable_to_zap_arrows')
        if any(card in common_cards for card in ['Wizard', 'Witch']):
            weaknesses.append('vulnerable_to_poison')

        # Analyze strategy patterns
        if self.strategy_patterns.get('aggressive', 0) > self.strategy_patterns.get('defensive', 0):
            weaknesses.append('overcommits_aggressively')

        return weaknesses

    def get_opponent_preferences(self):
        """
        Get opponent card and timing preferences.

        Returns:
            dict: Opponent preferences
        """
        preferences = {
            'favorite_cards': self._get_favorite_cards(),
            'preferred_timings': self._get_preferred_timings(),
            'strategy_consistency': self._calculate_strategy_consistency()
        }

        return preferences

    def _predict_from_cards(self):
        """Predict strategy from card usage patterns."""
        if not self.card_usage_patterns:
            return 'unknown'

        # Get most used cards
        top_cards = [card for card, _ in Counter(self.card_usage_patterns).most_common(5)]

        # Match against archetypes
        archetype_scores = defaultdict(int)

        for card in top_cards:
            for archetype, cards in self.strategy_archetypes.items():
                if card in cards:
                    archetype_scores[archetype] += 1

        if archetype_scores:
            return max(archetype_scores, key=archetype_scores.get)

        return 'balanced'

    def _get_favorite_cards(self):
        """Get opponent's favorite cards."""
        if not self.card_usage_patterns:
            return []

        return [card for card, count in Counter(self.card_usage_patterns).most_common(3)]

    def _get_preferred_timings(self):
        """Get opponent's preferred action timings."""
        if not self.timing_patterns:
            return []

        return [timing for timing, _ in Counter(self.timing_patterns).most_common(3)]

    def _calculate_strategy_consistency(self):
        """Calculate how consistent the opponent's strategy is."""
        if not self.strategy_patterns:
            return 0.0

        total_games = sum(self.strategy_patterns.values())
        most_common_count = max(self.strategy_patterns.values())

        return most_common_count / total_games if total_games > 0 else 0.0

    def reset_profile(self):
        """Reset the opponent profile."""
        self.opponent_history.clear()
        self.card_usage_patterns.clear()
        self.strategy_patterns.clear()
        self.timing_patterns.clear()
