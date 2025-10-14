"""
Base Emulator: Abstract interface for emulators.
Defines common methods that all emulators must implement.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseEmulator(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def start(self):
        """Start the emulator."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the emulator."""
        pass

    @abstractmethod
    def capture_screen(self):
        """Capture the current screen."""
        pass

    @abstractmethod
    def send_input(self, action):
        """Send input to the emulator."""
        pass

    @abstractmethod
    def is_running(self):
        """Check if the emulator is running."""
        pass
