# Documentation Index

Complete documentation for The Mirror CTF scenario.

## Quick Navigation

### Getting Started
- **[Quick Start Guide](reference/QUICK-START.md)** - Get The Mirror running in 5 minutes
- **[Deployment Guide](guides/DEPLOYMENT.md)** - Comprehensive deployment instructions
- **[Playbook](../PLAYBOOK.md)** - CTF participant guide and scenario overview

### For CTF Participants
- **[Game Master Guide](reference/GAMEMASTER.md)** - Running live CTF sessions
- **[Entry Points](reference/TOM_ENTRY_POINTS.md)** - Where to start attacking
- **[CTF Flags Reference](reference/CTF-FLAGS.md)** - Flag locations (for organizers)
- **[Password Puzzle](reference/TOM_CTF_PASSWORD_PUZZLE.md)** - Web dossier access puzzle

### Technical Guides

#### Deployment & Setup
- [OpenShift Deployment](guides/OPENSHIFT_DEPLOYMENT.md) - Deploy to OpenShift
- [Database Setup](guides/DATABASE-SETUP.md) - PostgreSQL configuration
- [Domain Setup](guides/DOMAIN-SETUP.md) - DNS and routing
- [Honeypot Setup](guides/HONEYPOT-SETUP.md) - Decoy service configuration
- [Secrets Management](guides/SECRETS_NEEDED.md) - Required API keys and credentials

#### Infrastructure Components
- [Istio Setup](guides/ISTIO-SETUP.md) - Service mesh configuration
- [Kafka Setup](guides/KAFKA-SETUP.md) - Event streaming
- [Observability Setup](guides/OBSERVABILITY-SETUP.md) - Monitoring and metrics
- [Hot Reload Setup](guides/HOT-RELOAD-SETUP.md) - Development workflow

#### Advanced Topics
- [OSINT Resilience](guides/OSINT-RESILIENCE.md) - Handling API failures
- [Testing Guide](guides/TESTING-GUIDE.md) - Test suite and validation

### Reference Documentation
- **[LLM Guide](reference/LLM-GUIDE.md)** - Local LLM server architecture and API
- **[Phase 2: LLM Integration](reference/PHASE2-LLM.md)** - Adding AI decision-making
- **[Defensive Actions Catalog](reference/DEFENSIVE_ACTIONS_CATALOG.md)** - Available response actions
- **[Template System](reference/PHASE8-TEMPLATES.md)** - Report template architecture

### Templates
All Jinja2 templates for automated report generation:
- [Dossier Template](templates/dossier-template.md)
- [Enhanced Dossier](templates/dossier-enhanced.md.j2)
- [Executive Summary](templates/executive-summary.md.j2)
- [Incident Report](templates/incident-report.md.j2)
- [Post-mortem Report](templates/postmortem-template.md)
- [PR Body Template](templates/pr-body.md)
- [Slack Notification](templates/slack-notification.md.j2)

### Historical Archive
Planning documents and status updates from development:
- Build status reports
- Implementation summaries
- Phase completion markers
- Feature tracking docs

Located in `docs/archive/` - preserved for historical reference but not needed for deployment.

## Documentation by Use Case

### I want to deploy The Mirror
1. Start with [Quick Start Guide](reference/QUICK-START.md)
2. Follow [Deployment Guide](guides/DEPLOYMENT.md)
3. Configure services using guides in `guides/`
4. Review [Secrets Management](guides/SECRETS_NEEDED.md)

### I want to run a CTF event
1. Read [Game Master Guide](reference/GAMEMASTER.md)
2. Review [CTF Flags Reference](reference/CTF-FLAGS.md)
3. Share [Playbook](../PLAYBOOK.md) with participants
4. Point participants to [Entry Points](reference/TOM_ENTRY_POINTS.md)

### I want to understand the AI agent
1. Read [LLM Guide](reference/LLM-GUIDE.md) for architecture
2. Review [Phase 2: LLM Integration](reference/PHASE2-LLM.md) for decision-making
3. Check [Defensive Actions Catalog](reference/DEFENSIVE_ACTIONS_CATALOG.md) for available actions
4. See [scenario-the-mirror/README.md](../scenario-the-mirror/README.md) for complete flow

### I want to customize templates
1. Browse templates in `docs/templates/`
2. Read [Template System Guide](reference/PHASE8-TEMPLATES.md)
3. Modify Jinja2 templates for your needs

## Key Concepts

- **Action Pool**: Pre-approved defensive actions the AI can execute autonomously
- **OSINT**: Open Source Intelligence - passive data gathering from public sources
- **Honeypot**: Decoy service that logs attacker behavior
- **Dossier**: Intelligence report combining OSINT + honeypot logs
- **Post-mortem**: Structured report of an incident and agent's response
- **Riposte**: The counter-attack metaphor - using attacker's momentum against them

## File Organization

```
docs/
├── README.md              # This file
├── guides/                # Setup and deployment guides
├── reference/             # Technical reference documentation
├── templates/             # Jinja2 report templates
└── archive/               # Historical planning docs
```

## Contributing to Documentation

When adding new documentation:
- **Setup guides** → `docs/guides/`
- **Reference material** → `docs/reference/`
- **Templates** → `docs/templates/`
- **General overview** → Root `README.md` or `PLAYBOOK.md`

Keep the main README focused on "what is this and how do I use it" - move implementation details to specific guides.
