"""
Emulator Factory: Factory pattern for creating emulator instances.
"""

import logging
from .memu_emulator import MEmuEmulator
from .bluestacks_emulator import BlueStacksEmulator

logger = logging.getLogger(__name__)

class EmulatorFactory:
    @staticmethod
    def create_emulator(emulator_type, config):
        """Create an emulator instance based on type."""
        if emulator_type.lower() == 'memu':
            return MEmuEmulator(config)
        elif emulator_type.lower() == 'bluestacks':
            return BlueStacksEmulator(config)
        else:
            raise ValueError(f"Unsupported emulator type: {emulator_type}")
