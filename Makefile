MAKEFLAGS += --no-print-directory

VERSION ?= latest
NAMESPACE ?= datamate

.PHONY: build-%
build-%:
	$(MAKE) $*-docker-build

.PHONY: build
build: backend-docker-build frontend-docker-build runtime-docker-build

.PHONY: create-namespace
create-namespace:
	@kubectl get namespace $(NAMESPACE) > /dev/null 2>&1 || kubectl create namespace $(NAMESPACE)

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

.PHONY: backend-docker-install
backend-docker-install:
	cd deployment/docker/datamate && docker-compose up -d backend

.PHONY: backend-docker-uninstall
backend-docker-uninstall:
	cd deployment/docker/datamate && docker-compose down backend

.PHONY: frontend-docker-install
frontend-docker-install:
	cd deployment/docker/datamate && docker-compose up -d frontend

.PHONY: frontend-docker-uninstall
frontend-docker-uninstall:
	cd deployment/docker/datamate && docker-compose down frontend

.PHONY: runtime-docker-install
runtime-docker-install:
	cd deployment/docker/datamate && docker-compose up -d runtime

.PHONY: runtime-docker-uninstall
runtime-docker-uninstall:
	cd deployment/docker/datamate && docker-compose down runtime

.PHONY: datamate-docker-install
datamate-docker-install:
	cd deployment/docker/datamate && docker-compose up -d

.PHONY: datamate-docker-uninstall
datamate-docker-uninstall:
	cd deployment/docker/datamate && docker-compose down

.PHONY: datamate-k8s-install
datamate-k8s-install: create-namespace
	kubectl create configmap datamate-init-sql --from-file=scripts/db/ --dry-run=client -o yaml | kubectl apply -f - -n $(NAMESPACE)
	helm upgrade datamate deployment/helm/datamate/ -n $(NAMESPACE) --install

.PHONY: datamate-k8s-uninstall
datamate-k8s-uninstall:
	helm uninstall datamate -n $(NAMESPACE) --ignore-not-found
	kubectl delete configmap datamate-init-sql -n $(NAMESPACE) --ignore-not-found
