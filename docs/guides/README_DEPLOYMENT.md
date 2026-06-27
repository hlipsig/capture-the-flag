# The Mirror CTF - Deployment Documentation Index

**Last Updated**: 2026-06-11  
**Status**: ✅ Ready for Tom (pending build #8 completion)

---

## 📚 Documentation Files

### 🎯 **START HERE**
- **[WELCOME_BACK.md](./WELCOME_BACK.md)** - Quick summary of what was completed while you were out
- **[READY_FOR_TOM.md](./READY_FOR_TOM.md)** - Complete CTF guide and Tom's instructions

### 🎮 CTF Design
- **[TOM_CTF_PASSWORD_PUZZLE.md](./TOM_CTF_PASSWORD_PUZZLE.md)** - Literary password puzzle details
- **[TOM_ENTRY_POINTS.md](./TOM_ENTRY_POINTS.md)** - Tom's entry points and expected journey
- **[CTF_DEPLOYMENT_COMPARISON.md](./CTF_DEPLOYMENT_COMPARISON.md)** - Comparison with capture-the-flag repo

### 🔧 Technical Details
- **[WEB_DOSSIER_DEPLOYED.md](./WEB_DOSSIER_DEPLOYED.md)** - Web dossier deployment status
- **[GITHUB_TOKEN_CONFIGURED.md](./GITHUB_TOKEN_CONFIGURED.md)** - GitHub integration setup
- **[SECRETS_NEEDED.md](./SECRETS_NEEDED.md)** - Original secrets requirements (now complete)

### 🧪 Testing
- **[test-ctf.sh](./test-ctf.sh)** - Automated test script
  ```bash
  ./test-ctf.sh
  ```

---

## 🚀 Quick Start

### For Tom:
```
Target: https://redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io

Find the flag!

Hint: Classic literature beats economics.
```

### For You (Testing):
```bash
# Run automated tests
./test-ctf.sh

# Manual tests
curl https://redteam-cyber-riposte.apps.../robots.txt
curl https://redteam-cyber-riposte.apps.../.credentials
curl -u "ctf:i_would_prefer_not_to" https://dossiers-cyber-riposte.apps.../dossiers
```

---

## ✅ What's Working

| Component | Status | URL |
|-----------|--------|-----|
| HTTP Honeypot | ✅ Live | https://redteam-cyber-riposte.apps... |
| Dossier Web | ✅ Live | https://dossiers-cyber-riposte.apps... |
| Database | ✅ Ready | Test incident created |
| Secrets | ✅ Set | All configured |
| Build #8 | 🔄 Running | Database fix |

---

## 🎭 The Password Puzzle

**Real**: `i_would_prefer_not_to` (Bartleby, the Scrivener)  
**Decoys**: Economics references (Adam Smith, Schumpeter)  
**Hints**: "scrivener's choice", "Bartleby would understand"

---

## 📋 Files in This Directory

```
scenario-the-mirror/
├── README_DEPLOYMENT.md          ← You are here
├── WELCOME_BACK.md               ← Start here after dinner
├── READY_FOR_TOM.md              ← Complete CTF guide
├── TOM_CTF_PASSWORD_PUZZLE.md    ← Password details
├── TOM_ENTRY_POINTS.md           ← Entry points guide
├── WEB_DOSSIER_DEPLOYED.md       ← Dossier deployment
├── GITHUB_TOKEN_CONFIGURED.md    ← GitHub setup
├── CTF_DEPLOYMENT_COMPARISON.md  ← Repo comparison
├── SECRETS_NEEDED.md             ← Original requirements
├── test-ctf.sh                   ← Automated tests
│
├── agent/
│   ├── main.py                   ← Agent with web dossier
│   ├── web_dossier.py            ← Flask dossier app
│   └── db.py                     ← Database with get_connection
│
├── k8s/
│   ├── simple-honeypot.yaml      ← HTTP honeypot
│   ├── dossier-service.yaml      ← Dossier web service
│   ├── honeypot-routes.yaml      ← OpenShift routes
│   └── agent-deployment.yaml     ← Updated agent config
│
├── honeypot/
│   └── admin-notes.txt           ← Password hints (for SSH)
│
└── db/
    └── schema.sql                ← Database schema (applied)
```

---

## 🎯 Next Steps

1. **Check build status**: 
   ```bash
   oc get builds -n cyber-riposte | grep mirror-agent
   ```

2. **After build #8 completes**:
   ```bash
   # Agent will auto-restart
   oc get pods -n cyber-riposte -l app=mirror-agent
   
   # Test dossier
   curl -u "ctf:i_would_prefer_not_to" \
     https://dossiers-cyber-riposte.apps.../dossiers
   ```

3. **Run tests**:
   ```bash
   ./test-ctf.sh
   ```

4. **Send Tom the URL**! 🚀

---

## 🆘 Troubleshooting

### Build #8 taking too long?
```bash
oc logs -f build/mirror-agent-8 -n cyber-riposte
```

### Dossier not working?
```bash
oc logs deployment/mirror-agent -n cyber-riposte | grep dossier
```

### Database issues?
```bash
oc exec postgres-0 -n cyber-riposte -- \
  psql -U mirror_agent -d mirror_audit -c "SELECT COUNT(*) FROM incidents;"
```

---

## 📞 Support

All components are configured and documented. If something doesn't work:

1. Check the relevant documentation file above
2. Run `./test-ctf.sh` to diagnose
3. Check build status and pod logs

---

**The Mirror is ready. Tom's adventure awaits!** 🪞🎯🎭
