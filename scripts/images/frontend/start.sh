#!/bin/bash

if [ -f "/cert/server.pem" ]; then
    cp /cert/server.pem /etc/nginx/cert/server.pem
    chown nginx:nginx /etc/nginx/cert/server.pem
fi

if [ -f "/cert/server.key" ]; then
  if openssl rsa -in /cert/server.key -passin pass:test_check -noout 2>/dev/null; then
    cp /cert/server.key /etc/nginx/cert/server.key
  else
    echo "$CERT_PASS" | openssl rsa -in /cert/server.key -out /etc/nginx/cert/server.key -passin stdin
  fi
  chown nginx:nginx /etc/nginx/cert/server.key
fi

if [ -f "/etc/nginx/cert/server.pem" ]; then
    cp /opt/frontend/https_backend.conf /etc/nginx/conf.d/default.conf
    cp /opt/frontend/routes.inc /etc/nginx/conf.d/routes.inc
    echo "Switching to HTTPS config"
else
    cp /opt/frontend/http_backend.conf /etc/nginx/conf.d/default.conf
    cp /opt/frontend/routes.inc /etc/nginx/conf.d/routes.inc
    echo "Switching to HTTP config"
fi

exec nginx -g "daemon off;"
