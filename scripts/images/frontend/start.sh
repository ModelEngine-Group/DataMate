#!/bin/bash

set -e

if [ -f "/etc/nginx/cert/ca.crt" ]; then
    cp /opt/frontend/https_backend.conf /etc/nginx/conf.d/default.conf
    cp /opt/frontend/routes.inc /etc/nginx/conf.d/routes.inc
    echo "Switching to HTTPS config"
else
    cp /opt/frontend/http_backend.conf /etc/nginx/conf.d/default.conf
    cp /opt/frontend/routes.inc /etc/nginx/conf.d/routes.inc
    echo "Switching to HTTP config"
fi

exec nginx -g "daemon off;"
