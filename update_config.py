#!/usr/bin/env python3
import json

# Update config to use LDPlayer
config = {
    'emulator_type': 'ldplayer',
    'memu_path': 'C:\\Program Files\\Microvirt\\MEmu\\MEmu.exe',
    'bluestacks_path': 'C:\\Program Files\\BlueStacks\\HD-Player.exe',
    'instance_id': 0,
    'debug': False
}

with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('Config updated to ldplayer')
