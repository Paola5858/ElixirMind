"""
Emulator Module: Now uses the emulator factory for abstraction.
"""

from emulators.emulator_factory import EmulatorFactory

def get_emulator(config):
    """Get an emulator instance based on config."""
    emulator_type = config.get('emulator_type', 'memu')
    return EmulatorFactory.create_emulator(emulator_type, config)
