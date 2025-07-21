.PHONY: build-mineru build-datax build-data-juicer build-unstructured install-datax install-ray install-unstructured \
	install-data-juicer

build-mineru:
	sh build/mineru/build.sh

build-datax:
	sh build/datax/build.sh

build-data-juicer:
	sh build/data-juicer/build.sh

build-unstructured:
	sh build/unstructured/build.sh

build-backend:
	sh build/backend/build.sh

build-frontend:
	sh build/frontend/build.sh

install-mineru:
	kubectl apply -f install/kubernetes/mineru/deploy.yaml

install-datax:
	kubectl apply -f install/kubernetes/datax/deploy.yaml

install-data-juicer:
	sh install/helm/data-juicer/install.sh

install-ray:
	sh install/helm/ray/install.sh

install-unstructured:
	kubectl apply -f install/kubernetes/unstructured/deploy.yaml

install-mysql:
	kubectl apply -f install/kubernetes/mysql/deploy.yaml

install-backend:
	kubectl apply -f install/kubernetes/backend/deploy.yaml

install-frontend:
	kubectl apply -f install/kubernetes/frontend/deploy.yaml
