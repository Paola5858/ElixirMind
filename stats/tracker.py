"""
Stats Tracker: Tracks bot performance and persists state for the dashboard.

Fixes vs previous version:
- update_stats() now consumes List[ActionResult] (typed), not List[Dict].
- _update_derived_stats() no longer inflates actions_total by including
  actions_successful / actions_failed in the per-type sum.
- Session state is written to data/session_stats.json so the dashboard
  can read real data without a shared in-process object.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional

from core.types import ActionResult

logger = logging.getLogger(__name__)

_STATS_FILE = Path("data/session_stats.json")
# Keys that are NOT per-type action counters — excluded from actions_total sum.
_RESULT_KEYS = frozenset({"actions_successful", "actions_failed", "actions_total"})


class StatsTracker:
    def __init__(self, config: Dict = None) -> None:
        self.config = config or {}
        self.stats: Dict = defaultdict(int)
        self.performance_history: deque = deque(maxlen=1000)
        self._session_start: Optional[float] = None
        self._last_update: Optional[float] = None

        # Optional monitoring components (injected externally)
        self.performance_profiler = None
        self.fps_monitor = None
        self.latency_tracker = None
        self.bottleneck_detector = None
        self.alert_manager = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        self._session_start = time.time()
        self._last_update = self._session_start
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        logger.info("StatsTracker initialized.")

    def shutdown(self) -> None:
        self._generate_session_report()
        logger.info("StatsTracker shut down.")

    # ------------------------------------------------------------------
    # Core update
    # ------------------------------------------------------------------

    def update_stats(
        self,
        results: List[ActionResult],
        game_state: Dict = None,
    ) -> None:
        """Update statistics from a list of ActionResults."""
        now = time.time()

        for result in results:
            action_type = result.action.type.value  # e.g. "play_card"
            self.stats[f"actions_{action_type}"] += 1
            if result.success:
                self.stats["actions_successful"] += 1
            else:
                self.stats["actions_failed"] += 1

        if game_state:
            self._update_game_stats(game_state)

        self.stats["total_runtime"] = now - (self._session_start or now)
        self._last_update = now

        perf = self._collect_performance_metrics()
        if perf:
            self.performance_history.append(perf)
            if self.alert_manager:
                from alerts.performance_alerts import PerformanceAlerts
                PerformanceAlerts(self.alert_manager).check_performance_alerts(perf)

        self._update_derived_stats()
        self._persist()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        result = dict(self.stats)
        if self._session_start:
            result["session_duration"] = time.time() - self._session_start
        if self.performance_history:
            result["performance_summary"] = self._performance_summary()
        return result

    def get_performance_report(self) -> str:
        stats = self.get_stats()
        lines = [
            "Performance Report", "=" * 50,
            f"Session Duration : {stats.get('session_duration', 0):.1f}s",
            f"Total Actions    : {stats.get('actions_total', 0)}",
            f"Successful       : {stats.get('actions_successful', 0)}",
            f"Failed           : {stats.get('actions_failed', 0)}",
        ]
        if "performance_summary" in stats:
            ps = stats["performance_summary"]
            lines += [
                "",
                "Performance Metrics:",
                f"  Avg CPU    : {ps.get('avg_cpu', 0):.1f}%",
                f"  Avg Memory : {ps.get('avg_memory', 0):.1f}%",
                f"  Avg FPS    : {ps.get('avg_fps', 0):.1f}",
            ]
        return "\n".join(lines)

    def get_game_stats_report(self) -> str:
        stats = self.get_stats()
        won   = stats.get("battles_won",  0)
        lost  = stats.get("battles_lost", 0)
        draw  = stats.get("battles_draw", 0)
        total = won + lost + draw
        lines = ["Game Statistics Report", "=" * 50]
        if total:
            lines += [
                f"Total Battles : {total}",
                f"Win Rate      : {won / total:.1%}",
                f"Wins / Losses / Draws: {won} / {lost} / {draw}",
            ]
        if "avg_elixir" in stats:
            lines += [
                "",
                "Resource Management:",
                f"  Avg Elixir : {stats['avg_elixir']:.1f}",
                f"  Max Elixir : {stats.get('max_elixir', 0)}",
                f"  Min Elixir : {stats.get('min_elixir', 10)}",
            ]
        if "success_rate" in stats:
            lines += [
                "",
                "Action Efficiency:",
                f"  Success Rate  : {stats['success_rate']:.1%}",
                f"  Total Actions : {stats.get('actions_total', 0)}",
            ]
        return "\n".join(lines)

    def register_monitoring(self, **monitors) -> None:
        for name, monitor in monitors.items():
            setattr(self, name, monitor)
            logger.info("Registered monitoring component: %s", name)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_derived_stats(self) -> None:
        # Sum only per-type counters; exclude result counters to avoid inflation.
        total = sum(
            v for k, v in self.stats.items()
            if k.startswith("actions_") and k not in _RESULT_KEYS
        )
        self.stats["actions_total"] = total

        successful = self.stats.get("actions_successful", 0)
        self.stats["success_rate"] = (
            successful / total if total > 0 else 0.0
        )

    def _update_game_stats(self, game_state: Dict) -> None:
        if "elixir" in game_state:
            e = game_state["elixir"]
            n = self.stats.get("elixir_samples", 0)
            self.stats["avg_elixir"] = (
                (self.stats.get("avg_elixir", 0) * n + e) / (n + 1)
            )
            self.stats["elixir_samples"] = n + 1
            self.stats["max_elixir"] = max(self.stats.get("max_elixir", 0), e)
            self.stats["min_elixir"] = min(self.stats.get("min_elixir", 10), e)

        for key in ("enemy_towers", "my_towers"):
            if key in game_state:
                self.stats[f"{key}_remaining"] = game_state[key]

        if "battle_result" in game_state:
            self.stats[f"battles_{game_state['battle_result']}"] += 1

        if "time_remaining" in game_state:
            tr = game_state["time_remaining"]
            n  = self.stats.get("time_samples", 0)
            self.stats["avg_time_remaining"] = (
                (self.stats.get("avg_time_remaining", 0) * n + tr) / (n + 1)
            )
            self.stats["time_samples"] = n + 1

    def _collect_performance_metrics(self) -> Optional[Dict]:
        if not self.performance_profiler:
            return None
        metrics = self.performance_profiler.get_current_metrics()
        if self.fps_monitor:
            metrics["fps"] = self.fps_monitor.get_fps_stats().get("current_fps", 0)
        if self.latency_tracker:
            all_stats = self.latency_tracker.get_all_stats()
            if all_stats:
                metrics["latency_ms"] = sum(
                    s["mean"] for s in all_stats.values()
                ) / len(all_stats)
        return metrics

    def _performance_summary(self) -> Dict:
        cpu  = [m.get("cpu_percent", 0)    for m in self.performance_history]
        mem  = [m.get("memory_percent", 0) for m in self.performance_history]
        fps  = [m.get("fps", 0)            for m in self.performance_history]
        n    = len(self.performance_history)
        return {
            "avg_cpu":    sum(cpu) / n,
            "avg_memory": sum(mem) / n,
            "avg_fps":    sum(fps) / n,
            "samples":    n,
        }

    def _persist(self) -> None:
        """Write current stats to disk so the dashboard can read them."""
        try:
            _STATS_FILE.write_text(
                json.dumps(self.get_stats(), default=str), encoding="utf-8"
            )
        except Exception:
            logger.debug("Could not persist stats to %s", _STATS_FILE)

    def _generate_session_report(self) -> None:
        logger.info("Session Performance:\n%s", self.get_performance_report())
        logger.info("Session Game Stats:\n%s",  self.get_game_stats_report())
