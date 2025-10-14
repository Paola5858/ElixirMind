"""
Orchestrator: Coordinates all components of the bot.
Manages interactions between vision, actions, strategy, and stats.
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.detector import Detector
from actions.controller import Controller
from strategy.base import Strategy
from stats.tracker import StatsTracker

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.detector = Detector(config)
        self.controller = Controller(config)
        self.strategy = Strategy(config)  # Assuming base strategy
        self.stats_tracker = StatsTracker()
        self.state_machine = None  # Will be set by bot_manager

    def set_state_machine(self, state_machine):
        self.state_machine = state_machine

    def initialize(self):
        """Initialize all components."""
        logger.info("Initializing orchestrator components...")
        self.detector.initialize()
        self.controller.initialize()
        self.strategy.initialize()
        self.stats_tracker.initialize()
        logger.info("Orchestrator initialized.")

    def check_for_battle(self):
        """Check if a battle is available."""
        screen = self.detector.capture_screen()
        battle_detected = self.detector.detect_battle(screen)
        if battle_detected:
            self.state_machine.set_state('battle')
            logger.info("Battle detected, entering battle state.")

    def handle_battle(self):
        """Handle battle logic."""
        screen = self.detector.capture_screen()
        actions = self.strategy.decide_actions(screen)
        self.controller.execute_actions(actions)
        self.stats_tracker.update_stats(actions)
        # Check if battle ended
        if self.detector.detect_battle_end(screen):
            self.state_machine.set_state('idle')
            logger.info("Battle ended, returning to idle state.")

    def shutdown(self):
        """Shutdown all components."""
        logger.info("Shutting down orchestrator...")
        self.detector.shutdown()
        self.controller.shutdown()
        self.strategy.shutdown()
        self.stats_tracker.shutdown()
        logger.info("Orchestrator shut down.")
