"""
Stats Tracker: Tracks bot statistics and performance.
Enhanced with monitoring integration.
"""

import logging
import time
from typing import Dict, List, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class StatsTracker:
    """
    Enhanced statistics tracker with monitoring integration.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.stats = defaultdict(int)
        self.performance_history = deque(maxlen=1000)
        self.session_start_time = None
        self.last_update_time = None

        # Monitoring components (to be injected)
        self.performance_profiler = None
        self.fps_monitor = None
        self.latency_tracker = None
        self.bottleneck_detector = None
        self.alert_manager = None

        logger.info("Enhanced Stats Tracker initialized")

    def initialize(self):
        """Initialize the stats tracker."""
        self.session_start_time = time.time()
        self.last_update_time = self.session_start_time
        logger.info("Stats Tracker initialized")

    def shutdown(self):
        """Shutdown the stats tracker."""
        self._generate_session_report()
        logger.info("Stats Tracker shutdown")

    def update_stats(self, actions: List[Dict], game_state: Dict = None):
        """
        Update statistics with new actions and game state.

        Args:
            actions: List of action dictionaries
            game_state: Optional game state information (elixir, towers, etc.)
        """
        current_time = time.time()

        # Update basic stats
        for action in actions:
            action_type = action.get('type', 'unknown')
            self.stats[f'actions_{action_type}'] += 1

            # Track success/failure
            if action.get('success', True):
                self.stats['actions_successful'] += 1
            else:
                self.stats['actions_failed'] += 1

        # Update game-specific stats if game state provided
        if game_state:
            self._update_game_stats(game_state)

        # Update timing stats
        time_since_last_update = current_time - self.last_update_time
        self.stats['total_runtime'] = current_time - self.session_start_time
        self.last_update_time = current_time

        # Collect performance metrics if monitoring is available
        performance_data = self._collect_performance_metrics()
        if performance_data:
            self.performance_history.append(performance_data)

            # Check for alerts
            if self.alert_manager:
                from alerts.performance_alerts import PerformanceAlerts
                alerts = PerformanceAlerts(self.alert_manager)
                alerts.check_performance_alerts(performance_data)

        # Update derived stats
        self._update_derived_stats()

    def get_stats(self) -> Dict:
        """
        Get current statistics.

        Returns:
            Dict with all statistics
        """
        stats_dict = dict(self.stats)

        # Add session info
        if self.session_start_time:
            stats_dict['session_duration'] = time.time() - self.session_start_time

        # Add performance summary
        if self.performance_history:
            stats_dict['performance_summary'] = self._get_performance_summary()

        return stats_dict

    def get_performance_report(self) -> str:
        """
        Generate a comprehensive performance report.

        Returns:
            Formatted performance report
        """
        report_lines = ["Performance Report", "=" * 50]

        # Basic stats
        stats = self.get_stats()
        report_lines.append(f"Session Duration: {stats.get('session_duration', 0):.1f}s")
        report_lines.append(f"Total Actions: {stats.get('actions_total', 0)}")
        report_lines.append(f"Successful Actions: {stats.get('actions_successful', 0)}")
        report_lines.append(f"Failed Actions: {stats.get('actions_failed', 0)}")

        # Performance metrics
        if self.performance_history:
            perf_summary = stats.get('performance_summary', {})
            report_lines.append("")
            report_lines.append("Performance Metrics:")
            report_lines.append(f"  Avg CPU: {perf_summary.get('avg_cpu', 0):.1f}%")
            report_lines.append(f"  Avg Memory: {perf_summary.get('avg_memory', 0):.1f}%")
            report_lines.append(f"  Avg FPS: {perf_summary.get('avg_fps', 0):.1f}")

        # Monitoring reports
        if self.latency_tracker:
            report_lines.append("")
            report_lines.append("Latency Analysis:")
            latency_report = self.latency_tracker.get_latency_report()
            report_lines.extend(latency_report.split('\n'))

        if self.bottleneck_detector:
            report_lines.append("")
            report_lines.append("Bottleneck Analysis:")
            bottleneck_report = self.bottleneck_detector.get_bottleneck_report()
            report_lines.extend(bottleneck_report.split('\n'))

        return "\n".join(report_lines)

    def register_monitoring(self, **monitors):
        """
        Register monitoring components.

        Args:
            **monitors: Monitoring component instances
        """
        for name, monitor in monitors.items():
            setattr(self, name, monitor)
            logger.info(f"Registered monitoring component: {name}")

    def _collect_performance_metrics(self) -> Optional[Dict]:
        """Collect performance metrics from monitoring components."""
        if not self.performance_profiler:
            return None

        metrics = self.performance_profiler.get_current_metrics()

        # Add FPS if available
        if self.fps_monitor:
            fps_stats = self.fps_monitor.get_fps_stats()
            metrics['fps'] = fps_stats.get('current_fps', 0)

        # Add latency info if available
        if self.latency_tracker:
            latency_stats = self.latency_tracker.get_all_stats()
            if latency_stats:
                # Get average latency across all operations
                total_latency = sum(stats['mean'] for stats in latency_stats.values())
                avg_latency = total_latency / len(latency_stats)
                metrics['latency_ms'] = avg_latency

        return metrics

    def _get_performance_summary(self) -> Dict:
        """Get performance summary from history."""
        if not self.performance_history:
            return {}

        # Calculate averages
        cpu_values = [m.get('cpu_percent', 0) for m in self.performance_history]
        memory_values = [m.get('memory_percent', 0) for m in self.performance_history]
        fps_values = [m.get('fps', 0) for m in self.performance_history]

        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'avg_memory': sum(memory_values) / len(memory_values) if memory_values else 0,
            'avg_fps': sum(fps_values) / len(fps_values) if fps_values else 0,
            'samples': len(self.performance_history)
        }

    def _update_derived_stats(self):
        """Update derived statistics."""
        total_actions = sum(v for k, v in self.stats.items() if k.startswith('actions_') and k != 'actions_total')
        self.stats['actions_total'] = total_actions

        # Calculate success rate
        successful = self.stats.get('actions_successful', 0)
        total = self.stats.get('actions_total', 0)
        if total > 0:
            self.stats['success_rate'] = successful / total
        else:
            self.stats['success_rate'] = 0.0

    def _update_game_stats(self, game_state: Dict):
        """Update game-specific statistics."""
        # Track elixir levels
        if 'elixir' in game_state:
            elixir = game_state['elixir']
            self.stats['avg_elixir'] = (self.stats.get('avg_elixir', 0) * self.stats.get('elixir_samples', 0) + elixir) / (self.stats.get('elixir_samples', 0) + 1)
            self.stats['elixir_samples'] = self.stats.get('elixir_samples', 0) + 1
            self.stats['max_elixir'] = max(self.stats.get('max_elixir', 0), elixir)
            self.stats['min_elixir'] = min(self.stats.get('min_elixir', 10), elixir)

        # Track tower status
        if 'enemy_towers' in game_state:
            self.stats['enemy_towers_remaining'] = game_state['enemy_towers']
        if 'my_towers' in game_state:
            self.stats['my_towers_remaining'] = game_state['my_towers']

        # Track battle outcomes
        if 'battle_result' in game_state:
            result = game_state['battle_result']
            self.stats[f'battles_{result}'] += 1

        # Track time management
        if 'time_remaining' in game_state:
            time_remaining = game_state['time_remaining']
            self.stats['avg_time_remaining'] = (self.stats.get('avg_time_remaining', 0) * self.stats.get('time_samples', 0) + time_remaining) / (self.stats.get('time_samples', 0) + 1)
            self.stats['time_samples'] = self.stats.get('time_samples', 0) + 1

    def get_game_stats_report(self) -> str:
        """
        Generate a detailed game statistics report.

        Returns:
            Formatted game statistics report
        """
        report_lines = ["Game Statistics Report", "=" * 50]

        stats = self.get_stats()

        # Battle statistics
        total_battles = (stats.get('battles_won', 0) + stats.get('battles_lost', 0) +
                        stats.get('battles_draw', 0))
        if total_battles > 0:
            win_rate = stats.get('battles_won', 0) / total_battles
            report_lines.append(f"Total Battles: {total_battles}")
            report_lines.append(f"Win Rate: {win_rate:.1%}")
            report_lines.append(f"Wins: {stats.get('battles_won', 0)}")
            report_lines.append(f"Losses: {stats.get('battles_lost', 0)}")
            report_lines.append(f"Draws: {stats.get('battles_draw', 0)}")

        # Resource management
        if 'avg_elixir' in stats:
            report_lines.append("")
            report_lines.append("Resource Management:")
            report_lines.append(f"  Average Elixir: {stats['avg_elixir']:.1f}")
            report_lines.append(f"  Max Elixir: {stats.get('max_elixir', 0)}")
            report_lines.append(f"  Min Elixir: {stats.get('min_elixir', 10)}")

        # Tower statistics
        if 'enemy_towers_remaining' in stats or 'my_towers_remaining' in stats:
            report_lines.append("")
            report_lines.append("Tower Status:")
            report_lines.append(f"  Enemy Towers: {stats.get('enemy_towers_remaining', 3)}")
            report_lines.append(f"  My Towers: {stats.get('my_towers_remaining', 3)}")

        # Action efficiency
        if 'success_rate' in stats:
            report_lines.append("")
            report_lines.append("Action Efficiency:")
            report_lines.append(f"  Success Rate: {stats['success_rate']:.1%}")
            report_lines.append(f"  Total Actions: {stats.get('actions_total', 0)}")

        return "\n".join(report_lines)

    def _generate_session_report(self):
        """Generate end-of-session report."""
        # Performance report
        perf_report = self.get_performance_report()
        logger.info("Session Performance Report:\n" + perf_report)

        # Game stats report
        game_report = self.get_game_stats_report()
        logger.info("Session Game Statistics Report:\n" + game_report)

        # Could save to file or send to dashboard
        # self._save_report_to_file(perf_report + "\n\n" + game_report)
