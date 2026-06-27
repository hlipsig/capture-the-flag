# The Mirror

> *"In fencing, a riposte is the counterattack launched immediately after parrying. You use your opponent's forward momentum against them. The Mirror is a digital riposte."*

An AI-powered active defense CTF (Capture The Flag) challenge where reconnaissance attempts trigger autonomous counter-intelligence gathering.

## What is The Mirror?

When an attacker scans your infrastructure, The Mirror doesn't just block them—it redirects them to a honeypot while simultaneously running passive OSINT (Open Source Intelligence) on the attacker's own infrastructure. Every probe they send reveals something about them.

An AI agent orchestrates the entire response autonomously:
- **Detect** the reconnaissance (IDS alerts + user-agent analysis)
- **Redirect** the attacker to a honeypot
- **Counter-recon** by running passive OSINT against the attacker
- **Document** everything in a structured intelligence dossier
- **Report** findings for morning review

All actions are executed from a **pre-approved playbook**—the agent can act at 3am with nobody awake, but every decision is logged, justified, and auditable.

## Key Features

- **Autonomous Detection**: Suricata IDS + user-agent fingerprinting detects port scans, directory brute-forcing, and offensive tooling
- **Smart Redirection**: nftables-based traffic redirection to honeypots without alerting the attacker
- **Passive OSINT**: WHOIS, reverse DNS, Shodan, Certificate Transparency logs—all public data, no active scanning
- **AI Decision Engine**: Local LLM (TinyLlama-1.1B) evaluates events and selects responses from the approved action pool
- **Full Audit Trail**: Every action logged with timestamp, trigger data, reasoning, and confidence scores
- **Intelligence Dossiers**: Auto-generated reports combining OSINT findings with honeypot behavior logs
- **GitHub Integration**: Incident reports posted automatically to GitHub issues for team review

## Architecture

```
Attacker Probe → Detection → Redirect to Honeypot → Passive OSINT → Intelligence Dossier
                     ↓              ↓                      ↓               ↓
                  IDS/Logs    nftables DNAT         Public APIs      GitHub Report
```

## CTF Scenario

In this CTF, **you are the attacker being watched**. Your goal is to:

1. Find the hidden web dossier (password-protected intelligence briefing)
2. Crack the password (hint: it's in the scenario narrative)
3. Locate the real flag among multiple decoys
4. Avoid triggering defensive actions that reveal your techniques

The twist: The Mirror is learning your reconnaissance patterns and building a profile on you as you work.

## Quick Start

### Prerequisites

- OpenShift or Kubernetes cluster
- Python 3.9+
- Suricata IDS
- nftables (for traffic redirection)
- Optional: Shodan API key for enhanced OSINT

### Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/capture-the-flag.git
cd capture-the-flag

# Build and deploy
./build.sh
oc apply -f k8s/

# Verify deployment
oc get pods -l app=mirror-agent
oc logs -f deployment/mirror-agent
```

See [docs/guides/DEPLOYMENT.md](docs/guides/DEPLOYMENT.md) for detailed deployment instructions.

### For CTF Participants

Entry points and challenges are documented in [docs/reference/GAMEMASTER.md](docs/reference/GAMEMASTER.md).

## Documentation

- **[PLAYBOOK.md](PLAYBOOK.md)** - CTF participant guide and scenario overview
- **[docs/guides/DEPLOYMENT.md](docs/guides/DEPLOYMENT.md)** - Full deployment guide
- **[docs/guides/QUICK-START.md](docs/guides/QUICK-START.md)** - Get running in 5 minutes
- **[docs/reference/GAMEMASTER.md](docs/reference/GAMEMASTER.md)** - Running live CTF sessions
- **[docs/reference/CTF-FLAGS.md](docs/reference/CTF-FLAGS.md)** - Flag locations and decoys
- **[scenario-the-mirror/README.md](scenario-the-mirror/README.md)** - Complete scenario implementation guide

## Technical Components

### Core Services
- **mirror-agent** - Main AI orchestrator (Python)
- **llm-server** - Local LLM inference server (TinyLlama-1.1B)
- **suricata** - IDS for threat detection
- **honeypot** - Decoy services for attacker engagement

### Key Modules
- `detector.py` - Event detection and classification
- `executor.py` - Action execution from approved playbook
- `evidence_collector.py` - OSINT gathering coordinator
- `github_reporter.py` - Automated incident reporting
- `web_dossier.py` - Intelligence report generator

### Configuration
- `action-pool.yaml` - Pre-approved defensive actions
- `suspicious-user-agents.yaml` - Offensive tool signatures
- `config.yaml` - Runtime configuration

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (dry-run mode, no actual network changes)
python main.py --dry-run

# Run tests
python -m pytest tests/

# Build container
docker build -t mirror-agent:latest .
```

## Legal & Ethical Notes

- All OSINT uses **publicly available data only** (WHOIS, DNS, Shodan, CT logs)
- **No active scanning** of attacker infrastructure
- Honeypots only collect data from traffic attackers **voluntarily send**
- Always consult legal counsel before implementing active defense in production

This is a CTF training environment. Do not deploy against real attackers without legal review.

## Contributing

This is a demonstration CTF scenario. For issues or improvements:

1. Check existing issues
2. Open a new issue describing the problem or enhancement
3. PRs welcome for bug fixes and feature additions

## License

MIT License - see LICENSE file for details

## Credits

Built as a demonstration of AI-powered active defense concepts combining IDS, honeypots, OSINT, and autonomous decision-making within constrained action pools.

---

**Status**: Feature-complete CTF scenario ready for deployment
**Last Updated**: June 2026
