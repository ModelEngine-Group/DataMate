#!/bin/bash

# install kuberay
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update
# Install both CRDs and KubeRay operator v1.4.0.
helm install kuberay-operator kuberay/kuberay-operator --version 1.4.0

# install raycluster
helm install raycluster deployment/helm/ray/ray-cluster/