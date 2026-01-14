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
	@echo "  dev=true             Use local images instead of registry (empty REGISTRY)"
	@echo "  VERSION=<version>    Set image version (default: latest)"
	@echo "  NAMESPACE=<name>     Set Kubernetes namespace (default: datamate)"
	@echo "  INSTALLER=<type>     Set installer type: docker or k8s"
	@echo "  PLATFORM=<platform>  Set platform for downloads (default: linux/amd64)"
	@echo "                       Options: linux/amd64, linux/arm64"
	@echo "  SAVE=true            Save images to dist/ during download (default: false)"
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
	@echo "  Note: Docker uninstall will prompt whether to delete volumes"
	@echo ""
	@echo "Upgrade Commands:"
	@echo "  make datamate-docker-upgrade   Upgrade datamate deployment"
	@echo ""
	@echo "Download Commands:"
	@echo "  make download                       Pull all images (no save by default)"
	@echo "  make download VERSION=<version>     Pull all images with specific version"
	@echo "  make download REGISTRY=<registry>   Pull images from specific registry"
	@echo "  make load-images                    Load all downloaded images from dist/"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make create-namespace          Create Kubernetes namespace"
	@echo "  make help                      Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make build dev=true            Build all images for local development"
	@echo "  make install INSTALLER=docker  Install via Docker Compose"
	@echo "  make install dev=true          Install using local images"
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

# Prompt user to choose installer and volume deletion for uninstall
define prompt-uninstaller
	@echo "Choose a deployment method:"
	@echo "1. Docker/Docker-Compose"
	@echo "2. Kubernetes/Helm"
	@echo -n "Enter choice: "
	@read installer_choice; \
	case $$installer_choice in \
		1) INSTALLER=docker ;; \
		2) INSTALLER=k8s ;; \
		*) echo "Invalid choice" && exit 1 ;; \
	esac; \
	if [ "$$INSTALLER" = "docker" ]; then \
		echo "Delete volumes? (This will remove all data)"; \
		echo "1. Yes - Delete volumes"; \
		echo "2. No - Keep volumes"; \
		echo -n "Enter choice (default: 2): "; \
		read DELETE_VOLUMES_CHOICE; \
		$(MAKE) $(1) DELETE_VOLUMES_CHOICE=$$DELETE_VOLUMES_CHOICE; \
	else \
		$(MAKE) $(1); \
	fi
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

# Prompt user to choose whether to delete volumes
define prompt-volume-deletion
	@echo "Delete volumes? (This will remove all data)"
	@echo "1. Yes - Delete volumes"
	@echo "2. No - Keep volumes"
	@echo -n "Enter choice (default: 2): "
	@read choice; \
	case $$choice in \
		1) echo "-v" ;; \
		*) echo "" ;; \
	esac
endef

# ========== Build Targets ==========

# Valid build targets
VALID_BUILD_TARGETS := backend database frontend runtime backend-python deer-flow mineru mineru-npu gateway label-studio

# Generic docker build target with service name as parameter
# Automatically prefixes image names with "datamate-" unless it's deer-flow
.PHONY: %-docker-build
%-docker-build:
	@if ! echo " $(VALID_BUILD_TARGETS) " | grep -q " $* "; then \
		echo "Error: Unknown build target '$*'"; \
		echo "Valid build targets are:"; \
		for target in $(VALID_BUILD_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "deer-flow" ]; then \
		$(call docker-build,deer-flow-backend,deer-flow-backend); \
		$(call docker-build,deer-flow-frontend,deer-flow-frontend); \
	else \
		$(call docker-build,$*,datamate-$*); \
	fi

.PHONY: build-%
build-%: %-docker-build
	@:

.PHONY: build
build: database-docker-build gateway-docker-build backend-docker-build frontend-docker-build runtime-docker-build backend-python-docker-build

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
	$(call prompt-uninstaller,$*-$$INSTALLER-uninstall)
else
	$(MAKE) $*-$(INSTALLER)-uninstall
endif

.PHONY: uninstall
uninstall:
ifeq ($(origin INSTALLER), undefined)
	$(call prompt-uninstaller,label-studio-$$INSTALLER-uninstall milvus-$$INSTALLER-uninstall deer-flow-$$INSTALLER-uninstall datamate-$$INSTALLER-uninstall)
else
	@if [ "$(INSTALLER)" = "docker" ]; then \
		echo "Delete volumes? (This will remove all data)"; \
    	echo "1. Yes - Delete volumes"; \
    	echo "2. No - Keep volumes"; \
    	echo -n "Enter choice (default: 2): "; \
    	read DELETE_VOLUMES_CHOICE; \
    	export DELETE_VOLUMES_CHOICE; \
	fi
	@$(MAKE) label-studio-$(INSTALLER)-uninstall DELETE_VOLUMES_CHOICE=$$DELETE_VOLUMES_CHOICE; \
	$(MAKE) milvus-$(INSTALLER)-uninstall DELETE_VOLUMES_CHOICE=$$DELETE_VOLUMES_CHOICE; \
	$(MAKE) deer-flow-$(INSTALLER)-uninstall DELETE_VOLUMES_CHOICE=$$DELETE_VOLUMES_CHOICE; \
	$(MAKE) datamate-$(INSTALLER)-uninstall DELETE_VOLUMES_CHOICE=$$DELETE_VOLUMES_CHOICE
endif

# ========== Docker Install/Uninstall Targets ==========

# Valid service targets for docker install/uninstall
VALID_SERVICE_TARGETS := datamate backend frontend runtime backend-python database gateway redis mineru deer-flow milvus label-studio data-juicer dj

# Generic docker service install target
.PHONY: %-docker-install
%-docker-install:
	@if ! echo " $(VALID_SERVICE_TARGETS) " | grep -q " $* "; then \
		echo "Error: Unknown service target '$*'"; \
		echo "Valid service targets are:"; \
		for target in $(VALID_SERVICE_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "label-studio" ]; then \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml --profile label-studio up -d; \
	elif [ "$*" = "datamate" ]; then \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml up -d; \
	elif [ "$*" = "mineru" ]; then \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml --profile mineru up -d datamate-mineru; \
	elif [ "$*" = "data-juicer" ] || [ "$*" = "dj" ]; then \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml --profile data-juicer up -d datamate-data-juicer; \
	elif [ "$*" = "redis" ]; then \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml --profile redis up -d datamate-redis; \
	elif [ "$*" = "milvus" ]; then \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml --profile milvus up -d; \
	elif [ "$*" = "deer-flow" ]; then \
		cp runtime/deer-flow/.env deployment/docker/datamate/.env; \
		cp runtime/deer-flow/conf.yaml deployment/docker/datamate/conf.yaml; \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml --profile deer-flow up -d; \
	else \
		REGISTRY=$(REGISTRY) docker compose -f deployment/docker/datamate/docker-compose.yml up -d datamate-$*; \
	fi

# Generic docker service uninstall target
.PHONY: %-docker-uninstall
%-docker-uninstall:
	@if ! echo " $(VALID_SERVICE_TARGETS) " | grep -q " $* "; then \
		echo "Error: Unknown service target '$*'"; \
		echo "Valid service targets are:"; \
		for target in $(VALID_SERVICE_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "label-studio" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml rm -f -s label-studio; \
	elif [ "$*" = "mineru" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml rm -f -s datamate-mineru; \
	elif [ "$*" = "data-juicer" ] || [ "$*" = "dj" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml rm -f -s datamate-data-juicer; \
	elif [ "$*" = "redis" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml rm -f -s datamate-redis; \
	elif [ "$*" = "datamate" ]; then \
		if [ "$(DELETE_VOLUMES_CHOICE)" = "1" ]; then \
			docker compose -f deployment/docker/datamate/docker-compose.yml --profile mineru --profile redis --profile data-juicer --profile deer-flow --profile label-studio --profile milvus down -v; \
		else \
			docker compose -f deployment/docker/datamate/docker-compose.yml --profile mineru --profile redis --profile data-juicer --profile deer-flow --profile label-studio --profile milvus down; \
		fi; \
	elif [ "$*" = "deer-flow" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml rm -f -s deer-flow-backend deer-flow-frontend; \
	elif [ "$*" = "milvus" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml rm -f -s milvus etcd minio; \
	else \
		$(call docker-compose-service,$*,down,deployment/docker/datamate); \
	fi

# ========== Kubernetes Install/Uninstall Targets ==========

# Valid k8s targets
VALID_K8S_TARGETS := mineru datamate deer-flow milvus label-studio data-juicer dj

# Generic k8s install target
.PHONY: %-k8s-install
%-k8s-install: create-namespace
	@if ! echo " $(VALID_K8S_TARGETS) " | grep -q " $* "; then \
		echo "Error: Unknown k8s target '$*'"; \
		echo "Valid k8s targets are:"; \
		for target in $(VALID_K8S_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "label-studio" ]; then \
     	helm upgrade label-studio deployment/helm/label-studio/ -n $(NAMESPACE) --install; \
    elif [ "$*" = "mineru" ]; then \
		kubectl apply -f deployment/kubernetes/mineru/deploy.yaml -n $(NAMESPACE); \
	elif [ "$*" = "datamate" ]; then \
		helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --install --set global.image.repository=$(REGISTRY); \
	elif [ "$*" = "deer-flow" ]; then \
		cp runtime/deer-flow/.env deployment/helm/deer-flow/charts/public/.env; \
		cp runtime/deer-flow/conf.yaml deployment/helm/deer-flow/charts/public/conf.yaml; \
		helm upgrade deer-flow deployment/helm/deer-flow -n $(NAMESPACE) --install --set global.image.repository=$(REGISTRY); \
	elif [ "$*" = "milvus" ]; then \
		helm upgrade milvus deployment/helm/milvus -n $(NAMESPACE) --install; \
	elif [ "$*" = "label-studio" ]; then \
		helm upgrade label-studio deployment/helm/label-studio -n $(NAMESPACE) --install; \
	elif [ "$*" = "data-juicer" ] || [ "$*" = "dj" ]; then \
		kubectl apply -f deployment/kubernetes/data-juicer/deploy.yaml -n $(NAMESPACE); \
	fi

# Generic k8s uninstall target
.PHONY: %-k8s-uninstall
%-k8s-uninstall:
	@if ! echo " $(VALID_K8S_TARGETS) " | grep -q " $* "; then \
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
	elif [ "$*" = "milvus" ]; then \
		helm uninstall milvus -n $(NAMESPACE) --ignore-not-found; \
	elif [ "$*" = "label-studio" ]; then \
		helm uninstall label-studio -n $(NAMESPACE) --ignore-not-found; \
	elif [ "$*" = "data-juicer" ] || [ "$*" = "dj" ]; then \
		kubectl delete -f deployment/kubernetes/data-juicer/deploy.yaml -n $(NAMESPACE); \
	fi

# ========== Upgrade Targets ==========

# Valid upgrade targets
VALID_UPGRADE_TARGETS := datamate

# Generic docker upgrade target
.PHONY: %-docker-upgrade
%-docker-upgrade:
	@if ! echo " $(VALID_UPGRADE_TARGETS) " | grep -q " $* "; then \
		echo "Error: Unknown upgrade target '$*'"; \
		echo "Valid upgrade targets are:"; \
		for target in $(VALID_UPGRADE_TARGETS); do \
			echo "  - $$target"; \
		done; \
		exit 1; \
	fi
	@if [ "$*" = "datamate" ]; then \
		docker compose -f deployment/docker/datamate/docker-compose.yml --profile mineru up -d --force-recreate --remove-orphans; \
	fi

# ========== Download Targets ==========

# List of all images to download
DOWNLOAD_IMAGES := \
	datamate-backend \
	datamate-frontend \
	datamate-database \
	datamate-runtime \
	datamate-backend-python \
	datamate-gateway \

# Detect architecture for smart default
CURRENT_ARCH := $(shell uname -m 2>/dev/null)
ifeq ($(CURRENT_ARCH),aarch64)
	DEFAULT_OPTION := 2
else ifeq ($(CURRENT_ARCH),arm64)
	DEFAULT_OPTION := 2
else
	DEFAULT_OPTION := 1
endif


#Usage: make download VERSION=1.0.0 REGISTRY=ghcr.io/modelengine-group/ SAVE=true
.PHONY: download
download:
	@echo "Select target platform for images:"
	@echo "  1) x86_64 (Intel/AMD, linux/amd64)"
	@echo "  2) ARM64  (Apple Silicon, Raspberry Pi 4+, linux/arm64)"
	@{ \
		read -p "Enter choice [1/2] (default: $(DEFAULT_OPTION)): " plat_choice; \
		case "$${plat_choice:-$(DEFAULT_OPTION)}" in \
			1) PLATFORM="linux/amd64" ;; \
			2) PLATFORM="linux/arm64" ;; \
			*) echo "Invalid choice. Using default option $(DEFAULT_OPTION)."; \
			   PLATFORM=$$([ "$(DEFAULT_OPTION)" = "1" ] && echo "linux/amd64" || echo "linux/arm64");; \
		esac; \
		\
		read -p "Save images to dist/ for offline use? (y/n): " save_resp; \
		case "$$save_resp" in \
			[yY]|[yY][eE][sS]) SAVE="true" ;; \
			*) SAVE="false" ;; \
		esac; \
		\
		if [ -z "$(REGISTRY)" ] && [ "$$SAVE" != "true" ]; then \
			echo "Error: REGISTRY unset and SAVE=false. Nothing to do."; \
			exit 1; \
		fi; \
		\
		if [ "$$SAVE" = "true" ]; then mkdir -p dist; fi; \
		failed=0; \
		\
		for image in $(DOWNLOAD_IMAGES); do \
			if [ -z "$(REGISTRY)" ]; then \
				src_image="$$image:$(VERSION)"; \
				echo "Using local image: $$src_image"; \
			else \
				src_image="$(REGISTRY)$$image:$(VERSION)"; \
				echo "Pulling $$src_image ($$PLATFORM)..."; \
				if ! docker pull --platform "$$PLATFORM" "$$src_image"; then \
					echo "✗ Failed to pull $$src_image"; \
					failed=$$(($$failed + 1)); \
					continue; \
				fi; \
			fi; \
			\
			if [ "$$SAVE" = "true" ]; then \
				output="dist/$$image-$(VERSION).tar"; \
				echo "Saving to $$output..."; \
				if docker save -o "$$output" "$$src_image"; then \
					echo "✓ Saved $$image"; \
				else \
					echo "✗ Failed to save $$src_image"; \
					failed=$$(($$failed + 1)); \
				fi; \
			else \
				echo "✓ Ready: $$src_image"; \
			fi; \
			echo ""; \
		done; \
		\
		if [ $$failed -eq 0 ]; then \
			if [ "$$SAVE" = "true" ]; then \
				echo "✅ All images saved to dist/"; \
				echo "Load on target: docker load -i <image>.tar"; \
			else \
				echo "✅ All images ready in local Docker daemon"; \
			fi; \
		else \
			echo "❌ $$failed image(s) failed"; \
			exit 1; \
		fi; \
	}

DEER_FLOW_IMAGES := \
	deer-flow-backend \
	deer-flow-frontend

.PHONY: download-deer-flow
download-deer-flow:
	$(MAKE) download DOWNLOAD_IMAGES="$(DEER_FLOW_IMAGES)"

# Load all downloaded images from dist/ directory
.PHONY: load-images
load-images:
	@if [ ! -d "dist" ]; then \
		echo "Error: dist/ directory not found"; \
		echo "Please run 'make download' first to download images"; \
		exit 1; \
	fi
	@echo "Loading images from dist/..."
	@count=0; \
	for tarfile in dist/*.tar.gz; do \
		if [ -f "$$tarfile" ]; then \
			echo "Loading $$tarfile..."; \
			docker load -i "$$tarfile"; \
			count=$$((count + 1)); \
			echo "✓ Loaded $$tarfile"; \
			echo ""; \
		fi; \
	done; \
	if [ $$count -eq 0 ]; then \
		echo "No image files found in dist/"; \
		echo "Please run 'make download' first"; \
		exit 1; \
	else \
		echo "Successfully loaded $$count image(s)"; \
	fi
