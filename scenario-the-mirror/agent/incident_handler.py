"""
Incident handler that executes active defense actions.

This module provides the core incident response logic that can be invoked
by any detection component (log watchers, stdin mode, kafka, etc.).
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def execute_active_defense(incident_id: str, attacker_ip: str, detection: dict):
    """
    Execute active defense actions for a detected incident.

    This is the unified incident response handler that:
    1. Redirects traffic to honeypot (Tier 1 auto-execute)
    2. Runs passive OSINT (Tier 1 auto-execute)
    3. Applies temporary block (Tier 1 auto-execute)
    4. Generates AI narrative and evidence

    Args:
        incident_id: Unique incident identifier
        attacker_ip: IP address of the attacker
        detection: Detection metadata including signature, confidence, etc.

    Returns:
        dict: Results of actions taken
    """
    logger.info(f"🛡️  Executing active defense for incident {incident_id}")
    logger.info(f"   Attacker: {attacker_ip}")
    logger.info(f"   Detection: {detection.get('signature', 'Unknown')}")
    logger.info(f"   Confidence: {detection.get('confidence', 0.0):.2f}")

    results = {
        'incident_id': incident_id,
        'attacker_ip': attacker_ip,
        'actions_taken': [],
        'osint_data': None,
        'ai_narrative': None,
    }

    # Import action executors (avoid circular imports)
    try:
        import sys
        import os
        # Add parent directory to path to import mirror_agent
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from mirror_agent import (
            execute_redirect,
            execute_osint,
            execute_temp_block,
            ActionPool,
            AuditLog
        )

        # Initialize action pool and audit log
        action_pool = ActionPool()
        audit = AuditLog()

        # Phase 1: Redirect to honeypot (Tier 1 — auto-execute)
        logger.info(f"[T1] Executing redirect-to-honeypot for {attacker_ip}")
        try:
            redirect_result = execute_redirect(attacker_ip, action_pool, audit, incident_id, detection)
            if redirect_result:
                results['actions_taken'].append('redirect-to-honeypot')
                logger.info(f"✅ Traffic redirected to honeypot")
        except Exception as e:
            logger.warning(f"⚠️  Redirect failed: {e}")

        # Phase 2: Passive OSINT (Tier 1 — auto-execute)
        logger.info(f"[T1] Running OSINT on {attacker_ip}")
        try:
            osint_data = execute_osint(attacker_ip, action_pool, audit, incident_id, detection)
            if osint_data:
                results['osint_data'] = osint_data
                results['actions_taken'].append('run-osint')
                logger.info(f"✅ OSINT data collected")
        except Exception as e:
            logger.warning(f"⚠️  OSINT failed: {e}")

        # Phase 3: Temp block (Tier 1 — auto-execute)
        logger.info(f"[T1] Applying temporary block on {attacker_ip}")
        try:
            block_result = execute_temp_block(attacker_ip, action_pool, audit, incident_id, detection)
            if block_result:
                results['actions_taken'].append('temp-block-ip')
                logger.info(f"✅ Temporary block applied")
        except Exception as e:
            logger.warning(f"⚠️  Temp block failed: {e}")

    except ImportError as e:
        logger.error(f"Failed to import action executors: {e}")
        logger.warning("Active defense actions will be skipped")

    # Phase 4: Generate AI narrative
    try:
        from agent.ai_narrator import generate_narrative

        narrative_context = {
            'attacker_ip': attacker_ip,
            'detection_signature': detection.get('signature', 'Unknown'),
            'detection_confidence': detection.get('confidence', 0.90),
            'incident_id': incident_id,
            'actions_taken': results['actions_taken'],
            'osint_data': results.get('osint_data'),
        }

        ai_narrative = generate_narrative(narrative_context, style='technical')
        results['ai_narrative'] = ai_narrative
        logger.info(f"✅ AI narrative generated ({len(ai_narrative)} chars)")

    except Exception as e:
        logger.warning(f"⚠️  AI narrative generation failed: {e}")

    logger.info(f"🎯 Active defense complete for {incident_id}")
    logger.info(f"   Actions: {', '.join(results['actions_taken']) if results['actions_taken'] else 'none'}")

    return results


def update_incident_with_actions(db, incident_id: str, results: dict):
    """
    Update incident in database with action results and AI narrative.

    Args:
        db: Database manager instance
        incident_id: Incident ID to update
        results: Results from execute_active_defense()
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                # Update incident with actions and narrative
                cur.execute("""
                    UPDATE incidents
                    SET actions_count = %s,
                        ai_narrative = %s,
                        last_updated = %s
                    WHERE incident_id = %s
                """, (
                    len(results.get('actions_taken', [])),
                    results.get('ai_narrative'),
                    datetime.now(timezone.utc),
                    incident_id
                ))

                # Store OSINT data as evidence if available
                if results.get('osint_data'):
                    cur.execute("""
                        INSERT INTO evidence (
                            incident_id, evidence_type, data, collected_at
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        incident_id,
                        'osint',
                        results['osint_data'],
                        datetime.now(timezone.utc)
                    ))

            conn.commit()
            logger.info(f"✅ Incident {incident_id} updated with action results")

    except Exception as e:
        logger.error(f"Failed to update incident {incident_id}: {e}")
