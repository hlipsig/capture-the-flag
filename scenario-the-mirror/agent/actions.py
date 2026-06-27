"""
Active defense action executors.

This module contains the actual implementations of defensive actions
that can be executed automatically when threats are detected.
"""

import logging
import subprocess
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def execute_redirect_to_honeypot(attacker_ip: str, incident_id: str) -> dict:
    """
    Execute nftables DNAT to redirect attacker traffic to honeypot.

    Returns:
        dict: Result with success status and details
    """
    honeypot_ip = os.getenv("HONEYPOT_IP", "simple-honeypot.cyber-riposte.svc.cluster.local")
    production_port = int(os.getenv("PRODUCTION_PORT", "8000"))
    honeypot_port = int(os.getenv("HONEYPOT_PORT", "8080"))

    logger.info(f"[redirect] {attacker_ip} → {honeypot_ip}:{honeypot_port}")

    rule_content = (
        f"table ip nat {{\n"
        f"    chain prerouting {{\n"
        f"        type nat hook prerouting priority -100; policy accept;\n"
        f'        ip saddr {attacker_ip} tcp dport {production_port} '
        f'dnat to {honeypot_ip}:{honeypot_port} '
        f'comment "mirror: {incident_id}"\n'
        f"    }}\n"
        f"}}\n"
    )

    try:
        result = subprocess.run(
            ["nft", "-f", "-"],
            input=rule_content,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            logger.info(f"[redirect] ✅ Traffic redirected: {attacker_ip}")
            return {
                'action': 'redirect-to-honeypot',
                'success': True,
                'details': f'Redirected {attacker_ip} to honeypot',
            }
        else:
            logger.warning(f"[redirect] ⚠️  nft failed: {result.stderr}")
            return {
                'action': 'redirect-to-honeypot',
                'success': False,
                'error': result.stderr,
            }
    except Exception as e:
        logger.error(f"[redirect] ❌ Exception: {e}")
        return {
            'action': 'redirect-to-honeypot',
            'success': False,
            'error': str(e),
        }


def execute_osint(attacker_ip: str, incident_id: str) -> dict:
    """
    Run passive OSINT lookups on attacker IP.

    Returns:
        dict: OSINT data collected
    """
    logger.info(f"[osint] Collecting data for {attacker_ip}")

    osint_data = {
        'ip': attacker_ip,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'sources': {},
    }

    # Try whois
    try:
        from agent.osint_modules.whois_lookup import whois_lookup
        whois_data = whois_lookup(attacker_ip)
        if whois_data:
            osint_data['sources']['whois'] = whois_data
            logger.info(f"[osint] ✅ whois collected")
    except Exception as e:
        logger.warning(f"[osint] whois failed: {e}")

    # Try reverse DNS
    try:
        from agent.osint_modules.reverse_dns import reverse_dns
        dns_data = reverse_dns(attacker_ip)
        if dns_data:
            osint_data['sources']['reverse_dns'] = dns_data
            logger.info(f"[osint] ✅ reverse DNS collected")
    except Exception as e:
        logger.warning(f"[osint] reverse DNS failed: {e}")

    # Try Shodan (if API key available)
    shodan_key = os.getenv('SHODAN_API_KEY')
    if shodan_key:
        try:
            from agent.osint_modules.shodan_lookup import shodan_lookup
            shodan_data = shodan_lookup(attacker_ip)
            if shodan_data:
                osint_data['sources']['shodan'] = shodan_data
                logger.info(f"[osint] ✅ Shodan collected")
        except Exception as e:
            logger.warning(f"[osint] Shodan failed: {e}")

    return osint_data


def execute_temp_block(attacker_ip: str, incident_id: str, duration_seconds: int = 3600) -> dict:
    """
    Apply temporary IP block using iptables.

    Returns:
        dict: Result with success status
    """
    logger.info(f"[block] Blocking {attacker_ip} for {duration_seconds}s")

    # Note: In Kubernetes, this would typically be done via NetworkPolicy
    # For now, just log the intent
    logger.warning(f"[block] ⚠️  Temporary block not implemented (requires NetworkPolicy)")

    return {
        'action': 'temp-block-ip',
        'success': False,
        'note': 'Not implemented - requires NetworkPolicy or external firewall',
    }


def record_action_to_database(db, incident_id: str, action_result: dict):
    """
    Record an executed action to the database.

    Args:
        db: Database manager
        incident_id: Incident ID
        action_result: Result dict from action execution
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                # Update incident actions count
                cur.execute("""
                    UPDATE incidents
                    SET actions_count = actions_count + 1,
                        last_updated = %s
                    WHERE incident_id = %s
                """, (datetime.now(timezone.utc), incident_id))

                # Store action details as evidence
                cur.execute("""
                    INSERT INTO evidence (
                        incident_id, evidence_type, data, collected_at
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    incident_id,
                    'action',
                    action_result,
                    datetime.now(timezone.utc)
                ))
            conn.commit()
            logger.info(f"[db] ✅ Action recorded for {incident_id}")
    except Exception as e:
        logger.error(f"[db] Failed to record action: {e}")
