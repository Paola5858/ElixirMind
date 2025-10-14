"""
Email Notifier: Sends alerts via email.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from .alert_manager import Alert, AlertSeverity

logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Sends alerts via email using SMTP.
    """

    def __init__(self, smtp_server: str, smtp_port: int, username: str,
                 password: str, from_email: str, config: Dict = None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.config = config or {}

        # Configuration
        self.use_tls = self.config.get('use_tls', True)
        self.recipients = self.config.get('recipients', [])
        self.subject_prefix = self.config.get('subject_prefix', '[ElixirMind Alert]')

        # Severity-based settings
        self.severity_recipients = self.config.get('severity_recipients', {})

        # Test connection
        self._test_connection()

    def send_alert(self, alert: Alert):
        """
        Send an alert via email.

        Args:
            alert: Alert object to send
        """
        recipients = self._get_recipients_for_alert(alert)

        if not recipients:
            logger.warning(f"No recipients configured for alert: {alert.title}")
            return

        subject = f"{self.subject_prefix} {alert.severity.value.upper()}: {alert.title}"
        body = self._create_email_body(alert)

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg, self.from_email, recipients)

            logger.info(f"Email alert sent to {len(recipients)} recipients: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def add_recipient(self, email: str, severity_levels: List[AlertSeverity] = None):
        """
        Add an email recipient.

        Args:
            email: Email address
            severity_levels: List of severity levels this recipient should receive
        """
        if severity_levels:
            for severity in severity_levels:
                if severity.value not in self.severity_recipients:
                    self.severity_recipients[severity.value] = []
                self.severity_recipients[severity.value].append(email)
        else:
            self.recipients.append(email)

        logger.info(f"Added email recipient: {email}")

    def _get_recipients_for_alert(self, alert: Alert) -> List[str]:
        """
        Get recipients for a specific alert based on severity.

        Args:
            alert: Alert object

        Returns:
            List of email addresses
        """
        recipients = set(self.recipients)  # Default recipients

        # Add severity-specific recipients
        severity_recipients = self.severity_recipients.get(alert.severity.value, [])
        recipients.update(severity_recipients)

        return list(recipients)

    def _create_email_body(self, alert: Alert) -> str:
        """
        Create HTML email body for the alert.

        Args:
            alert: Alert object

        Returns:
            HTML email body
        """
        severity_colors = {
            AlertSeverity.LOW: '#28a745',
            AlertSeverity.MEDIUM: '#ffc107',
            AlertSeverity.HIGH: '#fd7e14',
            AlertSeverity.CRITICAL: '#dc3545'
        }

        color = severity_colors.get(alert.severity, '#6c757d')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert-header {{ background-color: {color}; color: white; padding: 10px; border-radius: 5px; }}
                .alert-content {{ margin: 20px 0; }}
                .metadata {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; }}
                .metadata table {{ width: 100%; border-collapse: collapse; }}
                .metadata th, .metadata td {{ padding: 5px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            </style>
        </head>
        <body>
            <div class="alert-header">
                <h2>{alert.severity.value.upper()}: {alert.title}</h2>
            </div>

            <div class="alert-content">
                <p><strong>Source:</strong> {alert.source}</p>
                <p><strong>Time:</strong> {self._timestamp_to_readable(alert.timestamp)}</p>
                <p>{alert.message}</p>
            </div>
        """

        if alert.metadata:
            html += '<div class="metadata"><h3>Additional Information</h3><table>'
            for key, value in alert.metadata.items():
                if isinstance(value, (int, float)):
                    value = f"{value:.2f}"
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"
                else:
                    value = str(value)

                html += f"<tr><th>{key.replace('_', ' ').title()}</th><td>{value}</td></tr>"
            html += '</table></div>'

        html += """
            <hr>
            <p><small>This alert was generated by ElixirMind Bot monitoring system.</small></p>
        </body>
        </html>
        """

        return html

    def _timestamp_to_readable(self, timestamp: float) -> str:
        """
        Convert timestamp to readable format.

        Args:
            timestamp: Unix timestamp

        Returns:
            Readable timestamp string
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

    def _test_connection(self):
        """Test SMTP connection."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
            logger.info("Email SMTP connection test successful")

        except Exception as e:
            logger.error(f"Email SMTP connection test failed: {e}")
            raise

class EmailConfig:
    """
    Configuration helper for email notifiers.
    """

    @staticmethod
    def create_from_config(config: Dict) -> Optional[EmailNotifier]:
        """
        Create email notifier from configuration.

        Args:
            config: Configuration dict with email settings

        Returns:
            EmailNotifier instance or None if not configured
        """
        email_config = config.get('email', {})

        required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'from_email']
        if not all(field in email_config for field in required_fields):
            logger.warning("Email configuration incomplete")
            return None

        try:
            notifier = EmailNotifier(
                smtp_server=email_config['smtp_server'],
                smtp_port=email_config['smtp_port'],
                username=email_config['username'],
                password=email_config['password'],
                from_email=email_config['from_email'],
                config=email_config
            )

            # Add recipients
            recipients = email_config.get('recipients', [])
            for recipient in recipients:
                notifier.add_recipient(recipient)

            return notifier

        except Exception as e:
            logger.error(f"Failed to create email notifier: {e}")
            return None
