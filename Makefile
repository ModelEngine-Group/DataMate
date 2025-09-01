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
install: install-edatamate

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

.PHONY: mineru-docker-build
mineru-docker-build:
	sh scripts/image/mineru/build.sh

.PHONY: datax-docker-build
datax-docker-build:
	sh scripts/image/datax/build.sh

.PHONY: data-juicer-docker-build
data-juicer-docker-build:
	sh scripts/image/data-juicer/build.sh

.PHONY: unstructured-docker-build
unstructured-docker-build:
	sh scripts/image/unstructured/build.sh

.PHONY: backend-docker-build
backend-docker-build:
	sh scripts/image/backend/build.sh

.PHONY: frontend-docker-build
frontend-docker-build:
	sh scripts/image/frontend/build.sh

.PHONY: mineru-k8s-install
mineru-k8s-install:
	kubectl apply -f deployment/kubernetes/mineru/deploy.yaml

.PHONY: datax-k8s-install
datax-k8s-install:
	kubectl apply -f deployment/kubernetes/datax/deploy.yaml

.PHONY: datax-k8s-uninstall
datax-k8s-uninstall:
	kubectl delete -f deployment/kubernetes/datax/deploy.yaml

.PHONY: datax-docker-install
datax-docker-install:
	cd deployment/docker/data-platform && docker-compose up -d datax

.PHONY: datax-docker-uninstall
datax-docker-uninstall:
	cd deployment/docker/data-platform && docker-compose down datax

.PHONY: data-juicer-helm-install
data-juicer-helm-install:
	sh deployment/helm/data-juicer/install.sh

.PHONY: ray-helm-install
ray-helm-install:
	sh deployment/helm/ray/install.sh

.PHONY: es-helm-install
es-helm-install:
	sh deployment/helm/es/install.sh

.PHONY: unstructured-k8s-install
unstructured-k8s-install:
	kubectl apply -f deployment/kubernetes/unstructured/deploy.yaml

.PHONY: mysql-k8s-install
mysql-k8s-install:
	kubectl apply -f deployment/kubernetes/mysql/deploy.yaml

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

.PHONY: pgsql-k8s-install
pgsql-k8s-install:
	kubectl apply -f deployment/kubernetes/postgresql/deploy.yaml

.PHONY: pgsql-k8s-uninstall
pgsql-k8s-uninstall:
	kubectl delete -f deployment/kubernetes/postgresql/deploy.yaml

.PHONY: edatamate-docker-install
edatamate-docker-install:
	cd deployment/docker/data-platform && docker-compose up -d

.PHONY: edatamate-docker-uninstall
edatamate-docker-uninstall:
	cd deployment/docker/data-platform && docker-compose down

.PHONY: edatamate-k8s-install
edatamate-k8s-install: pgsql-k8s-install backend-k8s-install frontend-k8s-install datax-k8s-install

.PHONY: edatamate-k8s-uninstall
edatamate-k8s-uninstall: pgsql-k8s-uninstall backend-k8s-uninstall frontend-k8s-uninstall datax-k8s-uninstall
