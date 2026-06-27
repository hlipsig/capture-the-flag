# Makefile for building The Mirror CTF images
# Supports both local Docker builds and OpenShift builds

.PHONY: help all build-all build-agent build-llm build-llm-tiny build-llm-distil \
        push-all push-agent push-llm deploy-images clean login-check \
        build-openshift build-agent-openshift build-llm-openshift \
        test-agent test-llm info

# Configuration
REGISTRY ?= image-registry.openshift-image-registry.svc:5000
NAMESPACE ?= cyber-riposte
IMAGE_TAG ?= latest

# Image names
AGENT_IMAGE = $(REGISTRY)/$(NAMESPACE)/mirror-agent:$(IMAGE_TAG)
LLM_IMAGE = $(REGISTRY)/$(NAMESPACE)/llm-server:$(IMAGE_TAG)

# LLM Model selection
# Options: distilgpt2 (82M, fast), TinyLlama/TinyLlama-1.1B-Chat-v1.0 (1.1B, better quality)
LLM_MODEL ?= TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

##@ General

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(BLUE)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

info: ## Show build configuration
	@echo "$(BLUE)The Mirror - Build Configuration$(NC)"
	@echo "=================================="
	@echo "Registry:      $(YELLOW)$(REGISTRY)$(NC)"
	@echo "Namespace:     $(YELLOW)$(NAMESPACE)$(NC)"
	@echo "Image Tag:     $(YELLOW)$(IMAGE_TAG)$(NC)"
	@echo "LLM Model:     $(YELLOW)$(LLM_MODEL)$(NC)"
	@echo ""
	@echo "Images to build:"
	@echo "  Agent:  $(GREEN)$(AGENT_IMAGE)$(NC)"
	@echo "  LLM:    $(GREEN)$(LLM_IMAGE)$(NC)"
	@echo ""

##@ Local Docker Builds

build-all: build-agent build-llm ## Build all images locally with Docker

build-agent: ## Build the Mirror agent image locally
	@echo "$(BLUE)Building Mirror Agent image...$(NC)"
	docker build \
		-f scenario-the-mirror/Dockerfile \
		-t $(AGENT_IMAGE) \
		-t mirror-agent:latest \
		.
	@echo "$(GREEN)✓ Agent image built successfully$(NC)"

build-llm: ## Build LLM server image with TinyLlama (default)
	@echo "$(BLUE)Building LLM server image ($(LLM_MODEL))...$(NC)"
	@echo "$(YELLOW)Warning: This will download ~2.2GB model at build time$(NC)"
	docker build \
		-f Dockerfile \
		--build-arg MODEL_ID=$(LLM_MODEL) \
		-t $(LLM_IMAGE) \
		-t llm-server:latest \
		.
	@echo "$(GREEN)✓ LLM server image built successfully$(NC)"

build-llm-tiny: ## Build LLM server with TinyLlama-1.1B (recommended)
	@$(MAKE) build-llm LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0

build-llm-distil: ## Build LLM server with DistilGPT2 (lightweight, 82M params)
	@$(MAKE) build-llm LLM_MODEL=distilgpt2

##@ OpenShift Builds

login-check: ## Check OpenShift login
	@if ! oc whoami &> /dev/null; then \
		echo "$(RED)Error: Not logged into OpenShift$(NC)"; \
		echo "Run: oc login <cluster-url>"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Logged into OpenShift as $$(oc whoami)$(NC)"

build-openshift: login-check build-agent-openshift build-llm-openshift ## Build all images on OpenShift

build-agent-openshift: login-check ## Build Mirror agent on OpenShift
	@echo "$(BLUE)Building Mirror Agent on OpenShift...$(NC)"
	@# Ensure namespace exists
	@oc get namespace $(NAMESPACE) &> /dev/null || oc create namespace $(NAMESPACE)
	@oc project $(NAMESPACE)
	@# Create BuildConfig if it doesn't exist
	@if ! oc get bc/mirror-agent &> /dev/null; then \
		echo "Creating BuildConfig for mirror-agent..."; \
		oc new-build --binary --name=mirror-agent \
			--strategy=docker \
			-l app=mirror-agent; \
	fi
	@# Start build from root directory
	@echo "Starting build (copying files to OpenShift)..."
	@oc start-build mirror-agent --from-dir=. --follow
	@echo "$(GREEN)✓ Agent image built on OpenShift$(NC)"

build-llm-openshift: login-check ## Build LLM server on OpenShift
	@echo "$(BLUE)Building LLM server on OpenShift...$(NC)"
	@echo "$(YELLOW)Model: $(LLM_MODEL)$(NC)"
	@echo "$(YELLOW)Warning: Build will take 5-10 minutes (downloads model)$(NC)"
	@# Ensure namespace exists
	@oc get namespace $(NAMESPACE) &> /dev/null || oc create namespace $(NAMESPACE)
	@oc project $(NAMESPACE)
	@# Create BuildConfig if it doesn't exist
	@if ! oc get bc/llm-server &> /dev/null; then \
		echo "Creating BuildConfig for llm-server..."; \
		oc new-build --binary --name=llm-server \
			--strategy=docker \
			--build-arg MODEL_ID=$(LLM_MODEL) \
			-l app=llm-server; \
	fi
	@# Start build (only need Dockerfile and llm_server.py)
	@echo "Starting build..."
	@mkdir -p .tmp-llm-build
	@cp Dockerfile llm_server.py .tmp-llm-build/
	@oc start-build llm-server --from-dir=.tmp-llm-build --follow
	@rm -rf .tmp-llm-build
	@echo "$(GREEN)✓ LLM server image built on OpenShift$(NC)"

##@ Docker Push (for external registries)

push-all: push-agent push-llm ## Push all images to registry

push-agent: ## Push agent image to registry
	@echo "$(BLUE)Pushing agent image...$(NC)"
	docker push $(AGENT_IMAGE)
	@echo "$(GREEN)✓ Agent image pushed$(NC)"

push-llm: ## Push LLM image to registry
	@echo "$(BLUE)Pushing LLM image...$(NC)"
	docker push $(LLM_IMAGE)
	@echo "$(GREEN)✓ LLM image pushed$(NC)"

##@ Image Deployment

deploy-images: build-openshift ## Build and verify images are ready for Helm
	@echo "$(BLUE)Verifying images are available...$(NC)"
	@oc get imagestream mirror-agent -n $(NAMESPACE) &> /dev/null && \
		echo "$(GREEN)✓ mirror-agent imagestream exists$(NC)" || \
		echo "$(RED)✗ mirror-agent imagestream not found$(NC)"
	@oc get imagestream llm-server -n $(NAMESPACE) &> /dev/null && \
		echo "$(GREEN)✓ llm-server imagestream exists$(NC)" || \
		echo "$(RED)✗ llm-server imagestream not found$(NC)"
	@echo ""
	@echo "$(GREEN)Images are ready for Helm deployment!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Install Helm chart:"
	@echo "     $(BLUE)helm install the-mirror ./helm/the-mirror -n $(NAMESPACE) --create-namespace$(NC)"
	@echo ""
	@echo "  2. Watch deployment:"
	@echo "     $(BLUE)oc get pods -n $(NAMESPACE) -w$(NC)"

##@ Testing

test-agent: ## Test agent image locally (Docker)
	@echo "$(BLUE)Testing agent image...$(NC)"
	@docker run --rm mirror-agent:latest python3 -c "import agent; print('✓ Agent imports work')"
	@echo "$(GREEN)✓ Agent image test passed$(NC)"

test-llm: ## Test LLM server image locally (Docker)
	@echo "$(BLUE)Testing LLM server image...$(NC)"
	@echo "Starting LLM server container..."
	@docker run -d --name llm-test -p 8000:8000 llm-server:latest
	@echo "Waiting for server to be ready (60s timeout)..."
	@timeout 60 bash -c 'until curl -f http://localhost:8000/health 2>/dev/null; do sleep 2; done' && \
		echo "$(GREEN)✓ LLM server health check passed$(NC)" || \
		echo "$(RED)✗ LLM server health check failed$(NC)"
	@docker stop llm-test
	@docker rm llm-test

test-openshift: login-check ## Test images on OpenShift
	@echo "$(BLUE)Testing images on OpenShift...$(NC)"
	@# Check imagestreams exist
	@oc get is/mirror-agent -n $(NAMESPACE) -o jsonpath='{.status.tags[0].tag}' && \
		echo "$(GREEN)✓ mirror-agent image available$(NC)"
	@oc get is/llm-server -n $(NAMESPACE) -o jsonpath='{.status.tags[0].tag}' && \
		echo "$(GREEN)✓ llm-server image available$(NC)"

##@ Cleanup

clean: ## Remove local images
	@echo "$(YELLOW)Removing local images...$(NC)"
	@docker rmi mirror-agent:latest llm-server:latest || true
	@echo "$(GREEN)✓ Local images removed$(NC)"

clean-openshift: login-check ## Remove OpenShift BuildConfigs and ImageStreams
	@echo "$(RED)Warning: This will remove BuildConfigs and ImageStreams$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		oc delete bc/mirror-agent bc/llm-server -n $(NAMESPACE) --ignore-not-found; \
		oc delete is/mirror-agent is/llm-server -n $(NAMESPACE) --ignore-not-found; \
		echo "$(GREEN)✓ OpenShift resources cleaned$(NC)"; \
	fi

##@ Quick Start Recipes

quick-start: build-openshift deploy-images ## Build images and show deployment command
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(GREEN)  Quick Start Complete!$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(BLUE)Images built successfully in namespace: $(NAMESPACE)$(NC)"
	@echo ""
	@echo "Deploy with Helm:"
	@echo "  $(YELLOW)helm install the-mirror ./helm/the-mirror -n $(NAMESPACE) --create-namespace$(NC)"
	@echo ""

local-build: build-all ## Build all images locally with Docker
	@echo ""
	@echo "$(GREEN)Local images built!$(NC)"
	@echo ""
	@echo "To push to registry:"
	@echo "  $(YELLOW)make push-all$(NC)"
	@echo ""

.DEFAULT_GOAL := help
