MAKEFLAGS += --no-print-directory

override INSTALLER = docker

.PHONY: build-%
build-%:
	$(MAKE) $*-docker-build

.PHONY: install-%
install-%:
	@echo "Choose a deployment method:"
	@echo "1. Docker"
	@echo "2. Kubernetes"
	@echo "3. Helm"
	@echo -n "Enter choice: "
	@read choice; \
	case $$choice in \
		1) INSTALLER=docker ;; \
		2) INSTALLER=k8s ;; \
		3) INSTALLER=helm ;; \
		*) echo "Invalid choice" && exit 1 ;; \
	esac; \
	$(MAKE) $*-$$INSTALLER-install

.PHONY: install
install: install-data-platform

.PHONY: uninstall-%
uninstall-%:
	@echo "Choose a deployment method:"
	@echo "1. Docker"
	@echo "2. Kubernetes"
	@echo "3. Helm"
	@echo -n "Enter choice: "
	@read choice; \
	case $$choice in \
		1) INSTALLER=docker ;; \
		2) INSTALLER=k8s ;; \
		3) INSTALLER=helm ;; \
		*) echo "Invalid choice" && exit 1 ;; \
	esac; \
    $(MAKE) $*-$$INSTALLER-uninstall

.PHONY: uninstall
uninstall: uninstall-data-platform

# build
.PHONY: mineru-docker-build
mineru-docker-build:
	sh scripts/images/mineru/build.sh

.PHONY: datax-docker-build
datax-docker-build:
	sh scripts/images/datax/build.sh

.PHONY: data-juicer-docker-build
data-juicer-docker-build:
	sh scripts/images/data-juicer/build.sh

.PHONY: unstructured-docker-build
unstructured-docker-build:
	sh scripts/images/unstructured/build.sh

.PHONY: backend-docker-build
backend-docker-build:
	sh scripts/images/backend/build.sh

.PHONY: frontend-docker-build
frontend-docker-build:
	sh scripts/images/frontend/build.sh

.PHONY: runtime-docker-build
runtime-docker-build:
	sh scripts/images/runtime/build.sh

.PHONY: backend-docker-install
backend-docker-install:
	cd deployment/docker/data-platform && docker-compose up -d backend

.PHONY: backend-docker-uninstall
backend-docker-uninstall:
	cd deployment/docker/data-platform && docker-compose down backend

.PHONY: frontend-docker-install
frontend-docker-install:
	cd deployment/docker/data-platform && docker-compose up -d frontend

.PHONY: frontend-docker-uninstall
frontend-docker-uninstall:
	cd deployment/docker/data-platform && docker-compose down frontend

.PHONY: runtime-helm-install
runtime-helm-install:
	helm repo add kuberay https://ray-project.github.io/kuberay-helm/
	helm repo update
	helm upgrade kuberay-operator kuberay/kuberay-operator --version 1.4.0 --install
	helm upgrade raycluster deployment/helm/ray/ray-cluster/ --install
	kubectl apply -f deployment/helm/ray/service.yaml

.PHONY: unstructured-k8s-install
unstructured-k8s-install:
	kubectl apply -f deployment/kubernetes/unstructured/deploy.yaml

.PHONY: mysql-k8s-install
mysql-k8s-install:
	kubectl create configmap init-sql --from-file=scripts/db/ --dry-run=client -o yaml > deployment/kubernetes/mysql/init-sql.yaml
	kubectl apply -f deployment/kubernetes/mysql/init-sql.yaml
	kubectl apply -f deployment/kubernetes/mysql/deploy.yaml

.PHONY: mysql-k8s-uninstall
mysql-k8s-uninstall:
	kubectl delete configmap init-sql
	kubectl delete -f deployment/kubernetes/mysql/deploy.yaml

.PHONY: backend-k8s-install
backend-k8s-install:
	kubectl apply -f deployment/kubernetes/backend/deploy.yaml

.PHONY: backend-k8s-uninstall
backend-k8s-uninstall:
	kubectl delete -f deployment/kubernetes/backend/deploy.yaml

.PHONY: frontend-k8s-install
frontend-k8s-install:
	kubectl apply -f deployment/kubernetes/frontend/deploy.yaml

.PHONY: frontend-k8s-uninstall
frontend-k8s-uninstall:
	kubectl delete -f deployment/kubernetes/frontend/deploy.yaml

.PHONY: data-platform-docker-install
data-platform-docker-install:
	cd deployment/docker/data-platform && docker-compose up -d

.PHONY: data-platform-docker-uninstall
data-platform-docker-uninstall:
	cd deployment/docker/data-platform && docker-compose down

.PHONY: data-platform-k8s-install
data-platform-k8s-install: mysql-k8s-install backend-k8s-install frontend-k8s-install runtime-helm-install

.PHONY: data-platform-k8s-uninstall
data-platform-k8s-uninstall: mysql-k8s-uninstall backend-k8s-uninstall frontend-k8s-uninstall
