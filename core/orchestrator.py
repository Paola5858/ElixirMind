"""
Orchestrator: Coordinates all bot components.

Key fixes vs previous version:
- detect_battle() returns (bool, frame|None) — unpacked correctly now.
- All inter-module data flows through core.types, not raw dicts.
"""

import logging
from typing import Any, List

from actions.controller import Controller
from stats.tracker import StatsTracker
from strategy.base import Strategy
from vision.detector import Detector
from .state_machine import StateMachine
from .types import ActionResult

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config: dict[str, Any] = config
        self.detector = Detector(config)
        self.controller = Controller(config)
        self.strategy = Strategy(config)
        self.stats_tracker = StatsTracker(config)
        self.state_machine = None

    def set_state_machine(self, state_machine: StateMachine | None) -> None:
        self.state_machine = state_machine

    def initialize(self) -> None:
        logger.info("Initializing orchestrator components...")
        self.detector.initialize()
        self.controller.initialize()
        self.strategy.initialize()
        self.stats_tracker.initialize()
        logger.info("Orchestrator initialized.")

    def check_for_battle(self) -> None:
        """Check if a battle is active and transition state accordingly."""
        screen = self.detector.capture_screen()
        if screen is None:
            return

        # detect_battle returns (bool, debug_image|None) — unpack explicitly.
        battle_active, _ = self.detector.detect_battle(screen)

        if battle_active and self.state_machine is not None:
            self.state_machine.set_state("battle")
            logger.info("Battle detected, entering battle state.")

    def handle_battle(self) -> None:
        """Execute one battle tick: capture → decide → execute → track."""
        screen = self.detector.capture_screen()
        if screen is None:
            return

        actions = self.strategy.decide_actions(screen, detector=self.detector)

        results: List[ActionResult] = []
        if actions:
            logger.debug("Executing %d action(s).", len(actions))
            results = self.controller.execute_actions(actions)
            self.stats_tracker.update_stats(results)
        else:
            logger.debug("No actions for current frame.")

        if self.detector.detect_battle_end(screen) and self.state_machine is not None:
            self.state_machine.set_state("idle")
            logger.info("Battle ended, returning to idle.")

    def shutdown(self) -> None:
        logger.info("Shutting down orchestrator...")
        self.detector.shutdown()
        self.controller.shutdown()
        self.strategy.shutdown()
        self.stats_tracker.shutdown()
        logger.info("Orchestrator shut down.")
