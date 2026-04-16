ARG NODE_IMAGE=node:22-alpine
ARG NGINX_IMAGE=nginx:1.27-alpine

FROM ${NODE_IMAGE} AS build

WORKDIR /app

RUN corepack enable

COPY apps/web/package.json /app/package.json
COPY apps/web/pnpm-lock.yaml /app/pnpm-lock.yaml

RUN pnpm install --frozen-lockfile

COPY apps/web /app

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_USER_ID=00000000-0000-0000-0000-000000000001
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_USER_ID=${VITE_USER_ID}

RUN pnpm run build

FROM ${NGINX_IMAGE}

COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
