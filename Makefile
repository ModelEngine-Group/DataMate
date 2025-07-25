MAKEFLAGS += --no-print-directory

INSTALLER ?= docker

.PHONY: build-%
build-%:
	$(MAKE) $*-docker-build

.PHONY: install-%
install-%:
ifeq ($(INSTALLER),docker)
	@echo "Installing via Docker..."
	$(MAKE) $*-docker-install
else ifeq ($(INSTALLER),helm)
	@echo "Installing via Helm..."
	$(MAKE) $*-helm-install
else ifeq ($(INSTALLER),k8s)
	@echo "Installing via raw K8s manifests..."
	$(MAKE) $*-k8s-install
else
	@echo "Unknown INSTALLER: $(INSTALLER)"
endif

.PHONY: install
install: install-edatamate

.PHONY: uninstall-%
uninstall-%:
ifeq ($(INSTALLER),docker)
	@echo "Unstalling via Docker..."
	$(MAKE) $*-docker-uninstall
else ifeq ($(INSTALLER),helm)
	@echo "Unstalling via Helm..."
	$(MAKE) $*-helm-uninstall
else ifeq ($(INSTALLER),k8s)
	@echo "Unstalling via raw K8s manifests..."
	$(MAKE) $*-k8s-uninstall
else
	@echo "Unknown INSTALLER: $(INSTALLER)"
endif

.PHONY: mineru-docker-build
mineru-docker-build:
	sh build/mineru/build.sh

.PHONY: datax-docker-build
datax-docker-build:
	sh build/datax/build.sh

.PHONY: data-juicer-docker-build
data-juicer-docker-build:
	sh build/data-juicer/build.sh

.PHONY: unstructured-docker-build
unstructured-docker-build:
	sh build/unstructured/build.sh

.PHONY: backend-docker-build
backend-docker-build:
	sh build/backend/build.sh

.PHONY: frontend-docker-build
frontend-docker-build:
	sh build/frontend/build.sh

.PHONY: mineru-k8s-install
mineru-k8s-install:
	kubectl apply -f install/kubernetes/mineru/deploy.yaml

.PHONY: datax-k8s-install
datax-k8s-install:
	kubectl apply -f install/kubernetes/datax/deploy.yaml

.PHONY: datax-k8s-uninstall
datax-k8s-uninstall:
	kubectl delete -f install/kubernetes/datax/deploy.yaml

.PHONY: datax-docker-install
datax-docker-install:
	cd install/docker/data-platform && docker-compose up -d datax

.PHONY: datax-docker-uninstall
datax-docker-uninstall:
	cd install/docker/data-platform && docker-compose down datax

.PHONY: data-juicer-helm-install
data-juicer-helm-install:
	sh install/helm/data-juicer/install.sh

.PHONY: ray-helm-install
ray-helm-install:
	sh install/helm/ray/install.sh

.PHONY: es-helm-install
es-helm-install:
	sh install/helm/es/install.sh

.PHONY: unstructured-k8s-install
unstructured-k8s-install:
	kubectl apply -f install/kubernetes/unstructured/deploy.yaml

.PHONY: mysql-k8s-install
mysql-k8s-install:
	kubectl apply -f install/kubernetes/mysql/deploy.yaml

.PHONY: backend-k8s-install
backend-k8s-install:
	kubectl apply -f install/kubernetes/backend/deploy.yaml

.PHONY: backend-k8s-uninstall
backend-k8s-uninstall:
	kubectl delete -f install/kubernetes/backend/deploy.yaml

.PHONY: frontend-k8s-install
frontend-k8s-install:
	kubectl apply -f install/kubernetes/frontend/deploy.yaml

.PHONY: frontend-k8s-uninstall
frontend-k8s-uninstall:
	kubectl delete -f install/kubernetes/frontend/deploy.yaml

.PHONY: pgsql-k8s-install
pgsql-k8s-install:
	kubectl apply -f install/kubernetes/postgresql/deploy.yaml

.PHONY: pgsql-k8s-uninstall
pgsql-k8s-uninstall:
	kubectl delete -f install/kubernetes/postgresql/deploy.yaml

.PHONY: edatamate-docker-install
edatamate-docker-install:
	cd install/docker/data-platform && docker-compose up -d

.PHONY: edatamate-docker-uninstall
edatamate-docker-uninstall:
	cd install/docker/data-platform && docker-compose down

.PHONY: edatamate-k8s-install
edatamate-k8s-install: pgsql-k8s-install backend-k8s-install frontend-k8s-install datax-k8s-install

.PHONY: edatamate-k8s-uninstall
edatamate-k8s-uninstall: pgsql-k8s-uninstall backend-k8s-uninstall frontend-k8s-uninstall datax-k8s-uninstall
