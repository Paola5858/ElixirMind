"""
Discord Notifier: Sends alerts to Discord channels.
"""

import logging
import requests
from typing import Dict, Optional
from .alert_manager import Alert, AlertSeverity

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """
    Sends alerts to Discord webhooks.
    """

    def __init__(self, webhook_url: str, config: Dict = None):
        self.webhook_url = webhook_url
        self.config = config or {}

        # Configuration
        self.username = self.config.get('username', 'ElixirMind Bot')
        self.avatar_url = self.config.get('avatar_url')
        self.mention_role = self.config.get('mention_role')

        # Severity-based colors
        self.colors = {
            AlertSeverity.LOW: 0x00FF00,      # Green
            AlertSeverity.MEDIUM: 0xFFFF00,   # Yellow
            AlertSeverity.HIGH: 0xFF8000,     # Orange
            AlertSeverity.CRITICAL: 0xFF0000  # Red
        }

        # Test webhook
        self._test_webhook()

    def send_alert(self, alert: Alert):
        """
        Send an alert to Discord.

        Args:
            alert: Alert object to send
        """
        embed = self._create_embed(alert)

        payload = {
            'username': self.username,
            'embeds': [embed]
        }

        if self.avatar_url:
            payload['avatar_url'] = self.avatar_url

        # Add mention for high severity alerts
        if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] and self.mention_role:
            payload['content'] = f'<@&{self.mention_role}>'

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Discord alert sent: {alert.title}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord alert: {e}")

    def _create_embed(self, alert: Alert) -> Dict:
        """
        Create a Discord embed for the alert.

        Args:
            alert: Alert object

        Returns:
            Discord embed dict
        """
        embed = {
            'title': f"{alert.severity.value.upper()}: {alert.title}",
            'description': alert.message,
            'color': self.colors.get(alert.severity, 0x000000),
            'timestamp': self._timestamp_to_iso(alert.timestamp),
            'footer': {
                'text': f'Source: {alert.source}'
            }
        }

        # Add fields for metadata
        if alert.metadata:
            fields = []
            for key, value in alert.metadata.items():
                if isinstance(value, (int, float)):
                    value = f"{value:.2f}"
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"
                else:
                    value = str(value)

                fields.append({
                    'name': key.replace('_', ' ').title(),
                    'value': value,
                    'inline': True
                })

            if fields:
                embed['fields'] = fields[:25]  # Discord limit

        return embed

    def _timestamp_to_iso(self, timestamp: float) -> str:
        """
        Convert timestamp to ISO format.

        Args:
            timestamp: Unix timestamp

        Returns:
            ISO formatted timestamp
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.isoformat()

    def _test_webhook(self):
        """Test the webhook URL."""
        try:
            # Send a simple test message
            payload = {
                'username': self.username,
                'content': '🔔 Discord notifier initialized and ready to send alerts.'
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info("Discord webhook test successful")

        except requests.exceptions.RequestException as e:
            logger.error(f"Discord webhook test failed: {e}")
            raise

class DiscordConfig:
    """
    Configuration helper for Discord notifiers.
    """

    @staticmethod
    def create_from_config(config: Dict) -> Optional[DiscordNotifier]:
        """
        Create Discord notifier from configuration.

        Args:
            config: Configuration dict with discord settings

        Returns:
            DiscordNotifier instance or None if not configured
        """
        discord_config = config.get('discord', {})
        webhook_url = discord_config.get('webhook_url')

        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return None

        try:
            return DiscordNotifier(
                webhook_url=webhook_url,
                config=discord_config
            )
        except Exception as e:
            logger.error(f"Failed to create Discord notifier: {e}")
            return None
