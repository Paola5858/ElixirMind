"""
Rollback Manager: Manages rollback of configurations and system states.
"""

import os
import time
import shutil
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class RollbackManager:
    """
    Manages rollback operations for configurations, models, and system states.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Rollback settings
        self.rollback_directory = self.config.get('rollback_directory', 'data/rollbacks')
        self.max_rollback_points = self.config.get('max_rollback_points', 10)
        self.auto_rollback_enabled = self.config.get('auto_rollback', False)

        # Rollback targets
        self.rollback_targets = {
            'config': ['config.py', 'config.json'],
            'models': ['models/'],
            'strategies': ['strategy/'],
            'calibration': ['vision/calibration/']
        }

        # Rollback history
        self.rollback_history = []
        self.rollback_counter = 0

        # Ensure rollback directory exists
        os.makedirs(self.rollback_directory, exist_ok=True)

        logger.info(f"Rollback Manager initialized, rollback directory: {self.rollback_directory}")

    def create_rollback_point(self, point_name: str, description: str = "") -> Optional[str]:
        """
        Create a rollback point for current system state.

        Args:
            point_name: Name for the rollback point
            description: Description of the rollback point

        Returns:
            ID of created rollback point or None if failed
        """
        timestamp = int(time.time())
        rollback_id = f"{timestamp}_{self.rollback_counter}"

        try:
            # Create rollback directory
            rollback_path = os.path.join(self.rollback_directory, rollback_id)
            os.makedirs(rollback_path, exist_ok=True)

            # Backup current state
            backed_up_items = []
            for target_type, targets in self.rollback_targets.items():
                for target in targets:
                    if os.path.exists(target):
                        dest_path = os.path.join(rollback_path, target)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                        if os.path.isdir(target):
                            shutil.copytree(target, dest_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(target, dest_path)

                        backed_up_items.append(target)

            # Save metadata
            metadata = {
                'id': rollback_id,
                'name': point_name,
                'description': description,
                'timestamp': timestamp,
                'backed_up_items': backed_up_items,
                'size_mb': self._calculate_directory_size(rollback_path)
            }

            metadata_path = os.path.join(rollback_path, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Record rollback point
            self.rollback_history.append(metadata)
            self.rollback_counter += 1

            # Cleanup old rollback points
            self._cleanup_old_rollback_points()

            logger.info(f"Created rollback point: {point_name} ({rollback_id})")
            return rollback_id

        except Exception as e:
            logger.error(f"Failed to create rollback point: {e}")
            return None

    def rollback_to_point(self, rollback_id: str, targets: Optional[List[str]] = None) -> bool:
        """
        Rollback to a specific rollback point.

        Args:
            rollback_id: ID of rollback point to restore
            targets: Specific targets to rollback, or None for all

        Returns:
            True if rollback successful
        """
        rollback_path = os.path.join(self.rollback_directory, rollback_id)

        if not os.path.exists(rollback_path):
            logger.error(f"Rollback point not found: {rollback_id}")
            return False

        try:
            # Load metadata
            metadata_path = os.path.join(rollback_path, 'metadata.json')
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Determine targets to rollback
            targets_to_rollback = targets or metadata.get('backed_up_items', [])

            # Perform rollback
            rolled_back_items = []
            for target in targets_to_rollback:
                src_path = os.path.join(rollback_path, target)
                if os.path.exists(src_path):
                    self._restore_path(src_path, target)
                    rolled_back_items.append(target)

            logger.info(f"Rolled back {len(rolled_back_items)} items from point {rollback_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def list_rollback_points(self) -> List[Dict]:
        """
        List all available rollback points.

        Returns:
            List of rollback point information
        """
        rollback_points = []

        try:
            for dirname in os.listdir(self.rollback_directory):
                rollback_path = os.path.join(self.rollback_directory, dirname)
                metadata_path = os.path.join(rollback_path, 'metadata.json')

                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    rollback_points.append(metadata)

            # Sort by timestamp (newest first)
            rollback_points.sort(key=lambda x: x['timestamp'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list rollback points: {e}")

        return rollback_points

    def delete_rollback_point(self, rollback_id: str) -> bool:
        """
        Delete a rollback point.

        Args:
            rollback_id: ID of rollback point to delete

        Returns:
            True if deleted successfully
        """
        rollback_path = os.path.join(self.rollback_directory, rollback_id)

        try:
            if os.path.exists(rollback_path):
                shutil.rmtree(rollback_path)
                logger.info(f"Deleted rollback point: {rollback_id}")
                return True
            else:
                logger.warning(f"Rollback point not found: {rollback_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete rollback point: {e}")
            return False

    def auto_rollback_on_failure(self, failure_context: Dict) -> bool:
        """
        Automatically rollback on system failure.

        Args:
            failure_context: Context of the failure

        Returns:
            True if auto-rollback was performed
        """
        if not self.auto_rollback_enabled:
            return False

        # Check if we should rollback based on failure context
        if self._should_rollback(failure_context):
            # Get latest rollback point
            rollback_points = self.list_rollback_points()
            if rollback_points:
                latest_point = rollback_points[0]['id']
                logger.warning(f"Auto-rollback triggered, rolling back to {latest_point}")
                return self.rollback_to_point(latest_point)

        return False

    def compare_rollback_points(self, point_id1: str, point_id2: str) -> Dict:
        """
        Compare two rollback points.

        Args:
            point_id1: First rollback point ID
            point_id2: Second rollback point ID

        Returns:
            Dict with comparison results
        """
        try:
            metadata1 = self._get_rollback_metadata(point_id1)
            metadata2 = self._get_rollback_metadata(point_id2)

            if not metadata1 or not metadata2:
                return {'error': 'One or both rollback points not found'}

            comparison = {
                'point1': {'id': point_id1, 'name': metadata1['name'], 'timestamp': metadata1['timestamp']},
                'point2': {'id': point_id2, 'name': metadata2['name'], 'timestamp': metadata2['timestamp']},
                'time_difference': abs(metadata1['timestamp'] - metadata2['timestamp']),
                'size_difference_mb': metadata1['size_mb'] - metadata2['size_mb']
            }

            # Compare backed up items
            items1 = set(metadata1.get('backed_up_items', []))
            items2 = set(metadata2.get('backed_up_items', []))
            comparison['added_items'] = list(items2 - items1)
            comparison['removed_items'] = list(items1 - items2)
            comparison['common_items'] = list(items1 & items2)

            return comparison

        except Exception as e:
            logger.error(f"Failed to compare rollback points: {e}")
            return {'error': str(e)}

    def get_rollback_stats(self) -> Dict:
        """
        Get rollback statistics.

        Returns:
            Dict with rollback statistics
        """
        rollback_points = self.list_rollback_points()

        stats = {
            'total_rollback_points': len(rollback_points),
            'total_size_mb': sum(p['size_mb'] for p in rollback_points),
            'oldest_point': rollback_points[-1]['timestamp'] if rollback_points else None,
            'newest_point': rollback_points[0]['timestamp'] if rollback_points else None,
            'auto_rollback_enabled': self.auto_rollback_enabled
        }

        return stats

    def _restore_path(self, src_path: str, dest_path: str):
        """Restore a file or directory from rollback."""
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

    def _cleanup_old_rollback_points(self):
        """Clean up old rollback points."""
        rollback_points = self.list_rollback_points()

        if len(rollback_points) > self.max_rollback_points:
            points_to_delete = rollback_points[self.max_rollback_points:]
            for point in points_to_delete:
                self.delete_rollback_point(point['id'])

            logger.info(f"Cleaned up {len(points_to_delete)} old rollback points")

    def _calculate_directory_size(self, directory: str) -> float:
        """Calculate total size of a directory in MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return round(total_size / (1024 * 1024), 2)

    def _get_rollback_metadata(self, rollback_id: str) -> Optional[Dict]:
        """Get metadata for a rollback point."""
        metadata_path = os.path.join(self.rollback_directory, rollback_id, 'metadata.json')
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def _should_rollback(self, failure_context: Dict) -> bool:
        """Determine if auto-rollback should be triggered."""
        # Simple logic: rollback if there are multiple recent failures
        failure_count = failure_context.get('recent_failures', 0)
        severity = failure_context.get('severity', 'low')

        if severity == 'critical' or failure_count > 3:
            return True

        return False
