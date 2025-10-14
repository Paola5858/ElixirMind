"""
Safe Mode Manager: Manages safe mode operations and emergency protocols.
"""

import time
import logging
from typing import Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class SafeModeLevel(Enum):
    NORMAL = "normal"
    CAUTIOUS = "cautious"
    SAFE = "safe"
    EMERGENCY = "emergency"

class SafeModeManager:
    """
    Manages safe mode operations, emergency protocols, and system safety measures.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Safe mode settings
        self.current_mode = SafeModeLevel.NORMAL
        self.auto_escalation = self.config.get('auto_escalation', True)
        self.emergency_thresholds = self.config.get('emergency_thresholds', {})

        # Safety monitors
        self.safety_monitors = {}
        self.monitor_callbacks = {}

        # Emergency protocols
        self.emergency_protocols = {
            SafeModeLevel.CAUTIOUS: self._cautious_protocol,
            SafeModeLevel.SAFE: self._safe_protocol,
            SafeModeLevel.EMERGENCY: self._emergency_protocol
        }

        # Mode history
        self.mode_history = []
        self.last_mode_change = time.time()

        # Safety statistics
        self.safety_stats = {
            'mode_changes': 0,
            'emergency_triggers': 0,
            'safety_violations': 0,
            'recovery_attempts': 0
        }

        logger.info("Safe Mode Manager initialized")

    def register_safety_monitor(self, monitor_name: str, monitor_func: Callable,
                               threshold: float, escalation_level: SafeModeLevel):
        """
        Register a safety monitor.

        Args:
            monitor_name: Name of the monitor
            monitor_func: Function that returns a safety value (0-1, higher is safer)
            threshold: Threshold for triggering escalation
            escalation_level: Level to escalate to when threshold is crossed
        """
        self.safety_monitors[monitor_name] = {
            'function': monitor_func,
            'threshold': threshold,
            'escalation_level': escalation_level,
            'last_value': 1.0,
            'violation_count': 0
        }

        logger.info(f"Registered safety monitor: {monitor_name}")

    def check_safety_status(self) -> Dict:
        """
        Check all safety monitors and return current status.

        Returns:
            Dict with safety status information
        """
        status = {
            'current_mode': self.current_mode.value,
            'monitors': {},
            'violations': [],
            'recommendations': []
        }

        for monitor_name, monitor_data in self.safety_monitors.items():
            try:
                current_value = monitor_data['function']()
                monitor_data['last_value'] = current_value

                status['monitors'][monitor_name] = {
                    'value': current_value,
                    'threshold': monitor_data['threshold'],
                    'status': 'safe' if current_value >= monitor_data['threshold'] else 'unsafe'
                }

                # Check for violations
                if current_value < monitor_data['threshold']:
                    monitor_data['violation_count'] += 1
                    status['violations'].append({
                        'monitor': monitor_name,
                        'value': current_value,
                        'threshold': monitor_data['threshold'],
                        'escalation_level': monitor_data['escalation_level'].value
                    })

                    # Auto-escalation if enabled
                    if self.auto_escalation:
                        self.escalate_mode(monitor_data['escalation_level'],
                                         f"Safety violation in {monitor_name}")

            except Exception as e:
                logger.error(f"Error in safety monitor {monitor_name}: {e}")
                status['monitors'][monitor_name] = {'error': str(e)}

        # Generate recommendations
        status['recommendations'] = self._generate_safety_recommendations(status)

        return status

    def escalate_mode(self, new_mode: SafeModeLevel, reason: str):
        """
        Escalate to a higher safety mode.

        Args:
            new_mode: New safe mode level
            reason: Reason for escalation
        """
        if new_mode.value > self.current_mode.value:  # Only escalate up
            old_mode = self.current_mode
            self.current_mode = new_mode

            # Record mode change
            mode_change = {
                'timestamp': time.time(),
                'from_mode': old_mode.value,
                'to_mode': new_mode.value,
                'reason': reason,
                'auto_escalation': True
            }
            self.mode_history.append(mode_change)
            self.last_mode_change = time.time()
            self.safety_stats['mode_changes'] += 1

            # Execute emergency protocol
            if new_mode in self.emergency_protocols:
                self.emergency_protocols[new_mode]()

            logger.warning(f"Safe mode escalated: {old_mode.value} -> {new_mode.value} ({reason})")

    def deescalate_mode(self, new_mode: SafeModeLevel, reason: str):
        """
        De-escalate to a lower safety mode (manual only).

        Args:
            new_mode: New safe mode level
            reason: Reason for de-escalation
        """
        if new_mode.value < self.current_mode.value:  # Only de-escalate down
            old_mode = self.current_mode
            self.current_mode = new_mode

            # Record mode change
            mode_change = {
                'timestamp': time.time(),
                'from_mode': old_mode.value,
                'to_mode': new_mode.value,
                'reason': reason,
                'auto_escalation': False
            }
            self.mode_history.append(mode_change)
            self.last_mode_change = time.time()
            self.safety_stats['mode_changes'] += 1

            logger.info(f"Safe mode de-escalated: {old_mode.value} -> {new_mode.value} ({reason})")

    def apply_mode_restrictions(self, action: Dict) -> Dict:
        """
        Apply current mode restrictions to an action.

        Args:
            action: Bot action to modify

        Returns:
            Modified action with safety restrictions applied
        """
        if self.current_mode == SafeModeLevel.CAUTIOUS:
            action = self._apply_cautious_restrictions(action)
        elif self.current_mode == SafeModeLevel.SAFE:
            action = self._apply_safe_restrictions(action)
        elif self.current_mode == SafeModeLevel.EMERGENCY:
            action = self._apply_emergency_restrictions(action)

        return action

    def get_mode_history(self) -> List[Dict]:
        """
        Get history of mode changes.

        Returns:
            List of mode change records
        """
        return self.mode_history.copy()

    def get_safety_stats(self) -> Dict:
        """
        Get safety statistics.

        Returns:
            Dict with safety statistics
        """
        stats = self.safety_stats.copy()
        stats['current_mode'] = self.current_mode.value
        stats['time_in_current_mode'] = time.time() - self.last_mode_change
        stats['total_monitors'] = len(self.safety_monitors)

        return stats

    def _cautious_protocol(self):
        """Execute cautious mode protocol."""
        logger.info("Executing cautious mode protocol")
        # Reduce action frequency, increase delays, enable extra validation
        self.safety_stats['emergency_triggers'] += 1

    def _safe_protocol(self):
        """Execute safe mode protocol."""
        logger.warning("Executing safe mode protocol")
        # Further reduce activity, enable conservative behavior
        self.safety_stats['emergency_triggers'] += 1

    def _emergency_protocol(self):
        """Execute emergency protocol."""
        logger.critical("Executing emergency protocol - system may shut down")
        # Emergency shutdown or minimal operation mode
        self.safety_stats['emergency_triggers'] += 1

    def _apply_cautious_restrictions(self, action: Dict) -> Dict:
        """Apply cautious mode restrictions."""
        # Increase delays
        if 'delay' in action:
            action['delay'] *= 1.5
        else:
            action['delay'] = 0.5

        # Reduce speed/accuracy expectations
        if 'speed' in action:
            action['speed'] *= 0.7
        if 'accuracy' in action:
            action['accuracy'] *= 0.8

        action['caution_mode'] = True
        return action

    def _apply_safe_restrictions(self, action: Dict) -> Dict:
        """Apply safe mode restrictions."""
        # Significant delays and restrictions
        action['delay'] = max(action.get('delay', 0), 2.0)
        action['speed'] = min(action.get('speed', 1.0), 0.3)
        action['accuracy'] = min(action.get('accuracy', 1.0), 0.6)

        action['safe_mode'] = True
        return action

    def _apply_emergency_restrictions(self, action: Dict) -> Dict:
        """Apply emergency restrictions."""
        # Minimal operation or shutdown
        if random.random() < 0.8:  # 80% chance to skip action
            action['cancelled'] = True
            action['reason'] = 'emergency_mode'
        else:
            # Very conservative action
            action['delay'] = max(action.get('delay', 0), 5.0)
            action['emergency_mode'] = True

        return action

    def _generate_safety_recommendations(self, status: Dict) -> List[str]:
        """Generate safety recommendations based on current status."""
        recommendations = []

        violations = status.get('violations', [])
        if violations:
            recommendations.append(f"Address {len(violations)} safety violations")

        current_mode = status.get('current_mode')
        if current_mode == 'emergency':
            recommendations.append("Consider system shutdown or manual intervention")
        elif current_mode == 'safe':
            recommendations.append("Monitor system closely and consider gradual recovery")
        elif current_mode == 'cautious':
            recommendations.append("Continue cautious operation and monitor improvements")

        # Monitor-specific recommendations
        monitors = status.get('monitors', {})
        for monitor_name, monitor_data in monitors.items():
            if monitor_data.get('status') == 'unsafe':
                recommendations.append(f"Investigate issues with {monitor_name}")

        return recommendations

    def reset_violation_counts(self):
        """Reset violation counts for all monitors."""
        for monitor_data in self.safety_monitors.values():
            monitor_data['violation_count'] = 0
        logger.info("Reset violation counts")

    def force_emergency_shutdown(self, reason: str):
        """Force emergency shutdown."""
        self.escalate_mode(SafeModeLevel.EMERGENCY, f"Forced shutdown: {reason}")
        logger.critical(f"Emergency shutdown initiated: {reason}")

        # Could implement actual shutdown logic here
        # self._perform_emergency_shutdown()
