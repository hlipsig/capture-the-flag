"""
Unit tests for GitHub integration (agent/github_integration.py).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent.github_integration import GitHubIssueManager


@pytest.fixture
def mock_github():
    """Mock GitHub API."""
    with patch("agent.github_integration.Github") as mock_gh:
        mock_repo = Mock()
        mock_gh.return_value.get_repo.return_value = mock_repo
        yield mock_gh, mock_repo


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
            "whois": {
                "org": "Example ISP",
                "asn": "12345",
                "country": "US",
                "net_range": "203.0.113.0/24",
                "abuse_contact": "abuse@example.com",
            },
            "reverse_dns": {"ptr": "host.example.com", "provider_guess": "AWS"},
            "shodan": {"open_ports": [22, 80, 443], "os": "Linux"},
            "cert_transparency": {"certificates": ["example.com", "www.example.com"]},
        }
    }


@pytest.fixture
def sample_actions():
    """Sample actions list."""
    return [
        {
            "name": "Redirect to honeypot",
            "timestamp": "2024-06-15T03:14:10Z",
            "result": "success",
            "success": True,
        },
        {
            "name": "Run OSINT",
            "timestamp": "2024-06-15T03:14:12Z",
            "result": "success",
            "success": True,
        },
    ]


@pytest.fixture
def sample_timeline():
    """Sample timeline."""
    return [
        {"timestamp": "2024-06-15T03:14:07Z", "description": "Detection triggered"},
        {"timestamp": "2024-06-15T03:14:10Z", "description": "Redirected to honeypot"},
    ]


class TestGitHubIssueManager:
    """Test GitHub issue creation."""

    def test_initialization_with_token(self, mock_github):
        """Test initialization with provided token."""
        mock_gh, mock_repo = mock_github

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        assert mgr.token == "test_token"
        assert mgr.repo_name == "owner/repo"
        mock_gh.assert_called_once_with("test_token")

    def test_initialization_from_env(self, mock_github, monkeypatch):
        """Test initialization from environment variables."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        monkeypatch.setenv("GITHUB_REPO", "env_owner/env_repo")

        mock_gh, mock_repo = mock_github

        mgr = GitHubIssueManager()

        assert mgr.token == "env_token"
        assert mgr.repo_name == "env_owner/env_repo"

    def test_missing_token_raises_error(self, monkeypatch):
        """Test error when token is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            GitHubIssueManager()

    def test_create_incident_issue(
        self,
        mock_github,
        sample_detection,
        sample_osint,
        sample_actions,
        sample_timeline,
    ):
        """Test incident issue creation."""
        mock_gh, mock_repo = mock_github
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/owner/repo/issues/123"
        mock_repo.create_issue.return_value = mock_issue

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        issue = mgr.create_incident_issue(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            timeline=sample_timeline,
            recommendations=["Review OSINT", "Check for campaign"],
        )

        assert issue is not None
        assert issue.number == 123
        mock_repo.create_issue.assert_called_once()

        # Check issue title
        call_args = mock_repo.create_issue.call_args
        assert "[INC-TEST-001]" in call_args.kwargs["title"]
        assert "Nmap Port Scan" in call_args.kwargs["title"]

    def test_issue_body_contains_details(
        self,
        mock_github,
        sample_detection,
        sample_osint,
        sample_actions,
        sample_timeline,
    ):
        """Test issue body contains all required details."""
        mock_gh, mock_repo = mock_github
        mock_issue = Mock()
        mock_repo.create_issue.return_value = mock_issue

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        mgr.create_incident_issue(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            timeline=sample_timeline,
            recommendations=["Test recommendation"],
        )

        call_args = mock_repo.create_issue.call_args
        body = call_args.kwargs["body"]

        # Check body contains key information
        assert "INC-TEST-001" in body
        assert "203.0.113.42" in body
        assert "0.97" in body
        assert "Example ISP" in body
        assert "Redirect to honeypot" in body

    def test_labels_applied_correctly(
        self,
        mock_github,
        sample_detection,
        sample_osint,
        sample_actions,
        sample_timeline,
    ):
        """Test correct labels are applied to issue."""
        mock_gh, mock_repo = mock_github
        mock_issue = Mock()
        mock_repo.create_issue.return_value = mock_issue

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        mgr.create_incident_issue(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            timeline=sample_timeline,
            recommendations=[],
        )

        call_args = mock_repo.create_issue.call_args
        labels = call_args.kwargs["labels"]

        assert "security" in labels
        assert "incident" in labels
        assert "automated" in labels
        assert "severity:high" in labels  # confidence 0.97
        assert "attack:recon" in labels  # Nmap scan

    def test_osint_comment_posted(
        self,
        mock_github,
        sample_detection,
        sample_osint,
        sample_actions,
        sample_timeline,
    ):
        """Test OSINT dossier is posted as comment."""
        mock_gh, mock_repo = mock_github
        mock_issue = Mock()
        mock_repo.create_issue.return_value = mock_issue

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        mgr.create_incident_issue(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            timeline=sample_timeline,
            recommendations=[],
        )

        # Verify comment was created
        mock_issue.create_comment.assert_called()

        # Check first comment (OSINT dossier)
        first_comment = mock_issue.create_comment.call_args_list[0][0][0]
        assert "OSINT Dossier" in first_comment
        assert "203.0.113.42" in first_comment
        assert "Example ISP" in first_comment
        assert "AS12345" in first_comment

    def test_audit_comment_posted(
        self,
        mock_github,
        sample_detection,
        sample_osint,
        sample_actions,
        sample_timeline,
    ):
        """Test audit trail is posted as comment."""
        mock_gh, mock_repo = mock_github
        mock_issue = Mock()
        mock_repo.create_comment.return_value = None
        mock_repo.create_issue.return_value = mock_issue

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        mgr.create_incident_issue(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            timeline=sample_timeline,
            recommendations=[],
        )

        # Verify two comments were created (OSINT + audit)
        assert mock_issue.create_comment.call_count == 2

        # Check second comment (audit trail)
        second_comment = mock_issue.create_comment.call_args_list[1][0][0]
        assert "Audit Trail" in second_comment
        assert "Redirect to honeypot" in second_comment

    def test_close_incident_issue(self, mock_github):
        """Test closing an incident issue."""
        mock_gh, mock_repo = mock_github
        mock_issue = Mock()
        mock_repo.get_issue.return_value = mock_issue

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        result = mgr.close_incident_issue(123, resolution="resolved")

        assert result is True
        mock_repo.get_issue.assert_called_with(123)
        mock_issue.create_comment.assert_called_once()
        mock_issue.edit.assert_called_with(state="closed")

    def test_get_open_incidents(self, mock_github):
        """Test getting open incidents."""
        mock_gh, mock_repo = mock_github
        mock_issues = [Mock(), Mock(), Mock()]
        mock_repo.get_issues.return_value = mock_issues

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        issues = mgr.get_open_incidents()

        assert len(issues) == 3
        mock_repo.get_issues.assert_called_with(state="open", labels=["incident"])

    def test_error_handling_on_api_failure(
        self,
        mock_github,
        sample_detection,
        sample_osint,
        sample_actions,
        sample_timeline,
    ):
        """Test error handling when GitHub API fails."""
        from github import GithubException

        mock_gh, mock_repo = mock_github
        mock_repo.create_issue.side_effect = GithubException(
            status=403, data={"message": "Forbidden"}, headers={}
        )

        mgr = GitHubIssueManager(token="test_token", repo_name="owner/repo")

        issue = mgr.create_incident_issue(
            incident_id="INC-TEST-001",
            attacker_ip="203.0.113.42",
            detection=sample_detection,
            osint_data=sample_osint,
            actions=sample_actions,
            timeline=sample_timeline,
            recommendations=[],
        )

        # Should return None on failure
        assert issue is None
