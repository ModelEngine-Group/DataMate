#!/bin/bash

if [ -f "/cert/server.pem" ]; then
    cp /cert/server.pem /etc/nginx/cert/server.pem
    chown nginx:nginx /etc/nginx/cert/server.pem
fi

if [ -f "/cert/server.key" ]; then
    # Check if key is encrypted and decrypt if needed
    # Supports RSA, EC (Elliptic Curve), PKCS#8, and DSA keys
    if grep -q "ENCRYPTED" /cert/server.key 2>/dev/null; then
        # Key is encrypted, decrypt using generic pkey command (supports all key types)
        echo "$CERT_PASS" | openssl pkey -in /cert/server.key -out /etc/nginx/cert/server.key -passin stdin
    else
        # Key is not encrypted, copy directly
        cp /cert/server.key /etc/nginx/cert/server.key
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

    if [ -n "$DOMAIN" ]; then
      cron
      certbot --nginx "-d ${DOMAIN//,/ -d }"
      echo "Switching to HTTPS config, Domain: $DOMAIN"
      echo "0 0 1 * * root /usr/local/bin/certbot renew --quiet" | tee /etc/cron.d/certbot-renew
      chmod 0644 /etc/cron.d/certbot-renew
    else
      echo "Switching to HTTP config"
    fi
fi

exec nginx -g "daemon off;"
