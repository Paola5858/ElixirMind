"""
State Saver: Saves and restores bot state for recovery purposes.
"""

import json
import os
import time
import logging
from typing import Dict, Any, Optional
import pickle
import gzip

logger = logging.getLogger(__name__)

class StateSaver:
    """
    Handles saving and loading of bot state for crash recovery and persistence.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # State save settings
        self.save_directory = self.config.get('save_directory', 'data/state_saves')
        self.auto_save_interval = self.config.get('auto_save_interval', 300)  # 5 minutes
        self.max_save_files = self.config.get('max_save_files', 10)
        self.compression_enabled = self.config.get('compression', True)

        # State components to save
        self.state_components = [
            'bot_manager',
            'orchestrator',
            'state_machine',
            'stats_tracker',
            'strategy_state',
            'security_state'
        ]

        # Current state
        self.current_state = {}
        self.last_save_time = 0
        self.save_counter = 0

        # Ensure save directory exists
        os.makedirs(self.save_directory, exist_ok=True)

        logger.info(f"State Saver initialized, save directory: {self.save_directory}")

    def save_state(self, state_data: Dict, save_type: str = 'auto') -> str:
        """
        Save current bot state.

        Args:
            state_data: State data to save
            save_type: Type of save (auto, manual, emergency)

        Returns:
            Path to saved state file
        """
        timestamp = int(time.time())
        filename = f"state_{save_type}_{timestamp}_{self.save_counter}.pkl"

        if self.compression_enabled:
            filename += '.gz'

        filepath = os.path.join(self.save_directory, filename)

        try:
            # Prepare state data
            save_data = {
                'timestamp': timestamp,
                'save_type': save_type,
                'version': '1.0',
                'data': state_data
            }

            # Save with or without compression
            if self.compression_enabled:
                with gzip.open(filepath, 'wb') as f:
                    pickle.dump(save_data, f)
            else:
                with open(filepath, 'wb') as f:
                    pickle.dump(save_data, f)

            self.last_save_time = timestamp
            self.save_counter += 1

            # Clean up old saves
            self._cleanup_old_saves()

            logger.info(f"State saved: {filepath} ({save_type})")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return None

    def load_state(self, filepath: Optional[str] = None) -> Optional[Dict]:
        """
        Load bot state from file.

        Args:
            filepath: Specific file to load, or None for latest

        Returns:
            Loaded state data or None if failed
        """
        if filepath is None:
            filepath = self._get_latest_save_file()

        if not filepath or not os.path.exists(filepath):
            logger.warning("No state file found to load")
            return None

        try:
            # Load with or without compression
            if filepath.endswith('.gz'):
                with gzip.open(filepath, 'rb') as f:
                    save_data = pickle.load(f)
            else:
                with open(filepath, 'rb') as f:
                    save_data = pickle.load(f)

            # Validate save data
            if not self._validate_save_data(save_data):
                logger.error("Invalid save data format")
                return None

            state_data = save_data['data']
            logger.info(f"State loaded from: {filepath}")
            return state_data

        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None

    def auto_save(self, get_state_func: callable) -> bool:
        """
        Perform automatic state saving if interval has passed.

        Args:
            get_state_func: Function to get current state

        Returns:
            True if save was performed
        """
        current_time = time.time()

        if current_time - self.last_save_time >= self.auto_save_interval:
            try:
                state_data = get_state_func()
                self.save_state(state_data, 'auto')
                return True
            except Exception as e:
                logger.error(f"Auto-save failed: {e}")
                return False

        return False

    def emergency_save(self, get_state_func: callable) -> str:
        """
        Perform emergency state save.

        Args:
            get_state_func: Function to get current state

        Returns:
            Path to emergency save file
        """
        try:
            state_data = get_state_func()
            filepath = self.save_state(state_data, 'emergency')
            logger.warning("Emergency state save completed")
            return filepath
        except Exception as e:
            logger.error(f"Emergency save failed: {e}")
            return None

    def list_save_files(self) -> List[Dict]:
        """
        List all available save files.

        Returns:
            List of save file information
        """
        save_files = []

        try:
            for filename in os.listdir(self.save_directory):
                if filename.startswith('state_') and filename.endswith(('.pkl', '.pkl.gz')):
                    filepath = os.path.join(self.save_directory, filename)
                    file_info = self._get_file_info(filepath)
                    if file_info:
                        save_files.append(file_info)

            # Sort by timestamp (newest first)
            save_files.sort(key=lambda x: x['timestamp'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list save files: {e}")

        return save_files

    def delete_save_file(self, filepath: str) -> bool:
        """
        Delete a save file.

        Args:
            filepath: Path to save file to delete

        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted save file: {filepath}")
                return True
            else:
                logger.warning(f"Save file not found: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete save file: {e}")
            return False

    def get_save_stats(self) -> Dict:
        """
        Get statistics about saved states.

        Returns:
            Dict with save statistics
        """
        save_files = self.list_save_files()

        stats = {
            'total_saves': len(save_files),
            'auto_saves': len([f for f in save_files if f['save_type'] == 'auto']),
            'manual_saves': len([f for f in save_files if f['save_type'] == 'manual']),
            'emergency_saves': len([f for f in save_files if f['save_type'] == 'emergency']),
            'oldest_save': save_files[-1]['timestamp'] if save_files else None,
            'newest_save': save_files[0]['timestamp'] if save_files else None,
            'total_size_mb': sum(f['size_mb'] for f in save_files)
        }

        return stats

    def _get_latest_save_file(self) -> Optional[str]:
        """Get the path to the latest save file."""
        save_files = self.list_save_files()
        if save_files:
            return save_files[0]['filepath']
        return None

    def _cleanup_old_saves(self):
        """Clean up old save files to prevent disk space issues."""
        save_files = self.list_save_files()

        if len(save_files) > self.max_save_files:
            # Delete oldest files
            files_to_delete = save_files[self.max_save_files:]
            for file_info in files_to_delete:
                self.delete_save_file(file_info['filepath'])

            logger.info(f"Cleaned up {len(files_to_delete)} old save files")

    def _validate_save_data(self, save_data: Dict) -> bool:
        """Validate save data structure."""
        required_keys = ['timestamp', 'save_type', 'version', 'data']

        for key in required_keys:
            if key not in save_data:
                return False

        # Check version compatibility
        if save_data['version'] != '1.0':
            logger.warning(f"Save version {save_data['version']} may not be compatible")

        return True

    def _get_file_info(self, filepath: str) -> Optional[Dict]:
        """Get information about a save file."""
        try:
            filename = os.path.basename(filepath)
            parts = filename.replace('.pkl', '').replace('.gz', '').split('_')

            if len(parts) < 4:
                return None

            save_type = parts[1]
            timestamp = int(parts[2])
            counter = int(parts[3])

            # Get file size
            size_bytes = os.path.getsize(filepath)
            size_mb = size_bytes / (1024 * 1024)

            return {
                'filepath': filepath,
                'filename': filename,
                'save_type': save_type,
                'timestamp': timestamp,
                'counter': counter,
                'size_mb': round(size_mb, 2),
                'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            }

        except Exception as e:
            logger.error(f"Failed to get file info for {filepath}: {e}")
            return None
