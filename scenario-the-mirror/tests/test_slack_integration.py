"""
Unit tests for Slack integration (agent/slack_integration.py).
"""

import pytest
from unittest.mock import Mock, patch
from agent.slack_integration import SlackNotifier


@pytest.fixture
def sample_detection():
    """Sample detection data."""
    return {
        "signature": "Nmap Port Scan Detected",
        "confidence": 0.97,
        "timestamp": "2024-06-15T03:14:07Z",
    }


@pytest.fixture
def sample_osint():
    """Sample OSINT data."""
    return {
        "modules": {
            "whois": {"org": "Example ISP", "country": "US"},
            "reverse_dns": {"ptr": "host.example.com"},
            "shodan": {"open_ports": [22, 80]},
            "cert_transparency": {"certificates": []},
        }
    }


@pytest.fixture
def sample_actions():
    """Sample actions."""
    return [
        {"name": "Redirect to honeypot", "timestamp": "2024-06-15T03:14:10Z"},
        {"name": "Run OSINT", "timestamp": "2024-06-15T03:14:12Z"},
    ]


class TestSlackNotifier:
    """Test Slack notifications."""

    def test_initialization_with_webhook(self):
        """Test initialization with webhook URL."""
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        assert notifier.webhook_url == "https://hooks.slack.com/test"
        assert notifier.enabled is True

    def test_initialization_from_env(self, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/env")

        notifier = SlackNotifier()

        assert notifier.webhook_url == "https://hooks.slack.com/env"
        assert notifier.enabled is True

    def test_missing_webhook_disables_notifications(self, monkeypatch):
        """Test Slack is disabled when webhook is missing."""
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

        notifier = SlackNotifier()

        assert notifier.enabled is False

    @patch("agent.slack_integration.requests.post")
    def test_send_incident_notification(
        self, mock_post, sample_detection, sample_osint, sample_actions
    ):
        """Test sending incident notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        result = notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            github_issue_url="https://github.com/owner/repo/issues/123",
        )

        assert result is True
        mock_post.assert_called_once()

        # Check payload structure
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]

        assert "blocks" in payload
        blocks = payload["blocks"]

        # Check header block
        assert blocks[0]["type"] == "header"
        assert "New Security Incident" in blocks[0]["text"]["text"]

    @patch("agent.slack_integration.requests.post")
    def test_notification_contains_incident_details(
        self, mock_post, sample_detection, sample_osint, sample_actions
    ):
        """Test notification contains all incident details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
        )

        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        blocks = payload["blocks"]

        # Convert blocks to string for easy searching
        blocks_str = str(blocks)

        assert "INC-TEST-001" in blocks_str
        assert "203.0.113.42" in blocks_str
        assert "Example ISP" in blocks_str
        assert "Nmap Port Scan" in blocks_str
        assert "0.97" in blocks_str

    @patch("agent.slack_integration.requests.post")
    def test_notification_includes_github_link(
        self, mock_post, sample_detection, sample_osint, sample_actions
    ):
        """Test GitHub issue link is included when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        github_url = "https://github.com/owner/repo/issues/123"

        notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            github_issue_url=github_url,
        )

        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        blocks_str = str(payload["blocks"])

        assert github_url in blocks_str
        assert "View Full Report" in blocks_str

    @patch("agent.slack_integration.requests.post")
    def test_notification_shows_top_actions(
        self, mock_post, sample_detection, sample_osint
    ):
        """Test notification shows top 3 actions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        # Provide 5 actions, only top 3 should appear
        many_actions = [
            {"name": "Action 1"},
            {"name": "Action 2"},
            {"name": "Action 3"},
            {"name": "Action 4"},
            {"name": "Action 5"},
        ]

        notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=many_actions,
        )

        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        blocks_str = str(payload["blocks"])

        assert "Action 1" in blocks_str
        assert "Action 2" in blocks_str
        assert "Action 3" in blocks_str

    @patch("agent.slack_integration.requests.post")
    def test_send_simple_message(self, mock_post):
        """Test sending simple text message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        result = notifier.send_simple_message("Test message")

        assert result is True
        mock_post.assert_called_once()

        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]

        assert payload["text"] == "Test message"

    @patch("agent.slack_integration.requests.post")
    def test_error_handling_on_api_failure(
        self, mock_post, sample_detection, sample_osint, sample_actions
    ):
        """Test error handling when Slack API fails."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        result = notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
        )

        assert result is False

    @patch("agent.slack_integration.requests.post")
    def test_timeout_handling(
        self, mock_post, sample_detection, sample_osint, sample_actions
    ):
        """Test handling of request timeout."""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        result = notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
        )

        assert result is False

    def test_disabled_notifier_returns_false(
        self, sample_detection, sample_osint, sample_actions, monkeypatch
    ):
        """Test disabled notifier returns False without making requests."""
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

        notifier = SlackNotifier()

        result = notifier.send_incident_notification(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
        )

        assert result is False
