MAKEFLAGS += --no-print-directory

WITH_MINERU ?= false  # 默认不构建mineru
VERSION ?= latest
NAMESPACE ?= datamate

ifdef COMSPEC
    # Windows 环境
    MAKE := "C:/Program Files (x86)/GnuWin32/bin/make"
else
    # Linux/Mac 环境
    MAKE := make
endif

.PHONY: build-%
build-%:
	$(MAKE) $*-docker-build

.PHONY: build
build: backend-docker-build frontend-docker-build runtime-docker-build $(if $(WITH_MINERU),mineru-docker-build)

.PHONY: create-namespace
create-namespace:
	kubectl get namespace $(NAMESPACE) > /dev/null 2>&1 || kubectl create namespace $(NAMESPACE)

.PHONY: install-%
install-%:
ifeq ($(origin INSTALLER), undefined)
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
	$(MAKE) $*-$$INSTALLER-install
else
	$(MAKE) $*-$(INSTALLER)-install
endif

.PHONY: install
install: install-datamate

.PHONY: uninstall-%
uninstall-%:
ifeq ($(origin INSTALLER), undefined)
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
    $(MAKE) $*-$$INSTALLER-uninstall
else
	$(MAKE) $*-$(INSTALLER)-uninstall
endif

.PHONY: uninstall
uninstall: uninstall-datamate

# build
.PHONY: backend-docker-build
backend-docker-build:
	docker build -t datamate-backend:$(VERSION) . -f scripts/images/backend/Dockerfile

.PHONY: frontend-docker-build
frontend-docker-build:
	docker build -t datamate-frontend:$(VERSION) . -f scripts/images/frontend/Dockerfile

.PHONY: runtime-docker-build
runtime-docker-build:
	docker build -t datamate-runtime:$(VERSION) . -f scripts/images/runtime/Dockerfile

.PHONY: label-studio-adapter-docker-build
label-studio-adapter-docker-build:
	docker build -t label-studio-adapter:$(VERSION) . -f scripts/images/label-studio-adapter/Dockerfile

.PHONY: deer-flow-docker-build
deer-flow-docker-build:
	cp -n runtime/deer-flow/.env.example runtime/deer-flow/.env
	cp -n runtime/deer-flow/conf.yaml.example runtime/deer-flow/conf.yaml
	docker build -t deer-flow-backend:$(VERSION) . -f scripts/images/deer-flow-backend/Dockerfile
	docker build -t deer-flow-frontend:$(VERSION) . -f scripts/images/deer-flow-frontend/Dockerfile

.PHONY: mineru-docker-build
mineru-docker-build:
	docker build -t datamate-mineru:$(VERSION) . -f scripts/images/mineru/Dockerfile
.PHONY: backend-docker-install
backend-docker-install:
	cd deployment/docker/datamate && docker compose up -d backend

.PHONY: backend-docker-uninstall
backend-docker-uninstall:
	cd deployment/docker/datamate && docker compose down backend

.PHONY: frontend-docker-install
frontend-docker-install:
	cd deployment/docker/datamate && docker compose up -d frontend

.PHONY: frontend-docker-uninstall
frontend-docker-uninstall:
	cd deployment/docker/datamate && docker compose down frontend

.PHONY: runtime-docker-install
runtime-docker-install:
	cd deployment/docker/datamate && docker compose up -d runtime

.PHONY: runtime-docker-uninstall
runtime-docker-uninstall:
	cd deployment/docker/datamate && docker compose down runtime

.PHONY: mineru-docker-install
mineru-docker-install:
	cd deployment/docker/datamate && cp .env.example .env && docker compose up -d datamate-mineru

.PHONY: mineru-docker-uninstall
mineru-docker-uninstall:
	cd deployment/docker/datamate && docker compose down datamate-mineru

.PHONY: mineru-k8s-install
mineru-k8s-install: create-namespace
	kubectl apply -f deployment/kubernetes/mineru/deploy.yaml -n $(NAMESPACE)

.PHONY: mineru-k8s-uninstall
mineru-k8s-uninstall:
	kubectl delete -f deployment/kubernetes/mineru/deploy.yaml -n $(NAMESPACE)

.PHONY: datamate-docker-install
datamate-docker-install:
	cd deployment/docker/datamate && cp .env.example .env && docker compose -f docker-compose.yml up -d

.PHONY: datamate-docker-uninstall
datamate-docker-uninstall:
	cd deployment/docker/datamate && docker compose -f docker-compose.yml down -v

.PHONY: deer-flow-docker-install
deer-flow-docker-install:
	cd deployment/docker/datamate && cp .env.deer-flow.example .env && docker compose -f docker-compose.yml up -d
	cp -n runtime/deer-flow/.env.example runtime/deer-flow/.env
	cp -n runtime/deer-flow/conf.yaml.example runtime/deer-flow/conf.yaml
	cp runtime/deer-flow/.env deployment/docker/deer-flow/.env && cp runtime/deer-flow/conf.yaml deployment/docker/deer-flow/conf.yaml
	cd deployment/docker/deer-flow && docker compose -f docker-compose.yml up -d

.PHONY: deer-flow-docker-uninstall
deer-flow-docker-uninstall:
	@if docker compose ls --filter name=datamate | grep -q datamate; then \
		cd deployment/docker/datamate && docker compose -f docker-compose.yml up -d; \
	fi
	cd deployment/docker/deer-flow && docker compose -f docker-compose.yml down

.PHONY: datamate-k8s-install
datamate-k8s-install: create-namespace
	kubectl create configmap datamate-init-sql --from-file=scripts/db/ --dry-run=client -o yaml | kubectl apply -f - -n $(NAMESPACE)
	helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --install

.PHONY: datamate-k8s-uninstall
datamate-k8s-uninstall:
	helm uninstall datamate -n $(NAMESPACE) --ignore-not-found
	kubectl delete configmap datamate-init-sql -n $(NAMESPACE) --ignore-not-found

.PHONY: deer-flow-k8s-install
deer-flow-k8s-install:
	helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --install --set global.deerFlow.enable=true
	cp runtime/deer-flow/.env deployment/helm/deer-flow/charts/public/.env
	cp runtime/deer-flow/conf.yaml deployment/helm/deer-flow/charts/public/conf.yaml
	helm upgrade deer-flow deployment/helm/deer-flow -n $(NAMESPACE) --install

.PHONY: deer-flow-k8s-uninstall
deer-flow-k8s-uninstall:
	helm uninstall deer-flow -n $(NAMESPACE) --ignore-not-found

.PHONY: milvus-k8s-install
milvus-k8s-install:
	helm upgrade milvus deployment/helm/milvus -n $(NAMESPACE) --install

.PHONY: milvus-k8s-uninstall
milvus-k8s-uninstall:
	helm uninstall milvus -n $(NAMESPACE) --ignore-not-found