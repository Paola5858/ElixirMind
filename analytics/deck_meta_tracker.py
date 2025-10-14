"""
Deck Meta Tracker: Tracks and analyzes deck meta trends and performance.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DeckMetaTracker:
    """
    Tracks deck meta trends, popularity, and performance across different arenas and time periods.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Tracking settings
        self.tracking_window_days = self.config.get('tracking_window', 30)
        self.min_games_for_meta = self.config.get('min_games', 50)
        self.meta_update_interval = self.config.get('update_interval', 3600)  # 1 hour

        # Meta data storage
        self.arena_meta = defaultdict(dict)
        self.deck_popularity = defaultdict(int)
        self.deck_performance = defaultdict(dict)
        self.meta_trends = []

        # Last update timestamp
        self.last_update = 0

        logger.info("Deck Meta Tracker initialized")

    def update_meta_data(self, matches: List[Dict]) -> Dict:
        """
        Update meta data from recent matches.

        Args:
            matches: List of recent match data

        Returns:
            Dict with updated meta information
        """
        current_time = time.time()

        # Check if update is needed
        if current_time - self.last_update < self.meta_update_interval:
            return self.get_current_meta()

        # Filter recent matches
        recent_matches = self._filter_recent_matches(matches)

        if len(recent_matches) < self.min_games_for_meta:
            logger.warning(f"Insufficient matches for meta analysis: {len(recent_matches)}")
            return {'error': 'insufficient_data'}

        # Analyze by arena
        arena_analysis = self._analyze_by_arena(recent_matches)

        # Update deck popularity
        self._update_deck_popularity(recent_matches)

        # Update deck performance
        self._update_deck_performance(recent_matches)

        # Track meta trends
        self._track_meta_trends(arena_analysis)

        self.last_update = current_time

        meta_summary = {
            'total_matches_analyzed': len(recent_matches),
            'arenas_analyzed': len(arena_analysis),
            'top_decks': self.get_top_decks(limit=10),
            'meta_trends': self.get_meta_trends(),
            'updated_at': datetime.fromtimestamp(current_time).isoformat()
        }

        logger.info(f"Meta data updated: {len(recent_matches)} matches analyzed")
        return meta_summary

    def get_current_meta(self, arena: str = None) -> Dict:
        """
        Get current meta information.

        Args:
            arena: Specific arena to get meta for, or None for all

        Returns:
            Dict with current meta data
        """
        if arena:
            return self.arena_meta.get(arena, {})

        return {
            'global_meta': self._get_global_meta(),
            'arena_meta': dict(self.arena_meta),
            'top_decks': self.get_top_decks(limit=20),
            'emerging_decks': self.get_emerging_decks(),
            'declining_decks': self.get_declining_decks()
        }

    def get_top_decks(self, arena: str = None, limit: int = 10) -> List[Dict]:
        """
        Get top performing decks.

        Args:
            arena: Specific arena, or None for global
            limit: Maximum number of decks to return

        Returns:
            List of top deck information
        """
        if arena and arena in self.arena_meta:
            deck_data = self.arena_meta[arena].get('deck_performance', {})
        else:
            deck_data = self.deck_performance

        # Sort by win rate and popularity
        sorted_decks = []
        for deck_id, performance in deck_data.items():
            if performance.get('games', 0) >= 10:  # Minimum games threshold
                score = (performance.get('win_rate', 0) * 0.7 +
                        min(performance.get('games', 0) / 100, 1) * 0.3)  # Popularity factor

                sorted_decks.append({
                    'deck_id': deck_id,
                    'win_rate': performance.get('win_rate', 0),
                    'games': performance.get('games', 0),
                    'popularity': performance.get('popularity', 0),
                    'score': score,
                    'avg_trophies': performance.get('avg_trophies', 0)
                })

        sorted_decks.sort(key=lambda x: x['score'], reverse=True)
        return sorted_decks[:limit]

    def get_emerging_decks(self, days: int = 7) -> List[Dict]:
        """
        Get decks that are emerging in popularity.

        Args:
            days: Number of days to look back

        Returns:
            List of emerging decks
        """
        emerging = []

        for deck_id, performance in self.deck_performance.items():
            trend = self._calculate_deck_trend(deck_id, days)
            if trend.get('momentum', 0) > 0.1:  # Positive momentum
                emerging.append({
                    'deck_id': deck_id,
                    'trend': trend,
                    'current_popularity': performance.get('popularity', 0),
                    'win_rate': performance.get('win_rate', 0)
                })

        emerging.sort(key=lambda x: x['trend']['momentum'], reverse=True)
        return emerging[:10]

    def get_declining_decks(self, days: int = 7) -> List[Dict]:
        """
        Get decks that are declining in popularity.

        Args:
            days: Number of days to look back

        Returns:
            List of declining decks
        """
        declining = []

        for deck_id, performance in self.deck_performance.items():
            trend = self._calculate_deck_trend(deck_id, days)
            if trend.get('momentum', 0) < -0.1:  # Negative momentum
                declining.append({
                    'deck_id': deck_id,
                    'trend': trend,
                    'current_popularity': performance.get('popularity', 0),
                    'win_rate': performance.get('win_rate', 0)
                })

        declining.sort(key=lambda x: x['trend']['momentum'])
        return declining[:10]

    def predict_meta_shifts(self, days_ahead: int = 7) -> Dict:
        """
        Predict how the meta might shift in the future.

        Args:
            days_ahead: Number of days to predict ahead

        Returns:
            Dict with meta shift predictions
        """
        predictions = {
            'predicted_top_decks': [],
            'rising_decks': [],
            'falling_decks': [],
            'confidence': 0.0
        }

        # Simple prediction based on current trends
        current_top = self.get_top_decks(limit=20)

        for deck in current_top:
            trend = self._calculate_deck_trend(deck['deck_id'], 14)  # 2 weeks of data
            momentum = trend.get('momentum', 0)

            if momentum > 0.05:
                predictions['rising_decks'].append(deck)
            elif momentum < -0.05:
                predictions['falling_decks'].append(deck)

        # Predict future top decks
        future_scores = []
        for deck in current_top:
            trend = self._calculate_deck_trend(deck['deck_id'], 7)
            predicted_score = deck['score'] + (trend.get('momentum', 0) * days_ahead * 0.1)
            future_scores.append((deck['deck_id'], predicted_score))

        future_scores.sort(key=lambda x: x[1], reverse=True)
        predictions['predicted_top_decks'] = [deck_id for deck_id, _ in future_scores[:10]]

        # Calculate prediction confidence
        trend_strengths = [abs(self._calculate_deck_trend(d['deck_id'], 7).get('momentum', 0))
                          for d in current_top[:10]]
        predictions['confidence'] = statistics.mean(trend_strengths) if trend_strengths else 0

        return predictions

    def get_counter_recommendations(self, deck_id: str) -> List[Dict]:
        """
        Get counter deck recommendations for a specific deck.

        Args:
            deck_id: Target deck ID

        Returns:
            List of recommended counter decks
        """
        counters = []

        # Find decks that perform well against the target deck
        target_performance = self.deck_performance.get(deck_id, {})

        for counter_deck_id, performance in self.deck_performance.items():
            if counter_deck_id == deck_id:
                continue

            # Calculate counter effectiveness
            matchup_win_rate = self._calculate_matchup_win_rate(counter_deck_id, deck_id)
            if matchup_win_rate > 0.55:  # Good counter
                counters.append({
                    'counter_deck': counter_deck_id,
                    'win_rate_vs_target': matchup_win_rate,
                    'overall_win_rate': performance.get('win_rate', 0),
                    'popularity': performance.get('popularity', 0),
                    'confidence': min(performance.get('games', 0) / 100, 1.0)
                })

        counters.sort(key=lambda x: x['win_rate_vs_target'], reverse=True)
        return counters[:5]

    def get_meta_trends(self, days: int = 30) -> List[Dict]:
        """
        Get meta trends over time.

        Args:
            days: Number of days of trend data

        Returns:
            List of meta trend data points
        """
        # Return recent trend data
        recent_trends = [
            trend for trend in self.meta_trends
            if time.time() - trend.get('timestamp', 0) < (days * 24 * 3600)
        ]

        return recent_trends[-50:]  # Last 50 data points

    def _filter_recent_matches(self, matches: List[Dict]) -> List[Dict]:
        """Filter matches within the tracking window."""
        cutoff_time = time.time() - (self.tracking_window_days * 24 * 3600)

        return [
            match for match in matches
            if match.get('timestamp', 0) > cutoff_time
        ]

    def _analyze_by_arena(self, matches: List[Dict]) -> Dict:
        """Analyze matches grouped by arena."""
        arena_groups = defaultdict(list)

        for match in matches:
            arena = match.get('arena', 'unknown')
            arena_groups[arena].append(match)

        arena_analysis = {}
        for arena, arena_matches in arena_groups.items():
            if len(arena_matches) >= 20:  # Minimum matches per arena
                arena_analysis[arena] = {
                    'total_matches': len(arena_matches),
                    'avg_trophies': self._calculate_avg_trophies(arena_matches),
                    'deck_performance': self._analyze_deck_performance_in_arena(arena_matches),
                    'popular_strategies': self._analyze_strategies_in_arena(arena_matches)
                }

        return arena_analysis

    def _update_deck_popularity(self, matches: List[Dict]):
        """Update deck popularity statistics."""
        deck_counts = Counter(match.get('deck_id') for match in matches if match.get('deck_id'))

        total_matches = len(matches)
        for deck_id, count in deck_counts.items():
            self.deck_popularity[deck_id] = count / total_matches if total_matches > 0 else 0

    def _update_deck_performance(self, matches: List[Dict]):
        """Update deck performance statistics."""
        deck_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'trophies': 0})

        for match in matches:
            deck_id = match.get('deck_id')
            if deck_id:
                deck_stats[deck_id]['games'] += 1
                if match.get('result') == 'win':
                    deck_stats[deck_id]['wins'] += 1
                deck_stats[deck_id]['trophies'] += match.get('trophy_change', 0)

        for deck_id, stats in deck_stats.items():
            games = stats['games']
            if games > 0:
                self.deck_performance[deck_id].update({
                    'games': games,
                    'win_rate': stats['wins'] / games,
                    'avg_trophies': stats['trophies'] / games,
                    'popularity': self.deck_popularity.get(deck_id, 0),
                    'last_updated': time.time()
                })

    def _track_meta_trends(self, arena_analysis: Dict):
        """Track meta trends over time."""
        trend_data = {
            'timestamp': time.time(),
            'total_matches': sum(arena.get('total_matches', 0) for arena in arena_analysis.values()),
            'arenas_active': len(arena_analysis),
            'top_deck_win_rate': 0,
            'meta_diversity': len(self.deck_performance)
        }

        # Calculate top deck win rate
        top_decks = self.get_top_decks(limit=5)
        if top_decks:
            trend_data['top_deck_win_rate'] = statistics.mean(d['win_rate'] for d in top_decks)

        self.meta_trends.append(trend_data)

        # Keep only recent trends
        cutoff_time = time.time() - (90 * 24 * 3600)  # 90 days
        self.meta_trends = [
            trend for trend in self.meta_trends
            if trend['timestamp'] > cutoff_time
        ]

    def _get_global_meta(self) -> Dict:
        """Get global meta summary."""
        if not self.deck_performance:
            return {}

        total_games = sum(stats.get('games', 0) for stats in self.deck_performance.values())
        total_wins = sum(stats.get('games', 0) * stats.get('win_rate', 0)
                        for stats in self.deck_performance.values())

        return {
            'total_decks_tracked': len(self.deck_performance),
            'total_games_analyzed': total_games,
            'average_win_rate': total_wins / total_games if total_games > 0 else 0,
            'meta_stability': self._calculate_meta_stability(),
            'dominant_strategy': self._identify_dominant_strategy()
        }

    def _analyze_deck_performance_in_arena(self, matches: List[Dict]) -> Dict:
        """Analyze deck performance within a specific arena."""
        deck_stats = defaultdict(lambda: {'games': 0, 'wins': 0})

        for match in matches:
            deck_id = match.get('deck_id')
            if deck_id:
                deck_stats[deck_id]['games'] += 1
                if match.get('result') == 'win':
                    deck_stats[deck_id]['wins'] += 1

        performance = {}
        for deck_id, stats in deck_stats.items():
            if stats['games'] >= 5:  # Minimum games
                performance[deck_id] = {
                    'win_rate': stats['wins'] / stats['games'],
                    'games': stats['games'],
                    'confidence': min(stats['games'] / 50, 1.0)
                }

        return performance

    def _analyze_strategies_in_arena(self, matches: List[Dict]) -> Dict:
        """Analyze strategy popularity in an arena."""
        strategy_counts = Counter(match.get('strategy_used') for match in matches
                                 if match.get('strategy_used'))

        total_matches = len(matches)
        strategies = {}
        for strategy, count in strategy_counts.items():
            strategies[strategy] = {
                'usage_rate': count / total_matches if total_matches > 0 else 0,
                'games': count
            }

        return strategies

    def _calculate_avg_trophies(self, matches: List[Dict]) -> float:
        """Calculate average trophy level in matches."""
        trophies = []
        for match in matches:
            # Use opponent trophies as arena indicator
            opp_trophies = match.get('opponent_trophies')
            if opp_trophies:
                trophies.append(opp_trophies)

        return statistics.mean(trophies) if trophies else 0

    def _calculate_deck_trend(self, deck_id: str, days: int) -> Dict:
        """Calculate trend information for a deck."""
        # This would analyze historical data to calculate trends
        # For now, return a simple structure
        return {
            'momentum': 0.0,  # -1 to 1, trend direction and strength
            'volatility': 0.0,
            'days_analyzed': days,
            'data_points': 0
        }

    def _calculate_matchup_win_rate(self, deck1: str, deck2: str) -> float:
        """Calculate win rate of deck1 vs deck2."""
        # This would require matchup data
        # For now, return a neutral value
        return 0.5

    def _calculate_meta_stability(self) -> float:
        """Calculate how stable the current meta is."""
        if len(self.meta_trends) < 7:  # Need at least a week of data
            return 0.5

        # Calculate variance in top deck win rates
        recent_trends = self.meta_trends[-7:]
        win_rates = [trend.get('top_deck_win_rate', 0) for trend in recent_trends]

        if len(win_rates) > 1:
            variance = statistics.variance(win_rates)
            # Convert variance to stability score (0-1, higher is more stable)
            stability = 1 / (1 + variance * 100)
            return stability

        return 0.5

    def _identify_dominant_strategy(self) -> str:
        """Identify the currently dominant strategy."""
        strategy_popularity = defaultdict(float)

        for arena_data in self.arena_meta.values():
            strategies = arena_data.get('popular_strategies', {})
            for strategy, data in strategies.items():
                strategy_popularity[strategy] += data.get('usage_rate', 0)

        if strategy_popularity:
            return max(strategy_popularity.items(), key=lambda x: x[1])[0]

        return 'unknown'
