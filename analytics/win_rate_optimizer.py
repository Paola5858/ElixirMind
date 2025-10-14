"""
Win Rate Optimizer: Optimizes strategies and configurations for maximum win rate.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import statistics
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

class WinRateOptimizer:
    """
    Optimizes bot configuration and strategies to maximize win rate.
    Uses machine learning to identify optimal settings and predict outcomes.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Optimization settings
        self.min_samples_for_training = self.config.get('min_samples', 100)
        self.test_size = self.config.get('test_size', 0.2)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.75)

        # ML models
        self.win_prediction_model = None
        self.strategy_optimizer = None

        # Optimization data
        self.optimization_history = []
        self.factor_importance = {}

        logger.info("Win Rate Optimizer initialized")

    def optimize_win_rate(self, matches: List[Dict], current_config: Dict = None) -> Dict:
        """
        Optimize configuration for maximum win rate.

        Args:
            matches: Historical match data
            current_config: Current bot configuration

        Returns:
            Dict with optimization recommendations
        """
        if len(matches) < self.min_samples_for_training:
            return {'error': f'Need at least {self.min_samples_for_training} matches for optimization'}

        # Analyze current performance
        current_performance = self._analyze_current_performance(matches)

        # Train optimization models
        self._train_win_prediction_model(matches)

        # Identify key factors
        key_factors = self._identify_key_success_factors(matches)

        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(
            current_performance, key_factors, current_config or {}
        )

        # Predict potential improvements
        predicted_improvements = self._predict_improvement_potential(recommendations, matches)

        result = {
            'current_performance': current_performance,
            'key_factors': key_factors,
            'recommendations': recommendations,
            'predicted_improvements': predicted_improvements,
            'optimization_confidence': self._calculate_optimization_confidence(matches),
            'implementation_priority': self._prioritize_recommendations(recommendations)
        }

        # Store optimization attempt
        self.optimization_history.append({
            'timestamp': time.time(),
            'matches_analyzed': len(matches),
            'current_win_rate': current_performance['win_rate'],
            'recommendations_count': len(recommendations),
            'expected_improvement': predicted_improvements.get('expected_win_rate_gain', 0)
        })

        return result

    def find_optimal_deck_configuration(self, matches: List[Dict], available_cards: List[str] = None) -> Dict:
        """
        Find optimal deck configuration for maximum win rate.

        Args:
            matches: Historical match data
            available_cards: List of available cards

        Returns:
            Dict with optimal deck recommendations
        """
        # Analyze deck performance
        deck_analysis = self._analyze_deck_performance(matches)

        # Identify card synergies
        card_synergies = self._analyze_card_synergies(matches)

        # Generate deck recommendations
        deck_recommendations = self._generate_deck_recommendations(
            deck_analysis, card_synergies, available_cards
        )

        # Predict deck performance
        performance_predictions = self._predict_deck_performance(deck_recommendations, matches)

        result = {
            'current_best_deck': deck_analysis.get('best_performing_deck'),
            'recommended_decks': deck_recommendations,
            'card_synergies': card_synergies,
            'performance_predictions': performance_predictions,
            'deck_diversity_score': self._calculate_deck_diversity(matches)
        }

        return result

    def optimize_strategy_parameters(self, matches: List[Dict], strategy_config: Dict = None) -> Dict:
        """
        Optimize strategy parameters for better performance.

        Args:
            matches: Historical match data
            strategy_config: Current strategy configuration

        Returns:
            Dict with optimized strategy parameters
        """
        strategy_config = strategy_config or {}

        # Analyze strategy performance
        strategy_performance = self._analyze_strategy_performance(matches)

        # Identify optimal parameter ranges
        parameter_optimization = self._optimize_strategy_parameters(matches, strategy_config)

        # Generate parameter recommendations
        parameter_recommendations = self._generate_parameter_recommendations(
            strategy_performance, parameter_optimization
        )

        result = {
            'current_strategy_performance': strategy_performance,
            'parameter_optimization': parameter_optimization,
            'recommended_parameters': parameter_recommendations,
            'expected_improvements': self._predict_parameter_improvements(parameter_recommendations, matches),
            'parameter_sensitivity': self._analyze_parameter_sensitivity(matches)
        }

        return result

    def predict_match_outcome_probability(self, match_features: Dict, matches: List[Dict]) -> Dict:
        """
        Predict probability of winning a match with given features.

        Args:
            match_features: Features of the upcoming match
            matches: Historical match data for training

        Returns:
            Dict with outcome prediction
        """
        if not self.win_prediction_model:
            self._train_win_prediction_model(matches)

        if not self.win_prediction_model:
            return {'error': 'Could not train prediction model'}

        # Extract features
        features = self._extract_match_features(match_features)

        if not features:
            return {'error': 'Could not extract features from match data'}

        # Make prediction
        win_probability = self.win_prediction_model.predict_proba([features])[0][1]

        # Calculate confidence
        confidence = self._calculate_prediction_confidence(features, matches)

        # Identify key factors
        key_factors = self._identify_win_factors(match_features, win_probability)

        result = {
            'win_probability': win_probability,
            'loss_probability': 1 - win_probability,
            'confidence': confidence,
            'key_factors': key_factors,
            'recommendations': self._generate_pre_match_recommendations(win_probability, key_factors)
        }

        return result

    def analyze_performance_trends(self, matches: List[Dict], window_days: int = 7) -> Dict:
        """
        Analyze performance trends over time.

        Args:
            matches: Historical match data
            window_days: Analysis window in days

        Returns:
            Dict with trend analysis
        """
        # Group matches by time windows
        time_windows = self._group_matches_by_time(matches, window_days)

        # Calculate performance metrics for each window
        window_performance = []
        for window_start, window_matches in time_windows.items():
            if len(window_matches) >= 5:  # Minimum matches per window
                performance = self._calculate_window_performance(window_matches)
                performance['window_start'] = window_start
                window_performance.append(performance)

        # Analyze trends
        trends = self._analyze_performance_trends(window_performance)

        # Identify concerning patterns
        concerning_patterns = self._identify_concerning_patterns(window_performance)

        result = {
            'window_performance': window_performance,
            'trends': trends,
            'concerning_patterns': concerning_patterns,
            'trend_stability': self._calculate_trend_stability(window_performance),
            'recommendations': self._generate_trend_recommendations(trends, concerning_patterns)
        }

        return result

    def _analyze_current_performance(self, matches: List[Dict]) -> Dict:
        """Analyze current overall performance."""
        wins = sum(1 for match in matches if match.get('result') == 'win')
        total_matches = len(matches)

        win_rate = wins / total_matches if total_matches > 0 else 0

        # Calculate recent performance (last 50 matches)
        recent_matches = matches[-50:] if len(matches) > 50 else matches
        recent_wins = sum(1 for match in recent_matches if match.get('result') == 'win')
        recent_win_rate = recent_wins / len(recent_matches) if recent_matches else 0

        # Performance by different factors
        performance_by_deck = self._calculate_performance_by_factor(matches, 'deck_id')
        performance_by_strategy = self._calculate_performance_by_factor(matches, 'strategy_used')
        performance_by_time = self._calculate_performance_by_time(matches)

        return {
            'win_rate': win_rate,
            'recent_win_rate': recent_win_rate,
            'total_matches': total_matches,
            'performance_by_deck': performance_by_deck,
            'performance_by_strategy': performance_by_strategy,
            'performance_by_time': performance_by_time,
            'consistency_score': self._calculate_consistency_score(matches)
        }

    def _train_win_prediction_model(self, matches: List[Dict]):
        """Train machine learning model for win prediction."""
        if len(matches) < self.min_samples_for_training:
            logger.warning("Insufficient data for training win prediction model")
            return

        # Prepare training data
        X = []  # Features
        y = []  # Target (1 for win, 0 for loss)

        for match in matches:
            features = self._extract_match_features(match)
            if features:
                X.append(features)
                y.append(1 if match.get('result') == 'win' else 0)

        if len(X) < 20:
            logger.warning("Insufficient valid training samples")
            return

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=42
        )

        # Train model
        self.win_prediction_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        self.win_prediction_model.fit(X_train, y_train)

        # Evaluate model
        y_pred = self.win_prediction_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"Trained win prediction model with accuracy: {accuracy:.3f}")

        # Store feature importance
        self.factor_importance = dict(zip(
            ['opponent_level', 'deck_size', 'strategy_score', 'time_factor', 'confidence'],
            self.win_prediction_model.feature_importances_
        ))

    def _extract_match_features(self, match: Dict) -> Optional[List[float]]:
        """Extract features from match data for ML model."""
        try:
            features = [
                match.get('opponent_trophies', 0) / 5000,  # Normalized opponent level
                len(match.get('deck_used', [])) / 8,       # Deck size factor
                self._calculate_strategy_score(match),     # Strategy effectiveness score
                self._calculate_time_factor(match),        # Time of day factor
                match.get('confidence_score', 0.5),        # AI confidence score
            ]
            return features
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None

    def _identify_key_success_factors(self, matches: List[Dict]) -> Dict:
        """Identify key factors that contribute to success."""
        factors = {
            'deck_performance': self._analyze_factor_impact(matches, 'deck_id'),
            'strategy_effectiveness': self._analyze_factor_impact(matches, 'strategy_used'),
            'timing_importance': self._analyze_timing_impact(matches),
            'card_synergies': self._analyze_card_impact(matches),
            'opponent_level_impact': self._analyze_opponent_level_impact(matches)
        }

        return factors

    def _generate_optimization_recommendations(self, current_performance: Dict,
                                             key_factors: Dict, current_config: Dict) -> List[Dict]:
        """Generate optimization recommendations."""
        recommendations = []

        # Deck recommendations
        deck_perf = current_performance.get('performance_by_deck', {})
        if deck_perf:
            best_deck = max(deck_perf.items(), key=lambda x: x[1]['win_rate'])
            if best_deck[1]['win_rate'] > current_performance['win_rate'] * 1.1:
                recommendations.append({
                    'type': 'deck',
                    'priority': 'high',
                    'description': f"Switch to higher performing deck: {best_deck[0]}",
                    'expected_improvement': best_deck[1]['win_rate'] - current_performance['win_rate'],
                    'confidence': min(best_deck[1]['games'] / 50, 1.0)
                })

        # Strategy recommendations
        strategy_perf = current_performance.get('performance_by_strategy', {})
        if strategy_perf:
            best_strategy = max(strategy_perf.items(), key=lambda x: x[1]['win_rate'])
            if best_strategy[1]['win_rate'] > current_performance['win_rate'] * 1.05:
                recommendations.append({
                    'type': 'strategy',
                    'priority': 'medium',
                    'description': f"Adopt higher performing strategy: {best_strategy[0]}",
                    'expected_improvement': best_strategy[1]['win_rate'] - current_performance['win_rate'],
                    'confidence': min(best_strategy[1]['games'] / 30, 1.0)
                })

        # Timing recommendations
        time_perf = current_performance.get('performance_by_time', {})
        if time_perf:
            best_time = max(time_perf.items(), key=lambda x: x[1]['win_rate'])
            if best_time[1]['win_rate'] > current_performance['win_rate'] * 1.15:
                recommendations.append({
                    'type': 'timing',
                    'priority': 'low',
                    'description': f"Optimize play timing to {best_time[0]}",
                    'expected_improvement': best_time[1]['win_rate'] - current_performance['win_rate'],
                    'confidence': min(best_time[1]['games'] / 20, 1.0)
                })

        return recommendations

    def _predict_improvement_potential(self, recommendations: List[Dict], matches: List[Dict]) -> Dict:
        """Predict potential improvements from recommendations."""
        if not recommendations:
            return {'expected_win_rate_gain': 0, 'confidence': 0}

        # Calculate weighted expected improvement
        total_expected_gain = 0
        total_confidence = 0

        for rec in recommendations:
            gain = rec.get('expected_improvement', 0)
            confidence = rec.get('confidence', 0)
            priority_weight = {'high': 1.0, 'medium': 0.7, 'low': 0.4}.get(rec.get('priority', 'medium'), 0.7)

            weighted_gain = gain * confidence * priority_weight
            total_expected_gain += weighted_gain
            total_confidence += confidence

        avg_confidence = total_confidence / len(recommendations) if recommendations else 0

        return {
            'expected_win_rate_gain': total_expected_gain,
            'confidence': avg_confidence,
            'implementation_complexity': self._assess_implementation_complexity(recommendations)
        }

    def _calculate_optimization_confidence(self, matches: List[Dict]) -> float:
        """Calculate confidence in optimization recommendations."""
        if len(matches) < 50:
            return 0.3

        # Base confidence on data quality and quantity
        data_quality = min(len(matches) / 200, 1.0)  # More data = higher confidence
        recency_factor = self._calculate_data_recency(matches)

        return (data_quality * 0.7) + (recency_factor * 0.3)

    def _prioritize_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Prioritize recommendations by impact and ease of implementation."""
        priority_scores = []
        for rec in recommendations:
            impact_score = rec.get('expected_improvement', 0) * 100
            ease_score = {'high': 0.3, 'medium': 0.6, 'low': 1.0}.get(rec.get('priority', 'medium'), 0.6)
            confidence_score = rec.get('confidence', 0.5)

            total_score = impact_score * ease_score * confidence_score
            priority_scores.append((rec, total_score))

        # Sort by priority score
        priority_scores.sort(key=lambda x: x[1], reverse=True)

        # Add priority ranking
        prioritized = []
        for i, (rec, score) in enumerate(priority_scores):
            rec_copy = rec.copy()
            rec_copy['priority_rank'] = i + 1
            rec_copy['priority_score'] = score
            prioritized.append(rec_copy)

        return prioritized

    def _analyze_deck_performance(self, matches: List[Dict]) -> Dict:
        """Analyze performance by deck."""
        deck_stats = defaultdict(lambda: {'wins': 0, 'games': 0})

        for match in matches:
            deck_id = match.get('deck_id')
            if deck_id:
                deck_stats[deck_id]['games'] += 1
                if match.get('result') == 'win':
                    deck_stats[deck_id]['wins'] += 1

        deck_performance = {}
        for deck_id, stats in deck_stats.items():
            if stats['games'] >= 5:
                deck_performance[deck_id] = {
                    'win_rate': stats['wins'] / stats['games'],
                    'games': stats['games'],
                    'confidence': min(stats['games'] / 50, 1.0)
                }

        best_deck = max(deck_performance.items(), key=lambda x: x[1]['win_rate']) if deck_performance else None

        return {
            'deck_performance': deck_performance,
            'best_performing_deck': best_deck[0] if best_deck else None,
            'performance_variance': statistics.stdev([d['win_rate'] for d in deck_performance.values()]) if len(deck_performance) > 1 else 0
        }

    def _analyze_card_synergies(self, matches: List[Dict]) -> Dict:
        """Analyze card synergies and combinations."""
        # This would require more complex analysis of card combinations
        # For now, return a placeholder
        return {
            'top_synergies': [],
            'card_importance': {},
            'synergy_score': 0.5
        }

    def _generate_deck_recommendations(self, deck_analysis: Dict, card_synergies: Dict,
                                     available_cards: List[str] = None) -> List[Dict]:
        """Generate deck configuration recommendations."""
        recommendations = []

        best_deck = deck_analysis.get('best_performing_deck')
        if best_deck:
            recommendations.append({
                'deck_type': 'optimized',
                'base_deck': best_deck,
                'expected_win_rate': deck_analysis['deck_performance'][best_deck]['win_rate'],
                'confidence': deck_analysis['deck_performance'][best_deck]['confidence']
            })

        return recommendations

    def _predict_deck_performance(self, deck_recommendations: List[Dict], matches: List[Dict]) -> Dict:
        """Predict performance of recommended decks."""
        predictions = {}

        for rec in deck_recommendations:
            base_performance = rec.get('expected_win_rate', 0.5)
            # Add some prediction logic here
            predictions[rec.get('deck_type', 'unknown')] = {
                'predicted_win_rate': base_performance,
                'confidence': rec.get('confidence', 0.5)
            }

        return predictions

    def _calculate_deck_diversity(self, matches: List[Dict]) -> float:
        """Calculate deck diversity score."""
        decks_used = set(match.get('deck_id') for match in matches if match.get('deck_id'))
        total_matches = len(matches)

        if total_matches == 0:
            return 0

        # Diversity based on number of different decks used
        diversity = len(decks_used) / min(total_matches * 0.1, 10)  # Normalize
        return min(diversity, 1.0)

    def _analyze_strategy_performance(self, matches: List[Dict]) -> Dict:
        """Analyze performance by strategy."""
        return self._calculate_performance_by_factor(matches, 'strategy_used')

    def _optimize_strategy_parameters(self, matches: List[Dict], strategy_config: Dict) -> Dict:
        """Optimize strategy parameters."""
        # This would involve parameter tuning
        # For now, return placeholder
        return {
            'optimal_parameters': {},
            'parameter_ranges': {},
            'expected_improvement': 0
        }

    def _generate_parameter_recommendations(self, strategy_performance: Dict,
                                          parameter_optimization: Dict) -> List[Dict]:
        """Generate parameter optimization recommendations."""
        return []

    def _predict_parameter_improvements(self, parameter_recommendations: List[Dict],
                                      matches: List[Dict]) -> Dict:
        """Predict improvements from parameter changes."""
        return {'expected_gain': 0, 'confidence': 0}

    def _analyze_parameter_sensitivity(self, matches: List[Dict]) -> Dict:
        """Analyze how sensitive performance is to parameter changes."""
        return {}

    def _calculate_prediction_confidence(self, features: List[float], matches: List[Dict]) -> float:
        """Calculate confidence in win prediction."""
        # Base confidence on model accuracy and feature similarity
        return 0.7  # Placeholder

    def _identify_win_factors(self, match_features: Dict, win_probability: float) -> List[Dict]:
        """Identify key factors affecting win probability."""
        return []

    def _generate_pre_match_recommendations(self, win_probability: float,
                                          key_factors: List[Dict]) -> List[str]:
        """Generate pre-match recommendations."""
        return []

    def _group_matches_by_time(self, matches: List[Dict], window_days: int) -> Dict:
        """Group matches by time windows."""
        windows = defaultdict(list)

        for match in matches:
            timestamp = match.get('timestamp', 0)
            window_start = timestamp - (timestamp % (window_days * 24 * 3600))
            windows[window_start].append(match)

        return windows

    def _calculate_window_performance(self, window_matches: List[Dict]) -> Dict:
        """Calculate performance metrics for a time window."""
        wins = sum(1 for match in window_matches if match.get('result') == 'win')
        total = len(window_matches)

        return {
            'win_rate': wins / total if total > 0 else 0,
            'total_matches': total,
            'avg_trophy_change': statistics.mean([m.get('trophy_change', 0) for m in window_matches]) if window_matches else 0
        }

    def _analyze_performance_trends(self, window_performance: List[Dict]) -> Dict:
        """Analyze performance trends over time."""
        if len(window_performance) < 2:
            return {'trend': 'insufficient_data'}

        win_rates = [w['win_rate'] for w in window_performance]
        trend = 'improving' if win_rates[-1] > win_rates[0] else 'declining'

        return {
            'trend': trend,
            'change': win_rates[-1] - win_rates[0],
            'volatility': statistics.stdev(win_rates) if len(win_rates) > 1 else 0
        }

    def _identify_concerning_patterns(self, window_performance: List[Dict]) -> List[Dict]:
        """Identify concerning performance patterns."""
        patterns = []

        if len(window_performance) >= 3:
            recent_rates = [w['win_rate'] for w in window_performance[-3:]]
            if all(rate < 0.4 for rate in recent_rates):
                patterns.append({
                    'type': 'consistently_low_performance',
                    'severity': 'high',
                    'description': 'Win rate consistently below 40% in recent periods'
                })

        return patterns

    def _calculate_trend_stability(self, window_performance: List[Dict]) -> float:
        """Calculate stability of performance trends."""
        if len(window_performance) < 2:
            return 0

        win_rates = [w['win_rate'] for w in window_performance]
        return 1 - (statistics.stdev(win_rates) if len(win_rates) > 1 else 0)

    def _generate_trend_recommendations(self, trends: Dict, patterns: List[Dict]) -> List[str]:
        """Generate recommendations based on trend analysis."""
        recommendations = []

        if trends.get('trend') == 'declining':
            recommendations.append("Address declining performance trend - review recent changes")

        for pattern in patterns:
            if pattern['type'] == 'consistently_low_performance':
                recommendations.append("Investigate causes of consistently low performance")

        return recommendations

    def _calculate_performance_by_factor(self, matches: List[Dict], factor: str) -> Dict:
        """Calculate performance grouped by a factor."""
        factor_stats = defaultdict(lambda: {'wins': 0, 'games': 0})

        for match in matches:
            factor_value = match.get(factor)
            if factor_value:
                factor_stats[factor_value]['games'] += 1
                if match.get('result') == 'win':
                    factor_stats[factor_value]['wins'] += 1

        performance = {}
        for value, stats in factor_stats.items():
            if stats['games'] >= 3:
                performance[value] = {
                    'win_rate': stats['wins'] / stats['games'],
                    'games': stats['games']
                }

        return performance

    def _calculate_performance_by_time(self, matches: List[Dict]) -> Dict:
        """Calculate performance by time of day."""
        time_stats = defaultdict(lambda: {'wins': 0, 'games': 0})

        for match in matches:
            timestamp = match.get('timestamp', 0)
            hour = datetime.fromtimestamp(timestamp).hour
            time_stats[hour]['games'] += 1
            if match.get('result') == 'win':
                time_stats[hour]['wins'] += 1

        performance = {}
        for hour, stats in time_stats.items():
            if stats['games'] >= 3:
                performance[hour] = {
                    'win_rate': stats['wins'] / stats['games'],
                    'games': stats['games']
                }

        return performance

    def _calculate_consistency_score(self, matches: List[Dict]) -> float:
        """Calculate performance consistency score."""
        if len(matches) < 10:
            return 0

        # Group by recent periods
        recent_matches = matches[-50:] if len(matches) > 50 else matches
        win_rates = []

        # Calculate win rate in sliding windows
        window_size = 10
        for i in range(len(recent_matches) - window_size + 1):
            window = recent_matches[i:i + window_size]
            wins = sum(1 for m in window if m.get('result') == 'win')
            win_rates.append(wins / window_size)

        if len(win_rates) > 1:
            consistency = 1 - statistics.stdev(win_rates)
            return max(0, consistency)

        return 0.5

    def _calculate_strategy_score(self, match: Dict) -> float:
        """Calculate strategy effectiveness score."""
        # Placeholder implementation
        return match.get('confidence_score', 0.5)

    def _calculate_time_factor(self, match: Dict) -> float:
        """Calculate time-based factor."""
        timestamp = match.get('timestamp', time.time())
        hour = datetime.fromtimestamp(timestamp).hour

        # Optimal hours (evening)
        if 18 <= hour <= 23:
            return 1.0
        elif 12 <= hour <= 17:
            return 0.8
        else:
            return 0.6

    def _analyze_factor_impact(self, matches: List[Dict], factor: str) -> Dict:
        """Analyze impact of a factor on performance."""
        return self._calculate_performance_by_factor(matches, factor)

    def _analyze_timing_impact(self, matches: List[Dict]) -> Dict:
        """Analyze timing impact on performance."""
        return self._calculate_performance_by_time(matches)

    def _analyze_card_impact(self, matches: List[Dict]) -> Dict:
        """Analyze card impact on performance."""
        return {}

    def _analyze_opponent_level_impact(self, matches: List[Dict]) -> Dict:
        """Analyze opponent level impact."""
        return {}

    def _calculate_data_recency(self, matches: List[Dict]) -> float:
        """Calculate how recent the match data is."""
        if not matches:
            return 0

        now = time.time()
        timestamps = [m.get('timestamp', 0) for m in matches]
        avg_age_days = (now - statistics.mean(timestamps)) / (24 * 3600)

        # Convert to recency score (newer = higher score)
        recency = max(0, 1 - (avg_age_days / 30))  # 30 days max age
        return recency

    def _assess_implementation_complexity(self, recommendations: List[Dict]) -> str:
        """Assess complexity of implementing recommendations."""
        if not recommendations:
            return 'low'

        complexities = [rec.get('priority', 'medium') for rec in recommendations]
        high_count = sum(1 for c in complexities if c == 'high')

        if high_count > len(complexities) * 0.5:
            return 'high'
        elif high_count > 0:
            return 'medium'
        else:
            return 'low'
