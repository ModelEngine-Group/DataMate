FROM node:18-alpine AS builder

WORKDIR /app

COPY frontend ./

RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi && \
    npm run build

FROM nginx:1.29 AS runner

COPY --from=builder /app/dist /opt/frontend
COPY scripts/images/frontend/backend.conf /etc/nginx/conf.d/default.conf

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

CMD ["nginx", "-g", "daemon off;"]
