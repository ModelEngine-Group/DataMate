FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend ./

RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi && \
    npm run build

FROM nginx:1.29 AS runner

COPY --from=builder /app/dist /opt/frontend
COPY deployment/docker/datamate/backend.conf /etc/nginx/conf.d/backend.conf

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && rm -f /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
