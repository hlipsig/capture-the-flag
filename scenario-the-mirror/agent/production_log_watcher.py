"""
Production portal log watcher that follows pod logs and creates incidents.

Monitors the production-portal pod for attack patterns and creates
incidents automatically when suspicious activity is detected.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def watch_production_logs():
    """
    Watch production portal pod logs via Kubernetes API and create incidents for detections.

    This runs in a background thread and continuously follows the production portal logs.
    """
    logger.info("Starting production portal log watcher...")

    # Import here to avoid circular dependencies
    from agent.log_detector import LogDetector
    from agent.db import get_db_manager
    from kubernetes import client, config, watch

    detector = LogDetector()
    db = get_db_manager()

    # Track IPs we've already created incidents for (24h window)
    detected_ips = {}
    incident_expiry = 86400  # 24 hours

    # Load in-cluster config
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        logger.info("Kubernetes API client initialized for production portal")
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        return

    # Get production portal pod name
    try:
        pods = v1.list_namespaced_pod(
            namespace="cyber-riposte",
            label_selector="app=production-portal"
        )

        if not pods.items:
            logger.warning("No production portal pod found - watcher will retry")
            time.sleep(30)
            # Retry once
            pods = v1.list_namespaced_pod(
                namespace="cyber-riposte",
                label_selector="app=production-portal"
            )
            if not pods.items:
                logger.error("Production portal pod not found after retry - disabling watcher")
                return

        pod_name = pods.items[0].metadata.name
        logger.info(f"Watching production portal logs from pod: {pod_name}")

    except Exception as e:
        logger.error(f"Failed to get production portal pod: {e}")
        return

    # Follow logs using direct API call
    try:
        logger.info("✅ Production portal log watcher started")

        # Stream logs
        log_stream = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace="cyber-riposte",
            follow=True,
            _preload_content=False
        )

        for line in log_stream.stream():
            if not line:
                time.sleep(0.1)
                continue

            # Decode bytes to string
            if isinstance(line, bytes):
                line = line.decode('utf-8')

            line = line.strip()
            if not line:
                continue

            # Skip kubernetes/openshift probes
            if 'kube-probe' in line or 'readyz' in line or 'healthz' in line:
                continue

            # Strip Python logging prefix (INFO:__main__: or INFO:werkzeug:)
            # so the line starts with IP address for log_detector parsing
            if line.startswith('INFO:'):
                # Find the first ':' after 'INFO:'
                colon_pos = line.find(':', 5)  # Start search after 'INFO:'
                if colon_pos != -1:
                    line = line[colon_pos + 1:].strip()

            # Skip if line is now empty or still looks like a log prefix
            if not line or line.startswith('WARNING') or line.startswith('ERROR'):
                continue

            # Skip normal health checks
            if '/health' in line and '200' in line:
                continue

            # Parse log line for detection
            detection = detector.analyze_log_line(line)

            if detection and detection.get('attacker_ip'):
                attacker_ip = detection['attacker_ip']

                # Check if we've already created an incident for this IP recently
                now = time.time()
                if attacker_ip in detected_ips:
                    last_seen = detected_ips[attacker_ip]
                    if now - last_seen < incident_expiry:
                        # Already have an active incident for this IP
                        continue

                # Record this detection
                detected_ips[attacker_ip] = now

                # Create incident
                try:
                    # Generate incident ID with timestamp and IP
                    incident_time = datetime.now(timezone.utc)
                    ip_suffix = attacker_ip.replace('.', '-').replace(':', '-')
                    incident_id = f"INC-{incident_time.strftime('%Y%m%d-%H%M%S')}-{ip_suffix}"

                    logger.info(f"🚨 Creating incident {incident_id} for {attacker_ip}")
                    logger.info(f"   Detection: {detection.get('signature', 'Unknown')}")
                    logger.info(f"   Confidence: {detection.get('confidence', 0.0)}")

                    # Execute active defense actions
                    action_results = None
                    try:
                        from agent.incident_handler import execute_active_defense
                        action_results = execute_active_defense(incident_id, attacker_ip, detection)
                        logger.info(f"🛡️  Active defense executed: {', '.join(action_results.get('actions_taken', []))}")
                    except Exception as e:
                        logger.warning(f"Active defense execution failed: {e}")

                    # Create incident in database with action results
                    db.create_incident(
                        incident_id=incident_id,
                        attacker_ip=attacker_ip,
                        detection={
                            'signature': detection.get('signature', 'Unknown pattern'),
                            'confidence': detection.get('confidence', 0.90),
                            'source': 'production-portal',
                            'timestamp': incident_time.isoformat(),
                            'evidence': detection.get('evidence', []),
                            'actions_taken': action_results.get('actions_taken', []) if action_results else [],
                            'ai_narrative': action_results.get('ai_narrative') if action_results else None,
                        }
                    )

                    logger.info(f"✅ Incident {incident_id} created with {len(action_results.get('actions_taken', []))} actions")

                except Exception as e:
                    logger.error(f"Failed to create incident: {e}")
                    # Remove from detected IPs so we can retry
                    detected_ips.pop(attacker_ip, None)

            # Cleanup old entries from detected_ips
            if len(detected_ips) > 1000:  # Prevent unbounded growth
                current_time = time.time()
                detected_ips = {
                    ip: timestamp
                    for ip, timestamp in detected_ips.items()
                    if current_time - timestamp < incident_expiry
                }

    except Exception as e:
        logger.error(f"Production log watcher error: {e}")
        time.sleep(5)  # Brief pause before thread dies

    logger.info("Production portal log watcher stopped")
