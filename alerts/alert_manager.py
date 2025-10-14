"""
Alert Manager: Central system for managing and dispatching alerts.
"""

import logging
import time
from typing import Dict, List, Callable, Optional
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    PERFORMANCE = "performance"
    SYSTEM = "system"
    BOT = "bot"
    VISION = "vision"
    STRATEGY = "strategy"

class Alert:
    """Represents an alert in the system."""

    def __init__(self, alert_type: AlertType, severity: AlertSeverity,
                 title: str, message: str, source: str = None,
                 metadata: Dict = None, auto_resolve: bool = False):
        self.id = f"{int(time.time() * 1000)}_{hash(title + message)}"
        self.type = alert_type
        self.severity = severity
        self.title = title
        self.message = message
        self.source = source or "unknown"
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.resolved = False
        self.resolved_at = None
        self.auto_resolve = auto_resolve
        self.resolve_time = None

    def resolve(self):
        """Mark the alert as resolved."""
        self.resolved = True
        self.resolved_at = time.time()

    def to_dict(self) -> Dict:
        """Convert alert to dictionary representation."""
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at,
            'auto_resolve': self.auto_resolve
        }

class AlertManager:
    """
    Central manager for alerts in the ElixirMind system.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_alerts = self.config.get('max_alerts', 1000)
        self.alert_ttl = self.config.get('alert_ttl_seconds', 3600)  # 1 hour

        # Alert storage
        self.active_alerts = {}
        self.resolved_alerts = []

        # Notifier registry
        self.notifiers = []

        # Alert filters and rules
        self.alert_filters = []
        self.suppression_rules = defaultdict(list)

        # Statistics
        self.alert_stats = defaultdict(int)

        logger.info("Alert Manager initialized")

    def register_notifier(self, notifier):
        """
        Register an alert notifier.

        Args:
            notifier: Object with send_alert(alert) method
        """
        self.notifiers.append(notifier)
        logger.info(f"Registered notifier: {type(notifier).__name__}")

    def add_filter(self, filter_func: Callable[[Alert], bool]):
        """
        Add an alert filter function.

        Args:
            filter_func: Function that returns True if alert should be processed
        """
        self.alert_filters.append(filter_func)

    def suppress_alerts(self, alert_type: AlertType, source: str, duration_seconds: int):
        """
        Suppress alerts of a specific type from a source for a duration.

        Args:
            alert_type: Type of alerts to suppress
            source: Source to suppress alerts from
            duration_seconds: How long to suppress alerts
        """
        suppression_key = f"{alert_type.value}:{source}"
        suppress_until = time.time() + duration_seconds
        self.suppression_rules[suppression_key].append(suppress_until)
        logger.info(f"Suppressed {alert_type.value} alerts from {source} for {duration_seconds}s")

    def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                    title: str, message: str, source: str = None,
                    metadata: Dict = None, auto_resolve: bool = False) -> Optional[str]:
        """
        Create and process a new alert.

        Args:
            alert_type: Type of the alert
            severity: Severity level
            title: Alert title
            message: Alert message
            source: Source of the alert
            metadata: Additional metadata
            auto_resolve: Whether to auto-resolve similar alerts

        Returns:
            Alert ID if created, None if filtered/suppressed
        """
        alert = Alert(alert_type, severity, title, message, source, metadata, auto_resolve)

        # Check filters
        if not self._passes_filters(alert):
            return None

        # Check suppression
        if self._is_suppressed(alert):
            return None

        # Auto-resolve similar alerts if requested
        if auto_resolve:
            self._auto_resolve_similar(alert)

        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_stats[f"{alert_type.value}_{severity.value}"] += 1

        # Clean up old alerts
        self._cleanup_old_alerts()

        # Notify
        self._notify_alert(alert)

        logger.warning(f"Alert created: [{severity.value.upper()}] {title}")
        return alert.id

    def resolve_alert(self, alert_id: str):
        """
        Resolve an active alert.

        Args:
            alert_id: ID of the alert to resolve
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            alert.resolve()
            self.resolved_alerts.append(alert)

            # Keep resolved alerts list manageable
            if len(self.resolved_alerts) > self.max_alerts:
                self.resolved_alerts = self.resolved_alerts[-self.max_alerts:]

            logger.info(f"Alert resolved: {alert.title}")

    def get_active_alerts(self, alert_type: AlertType = None,
                         severity: AlertSeverity = None) -> List[Alert]:
        """
        Get active alerts, optionally filtered by type and severity.

        Args:
            alert_type: Filter by alert type
            severity: Filter by severity

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())

        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def get_alert_stats(self) -> Dict:
        """
        Get alert statistics.

        Returns:
            Dict with alert statistics
        """
        return dict(self.alert_stats)

    def clear_resolved_alerts(self, older_than_seconds: int = None):
        """
        Clear resolved alerts.

        Args:
            older_than_seconds: Clear alerts older than this many seconds
        """
        if older_than_seconds:
            cutoff_time = time.time() - older_than_seconds
            self.resolved_alerts = [
                a for a in self.resolved_alerts
                if a.resolved_at and a.resolved_at > cutoff_time
            ]
        else:
            self.resolved_alerts.clear()

        logger.info("Cleared resolved alerts")

    def _passes_filters(self, alert: Alert) -> bool:
        """Check if alert passes all filters."""
        for filter_func in self.alert_filters:
            if not filter_func(alert):
                return False
        return True

    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert is currently suppressed."""
        current_time = time.time()
        suppression_key = f"{alert.type.value}:{alert.source}"

        # Clean up expired suppressions
        self.suppression_rules[suppression_key] = [
            t for t in self.suppression_rules[suppression_key]
            if t > current_time
        ]

        return len(self.suppression_rules[suppression_key]) > 0

    def _auto_resolve_similar(self, new_alert: Alert):
        """Auto-resolve similar active alerts."""
        to_resolve = []
        for alert_id, alert in self.active_alerts.items():
            if (alert.type == new_alert.type and
                alert.source == new_alert.source and
                alert.title == new_alert.title):
                to_resolve.append(alert_id)

        for alert_id in to_resolve:
            self.resolve_alert(alert_id)

    def _notify_alert(self, alert: Alert):
        """Send alert to all registered notifiers."""
        for notifier in self.notifiers:
            try:
                notifier.send_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {type(notifier).__name__}: {e}")

    def _cleanup_old_alerts(self):
        """Clean up old alerts based on TTL."""
        current_time = time.time()
        cutoff_time = current_time - self.alert_ttl

        # Remove old active alerts
        to_remove = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.timestamp < cutoff_time
        ]
        for alert_id in to_remove:
            del self.active_alerts[alert_id]

        # Remove old resolved alerts
        self.resolved_alerts = [
            a for a in self.resolved_alerts
            if a.resolved_at and a.resolved_at > cutoff_time
        ]
