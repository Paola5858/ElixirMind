"""
Configuration module for ElixirMind.
"""

import json
import os

def load_config(config_path='config.json'):
    """Load configuration from JSON file."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        return {
            'emulator_type': 'memu',
            'memu_path': 'C:\\Program Files\\Microvirt\\MEmu\\MEmu.exe',
            'bluestacks_path': 'C:\\Program Files\\BlueStacks\\HD-Player.exe',
            'instance_id': 0,
            'debug': False
        }
