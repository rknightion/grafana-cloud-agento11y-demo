# syntax=docker/dockerfile:1
# Build context: apps/. One image serves the five HTTP roles, loadgen and experiments.
FROM node:24-alpine AS deps
WORKDIR /app/regulatory
COPY regulatory/package.json regulatory/package-lock.json ./
# The optional Strands peer is not used by this app.
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund --legacy-peer-deps \
 && find node_modules -type f \( -name '*.map' -o -name '*.d.ts' -o -name '*.d.mts' -o -name '*.d.cts' \) -delete \
 && npm cache clean --force

FROM node:24-alpine
ENV NODE_ENV=production PORT=8080
WORKDIR /app/regulatory
COPY --from=deps /app/regulatory/node_modules ./node_modules
COPY regulatory/package.json ./
COPY regulatory/src ./src
COPY regulatory/config ./config
COPY regulatory/corpus ./corpus
COPY regulatory/experiments ./experiments
# Runtime uses node directly, so do not ship npm's unused dependency tree.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack
USER 10001:10001
EXPOSE 8080
CMD ["node", "--experimental-loader=@opentelemetry/instrumentation/hook.mjs", "--import", "./src/instrumentation.mjs", "src/server.mjs"]
