"""
Bot Manager: Manages the lifecycle of the bot.
Handles initialization, running, and shutdown of the bot.
"""

import logging
from .orchestrator import Orchestrator
from .state_machine import StateMachine

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self, config):
        self.config = config
        self.orchestrator = Orchestrator(config)
        self.state_machine = StateMachine()
        self.orchestrator.set_state_machine(self.state_machine)
        self.running = False

    def start(self):
        """Start the bot lifecycle."""
        logger.info("Starting ElixirMind Bot...")
        self.running = True
        self.orchestrator.initialize()
        self.state_machine.set_state('idle')
        logger.info("Bot started successfully.")

    def run(self):
        """Main bot loop."""
        while self.running:
            current_state = self.state_machine.get_state()
            if current_state == 'idle':
                self.orchestrator.check_for_battle()
            elif current_state == 'battle':
                self.orchestrator.handle_battle()
            elif current_state == 'shutdown':
                self.stop()
                break
            # Add more states as needed

    def stop(self):
        """Stop the bot lifecycle."""
        logger.info("Stopping ElixirMind Bot...")
        self.running = False
        self.orchestrator.shutdown()
        logger.info("Bot stopped.")

    def is_running(self):
        return self.running
