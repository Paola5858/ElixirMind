"""
Match Analyzer: Detailed analysis of match performance and patterns.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import statistics
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MatchAnalyzer:
    """
    Analyzes match data to identify patterns, performance trends, and optimization opportunities.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Analysis settings
        self.min_matches_for_analysis = self.config.get('min_matches', 10)
        self.performance_window_days = self.config.get('performance_window', 7)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)

        logger.info("Match Analyzer initialized")

    def analyze_match_performance(self, matches: List[Dict]) -> Dict:
        """
        Analyze overall match performance.

        Args:
            matches: List of match data

        Returns:
            Dict with performance analysis
        """
        if len(matches) < self.min_matches_for_analysis:
            return {'error': f'Need at least {self.min_matches_for_analysis} matches for analysis'}

        analysis = {
            'total_matches': len(matches),
            'win_rate': self._calculate_win_rate(matches),
            'avg_match_duration': self._calculate_avg_duration(matches),
            'trophy_performance': self._analyze_trophy_changes(matches),
            'deck_performance': self._analyze_deck_performance(matches),
            'time_based_performance': self._analyze_time_based_performance(matches),
            'strategy_effectiveness': self._analyze_strategy_effectiveness(matches),
            'performance_trends': self._analyze_performance_trends(matches),
            'recommendations': []
        }

        # Generate recommendations
        analysis['recommendations'] = self._generate_performance_recommendations(analysis)

        return analysis

    def analyze_match_patterns(self, matches: List[Dict]) -> Dict:
        """
        Analyze patterns in match data.

        Args:
            matches: List of match data

        Returns:
            Dict with pattern analysis
        """
        patterns = {
            'card_play_patterns': self._analyze_card_play_patterns(matches),
            'timing_patterns': self._analyze_timing_patterns(matches),
            'opponent_adaptation': self._analyze_opponent_adaptation(matches),
            'mistake_patterns': self._analyze_mistake_patterns(matches),
            'success_patterns': self._analyze_success_patterns(matches)
        }

        return patterns

    def predict_match_outcome(self, current_state: Dict, historical_matches: List[Dict]) -> Dict:
        """
        Predict match outcome based on current state and historical data.

        Args:
            current_state: Current match state
            historical_matches: Historical match data

        Returns:
            Dict with outcome prediction
        """
        # Simple prediction based on historical patterns
        similar_matches = self._find_similar_matches(current_state, historical_matches)

        if not similar_matches:
            return {'prediction': 'unknown', 'confidence': 0.0}

        win_rate = self._calculate_win_rate(similar_matches)
        confidence = min(len(similar_matches) / 50.0, 1.0)  # More matches = higher confidence

        prediction = 'win' if win_rate > 0.5 else 'loss'

        return {
            'prediction': prediction,
            'confidence': confidence,
            'win_probability': win_rate,
            'sample_size': len(similar_matches),
            'factors': self._identify_prediction_factors(current_state, similar_matches)
        }

    def identify_weaknesses(self, matches: List[Dict]) -> List[Dict]:
        """
        Identify performance weaknesses from match data.

        Args:
            matches: List of match data

        Returns:
            List of identified weaknesses
        """
        weaknesses = []

        # Analyze loss patterns
        losses = [m for m in matches if m.get('result') == 'loss']
        if losses:
            loss_analysis = self._analyze_loss_patterns(losses)
            weaknesses.extend(loss_analysis)

        # Analyze timing issues
        timing_issues = self._analyze_timing_weaknesses(matches)
        weaknesses.extend(timing_issues)

        # Analyze card performance
        card_issues = self._analyze_card_weaknesses(matches)
        weaknesses.extend(card_issues)

        return weaknesses

    def generate_match_report(self, matches: List[Dict], player_id: str = None) -> Dict:
        """
        Generate comprehensive match report.

        Args:
            matches: List of match data
            player_id: Specific player ID for personalized report

        Returns:
            Dict with comprehensive match report
        """
        report = {
            'summary': self.analyze_match_performance(matches),
            'patterns': self.analyze_match_patterns(matches),
            'weaknesses': self.identify_weaknesses(matches),
            'recommendations': [],
            'generated_at': datetime.now().isoformat()
        }

        # Combine all recommendations
        all_recommendations = []
        if 'recommendations' in report['summary']:
            all_recommendations.extend(report['summary']['recommendations'])

        # Add pattern-based recommendations
        pattern_recs = self._generate_pattern_recommendations(report['patterns'])
        all_recommendations.extend(pattern_recs)

        # Add weakness-based recommendations
        weakness_recs = self._generate_weakness_recommendations(report['weaknesses'])
        all_recommendations.extend(weakness_recs)

        report['recommendations'] = self._prioritize_recommendations(all_recommendations)

        return report

    def _calculate_win_rate(self, matches: List[Dict]) -> float:
        """Calculate win rate from matches."""
        if not matches:
            return 0.0

        wins = sum(1 for match in matches if match.get('result') == 'win')
        return wins / len(matches)

    def _calculate_avg_duration(self, matches: List[Dict]) -> float:
        """Calculate average match duration."""
        durations = [m.get('duration', 0) for m in matches if m.get('duration')]
        return statistics.mean(durations) if durations else 0.0

    def _analyze_trophy_changes(self, matches: List[Dict]) -> Dict:
        """Analyze trophy performance."""
        trophy_changes = [m.get('trophy_change', 0) for m in matches]

        return {
            'total_change': sum(trophy_changes),
            'avg_change': statistics.mean(trophy_changes) if trophy_changes else 0,
            'best_gain': max(trophy_changes) if trophy_changes else 0,
            'worst_loss': min(trophy_changes) if trophy_changes else 0,
            'volatility': statistics.stdev(trophy_changes) if len(trophy_changes) > 1 else 0
        }

    def _analyze_deck_performance(self, matches: List[Dict]) -> Dict:
        """Analyze performance by deck."""
        deck_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'trophies': 0})

        for match in matches:
            deck_id = match.get('deck_id', 'unknown')
            deck_stats[deck_id]['games'] += 1
            if match.get('result') == 'win':
                deck_stats[deck_id]['wins'] += 1
            deck_stats[deck_id]['trophies'] += match.get('trophy_change', 0)

        # Calculate win rates and sort
        deck_performance = []
        for deck_id, stats in deck_stats.items():
            win_rate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            avg_trophies = stats['trophies'] / stats['games'] if stats['games'] > 0 else 0

            deck_performance.append({
                'deck_id': deck_id,
                'games': stats['games'],
                'win_rate': win_rate,
                'avg_trophies': avg_trophies,
                'total_trophies': stats['trophies']
            })

        deck_performance.sort(key=lambda x: x['win_rate'], reverse=True)

        return {
            'deck_performance': deck_performance,
            'best_deck': deck_performance[0] if deck_performance else None,
            'worst_deck': deck_performance[-1] if deck_performance else None
        }

    def _analyze_time_based_performance(self, matches: List[Dict]) -> Dict:
        """Analyze performance by time of day."""
        hourly_stats = defaultdict(lambda: {'games': 0, 'wins': 0})

        for match in matches:
            timestamp = match.get('timestamp')
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    hour = dt.hour
                    hourly_stats[hour]['games'] += 1
                    if match.get('result') == 'win':
                        hourly_stats[hour]['wins'] += 1
                except (ValueError, TypeError):
                    continue

        time_performance = []
        for hour in range(24):
            stats = hourly_stats[hour]
            win_rate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            time_performance.append({
                'hour': hour,
                'games': stats['games'],
                'win_rate': win_rate
            })

        return {
            'hourly_performance': time_performance,
            'best_hour': max(time_performance, key=lambda x: x['win_rate']) if time_performance else None,
            'worst_hour': min(time_performance, key=lambda x: x['win_rate']) if time_performance else None
        }

    def _analyze_strategy_effectiveness(self, matches: List[Dict]) -> Dict:
        """Analyze effectiveness of different strategies."""
        strategy_stats = defaultdict(lambda: {'games': 0, 'wins': 0})

        for match in matches:
            strategy = match.get('strategy_used', 'unknown')
            strategy_stats[strategy]['games'] += 1
            if match.get('result') == 'win':
                strategy_stats[strategy]['wins'] += 1

        strategy_performance = []
        for strategy, stats in strategy_stats.items():
            win_rate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            strategy_performance.append({
                'strategy': strategy,
                'games': stats['games'],
                'win_rate': win_rate
            })

        strategy_performance.sort(key=lambda x: x['win_rate'], reverse=True)

        return {
            'strategy_performance': strategy_performance,
            'most_effective': strategy_performance[0] if strategy_performance else None
        }

    def _analyze_performance_trends(self, matches: List[Dict]) -> Dict:
        """Analyze performance trends over time."""
        if len(matches) < 5:
            return {'trend': 'insufficient_data'}

        # Sort matches by timestamp
        sorted_matches = sorted(matches, key=lambda x: x.get('timestamp', 0))

        # Calculate rolling win rate
        window_size = min(20, len(sorted_matches) // 4)
        rolling_win_rates = []

        for i in range(window_size, len(sorted_matches) + 1):
            window = sorted_matches[i - window_size:i]
            win_rate = self._calculate_win_rate(window)
            rolling_win_rates.append(win_rate)

        if len(rolling_win_rates) >= 2:
            trend = 'improving' if rolling_win_rates[-1] > rolling_win_rates[0] else 'declining'
            change = rolling_win_rates[-1] - rolling_win_rates[0]
        else:
            trend = 'stable'
            change = 0

        return {
            'trend': trend,
            'change': change,
            'current_win_rate': rolling_win_rates[-1] if rolling_win_rates else 0,
            'initial_win_rate': rolling_win_rates[0] if rolling_win_rates else 0,
            'volatility': statistics.stdev(rolling_win_rates) if len(rolling_win_rates) > 1 else 0
        }

    def _analyze_card_play_patterns(self, matches: List[Dict]) -> Dict:
        """Analyze patterns in card play timing and success."""
        card_patterns = defaultdict(lambda: {
            'plays': 0, 'successes': 0, 'avg_timing': 0, 'timings': []
        })

        for match in matches:
            actions = match.get('actions', [])
            for action in actions:
                if action.get('action_type') == 'play_card':
                    card_id = action.get('card_id')
                    if card_id:
                        card_patterns[card_id]['plays'] += 1
                        if action.get('success'):
                            card_patterns[card_id]['successes'] += 1

                        timing = action.get('timing', 0)
                        card_patterns[card_id]['timings'].append(timing)

        # Calculate averages and success rates
        for card_id, data in card_patterns.items():
            if data['plays'] > 0:
                data['success_rate'] = data['successes'] / data['plays']
            if data['timings']:
                data['avg_timing'] = statistics.mean(data['timings'])

        return dict(card_patterns)

    def _analyze_timing_patterns(self, matches: List[Dict]) -> Dict:
        """Analyze timing patterns in matches."""
        timing_stats = {
            'early_game_actions': 0,
            'mid_game_actions': 0,
            'late_game_actions': 0,
            'rush_downs': 0,
            'slow_rolls': 0
        }

        for match in matches:
            duration = match.get('duration', 180)  # Default 3 minutes
            actions = match.get('actions', [])

            for action in actions:
                game_time = action.get('game_time', 0)
                relative_time = game_time / duration

                if relative_time < 0.3:
                    timing_stats['early_game_actions'] += 1
                elif relative_time < 0.7:
                    timing_stats['mid_game_actions'] += 1
                else:
                    timing_stats['late_game_actions'] += 1

            # Classify playstyle
            if timing_stats['early_game_actions'] > timing_stats['late_game_actions'] * 1.5:
                timing_stats['rush_downs'] += 1
            elif timing_stats['late_game_actions'] > timing_stats['early_game_actions'] * 1.5:
                timing_stats['slow_rolls'] += 1

        return timing_stats

    def _analyze_opponent_adaptation(self, matches: List[Dict]) -> Dict:
        """Analyze how well the bot adapts to different opponents."""
        opponent_performance = defaultdict(lambda: {'games': 0, 'wins': 0, 'avg_trophies': 0})

        for match in matches:
            opponent_trophies = match.get('opponent_trophies', 0)
            trophy_bracket = self._get_trophy_bracket(opponent_trophies)

            opponent_performance[trophy_bracket]['games'] += 1
            opponent_performance[trophy_bracket]['avg_trophies'] += opponent_trophies
            if match.get('result') == 'win':
                opponent_performance[trophy_bracket]['wins'] += 1

        # Calculate averages
        for bracket, stats in opponent_performance.items():
            if stats['games'] > 0:
                stats['win_rate'] = stats['wins'] / stats['games']
                stats['avg_trophies'] = stats['avg_trophies'] / stats['games']

        return dict(opponent_performance)

    def _analyze_mistake_patterns(self, matches: List[Dict]) -> List[Dict]:
        """Analyze patterns in mistakes made during matches."""
        mistakes = []

        for match in matches:
            actions = match.get('actions', [])
            for action in actions:
                if not action.get('success', True):
                    mistake = {
                        'match_id': match.get('match_id'),
                        'action_type': action.get('action_type'),
                        'card_id': action.get('card_id'),
                        'timing': action.get('timing'),
                        'reason': action.get('failure_reason', 'unknown')
                    }
                    mistakes.append(mistake)

        # Group by type
        mistake_types = Counter(m['action_type'] for m in mistakes)

        return [
            {'type': mistake_type, 'count': count, 'frequency': count / len(matches)}
            for mistake_type, count in mistake_types.most_common()
        ]

    def _analyze_success_patterns(self, matches: List[Dict]) -> Dict:
        """Analyze patterns that lead to successful outcomes."""
        win_factors = defaultdict(int)
        loss_factors = defaultdict(int)

        for match in matches:
            is_win = match.get('result') == 'win'
            factors = self._extract_success_factors(match)

            for factor in factors:
                if is_win:
                    win_factors[factor] += 1
                else:
                    loss_factors[factor] += 1

        # Calculate factor importance
        success_patterns = {}
        all_factors = set(win_factors.keys()) | set(loss_factors.keys())

        for factor in all_factors:
            wins = win_factors[factor]
            losses = loss_factors[factor]
            total = wins + losses

            if total > 0:
                win_rate = wins / total
                success_patterns[factor] = {
                    'win_rate': win_rate,
                    'occurrences': total,
                    'importance': abs(win_rate - 0.5) * total  # Importance score
                }

        return success_patterns

    def _find_similar_matches(self, current_state: Dict, historical_matches: List[Dict]) -> List[Dict]:
        """Find matches similar to current state."""
        similar_matches = []

        current_deck = current_state.get('deck_id')
        current_opponent_level = self._get_trophy_bracket(current_state.get('opponent_trophies', 0))

        for match in historical_matches:
            if (match.get('deck_id') == current_deck and
                self._get_trophy_bracket(match.get('opponent_trophies', 0)) == current_opponent_level):
                similar_matches.append(match)

        return similar_matches

    def _identify_prediction_factors(self, current_state: Dict, similar_matches: List[Dict]) -> List[str]:
        """Identify factors influencing prediction."""
        factors = []

        win_rate = self._calculate_win_rate(similar_matches)
        if win_rate > 0.6:
            factors.append("Strong historical performance")
        elif win_rate < 0.4:
            factors.append("Weak historical performance")

        sample_size = len(similar_matches)
        if sample_size < 5:
            factors.append("Limited historical data")

        return factors

    def _analyze_loss_patterns(self, losses: List[Dict]) -> List[Dict]:
        """Analyze patterns in losses."""
        weaknesses = []

        # Common loss reasons
        loss_reasons = Counter()
        for loss in losses:
            reason = loss.get('loss_reason', 'unknown')
            loss_reasons[reason] += 1

        for reason, count in loss_reasons.most_common(3):
            weaknesses.append({
                'type': 'loss_pattern',
                'description': f"Frequent losses due to: {reason}",
                'frequency': count / len(losses),
                'severity': 'high' if count / len(losses) > 0.3 else 'medium'
            })

        return weaknesses

    def _analyze_timing_weaknesses(self, matches: List[Dict]) -> List[Dict]:
        """Analyze timing-related weaknesses."""
        weaknesses = []

        # Check for rushed plays
        rushed_plays = 0
        total_plays = 0

        for match in matches:
            actions = match.get('actions', [])
            for action in actions:
                if action.get('action_type') == 'play_card':
                    total_plays += 1
                    if action.get('timing', 0) < 0.5:  # Too early
                        rushed_plays += 1

        if total_plays > 0:
            rush_rate = rushed_plays / total_plays
            if rush_rate > 0.2:
                weaknesses.append({
                    'type': 'timing',
                    'description': "Too many rushed card plays",
                    'frequency': rush_rate,
                    'severity': 'medium'
                })

        return weaknesses

    def _analyze_card_weaknesses(self, matches: List[Dict]) -> List[Dict]:
        """Analyze card-specific weaknesses."""
        weaknesses = []

        card_performance = defaultdict(lambda: {'plays': 0, 'successes': 0})

        for match in matches:
            actions = match.get('actions', [])
            for action in actions:
                if action.get('action_type') == 'play_card':
                    card_id = action.get('card_id')
                    if card_id:
                        card_performance[card_id]['plays'] += 1
                        if action.get('success'):
                            card_performance[card_id]['successes'] += 1

        for card_id, stats in card_performance.items():
            if stats['plays'] >= 5:  # Minimum plays for analysis
                success_rate = stats['successes'] / stats['plays']
                if success_rate < 0.3:  # Poor performance
                    weaknesses.append({
                        'type': 'card_performance',
                        'description': f"Poor performance with card: {card_id}",
                        'success_rate': success_rate,
                        'plays': stats['plays'],
                        'severity': 'high' if success_rate < 0.2 else 'medium'
                    })

        return weaknesses

    def _generate_performance_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on performance analysis."""
        recommendations = []

        win_rate = analysis.get('win_rate', 0)
        if win_rate < 0.5:
            recommendations.append("Focus on improving overall win rate through deck optimization")

        deck_performance = analysis.get('deck_performance', {})
        best_deck = deck_performance.get('best_deck')
        if best_deck and best_deck['games'] >= 10:
            recommendations.append(f"Prioritize using high-performing deck: {best_deck['deck_id']}")

        trends = analysis.get('performance_trends', {})
        if trends.get('trend') == 'declining':
            recommendations.append("Address declining performance trend - review recent changes")

        return recommendations

    def _generate_pattern_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations based on pattern analysis."""
        recommendations = []

        timing_patterns = patterns.get('timing_patterns', {})
        if timing_patterns.get('rush_downs', 0) > timing_patterns.get('slow_rolls', 0) * 2:
            recommendations.append("Reduce aggressive playstyle - focus on more balanced timing")

        return recommendations

    def _generate_weakness_recommendations(self, weaknesses: List[Dict]) -> List[str]:
        """Generate recommendations based on identified weaknesses."""
        recommendations = []

        for weakness in weaknesses:
            if weakness['type'] == 'card_performance':
                recommendations.append(f"Review and possibly replace underperforming card: {weakness.get('card_id', 'unknown')}")
            elif weakness['type'] == 'timing':
                recommendations.append("Work on timing discipline - avoid rushed plays")

        return recommendations

    def _prioritize_recommendations(self, recommendations: List[str]) -> List[Dict]:
        """Prioritize recommendations by importance."""
        # Simple prioritization - could be enhanced with ML
        prioritized = []
        for rec in recommendations:
            priority = 'medium'
            if 'high' in rec.lower() or 'critical' in rec.lower():
                priority = 'high'
            elif 'review' in rec.lower() or 'focus' in rec.lower():
                priority = 'medium'
            else:
                priority = 'low'

            prioritized.append({
                'recommendation': rec,
                'priority': priority
            })

        return sorted(prioritized, key=lambda x: ['high', 'medium', 'low'].index(x['priority']))

    def _get_trophy_bracket(self, trophies: int) -> str:
        """Get trophy bracket for analysis."""
        if trophies < 1000:
            return 'bronze'
        elif trophies < 2000:
            return 'silver'
        elif trophies < 3000:
            return 'gold'
        elif trophies < 4000:
            return 'master'
        elif trophies < 5000:
            return 'champion'
        else:
            return 'grand_champion'

    def _extract_success_factors(self, match: Dict) -> List[str]:
        """Extract factors that contribute to match success."""
        factors = []

        # Strategy factor
        if match.get('strategy_used'):
            factors.append(f"strategy_{match['strategy_used']}")

        # Deck factor
        if match.get('deck_id'):
            factors.append(f"deck_{match['deck_id']}")

        # Timing factor
        duration = match.get('duration', 180)
        if duration < 120:
            factors.append('fast_match')
        elif duration > 240:
            factors.append('long_match')

        # Opponent level
        opponent_level = self._get_trophy_bracket(match.get('opponent_trophies', 0))
        factors.append(f"opponent_{opponent_level}")

        return factors
