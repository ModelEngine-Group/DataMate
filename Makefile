MAKEFLAGS += --no-print-directory

WITH_MINERU ?= false  # 默认不构建mineru
VERSION ?= latest
NAMESPACE ?= datamate

# Registry configuration: use --dev for local images, otherwise use GitHub registry
ifdef dev
    REGISTRY :=
else
    REGISTRY ?= ghcr.io/modelengine-group/
endif

ifdef COMSPEC
    # Windows
    MAKE := "C:/Program Files (x86)/GnuWin32/bin/make"
else
    # Linux/Mac
    MAKE := make
endif

# ========== Help ==========

.PHONY: help
help:
	@echo "DataMate Makefile - Available Commands"
	@echo ""
	@echo "Usage: make <target> [options]"
	@echo ""
	@echo "Options:"
	@echo "  --dev              Use local images instead of registry (empty REGISTRY)"
	@echo "  VERSION=<version>  Set image version (default: latest)"
	@echo "  NAMESPACE=<name>   Set Kubernetes namespace (default: datamate)"
	@echo "  INSTALLER=<type>   Set installer type: docker or k8s"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build                     Build all core images"
	@echo "  make <service>-docker-build    Build specific service image"
	@echo "    Valid services: backend, database, frontend, runtime,"
	@echo "                    backend-python, deer-flow, mineru"
	@echo ""
	@echo "Install Commands:"
	@echo "  make install                        Install datamate + milvus (prompts for method)"
	@echo "  make install INSTALLER=docker       Install using Docker Compose"
	@echo "  make install INSTALLER=k8s          Install using Kubernetes/Helm"
	@echo "  make install-<component>            Install specific component (prompts)"
	@echo "  make <component>-docker-install     Install component via Docker"
	@echo "  make <component>-k8s-install        Install component via Kubernetes"
	@echo "    Valid components: datamate, milvus, deer-flow, mineru"
	@echo "    Valid services: backend, frontend, runtime, label-studio"
	@echo ""
	@echo "Uninstall Commands:"
	@echo "  make uninstall                      Uninstall datamate + milvus (prompts)"
	@echo "  make uninstall INSTALLER=docker     Uninstall using Docker Compose"
	@echo "  make uninstall INSTALLER=k8s        Uninstall using Kubernetes/Helm"
	@echo "  make uninstall-<component>          Uninstall specific component (prompts)"
	@echo "  make <component>-docker-uninstall   Uninstall component via Docker"
	@echo "  make <component>-k8s-uninstall      Uninstall component via Kubernetes"
	@echo ""
	@echo "Upgrade Commands:"
	@echo "  make datamate-docker-upgrade   Upgrade datamate deployment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make create-namespace          Create Kubernetes namespace"
	@echo "  make help                      Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make build --dev               Build all images for local development"
	@echo "  make install INSTALLER=docker  Install via Docker Compose"
	@echo "  make install --dev             Install using local images"
	@echo "  make datamate-docker-upgrade   Upgrade running datamate services"
	@echo ""

.DEFAULT_GOAL := help

# ========== Functions ==========

# Prompt user to choose installer if not specified
define prompt-installer
	@echo "Choose a deployment method:"
	@echo "1. Docker/Docker-Compose"
	@echo "2. Kubernetes/Helm"
	@echo -n "Enter choice: "
	@read choice; \
	case $$choice in \
		1) INSTALLER=docker ;; \
		2) INSTALLER=k8s ;; \
		*) echo "Invalid choice" && exit 1 ;; \
	esac; \
	$(MAKE) $(1)
endef

# Generic docker build function
# Usage: $(call docker-build,service-name,image-name)
define docker-build
	docker build -t $(2):$(VERSION) . -f scripts/images/$(1)/Dockerfile
endef

# Generic docker compose service action
# Usage: $(call docker-compose-service,service-name,action,compose-dir)
define docker-compose-service
	cd $(3) && docker compose $(2) $(1)
endef

# ========== Build Targets ==========

# Valid build targets
VALID_BUILD_TARGETS := backend database frontend runtime backend-python deer-flow mineru

# Generic docker build target with service name as parameter
# Automatically prefixes image names with "datamate-" unless it's deer-flow
.PHONY: %-docker-build
%-docker-build:
	@if ! echo "$(VALID_BUILD_TARGETS)" | grep -wq "$*"; then \
		echo "Error: Unknown build target '$*'"; \
		echo "Valid build targets are:"; \
		for target in $(VALID_BUILD_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "deer-flow" ]; then \
		cp -n runtime/deer-flow/.env.example runtime/deer-flow/.env; \
		cp -n runtime/deer-flow/conf.yaml.example runtime/deer-flow/conf.yaml; \
		$(call docker-build,deer-flow-backend,deer-flow-backend); \
		$(call docker-build,deer-flow-frontend,deer-flow-frontend); \
	else \
		$(call docker-build,$*,datamate-$*); \
	fi

.PHONY: build
build: database-docker-build backend-docker-build frontend-docker-build runtime-docker-build backend-python-docker-build

# ========== Utility Targets ==========

.PHONY: create-namespace
create-namespace:
	kubectl get namespace $(NAMESPACE) > /dev/null 2>&1 || kubectl create namespace $(NAMESPACE)

# ========== Generic Install/Uninstall Targets (Redirect to prompt-installer) ==========

.PHONY: install-%
install-%:
ifeq ($(origin INSTALLER), undefined)
	$(call prompt-installer,$*-$$INSTALLER-install)
else
	$(MAKE) $*-$(INSTALLER)-install
endif

.PHONY: install
install:
ifeq ($(origin INSTALLER), undefined)
	$(call prompt-installer,datamate-$$INSTALLER-install milvus-$$INSTALLER-install)
else
	$(MAKE) datamate-$(INSTALLER)-install
	$(MAKE) milvus-$(INSTALLER)-install
endif

.PHONY: uninstall-%
uninstall-%:
ifeq ($(origin INSTALLER), undefined)
	$(call prompt-installer,$*-$$INSTALLER-uninstall)
else
	$(MAKE) $*-$(INSTALLER)-uninstall
endif

.PHONY: uninstall
uninstall:
ifeq ($(origin INSTALLER), undefined)
	$(call prompt-installer,milvus-$$INSTALLER-uninstall datamate-$$INSTALLER-uninstall)
else
	$(MAKE) milvus-$(INSTALLER)-uninstall
	$(MAKE) datamate-$(INSTALLER)-uninstall
endif

# ========== Docker Install/Uninstall Targets ==========

# Valid service targets for docker install/uninstall
VALID_SERVICE_TARGETS := datamate backend frontend runtime label-studio mineru deer-flow milvus

# Generic docker service install target
.PHONY: %-docker-install
%-docker-install:
	@if ! echo "$(VALID_SERVICE_TARGETS)" | grep -wq "$*"; then \
		echo "Error: Unknown service target '$*'"; \
		echo "Valid service targets are:"; \
		for target in $(VALID_SERVICE_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "label-studio" ]; then \
		$(call docker-compose-service,label-studio,up -d,deployment/docker/label-studio); \
	elif [ "$*" = "mineru" ]; then \
		cd deployment/docker/datamate && export REGISTRY=$(REGISTRY) && docker compose up -d datamate-mineru; \
	elif [ "$*" = "datamate" ]; then \
		if docker compose ls --filter name=deer-flow | grep -q deer-flow; then \
			(cd deployment/docker/datamate && NGINX_CONF="./backend-with-deer-flow.conf" REGISTRY=$(REGISTRY) docker compose -f docker-compose.yml up -d) && \
			$(MAKE) label-studio-docker-install; \
		else \
			(cd deployment/docker/datamate && REGISTRY=$(REGISTRY) docker compose -f docker-compose.yml up -d) && \
			$(MAKE) label-studio-docker-install; \
		fi; \
	elif [ "$*" = "deer-flow" ]; then \
		cd deployment/docker/datamate && export NGINX_CONF="./backend-with-deer-flow.conf" && export REGISTRY=$(REGISTRY) && docker compose -f docker-compose.yml up -d; \
		cp -n runtime/deer-flow/.env.example runtime/deer-flow/.env; \
		cp -n runtime/deer-flow/conf.yaml.example runtime/deer-flow/conf.yaml; \
		cp runtime/deer-flow/.env deployment/docker/deer-flow/.env; \
		cp runtime/deer-flow/conf.yaml deployment/docker/deer-flow/conf.yaml; \
		cd deployment/docker/deer-flow && export REGISTRY=$(REGISTRY) && docker compose -f docker-compose.yml up -d; \
	elif [ "$*" = "milvus" ]; then \
		$(call docker-compose-service,--file docker-compose.yml,up -d,deployment/docker/milvus); \
	else \
		$(call docker-compose-service,$*,up -d,deployment/docker/datamate); \
	fi

# Generic docker service uninstall target
.PHONY: %-docker-uninstall
%-docker-uninstall:
	@if ! echo "$(VALID_SERVICE_TARGETS)" | grep -wq "$*"; then \
		echo "Error: Unknown service target '$*'"; \
		echo "Valid service targets are:"; \
		for target in $(VALID_SERVICE_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "label-studio" ]; then \
		$(call docker-compose-service,label-studio,down,deployment/docker/label-studio); \
	elif [ "$*" = "mineru" ]; then \
		$(call docker-compose-service,datamate-mineru,down,deployment/docker/datamate); \
	elif [ "$*" = "datamate" ]; then \
		cd deployment/docker/datamate && docker compose -f docker-compose.yml --profile mineru down -v; \
		$(MAKE) label-studio-docker-uninstall; \
	elif [ "$*" = "deer-flow" ]; then \
		if docker compose ls --filter name=datamate | grep -q datamate; then \
			cd deployment/docker/datamate && export REGISTRY=$(REGISTRY) && docker compose -f docker-compose.yml up -d; \
		fi; \
		cd deployment/docker/deer-flow && docker compose -f docker-compose.yml down; \
	elif [ "$*" = "milvus" ]; then \
		$(call docker-compose-service,--file docker-compose.yml,down,deployment/docker/milvus); \
	else \
		$(call docker-compose-service,$*,down,deployment/docker/datamate); \
	fi

# ========== Kubernetes Install/Uninstall Targets ==========

# Valid k8s targets
VALID_K8S_TARGETS := mineru datamate deer-flow milvus

# Generic k8s install target
.PHONY: %-k8s-install
%-k8s-install: create-namespace
	@if ! echo "$(VALID_K8S_TARGETS)" | grep -wq "$*"; then \
		echo "Error: Unknown k8s target '$*'"; \
		echo "Valid k8s targets are:"; \
		for target in $(VALID_K8S_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "mineru" ]; then \
		kubectl apply -f deployment/kubernetes/mineru/deploy.yaml -n $(NAMESPACE); \
	elif [ "$*" = "datamate" ]; then \
		helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --install --set global.image.repository=$(REGISTRY); \
	elif [ "$*" = "deer-flow" ]; then \
		helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --install --set global.deerFlow.enable=true --set global.image.repository=$(REGISTRY); \
		cp runtime/deer-flow/.env deployment/helm/deer-flow/charts/public/.env; \
		cp runtime/deer-flow/conf.yaml deployment/helm/deer-flow/charts/public/conf.yaml; \
		helm upgrade deer-flow deployment/helm/deer-flow -n $(NAMESPACE) --install --set global.image.repository=$(REGISTRY); \
	elif [ "$*" = "milvus" ]; then \
		helm upgrade milvus deployment/helm/milvus -n $(NAMESPACE) --install; \
	fi

# Generic k8s uninstall target
.PHONY: %-k8s-uninstall
%-k8s-uninstall:
	@if ! echo "$(VALID_K8S_TARGETS)" | grep -wq "$*"; then \
		echo "Error: Unknown k8s target '$*'"; \
		echo "Valid k8s targets are:"; \
		for target in $(VALID_K8S_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "mineru" ]; then \
		kubectl delete -f deployment/kubernetes/mineru/deploy.yaml -n $(NAMESPACE); \
	elif [ "$*" = "datamate" ]; then \
		helm uninstall datamate -n $(NAMESPACE) --ignore-not-found; \
	elif [ "$*" = "deer-flow" ]; then \
		helm uninstall deer-flow -n $(NAMESPACE) --ignore-not-found; \
		if helm ls -n $(NAMESPACE) --filter datamate | grep -q datamate; then \
			helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --set global.deerFlow.enable=false; \
		fi; \
	elif [ "$*" = "milvus" ]; then \
		helm uninstall milvus -n $(NAMESPACE) --ignore-not-found; \
	fi

# ========== Upgrade Targets ==========

# Valid upgrade targets
VALID_UPGRADE_TARGETS := datamate

# Generic docker upgrade target
.PHONY: %-docker-upgrade
%-docker-upgrade:
	@if ! echo "$(VALID_UPGRADE_TARGETS)" | grep -wq "$*"; then \
		echo "Error: Unknown upgrade target '$*'"; \
		echo "Valid upgrade targets are:"; \
		for target in $(VALID_UPGRADE_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "datamate" ]; then \
		cd deployment/docker/datamate && docker compose -f docker-compose.yml --profile mineru up -d --force-recreate --remove-orphans; \
	fi