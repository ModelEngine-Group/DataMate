MAKEFLAGS += --no-print-directory

INSTALLER ?= docker

.PHONY: install-%
install-%:
ifeq ($(INSTALLER),docker)
	@echo "Installing via Docker..."
	$(MAKE) docker-$*
else ifeq ($(INSTALLER),helm)
	@echo "Installing via Helm..."
	$(MAKE) helm-$*
else ifeq ($(INSTALLER),k8s)
	@echo "Installing via raw K8s manifests..."
	$(MAKE) k8s-$*
else
	@echo "Unknown INSTALLER: $(INSTALLER)"
endif

.PHONY: build-%
build-%:
	$(MAKE) $*

.PHONY: mineru
mineru:
	sh build/mineru/build.sh

.PHONY: datax
datax:
	sh build/datax/build.sh

.PHONY: data-juicer
data-juicer:
	sh build/data-juicer/build.sh

.PHONY: unstructured
unstructured:
	sh build/unstructured/build.sh

.PHONY: backend
backend:
	sh build/backend/build.sh

.PHONY: frontend
frontend:
	sh build/frontend/build.sh

.PHONY: k8s-mineru
k8s-mineru:
	kubectl apply -f install/kubernetes/mineru/deploy.yaml

.PHONY: k8s-datax
k8s-datax:
	kubectl apply -f install/kubernetes/datax/deploy.yaml

.PHONY: docker-datax
docker-datax:
	cd install/docker/data-platform && docker-compose up -d datax

.PHONY: helm-data-juicer
helm-data-juicer:
	sh install/helm/data-juicer/install.sh

.PHONY: helm-ray
helm-ray:
	sh install/helm/ray/install.sh

.PHONY: k8s-unstructured
k8s-unstructured:
	kubectl apply -f install/kubernetes/unstructured/deploy.yaml

.PHONY: k8s-mysql
k8s-mysql:
	kubectl apply -f install/kubernetes/mysql/deploy.yaml

.PHONY: k8s-backend
k8s-backend:
	kubectl apply -f install/kubernetes/backend/deploy.yaml

.PHONY: k8s-frontend
k8s-frontend:
	kubectl apply -f install/kubernetes/frontend/deploy.yaml

.PHONY: k8s-pgsql
k8s-pgsql:
	kubectl apply -f install/kubernetes/postgresql/deploy.yaml

.PHONY: docker-edatamate
docker-edatamate:
	cd install/docker/data-platform && docker-compose up -d

.PHONY: k8s-edatamate
k8s-edatamate: k8s-pgsql k8s-backend k8s-frontend datax