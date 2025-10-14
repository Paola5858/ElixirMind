"""
Trophy Predictor: Predicts trophy progression and optimal strategies.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import statistics
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class TrophyPredictor:
    """
    Predicts trophy progression, optimal play times, and strategies for trophy gains.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Prediction settings
        self.prediction_window_days = self.config.get('prediction_window', 30)
        self.min_data_points = self.config.get('min_data_points', 50)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)

        # Models
        self.trophy_model = None
        self.scaler = StandardScaler()

        # Historical data
        self.trophy_history = []
        self.performance_factors = defaultdict(list)

        logger.info("Trophy Predictor initialized")

    def predict_trophy_progression(self, current_trophies: int, matches: List[Dict],
                                 days_ahead: int = 7) -> Dict:
        """
        Predict trophy progression over time.

        Args:
            current_trophies: Current trophy count
            matches: Historical match data
            days_ahead: Days to predict ahead

        Returns:
            Dict with trophy progression predictions
        """
        if len(matches) < self.min_data_points:
            return {'error': f'Need at least {self.min_data_points} matches for prediction'}

        # Analyze historical trophy changes
        trophy_changes = self._analyze_trophy_changes(matches)

        # Build prediction model
        self._build_trophy_model(matches)

        # Generate predictions
        predictions = self._generate_trophy_predictions(current_trophies, trophy_changes, days_ahead)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_prediction_confidence(predictions, matches)

        result = {
            'current_trophies': current_trophies,
            'predicted_trophies': predictions,
            'confidence_intervals': confidence_intervals,
            'expected_daily_gain': self._calculate_expected_daily_gain(trophy_changes),
            'optimal_play_times': self._find_optimal_play_times(matches),
            'risk_assessment': self._assess_trophy_risk(current_trophies, matches),
            'recommendations': self._generate_trophy_recommendations(predictions, current_trophies)
        }

        return result

    def predict_trophy_milestone(self, current_trophies: int, target_trophies: int,
                               matches: List[Dict]) -> Dict:
        """
        Predict time to reach trophy milestone.

        Args:
            current_trophies: Current trophy count
            target_trophies: Target trophy count
            matches: Historical match data

        Returns:
            Dict with milestone prediction
        """
        if target_trophies <= current_trophies:
            return {'error': 'Target trophies must be higher than current trophies'}

        # Calculate required gain
        required_gain = target_trophies - current_trophies

        # Get expected daily gain
        trophy_changes = self._analyze_trophy_changes(matches)
        daily_gain = self._calculate_expected_daily_gain(trophy_changes)

        if daily_gain <= 0:
            return {'error': 'No positive trophy progression detected'}

        # Estimate days needed
        estimated_days = required_gain / daily_gain

        # Account for variance
        variance = statistics.variance([change['net_change'] for change in trophy_changes]) if len(trophy_changes) > 1 else 0
        std_dev = variance ** 0.5 if variance > 0 else 0

        # Confidence intervals
        pessimistic_days = required_gain / max(daily_gain - std_dev, 0.1)
        optimistic_days = required_gain / (daily_gain + std_dev) if std_dev > 0 else estimated_days * 0.8

        # Calculate probability of reaching milestone
        success_probability = self._calculate_milestone_probability(required_gain, trophy_changes)

        result = {
            'current_trophies': current_trophies,
            'target_trophies': target_trophies,
            'required_gain': required_gain,
            'estimated_days': estimated_days,
            'estimated_date': (datetime.now() + timedelta(days=estimated_days)).isoformat(),
            'confidence_intervals': {
                'optimistic_days': optimistic_days,
                'pessimistic_days': pessimistic_days
            },
            'success_probability': success_probability,
            'daily_gain_stats': {
                'average': daily_gain,
                'std_dev': std_dev,
                'best_day': max((change['net_change'] for change in trophy_changes), default=0),
                'worst_day': min((change['net_change'] for change in trophy_changes), default=0)
            },
            'recommendations': self._generate_milestone_recommendations(estimated_days, success_probability)
        }

        return result

    def find_optimal_play_strategy(self, current_trophies: int, matches: List[Dict]) -> Dict:
        """
        Find optimal play strategy for trophy gains.

        Args:
            current_trophies: Current trophy count
            matches: Historical match data

        Returns:
            Dict with optimal strategy recommendations
        """
        # Analyze performance by various factors
        time_analysis = self._analyze_performance_by_time(matches)
        deck_analysis = self._analyze_performance_by_deck(matches)
        strategy_analysis = self._analyze_performance_by_strategy(matches)

        # Calculate trophy efficiency for each factor
        time_efficiency = self._calculate_trophy_efficiency(time_analysis)
        deck_efficiency = self._calculate_trophy_efficiency(deck_analysis)
        strategy_efficiency = self._calculate_trophy_efficiency(strategy_analysis)

        # Find optimal combinations
        optimal_combinations = self._find_optimal_combinations(
            time_efficiency, deck_efficiency, strategy_efficiency
        )

        result = {
            'optimal_times': self._get_top_factors(time_efficiency, 'time'),
            'optimal_decks': self._get_top_factors(deck_efficiency, 'deck'),
            'optimal_strategies': self._get_top_factors(strategy_efficiency, 'strategy'),
            'optimal_combinations': optimal_combinations,
            'expected_gain_per_match': self._calculate_expected_gain_per_match(matches),
            'risk_adjusted_strategy': self._calculate_risk_adjusted_strategy(optimal_combinations, matches)
        }

        return result

    def predict_season_end_trophies(self, current_trophies: int, matches: List[Dict],
                                  season_days_remaining: int = 14) -> Dict:
        """
        Predict final trophy count at season end.

        Args:
            current_trophies: Current trophy count
            matches: Historical match data
            season_days_remaining: Days remaining in season

        Returns:
            Dict with season end predictions
        """
        # Get daily gain statistics
        trophy_changes = self._analyze_trophy_changes(matches)
        daily_stats = self._calculate_daily_trophy_stats(trophy_changes)

        # Project forward
        projected_gains = []
        total_projected_gain = 0

        for day in range(season_days_remaining):
            # Account for diminishing returns (players get harder opponents)
            day_multiplier = self._calculate_day_multiplier(day, current_trophies)
            daily_gain = daily_stats['average'] * day_multiplier
            total_projected_gain += daily_gain
            projected_gains.append(daily_gain)

        final_trophies = current_trophies + total_projected_gain

        # Calculate confidence intervals
        std_dev = daily_stats.get('std_dev', 0)
        confidence_range = std_dev * (season_days_remaining ** 0.5) * 1.96  # 95% confidence

        result = {
            'current_trophies': current_trophies,
            'projected_final_trophies': final_trophies,
            'total_projected_gain': total_projected_gain,
            'average_daily_gain': total_projected_gain / season_days_remaining,
            'confidence_interval': {
                'lower': final_trophies - confidence_range,
                'upper': final_trophies + confidence_range
            },
            'daily_projections': projected_gains,
            'season_progression': self._calculate_season_progression(current_trophies, projected_gains),
            'recommendations': self._generate_season_recommendations(final_trophies, season_days_remaining)
        }

        return result

    def _analyze_trophy_changes(self, matches: List[Dict]) -> List[Dict]:
        """Analyze trophy changes from matches."""
        trophy_changes = []

        # Group matches by day
        daily_matches = defaultdict(list)
        for match in matches:
            timestamp = match.get('timestamp', 0)
            day = datetime.fromtimestamp(timestamp).date()
            daily_matches[day].append(match)

        for day, day_matches in daily_matches.items():
            daily_change = sum(match.get('trophy_change', 0) for match in day_matches)
            games_played = len(day_matches)
            wins = sum(1 for match in day_matches if match.get('result') == 'win')

            trophy_changes.append({
                'date': day.isoformat(),
                'net_change': daily_change,
                'games_played': games_played,
                'wins': wins,
                'win_rate': wins / games_played if games_played > 0 else 0,
                'avg_change_per_game': daily_change / games_played if games_played > 0 else 0
            })

        return trophy_changes

    def _build_trophy_model(self, matches: List[Dict]):
        """Build predictive model for trophy changes."""
        if len(matches) < 20:
            return

        # Prepare training data
        X = []  # Features
        y = []  # Target (trophy change)

        for match in matches:
            features = self._extract_match_features(match)
            trophy_change = match.get('trophy_change', 0)

            if features and trophy_change is not None:
                X.append(features)
                y.append(trophy_change)

        if len(X) >= 10:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.trophy_model = LinearRegression()
            self.trophy_model.fit(X_scaled, y)

            logger.info(f"Trained trophy prediction model with {len(X)} samples")

    def _extract_match_features(self, match: Dict) -> Optional[List[float]]:
        """Extract features from a match for prediction."""
        try:
            features = [
                match.get('opponent_trophies', 0) / 5000,  # Normalized opponent level
                1 if match.get('result') == 'win' else 0,   # Win indicator
                match.get('duration', 180) / 300,          # Normalized duration
                len(match.get('deck_used', [])) / 8,       # Deck size factor
                match.get('confidence_score', 0.5),        # AI confidence
            ]

            # Time of day factor
            timestamp = match.get('timestamp', time.time())
            hour = datetime.fromtimestamp(timestamp).hour
            time_factor = 1 if 18 <= hour <= 23 else 0.7  # Evening bonus
            features.append(time_factor)

            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None

    def _generate_trophy_predictions(self, current_trophies: int, trophy_changes: List[Dict],
                                   days_ahead: int) -> List[Dict]:
        """Generate trophy predictions for future days."""
        predictions = []

        # Calculate trend
        if len(trophy_changes) >= 7:
            recent_changes = trophy_changes[-7:]
            avg_daily_change = statistics.mean(change['net_change'] for change in recent_changes)
            trend = self._calculate_trend_slope(trophy_changes)
        else:
            avg_daily_change = statistics.mean(change['net_change'] for change in trophy_changes) if trophy_changes else 0
            trend = 0

        for day in range(1, days_ahead + 1):
            # Apply trend and some randomness
            base_change = avg_daily_change + (trend * day * 0.1)
            predicted_change = base_change * (0.9 + np.random.random() * 0.2)  # ±10% variance

            predicted_trophies = current_trophies + sum(p['predicted_change'] for p in predictions) + predicted_change

            predictions.append({
                'day': day,
                'predicted_change': predicted_change,
                'predicted_trophies': predicted_trophies,
                'confidence': max(0.5, 1 - (day * 0.05))  # Decreasing confidence over time
            })

        return predictions

    def _calculate_prediction_confidence(self, predictions: List[Dict], matches: List[Dict]) -> Dict:
        """Calculate confidence intervals for predictions."""
        if not predictions:
            return {}

        # Calculate historical variance
        trophy_changes = [match.get('trophy_change', 0) for match in matches]
        variance = statistics.variance(trophy_changes) if len(trophy_changes) > 1 else 0
        std_dev = variance ** 0.5 if variance > 0 else 10  # Default std dev

        confidence_intervals = {}
        cumulative_change = 0

        for prediction in predictions:
            cumulative_change += prediction['predicted_change']
            day = prediction['day']

            # Confidence interval grows with time
            interval_width = std_dev * (day ** 0.5) * 1.96  # 95% confidence

            confidence_intervals[day] = {
                'lower': prediction['predicted_trophies'] - interval_width,
                'upper': prediction['predicted_trophies'] + interval_width,
                'width': interval_width
            }

        return confidence_intervals

    def _calculate_expected_daily_gain(self, trophy_changes: List[Dict]) -> float:
        """Calculate expected daily trophy gain."""
        if not trophy_changes:
            return 0

        daily_gains = [change['net_change'] for change in trophy_changes]
        return statistics.mean(daily_gains)

    def _find_optimal_play_times(self, matches: List[Dict]) -> List[Dict]:
        """Find optimal times for playing."""
        hourly_performance = defaultdict(lambda: {'games': 0, 'total_change': 0})

        for match in matches:
            timestamp = match.get('timestamp', 0)
            hour = datetime.fromtimestamp(timestamp).hour
            trophy_change = match.get('trophy_change', 0)

            hourly_performance[hour]['games'] += 1
            hourly_performance[hour]['total_change'] += trophy_change

        optimal_times = []
        for hour in range(24):
            stats = hourly_performance[hour]
            if stats['games'] >= 5:  # Minimum games
                avg_gain = stats['total_change'] / stats['games']
                optimal_times.append({
                    'hour': hour,
                    'avg_trophy_gain': avg_gain,
                    'games': stats['games'],
                    'total_gain': stats['total_change']
                })

        optimal_times.sort(key=lambda x: x['avg_trophy_gain'], reverse=True)
        return optimal_times[:5]

    def _assess_trophy_risk(self, current_trophies: int, matches: List[Dict]) -> Dict:
        """Assess trophy-related risks."""
        trophy_changes = [match.get('trophy_change', 0) for match in matches]

        if not trophy_changes:
            return {'risk_level': 'unknown'}

        # Calculate risk metrics
        negative_changes = [change for change in trophy_changes if change < 0]
        avg_loss = statistics.mean(negative_changes) if negative_changes else 0
        loss_probability = len(negative_changes) / len(trophy_changes)

        # Risk levels based on trophy count and loss patterns
        if current_trophies < 2000:
            base_risk = 'low'  # Easier opponents
        elif current_trophies < 4000:
            base_risk = 'medium'
        else:
            base_risk = 'high'  # Harder opponents

        # Adjust based on loss patterns
        if loss_probability > 0.6:
            risk_level = 'high'
        elif loss_probability > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'risk_level': risk_level,
            'avg_loss_when_losing': avg_loss,
            'loss_probability': loss_probability,
            'recommended_conservatism': 'high' if risk_level == 'high' else 'medium' if risk_level == 'medium' else 'low'
        }

    def _calculate_trend_slope(self, trophy_changes: List[Dict]) -> float:
        """Calculate trend slope from trophy changes."""
        if len(trophy_changes) < 2:
            return 0

        # Simple linear regression for trend
        x = list(range(len(trophy_changes)))
        y = [change['net_change'] for change in trophy_changes]

        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return slope

        return 0

    def _calculate_milestone_probability(self, required_gain: int, trophy_changes: List[Dict]) -> float:
        """Calculate probability of reaching trophy milestone."""
        if not trophy_changes:
            return 0

        daily_gains = [change['net_change'] for change in trophy_changes]
        avg_gain = statistics.mean(daily_gains)
        std_dev = statistics.stdev(daily_gains) if len(daily_gains) > 1 else 0

        if avg_gain <= 0:
            return 0

        # Estimate days needed
        estimated_days = required_gain / avg_gain

        # Use normal distribution to estimate probability
        # This is a simplified calculation
        z_score = (required_gain - (avg_gain * estimated_days)) / (std_dev * (estimated_days ** 0.5)) if std_dev > 0 else 0

        # Convert z-score to probability (simplified)
        if z_score >= 2:
            return 0.95
        elif z_score >= 1:
            return 0.85
        elif z_score >= 0:
            return 0.65
        elif z_score >= -1:
            return 0.35
        else:
            return 0.15

    def _calculate_day_multiplier(self, day: int, current_trophies: int) -> float:
        """Calculate multiplier for trophy gains on a given day (diminishing returns)."""
        # Simulate increasing difficulty as season progresses
        base_multiplier = 1.0
        day_factor = max(0.7, 1 - (day * 0.02))  # Slight decrease over time
        trophy_factor = max(0.5, 1 - (current_trophies / 8000))  # Harder at higher trophies

        return base_multiplier * day_factor * trophy_factor

    def _calculate_daily_trophy_stats(self, trophy_changes: List[Dict]) -> Dict:
        """Calculate daily trophy statistics."""
        if not trophy_changes:
            return {'average': 0, 'std_dev': 0}

        daily_gains = [change['net_change'] for change in trophy_changes]

        return {
            'average': statistics.mean(daily_gains),
            'std_dev': statistics.stdev(daily_gains) if len(daily_gains) > 1 else 0,
            'max': max(daily_gains),
            'min': min(daily_gains),
            'total_days': len(trophy_changes)
        }

    def _calculate_season_progression(self, current_trophies: int, daily_gains: List[float]) -> List[Dict]:
        """Calculate season progression data."""
        progression = []
        running_total = current_trophies

        for i, gain in enumerate(daily_gains):
            running_total += gain
            progression.append({
                'day': i + 1,
                'trophies': running_total,
                'daily_gain': gain
            })

        return progression

    def _analyze_performance_by_time(self, matches: List[Dict]) -> Dict:
        """Analyze performance by time of day."""
        # Implementation similar to _find_optimal_play_times
        return {}

    def _analyze_performance_by_deck(self, matches: List[Dict]) -> Dict:
        """Analyze performance by deck."""
        return {}

    def _analyze_performance_by_strategy(self, matches: List[Dict]) -> Dict:
        """Analyze performance by strategy."""
        return {}

    def _calculate_trophy_efficiency(self, analysis: Dict) -> Dict:
        """Calculate trophy efficiency for different factors."""
        return {}

    def _find_optimal_combinations(self, time_eff: Dict, deck_eff: Dict, strategy_eff: Dict) -> List[Dict]:
        """Find optimal combinations of factors."""
        return []

    def _get_top_factors(self, efficiency: Dict, factor_type: str) -> List[Dict]:
        """Get top performing factors."""
        return []

    def _calculate_expected_gain_per_match(self, matches: List[Dict]) -> float:
        """Calculate expected trophy gain per match."""
        trophy_changes = [match.get('trophy_change', 0) for match in matches]
        return statistics.mean(trophy_changes) if trophy_changes else 0

    def _calculate_risk_adjusted_strategy(self, combinations: List[Dict], matches: List[Dict]) -> Dict:
        """Calculate risk-adjusted optimal strategy."""
        return {}

    def _generate_trophy_recommendations(self, predictions: Dict, current_trophies: int) -> List[str]:
        """Generate trophy-related recommendations."""
        return []

    def _generate_milestone_recommendations(self, estimated_days: float, success_probability: float) -> List[str]:
        """Generate milestone achievement recommendations."""
        return []

    def _generate_season_recommendations(self, final_trophies: float, days_remaining: int) -> List[str]:
        """Generate season end recommendations."""
        return []
