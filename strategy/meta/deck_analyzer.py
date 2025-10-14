"""
Deck Analyzer for Meta-Learning.
Analyzes deck composition and provides strategic insights.
"""

import logging
from collections import Counter

logger = logging.getLogger(__name__)

class DeckAnalyzer:
    """
    Analyzes deck composition and provides strategic recommendations.
    """
    def __init__(self, config):
        self.config = config

        # Card type categories
        self.card_categories = {
            'troops': ['Knight', 'Archers', 'Goblins', 'Giant', 'P.E.K.K.A', 'Mini P.E.K.K.A',
                      'Valkyrie', 'Skeleton Army', 'Barbarians', 'Royal Giant', 'Princess',
                      'Dark Prince', 'Three Musketeers', 'Lumberjack', 'Battle Ram'],
            'buildings': ['Cannon', 'Bomb Tower', 'Inferno Tower', 'Barbarian Hut', 'Tesla',
                         'Elixir Collector', 'X-Bow', 'Mortar', 'Goblin Hut'],
            'spells': ['Arrows', 'Zap', 'Fireball', 'Rocket', 'Lightning', 'Freeze', 'Poison',
                      'Earthquake', 'Barbarian Barrel', 'Tornado', 'Clone', 'Mirror'],
            'wins': ['The Log', 'Royal Delivery', 'Earthquake']
        }

        # Card stats (simplified)
        self.card_stats = {
            'Knight': {'cost': 3, 'damage': 75, 'hitpoints': 600},
            'Archers': {'cost': 3, 'damage': 33, 'hitpoints': 125},
            'Goblins': {'cost': 2, 'damage': 50, 'hitpoints': 80},
            'Giant': {'cost': 5, 'damage': 126, 'hitpoints': 2000},
            'P.E.K.K.A': {'cost': 7, 'damage': 678, 'hitpoints': 3120},
            # Add more cards as needed
        }

    def analyze_deck(self, deck_cards):
        """
        Analyze deck composition.

        Args:
            deck_cards: List of card names in the deck

        Returns:
            dict: Analysis results
        """
        analysis = {
            'composition': self._analyze_composition(deck_cards),
            'strengths': self._identify_strengths(deck_cards),
            'weaknesses': self._identify_weaknesses(deck_cards),
            'counters': self._suggest_counters(deck_cards),
            'synergies': self._analyze_synergies(deck_cards),
            'elixir_cost': self._calculate_elixir_cost(deck_cards),
            'strategy_type': self._classify_strategy(deck_cards)
        }

        return analysis

    def _analyze_composition(self, deck_cards):
        """Analyze deck composition by categories."""
        composition = {'troops': 0, 'buildings': 0, 'spells': 0, 'wins': 0}

        for card in deck_cards:
            for category, cards in self.card_categories.items():
                if card in cards:
                    composition[category] += 1
                    break

        return composition

    def _identify_strengths(self, deck_cards):
        """Identify deck strengths."""
        strengths = []

        composition = self._analyze_composition(deck_cards)

        if composition['troops'] >= 6:
            strengths.append('Strong troop presence')
        if composition['buildings'] >= 3:
            strengths.append('Good building defense')
        if composition['spells'] >= 4:
            strengths.append('Spell heavy deck')
        if composition['wins'] >= 2:
            strengths.append('Win condition cards')

        # Check for specific strong combinations
        if 'P.E.K.K.A' in deck_cards and 'Earthquake' in deck_cards:
            strengths.append('PEKKA-Earthquake synergy')

        return strengths

    def _identify_weaknesses(self, deck_cards):
        """Identify deck weaknesses."""
        weaknesses = []

        composition = self._analyze_composition(deck_cards)

        if composition['troops'] < 4:
            weaknesses.append('Weak troop presence')
        if composition['buildings'] < 2:
            weaknesses.append('Poor building defense')
        if composition['spells'] < 2:
            weaknesses.append('Limited spell options')

        # Check for common vulnerabilities
        if 'Giant' in deck_cards and 'Lightning' not in deck_cards:
            weaknesses.append('Vulnerable to Lightning')
        if 'Hog Rider' in deck_cards and 'Fireball' not in deck_cards:
            weaknesses.append('Weak against Fireball counters')

        return weaknesses

    def _suggest_counters(self, deck_cards):
        """Suggest counter strategies."""
        counters = []

        if 'Giant' in deck_cards:
            counters.append('Use Lightning or Poison for buildings')
        if 'Hog Rider' in deck_cards:
            counters.append('Deploy Fireball or Inferno Tower')
        if 'Balloon' in deck_cards:
            counters.append('Use Zap and Arrows combination')
        if 'P.E.K.K.A' in deck_cards:
            counters.append('Use Earthquake and Poison')

        return counters

    def _analyze_synergies(self, deck_cards):
        """Analyze card synergies."""
        synergies = []

        # Common synergies
        synergy_pairs = [
            (['Giant', 'Wizard'], 'Giant-Wizard: Wizard protects Giant'),
            (['Hog Rider', 'Freeze'], 'Hog Rider-Freeze: Freeze enables Hog Rider'),
            (['Balloon', 'Lightning'], 'Balloon-Lightning: Lightning counters buildings'),
            (['P.E.K.K.A', 'Earthquake'], 'PEKKA-Earthquake: Earthquake destroys buildings'),
        ]

        for pair, description in synergy_pairs:
            if all(card in deck_cards for card in pair):
                synergies.append(description)

        return synergies

    def _calculate_elixir_cost(self, deck_cards):
        """Calculate average elixir cost."""
        total_cost = 0
        valid_cards = 0

        for card in deck_cards:
            if card in self.card_stats:
                total_cost += self.card_stats[card]['cost']
                valid_cards += 1

        if valid_cards == 0:
            return 0

        return total_cost / valid_cards

    def _classify_strategy(self, deck_cards):
        """Classify the deck strategy type."""
        composition = self._analyze_composition(deck_cards)

        if composition['buildings'] >= 4:
            return 'Control/Defense'
        elif 'P.E.K.K.A' in deck_cards or 'Giant' in deck_cards:
            return 'Beat Down'
        elif 'Balloon' in deck_cards or 'Hog Rider' in deck_cards:
            return 'Fast Attack'
        elif composition['spells'] >= 5:
            return 'Spell Bait'
        else:
            return 'Balanced'
