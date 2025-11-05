##### DEPENDENCIES

FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat openssl git
WORKDIR /app

RUN git clone https://github.com/bytedance/deer-flow.git /deer-flow \
    && mv /deer-flow/web/* /app \
    && rm -rf /deer-flow
# Install dependencies based on the preferred package manager

RUN if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then npm install -g pnpm && pnpm i; \
    else echo "Lockfile not found." && exit 1; \
    fi

##### BUILDER

FROM node:20-alpine AS builder

RUN apk add --no-cache git

WORKDIR /app
ARG NEXT_PUBLIC_API_URL="/deer-flow-backend"

RUN git clone https://github.com/bytedance/deer-flow.git /deer-flow

COPY runtime/deer-flow/feature_collection.patch /deer-flow/feature_collection.patch

RUN cd /deer-flow \
    && git apply feature_collection.patch \
    && mv /deer-flow/web/* /app \
    && rm -rf /deer-flow

COPY --from=deps /app/node_modules ./node_modules

ENV NEXT_TELEMETRY_DISABLED=1

RUN if [ -f yarn.lock ]; then SKIP_ENV_VALIDATION=1 yarn build; \
    elif [ -f package-lock.json ]; then SKIP_ENV_VALIDATION=1 npm run build; \
    elif [ -f pnpm-lock.yaml ]; then npm install -g pnpm && SKIP_ENV_VALIDATION=1 pnpm run build; \
    else echo "Lockfile not found." && exit 1; \
    fi

##### RUNNER

FROM gcr.io/distroless/nodejs20-debian12 AS runner
WORKDIR /app

ENV NODE_ENV=production

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000

CMD ["server.js"]
