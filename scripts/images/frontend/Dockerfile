FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend ./

RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi && \
    npm run build

FROM nginx:1.29 AS runner

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update \
    && apt install -y dos2unix

COPY --from=builder /app/dist /opt/frontend/statics
COPY scripts/images/frontend/routes.inc /opt/frontend/routes.inc
COPY scripts/images/frontend/http_backend.conf /opt/frontend/http_backend.conf
COPY scripts/images/frontend/https_backend.conf /opt/frontend/https_backend.conf

COPY scripts/images/frontend/start.sh /opt/frontend/start.sh

RUN dos2unix /opt/frontend/start.sh \
    && chmod +x /opt/frontend/start.sh \
    && mkdir -p /etc/nginx/cert \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && rm -f /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["/opt/frontend/start.sh"]
