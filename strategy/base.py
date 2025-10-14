"""
Base Strategy: Abstract base for all strategies.
"""

class Strategy:
    def __init__(self, config):
        self.config = config

    def initialize(self):
        pass

    def shutdown(self):
        pass

    def decide_actions(self, screen):
        return []
