"""
State Machine: Manages the states of the bot.
States: idle, battle, shutdown, etc.
"""

import logging

logger = logging.getLogger(__name__)

class StateMachine:
    def __init__(self):
        self.current_state = 'idle'
        self.states = ['idle', 'battle', 'shutdown']

    def set_state(self, state):
        if state in self.states:
            logger.info(f"State changed from {self.current_state} to {state}")
            self.current_state = state
        else:
            logger.warning(f"Invalid state: {state}")

    def get_state(self):
        return self.current_state

    def is_idle(self):
        return self.current_state == 'idle'

    def is_battle(self):
        return self.current_state == 'battle'

    def is_shutdown(self):
        return self.current_state == 'shutdown'
