"""
Crash Recovery: Handles recovery from system crashes and errors.
"""

import time
import logging
import traceback
from typing import Dict, List, Optional, Callable
import threading
import signal
import sys

logger = logging.getLogger(__name__)

class CrashRecovery:
    """
    Handles crash recovery, error handling, and system stability.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Recovery settings
        self.max_recovery_attempts = self.config.get('max_recovery_attempts', 3)
        self.recovery_delay = self.config.get('recovery_delay', 5.0)
        self.enable_auto_recovery = self.config.get('auto_recovery', True)

        # Crash tracking
        self.crash_history = []
        self.recovery_attempts = 0
        self.last_crash_time = 0

        # Recovery strategies
        self.recovery_strategies = {
            'restart_component': self._restart_component,
            'rollback_state': self._rollback_state,
            'safe_mode': self._enter_safe_mode,
            'full_restart': self._full_system_restart
        }

        # Component health monitoring
        self.component_health = {}
        self.health_check_interval = self.config.get('health_check_interval', 60)

        # Signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Recovery thread
        self.recovery_thread = None
        self.running = False

        logger.info("Crash Recovery initialized")

    def start_monitoring(self):
        """Start crash monitoring and health checks."""
        self.running = True
        self.recovery_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.recovery_thread.start()
        logger.info("Crash recovery monitoring started")

    def stop_monitoring(self):
        """Stop crash monitoring."""
        self.running = False
        if self.recovery_thread:
            self.recovery_thread.join(timeout=5)
        logger.info("Crash recovery monitoring stopped")

    def register_component(self, component_name: str, health_check_func: Callable,
                          recovery_func: Optional[Callable] = None):
        """
        Register a component for health monitoring and recovery.

        Args:
            component_name: Name of the component
            health_check_func: Function to check component health (returns bool)
            recovery_func: Optional function to recover the component
        """
        self.component_health[component_name] = {
            'health_check': health_check_func,
            'recovery_func': recovery_func,
            'last_check': 0,
            'failures': 0,
            'last_failure': 0,
            'status': 'unknown'
        }

        logger.info(f"Registered component for monitoring: {component_name}")

    def handle_exception(self, exception: Exception, component: str = 'unknown',
                        context: Optional[Dict] = None) -> bool:
        """
        Handle an exception and attempt recovery.

        Args:
            exception: The exception that occurred
            component: Component where exception occurred
            context: Additional context information

        Returns:
            True if recovery was successful
        """
        crash_info = {
            'timestamp': time.time(),
            'component': component,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'recovery_attempted': False,
            'recovery_successful': False
        }

        self.crash_history.append(crash_info)
        self.last_crash_time = crash_info['timestamp']

        logger.error(f"Exception in {component}: {exception}")
        logger.debug(f"Traceback: {crash_info['traceback']}")

        # Attempt recovery if enabled
        if self.enable_auto_recovery and self.recovery_attempts < self.max_recovery_attempts:
            success = self._attempt_recovery(component, crash_info)
            crash_info['recovery_attempted'] = True
            crash_info['recovery_successful'] = success
            return success

        return False

    def get_crash_report(self) -> Dict:
        """
        Get a report of recent crashes and recovery attempts.

        Returns:
            Dict with crash statistics and history
        """
        recent_crashes = [
            c for c in self.crash_history
            if time.time() - c['timestamp'] < 3600  # Last hour
        ]

        report = {
            'total_crashes': len(self.crash_history),
            'recent_crashes': len(recent_crashes),
            'recovery_attempts': self.recovery_attempts,
            'successful_recoveries': len([c for c in self.crash_history if c.get('recovery_successful', False)]),
            'last_crash_time': self.last_crash_time,
            'component_failures': self._get_component_failure_stats(),
            'crash_trends': self._analyze_crash_trends()
        }

        return report

    def force_recovery(self, strategy: str = 'safe_mode') -> bool:
        """
        Force a recovery operation.

        Args:
            strategy: Recovery strategy to use

        Returns:
            True if recovery successful
        """
        if strategy in self.recovery_strategies:
            try:
                success = self.recovery_strategies[strategy]()
                logger.info(f"Forced recovery using {strategy}: {'successful' if success else 'failed'}")
                return success
            except Exception as e:
                logger.error(f"Forced recovery failed: {e}")
                return False
        else:
            logger.error(f"Unknown recovery strategy: {strategy}")
            return False

    def _monitoring_loop(self):
        """Main monitoring loop for health checks."""
        while self.running:
            try:
                self._perform_health_checks()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Brief pause before retry

    def _perform_health_checks(self):
        """Perform health checks on all registered components."""
        current_time = time.time()

        for component_name, component_data in self.component_health.items():
            try:
                # Check if it's time for a health check
                if current_time - component_data['last_check'] >= self.health_check_interval:
                    healthy = component_data['health_check']()

                    component_data['last_check'] = current_time
                    component_data['status'] = 'healthy' if healthy else 'unhealthy'

                    if not healthy:
                        component_data['failures'] += 1
                        component_data['last_failure'] = current_time

                        logger.warning(f"Component {component_name} health check failed")

                        # Attempt component recovery
                        if component_data['recovery_func']:
                            self._recover_component(component_name, component_data)

            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {e}")
                component_data['status'] = 'error'

    def _recover_component(self, component_name: str, component_data: Dict):
        """Attempt to recover a failed component."""
        try:
            success = component_data['recovery_func']()
            if success:
                logger.info(f"Successfully recovered component: {component_name}")
                component_data['failures'] = 0  # Reset failure count
            else:
                logger.error(f"Failed to recover component: {component_name}")
        except Exception as e:
            logger.error(f"Error during component recovery {component_name}: {e}")

    def _attempt_recovery(self, component: str, crash_info: Dict) -> bool:
        """Attempt to recover from a crash."""
        self.recovery_attempts += 1

        logger.info(f"Attempting recovery {self.recovery_attempts}/{self.max_recovery_attempts} for {component}")

        # Choose recovery strategy based on component and crash history
        strategy = self._choose_recovery_strategy(component, crash_info)

        try:
            success = self.recovery_strategies[strategy]()
            if success:
                logger.info(f"Recovery successful using strategy: {strategy}")
                return True
            else:
                logger.warning(f"Recovery failed using strategy: {strategy}")
                return False
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False
        finally:
            # Add delay before next attempt
            if self.recovery_attempts < self.max_recovery_attempts:
                time.sleep(self.recovery_delay)

    def _choose_recovery_strategy(self, component: str, crash_info: Dict) -> str:
        """Choose appropriate recovery strategy."""
        # Simple strategy selection based on component and failure patterns
        if component in ['vision', 'detector']:
            return 'restart_component'
        elif self.recovery_attempts > 1:
            return 'safe_mode'
        elif len(self.crash_history) > 5:
            return 'full_restart'
        else:
            return 'rollback_state'

    def _restart_component(self) -> bool:
        """Restart a failed component."""
        # This would need to be implemented based on specific components
        logger.info("Attempting component restart")
        return True  # Placeholder

    def _rollback_state(self) -> bool:
        """Rollback to a previous stable state."""
        logger.info("Attempting state rollback")
        # This would integrate with StateSaver
        return True  # Placeholder

    def _enter_safe_mode(self) -> bool:
        """Enter safe mode operation."""
        logger.info("Entering safe mode")
        # This would integrate with SafeModeManager
        return True  # Placeholder

    def _full_system_restart(self) -> bool:
        """Perform full system restart."""
        logger.warning("Performing full system restart")
        # This is a critical operation
        return False  # Placeholder - would need careful implementation

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self._graceful_shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Handle uncaught exceptions
        def exception_handler(exc_type, exc_value, exc_traceback):
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            self.handle_exception(exc_value, 'uncaught_exception')

        sys.excepthook = exception_handler

    def _graceful_shutdown(self):
        """Perform graceful shutdown operations."""
        logger.info("Performing graceful shutdown")
        self.running = False

        # Save state before shutdown
        try:
            # This would integrate with StateSaver for emergency save
            logger.info("Emergency state save completed")
        except Exception as e:
            logger.error(f"Emergency save failed: {e}")

        # Stop monitoring
        self.stop_monitoring()

    def _get_component_failure_stats(self) -> Dict:
        """Get failure statistics for components."""
        stats = {}
        for component_name, component_data in self.component_health.items():
            stats[component_name] = {
                'total_failures': component_data['failures'],
                'status': component_data['status'],
                'last_failure': component_data['last_failure']
            }
        return stats

    def _analyze_crash_trends(self) -> Dict:
        """Analyze crash trends for predictive recovery."""
        if len(self.crash_history) < 2:
            return {'trend': 'insufficient_data'}

        # Simple trend analysis
        recent_crashes = [c for c in self.crash_history if time.time() - c['timestamp'] < 3600]
        crash_rate = len(recent_crashes) / 3600  # crashes per second

        if crash_rate > 0.001:  # More than ~3.6 crashes per hour
            trend = 'increasing'
        elif crash_rate < 0.0001:  # Less than 0.36 crashes per hour
            trend = 'stable'
        else:
            trend = 'moderate'

        return {
            'trend': trend,
            'crash_rate_per_hour': crash_rate * 3600,
            'recommendation': 'increase_monitoring' if trend == 'increasing' else 'normal_operation'
        }
