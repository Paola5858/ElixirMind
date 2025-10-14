"""
Data Backup: Handles automatic backup of critical data and configurations.
"""

import os
import time
import shutil
import logging
from typing import Dict, List, Optional, Set
import hashlib
import json

logger = logging.getLogger(__name__)

class DataBackup:
    """
    Manages automatic backup of critical bot data, configurations, and logs.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Backup settings
        self.backup_directory = self.config.get('backup_directory', 'data/backups')
        self.backup_interval = self.config.get('backup_interval', 3600)  # 1 hour
        self.max_backups = self.config.get('max_backups', 24)  # Keep 24 hourly backups
        self.compression_enabled = self.config.get('compression', True)

        # Data to backup
        self.backup_targets = {
            'configs': ['config.py', 'config.json'],
            'data': ['data/'],
            'logs': ['logs/'],
            'stats': ['stats/'],
            'models': ['models/']
        }

        # Custom backup targets
        self.custom_targets = set()

        # Backup tracking
        self.last_backup_time = 0
        self.backup_history = []
        self.backup_counter = 0

        # Ensure backup directory exists
        os.makedirs(self.backup_directory, exist_ok=True)

        logger.info(f"Data Backup initialized, backup directory: {self.backup_directory}")

    def add_backup_target(self, target_path: str, target_type: str = 'custom'):
        """
        Add a custom backup target.

        Args:
            target_path: Path to backup
            target_type: Type of target (for organization)
        """
        self.custom_targets.add(target_path)
        logger.info(f"Added backup target: {target_path}")

    def remove_backup_target(self, target_path: str):
        """
        Remove a backup target.

        Args:
            target_path: Path to remove from backups
        """
        self.custom_targets.discard(target_path)
        logger.info(f"Removed backup target: {target_path}")

    def perform_backup(self, backup_type: str = 'scheduled') -> Optional[str]:
        """
        Perform a data backup.

        Args:
            backup_type: Type of backup (scheduled, manual, emergency)

        Returns:
            Path to backup archive or None if failed
        """
        timestamp = int(time.time())
        backup_name = f"backup_{backup_type}_{timestamp}_{self.backup_counter}"

        try:
            # Create backup archive
            backup_path = self._create_backup_archive(backup_name, backup_type)

            if backup_path:
                # Record backup
                backup_info = {
                    'timestamp': timestamp,
                    'type': backup_type,
                    'path': backup_path,
                    'size_mb': self._get_file_size_mb(backup_path),
                    'files_backed_up': self._count_backup_files(backup_path)
                }

                self.backup_history.append(backup_info)
                self.last_backup_time = timestamp
                self.backup_counter += 1

                # Cleanup old backups
                self._cleanup_old_backups()

                logger.info(f"Backup completed: {backup_path}")
                return backup_path
            else:
                logger.error("Backup creation failed")
                return None

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def auto_backup(self) -> bool:
        """
        Perform automatic backup if interval has passed.

        Returns:
            True if backup was performed
        """
        current_time = time.time()

        if current_time - self.last_backup_time >= self.backup_interval:
            self.perform_backup('scheduled')
            return True

        return False

    def emergency_backup(self) -> Optional[str]:
        """
        Perform emergency backup of critical data.

        Returns:
            Path to emergency backup
        """
        logger.warning("Performing emergency backup")
        return self.perform_backup('emergency')

    def restore_backup(self, backup_path: str, restore_targets: Optional[List[str]] = None) -> bool:
        """
        Restore data from a backup.

        Args:
            backup_path: Path to backup archive
            restore_targets: Specific targets to restore, or None for all

        Returns:
            True if restore successful
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False

        try:
            # Extract backup
            extract_path = self._extract_backup(backup_path)

            if not extract_path:
                return False

            # Restore files
            restored_files = []
            targets_to_restore = restore_targets or list(self.backup_targets.keys()) + list(self.custom_targets)

            for target in targets_to_restore:
                if target in self.backup_targets:
                    # Restore predefined targets
                    for target_path in self.backup_targets[target]:
                        src_path = os.path.join(extract_path, target_path)
                        if os.path.exists(src_path):
                            self._restore_path(src_path, target_path)
                            restored_files.append(target_path)
                elif target in self.custom_targets:
                    # Restore custom targets
                    src_path = os.path.join(extract_path, target)
                    if os.path.exists(src_path):
                        self._restore_path(src_path, target)
                        restored_files.append(target)

            # Cleanup extraction directory
            shutil.rmtree(extract_path)

            logger.info(f"Restored {len(restored_files)} items from backup")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """
        List all available backups.

        Returns:
            List of backup information
        """
        backups = []

        try:
            for filename in os.listdir(self.backup_directory):
                if filename.startswith('backup_'):
                    filepath = os.path.join(self.backup_directory, filename)
                    backup_info = self._get_backup_info(filepath)
                    if backup_info:
                        backups.append(backup_info)

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        return backups

    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a backup file.

        Args:
            backup_path: Path to backup file

        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logger.info(f"Deleted backup: {backup_path}")
                return True
            else:
                logger.warning(f"Backup not found: {backup_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    def get_backup_stats(self) -> Dict:
        """
        Get backup statistics.

        Returns:
            Dict with backup statistics
        """
        backups = self.list_backups()

        stats = {
            'total_backups': len(backups),
            'scheduled_backups': len([b for b in backups if b['type'] == 'scheduled']),
            'manual_backups': len([b for b in backups if b['type'] == 'manual']),
            'emergency_backups': len([b for b in backups if b['type'] == 'emergency']),
            'total_size_mb': sum(b['size_mb'] for b in backups),
            'oldest_backup': backups[-1]['timestamp'] if backups else None,
            'newest_backup': backups[0]['timestamp'] if backups else None
        }

        return stats

    def verify_backup_integrity(self, backup_path: str) -> bool:
        """
        Verify the integrity of a backup file.

        Args:
            backup_path: Path to backup file

        Returns:
            True if backup is intact
        """
        try:
            # Attempt to extract and check files
            extract_path = self._extract_backup(backup_path)
            if not extract_path:
                return False

            # Check for expected files
            expected_files = []
            for target_list in self.backup_targets.values():
                expected_files.extend(target_list)

            missing_files = []
            for expected_file in expected_files:
                if not os.path.exists(os.path.join(extract_path, expected_file)):
                    missing_files.append(expected_file)

            # Cleanup
            shutil.rmtree(extract_path)

            if missing_files:
                logger.warning(f"Backup missing files: {missing_files}")
                return False

            return True

        except Exception as e:
            logger.error(f"Backup integrity check failed: {e}")
            return False

    def _create_backup_archive(self, backup_name: str, backup_type: str) -> Optional[str]:
        """Create a backup archive."""
        try:
            # Create temporary directory for backup
            temp_dir = os.path.join(self.backup_directory, f"temp_{backup_name}")
            os.makedirs(temp_dir, exist_ok=True)

            # Copy files to backup
            files_backed_up = 0
            for target_type, targets in self.backup_targets.items():
                for target in targets:
                    if os.path.exists(target):
                        dest_path = os.path.join(temp_dir, target)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                        if os.path.isdir(target):
                            shutil.copytree(target, dest_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(target, dest_path)
                        files_backed_up += 1

            # Copy custom targets
            for custom_target in self.custom_targets:
                if os.path.exists(custom_target):
                    dest_path = os.path.join(temp_dir, custom_target)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                    if os.path.isdir(custom_target):
                        shutil.copytree(custom_target, dest_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(custom_target, dest_path)
                    files_backed_up += 1

            # Create archive
            archive_path = os.path.join(self.backup_directory, f"{backup_name}.tar.gz")
            shutil.make_archive(archive_path.replace('.tar.gz', ''), 'gztar', temp_dir)

            # Cleanup temp directory
            shutil.rmtree(temp_dir)

            return archive_path

        except Exception as e:
            logger.error(f"Failed to create backup archive: {e}")
            return None

    def _extract_backup(self, backup_path: str) -> Optional[str]:
        """Extract a backup archive."""
        try:
            extract_path = backup_path.replace('.tar.gz', '_extracted')
            shutil.unpack_archive(backup_path, extract_path, 'gztar')
            return extract_path
        except Exception as e:
            logger.error(f"Failed to extract backup: {e}")
            return None

    def _restore_path(self, src_path: str, dest_path: str):
        """Restore a file or directory."""
        try:
            if os.path.isdir(src_path):
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(src_path, dest_path)
            else:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
        except Exception as e:
            logger.error(f"Failed to restore {dest_path}: {e}")

    def _cleanup_old_backups(self):
        """Clean up old backup files."""
        backups = self.list_backups()

        if len(backups) > self.max_backups:
            backups_to_delete = backups[self.max_backups:]
            for backup in backups_to_delete:
                self.delete_backup(backup['path'])

            logger.info(f"Cleaned up {len(backups_to_delete)} old backups")

    def _get_backup_info(self, filepath: str) -> Optional[Dict]:
        """Get information about a backup file."""
        try:
            filename = os.path.basename(filepath)
            parts = filename.replace('.tar.gz', '').split('_')

            if len(parts) < 4:
                return None

            backup_type = parts[1]
            timestamp = int(parts[2])
            counter = int(parts[3])

            return {
                'path': filepath,
                'filename': filename,
                'type': backup_type,
                'timestamp': timestamp,
                'counter': counter,
                'size_mb': self._get_file_size_mb(filepath),
                'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            }

        except Exception as e:
            logger.error(f"Failed to get backup info for {filepath}: {e}")
            return None

    def _get_file_size_mb(self, filepath: str) -> float:
        """Get file size in MB."""
        try:
            size_bytes = os.path.getsize(filepath)
            return round(size_bytes / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def _count_backup_files(self, backup_path: str) -> int:
        """Count files in a backup archive."""
        try:
            extract_path = self._extract_backup(backup_path)
            if not extract_path:
                return 0

            file_count = 0
            for root, dirs, files in os.walk(extract_path):
                file_count += len(files)

            shutil.rmtree(extract_path)
            return file_count

        except Exception:
            return 0
