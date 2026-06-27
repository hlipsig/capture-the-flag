# Makefile Build Guide - The Mirror CTF

Quick reference for building container images for The Mirror deployment.

## 🚀 Quick Start (OpenShift)

Build images and deploy in one command:

```bash
make quick-start
```

This will:
1. Check OpenShift login
2. Build mirror-agent image
3. Build llm-server image (TinyLlama-1.1B)
4. Show Helm deployment command

**Time**: ~15-20 minutes total

### ⏱️ What to Expect

The build process has 2 phases with different timing:

**Phase 1: mirror-agent build** (~5-7 minutes)
- Downloads base image (UBI Python 3.11)
- Installs Python dependencies
- Multi-stage build for smaller final image
- **Watch for**: "Successfully pushed image-registry.../mirror-agent"

**Phase 2: llm-server build** (~10-15 minutes) ⚠️
- Downloads base image (Python 3.11 slim)
- Installs ML libraries (PyTorch ~2GB)
- **Downloads TinyLlama model (~2.2GB)** - This is the longest step!
- Pre-caches model to avoid runtime download
- **Watch for**: "Model downloaded successfully: distilgpt2" or "TinyLlama-1.1B"

**Why so long?**
- Model download: ~2.2GB for TinyLlama (or ~330MB for DistilGPT2)
- PyTorch + dependencies: ~2GB
- OpenShift image push: Large images take time to push to registry

**Pro tip**: Use `oc logs -f bc/llm-server` in another terminal to watch the build progress in real-time.

## 📋 Prerequisites

### For OpenShift Builds
```bash
# Login to OpenShift
oc login <your-cluster-url>

# Verify login
make login-check
```

### For Local Docker Builds
```bash
# Docker must be running
docker info
```

## 🎯 Common Commands

### View Configuration

```bash
# Show current build configuration
make info
```

Output:
```
Registry:   image-registry.openshift-image-registry.svc:5000
Namespace:  cyber-riposte
Image Tag:  latest
LLM Model:  TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

### Build on OpenShift (Recommended)

```bash
# Build both images on OpenShift
make build-openshift

# Build individual images
make build-agent-openshift
make build-llm-openshift
```

### Build Locally with Docker

```bash
# Build both images
make build-all

# Build individual images
make build-agent
make build-llm
```

### Test Images

```bash
# Test on OpenShift (checks imagestreams exist)
make test-openshift

# Test locally (Docker)
make test-agent
make test-llm
```

## 🔧 Customization

### Change Namespace

```bash
make build-openshift NAMESPACE=my-ctf
```

### Change LLM Model

```bash
# Use lightweight DistilGPT2 (82M params, ~330MB)
make build-llm-openshift LLM_MODEL=distilgpt2

# Or use the convenience target
make build-llm-distil
```

### Change Image Tag

```bash
make build-openshift IMAGE_TAG=v1.0.0
```

### Use External Registry

```bash
make build-all REGISTRY=quay.io/myorg IMAGE_TAG=latest
make push-all
```

## 📊 Build Times & Sizes

| Image | Build Time | Size | Notes |
|-------|------------|------|-------|
| **mirror-agent** | ~5 min | ~500MB | Multi-stage build with Python deps |
| **llm-server (TinyLlama)** | ~10 min | ~2.5GB | Downloads 2.2GB model |
| **llm-server (DistilGPT2)** | ~3 min | ~800MB | Lightweight alternative |

## 🎓 Step-by-Step Workflow

### 1. Login to OpenShift

```bash
oc login https://api.your-cluster.com:6443
```

### 2. Build Images

```bash
# See what will be built
make info

# Build everything
make build-openshift
```

You'll see:
```
✓ Logged into OpenShift as your-user
Building Mirror Agent on OpenShift...
Building LLM server on OpenShift...
Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
Warning: Build will take 5-10 minutes (downloads model)
```

### 3. Verify Images

```bash
# Check imagestreams exist
make test-openshift

# Or manually
oc get imagestreams -n cyber-riposte
```

Expected output:
```
NAME           IMAGE REPOSITORY
mirror-agent   image-registry.../cyber-riposte/mirror-agent
llm-server     image-registry.../cyber-riposte/llm-server
```

### 4. Deploy with Helm

```bash
helm install the-mirror ./helm/the-mirror -n cyber-riposte --create-namespace
```

## 🐛 Troubleshooting

### "Not logged into OpenShift"

```bash
# Login first
oc login <cluster-url>

# Verify
make login-check
```

### "BuildConfig already exists"

This is normal - the Makefile reuses existing BuildConfigs.

```bash
# To start fresh (WARNING: deletes builds)
make clean-openshift
```

### LLM Build Timeout

If the LLM build times out (large model download):

```bash
# Use smaller model
make build-llm-distil

# Or in Helm, disable LLM
helm install the-mirror ./helm/the-mirror --set llm.enabled=false
```

### Image Pull Errors in Helm

Verify images exist:

```bash
oc get is -n cyber-riposte
oc describe is/mirror-agent -n cyber-riposte
oc describe is/llm-server -n cyber-riposte
```

## 🧹 Cleanup

### Remove Local Images

```bash
make clean
```

### Remove OpenShift Resources

```bash
# This will ask for confirmation
make clean-openshift
```

Removes:
- BuildConfigs (mirror-agent, llm-server)
- ImageStreams (mirror-agent, llm-server)

## 📝 Makefile Targets Reference

### General
- `help` - Display all available targets
- `info` - Show build configuration
- `quick-start` - Build images and show deployment command

### OpenShift Builds
- `build-openshift` - Build both images on OpenShift
- `build-agent-openshift` - Build mirror-agent only
- `build-llm-openshift` - Build llm-server only
- `deploy-images` - Build and verify for Helm

### Local Docker Builds
- `build-all` - Build both images locally
- `build-agent` - Build mirror-agent locally
- `build-llm` - Build llm-server locally
- `build-llm-tiny` - Build with TinyLlama-1.1B
- `build-llm-distil` - Build with DistilGPT2 (lightweight)

### Testing
- `test-openshift` - Verify OpenShift imagestreams
- `test-agent` - Test agent image (Docker)
- `test-llm` - Test LLM server (Docker)

### Cleanup
- `clean` - Remove local Docker images
- `clean-openshift` - Remove OpenShift BuildConfigs/ImageStreams

## 💡 Tips

### Faster Builds

1. **Use smaller LLM model** for development:
   ```bash
   make build-llm-distil
   ```

2. **Skip LLM entirely** during Helm install:
   ```bash
   helm install the-mirror ./helm/the-mirror --set llm.enabled=false
   ```

3. **Build in parallel** (if you have multiple terminal windows):
   ```bash
   # Terminal 1
   make build-agent-openshift
   
   # Terminal 2  
   make build-llm-openshift
   ```

### Avoid Re-downloads

OpenShift BuildConfigs cache layers, so rebuilds are faster. The model is only downloaded once per BuildConfig.

### Monitor Build Progress

```bash
# In another terminal
oc logs -f bc/llm-server -n cyber-riposte
```

## 🔗 Next Steps After Building

1. **Verify images exist**:
   ```bash
   make test-openshift
   ```

2. **Deploy with Helm**:
   ```bash
   helm install the-mirror ./helm/the-mirror -n cyber-riposte --create-namespace
   ```

3. **Watch pods come up**:
   ```bash
   oc get pods -n cyber-riposte -w
   ```

4. **Get access URLs**:
   ```bash
   oc get routes -n cyber-riposte
   ```

---

## Example: Complete Workflow

```bash
# 1. Login
oc login https://api.cluster.example.com:6443

# 2. Build images (10-15 min)
make quick-start

# 3. Deploy with Helm
helm install the-mirror ./helm/the-mirror -n cyber-riposte --create-namespace

# 4. Watch deployment
oc get pods -n cyber-riposte -w

# 5. Get URLs
echo "Honeypot: https://$(oc get route honeypot -n cyber-riposte -o jsonpath='{.spec.host}')"
echo "Dossier: https://$(oc get route dossier -n cyber-riposte -o jsonpath='{.spec.host}')"
```

**Total time**: ~20 minutes from zero to running CTF!
