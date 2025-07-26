#!/bin/bash

helm repo add elastic https://helm.elastic.co
helm repo update elastic

helm install elastic-operator elastic/eck-operator -n elastic-system --create-namespace
helm install es-kb elastic/eck-stack \
    --set eck-kibana.http.service.spec.type=NodePort \
    --set eck-kibana.config.i18n.locale=zh-CN