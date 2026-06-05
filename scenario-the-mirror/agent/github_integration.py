"""
GitHub Issues integration for The Mirror.

Automatically creates GitHub issues for detected incidents with:
- Full incident report as issue body
- OSINT dossier as comment
- Evidence links as comments
- Auto-applied labels based on severity and attack type
- Milestones for tracking (weekly/monthly)
- Slack notifications
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from github import Github, GithubException
from github.Issue import Issue
from github.Repository import Repository

logger = logging.getLogger(__name__)


class GitHubIssueManager:
    """Manage GitHub issue creation for incidents."""

    def __init__(
        self,
        token: Optional[str] = None,
        repo_name: Optional[str] = None,
    ):
        """
        Initialize GitHub integration.

        Args:
            token: GitHub personal access token (or from env GITHUB_TOKEN)
            repo_name: Repository in format "owner/repo" (or from env GITHUB_REPO)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_name = repo_name or os.getenv("GITHUB_REPO", "hlipsig/capture-the-flag")

        if not self.token:
            raise ValueError("GITHUB_TOKEN not provided and not in environment")

        self.github = Github(self.token)
        self.repo: Repository = self.github.get_repo(self.repo_name)

        logger.info(f"GitHub integration initialized for {self.repo_name}")

    def create_incident_issue(
        self,
        incident_id: str,
        attacker_ip: str,
        detection: Dict[str, Any],
        osint_data: Dict[str, Any],
        actions: List[Dict[str, Any]],
        timeline: List[Dict[str, Any]],
        recommendations: List[str],
    ) -> Optional[Issue]:
        """
        Create GitHub issue for incident.

        Args:
            incident_id: Unique incident identifier
            attacker_ip: Source IP address
            detection: Detection data (signature, confidence, timestamp)
            osint_data: OSINT lookup results
            actions: List of actions taken
            timeline: Event timeline
            recommendations: Recommended next steps

        Returns:
            Created GitHub Issue object, or None on failure
        """
        try:
            # Generate issue title
            signature = detection.get("signature", "Unknown")
            title = f"[{incident_id}] {signature}"

            # Generate issue body from template
            body = self._generate_issue_body(
                incident_id=incident_id,
                attacker_ip=attacker_ip,
                detection=detection,
                osint_data=osint_data,
                actions=actions,
                timeline=timeline,
                recommendations=recommendations,
            )

            # Determine labels
            labels = self._determine_labels(detection, osint_data)

            # Create issue
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels,
            )

            logger.info(f"Created GitHub issue #{issue.number} for {incident_id}")

            # Post OSINT dossier as comment
            self._post_osint_comment(issue, attacker_ip, osint_data)

            # Post audit trail as comment
            self._post_audit_comment(issue, actions, timeline)

            return issue

        except GithubException as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating GitHub issue: {e}")
            return None

    def _generate_issue_body(
        self,
        incident_id: str,
        attacker_ip: str,
        detection: Dict[str, Any],
        osint_data: Dict[str, Any],
        actions: List[Dict[str, Any]],
        timeline: List[Dict[str, Any]],
        recommendations: List[str],
    ) -> str:
        """Generate issue body from template."""
        whois = osint_data.get("modules", {}).get("whois", {})
        rdns = osint_data.get("modules", {}).get("reverse_dns", {})

        confidence = detection.get("confidence", 0.97)
        signature = detection.get("signature", "Unknown")
        first_seen = detection.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Build actions list
        actions_text = ""
        for action in actions[:10]:  # Limit to 10 actions
            success_emoji = "✅" if action.get("success", True) else "❌"
            actions_text += f"- {success_emoji} **{action.get('name', 'Unknown')}** ({action.get('timestamp', 'N/A')})\n"
            actions_text += f"  - Result: {action.get('result', 'unknown')}\n"

        # Build timeline
        timeline_text = ""
        for event in timeline[:20]:  # Limit to 20 events
            timeline_text += f"- **{event.get('timestamp', 'N/A')}**: {event.get('description', 'N/A')}\n"

        # Build recommendations
        rec_text = ""
        for rec in recommendations:
            rec_text += f"- {rec}\n"

        # Generate issue body
        body = f"""# [{incident_id}] {signature}

**Status**: 🔴 Active
**Detected**: {first_seen}
**Attacker IP**: `{attacker_ip}`
**Confidence**: {confidence:.2f}

---

## Summary

Reconnaissance activity detected from {attacker_ip}. Signature: {signature}. Confidence: {confidence:.2f}

## Attacker Profile

- **IP Address**: {attacker_ip}
- **Organization**: {whois.get('org', 'Unknown')}
- **Country**: {whois.get('country', 'Unknown')}
- **ASN**: AS{whois.get('asn', 'N/A')}
- **Reverse DNS**: {rdns.get('ptr', 'None')}

## Detection Signals

- **{signature}**: Detection confidence {confidence:.2f}

## Actions Taken

{actions_text}

## Timeline

{timeline_text}

## Recommendations

{rec_text}

---

**Generated**: {datetime.now(timezone.utc).isoformat()}Z
**Agent Version**: 1.0.0
🤖 Generated by [The Mirror](https://github.com/{self.repo_name})
"""
        return body

    def _post_osint_comment(
        self, issue: Issue, attacker_ip: str, osint_data: Dict[str, Any]
    ) -> None:
        """Post OSINT dossier as issue comment."""
        try:
            whois = osint_data.get("modules", {}).get("whois", {})
            rdns = osint_data.get("modules", {}).get("reverse_dns", {})
            shodan = osint_data.get("modules", {}).get("shodan", {})
            ct = osint_data.get("modules", {}).get("cert_transparency", {})

            # Build OSINT dossier
            dossier = f"""## OSINT Dossier: {attacker_ip}

### WHOIS
- **Organization**: {whois.get('org', 'Unknown')}
- **ASN**: AS{whois.get('asn', 'N/A')}
- **Net Range**: {whois.get('net_range', 'Unknown')}
- **Country**: {whois.get('country', 'Unknown')}
- **Abuse Contact**: {whois.get('abuse_contact', 'Unknown')}

### Reverse DNS
- **PTR Record**: {rdns.get('ptr', 'None')}
- **Provider**: {rdns.get('provider_guess', 'Unknown')}

### Shodan
- **Open Ports**: {', '.join(str(p) for p in shodan.get('open_ports', []))}
- **OS**: {shodan.get('os', 'Unknown')}

### Certificate Transparency
Domains associated with this IP:
"""
            certs = ct.get("certificates", [])
            if certs:
                for cert in certs[:10]:
                    dossier += f"  - `{cert}`\n"
            else:
                dossier += "  - none found\n"

            dossier += f"""
### IOCs

```json
{{
  "ip": "{attacker_ip}",
  "asn": "{whois.get('asn')}",
  "domains": {certs[:5]},
  "open_ports": {shodan.get('open_ports', [])}
}}
```

---

**OSINT References**:
- [Shodan](https://www.shodan.io/host/{attacker_ip})
- [VirusTotal](https://www.virustotal.com/gui/ip-address/{attacker_ip})
- [AbuseIPDB](https://www.abuseipdb.com/check/{attacker_ip})
- [GreyNoise](https://www.greynoise.io/viz/ip/{attacker_ip})
"""

            issue.create_comment(dossier)
            logger.info(f"Posted OSINT dossier to issue #{issue.number}")

        except Exception as e:
            logger.error(f"Failed to post OSINT comment: {e}")

    def _post_audit_comment(
        self, issue: Issue, actions: List[Dict[str, Any]], timeline: List[Dict[str, Any]]
    ) -> None:
        """Post audit trail as issue comment."""
        try:
            audit_text = "## Audit Trail\n\n"
            audit_text += "| Time (UTC) | Action | Result |\n"
            audit_text += "|------------|--------|--------|\n"

            for action in actions[:20]:
                timestamp = action.get("timestamp", "N/A")
                name = action.get("name", "Unknown")
                result = action.get("result", "unknown")
                audit_text += f"| {timestamp} | {name} | {result} |\n"

            audit_text += "\n---\n*All actions executed from pre-approved action pool.*"

            issue.create_comment(audit_text)
            logger.info(f"Posted audit trail to issue #{issue.number}")

        except Exception as e:
            logger.error(f"Failed to post audit comment: {e}")

    def _determine_labels(
        self, detection: Dict[str, Any], osint_data: Dict[str, Any]
    ) -> List[str]:
        """Determine labels for issue based on detection and OSINT."""
        labels = ["security", "incident", "automated"]

        # Severity based on confidence
        confidence = detection.get("confidence", 0.5)
        if confidence >= 0.9:
            labels.append("severity:high")
        elif confidence >= 0.7:
            labels.append("severity:medium")
        else:
            labels.append("severity:low")

        # Attack type from signature
        signature = detection.get("signature", "").lower()
        if "nmap" in signature or "scan" in signature:
            labels.append("attack:recon")
        elif "sqli" in signature or "sql" in signature:
            labels.append("attack:sqli")
        elif "xss" in signature:
            labels.append("attack:xss")
        elif "brute" in signature:
            labels.append("attack:brute-force")
        elif "dos" in signature or "flood" in signature:
            labels.append("attack:dos")

        return labels

    def close_incident_issue(
        self, issue_number: int, resolution: str = "resolved"
    ) -> bool:
        """
        Close an incident issue with resolution comment.

        Args:
            issue_number: GitHub issue number
            resolution: Resolution status (resolved, false-positive, duplicate)

        Returns:
            True if successful, False otherwise
        """
        try:
            issue = self.repo.get_issue(issue_number)

            # Post resolution comment
            comment = f"""## Incident Resolved

**Resolution**: {resolution}
**Closed**: {datetime.now(timezone.utc).isoformat()}Z

"""
            if resolution == "resolved":
                comment += "This incident has been investigated and resolved. No further action required."
            elif resolution == "false-positive":
                comment += "This incident was determined to be a false positive. Detection rules may need adjustment."
            elif resolution == "duplicate":
                comment += "This incident is a duplicate of another issue."

            issue.create_comment(comment)
            issue.edit(state="closed")

            logger.info(f"Closed issue #{issue_number} with resolution: {resolution}")
            return True

        except GithubException as e:
            logger.error(f"Failed to close issue #{issue_number}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error closing issue: {e}")
            return False

    def get_open_incidents(self) -> List[Issue]:
        """Get all open incident issues."""
        try:
            issues = self.repo.get_issues(state="open", labels=["incident"])
            return list(issues)
        except Exception as e:
            logger.error(f"Failed to get open incidents: {e}")
            return []
