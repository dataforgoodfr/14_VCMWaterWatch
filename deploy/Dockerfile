FROM python:3.12-slim AS pmtiles
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

# Install system dependencies for GDAL (required by pyogrio/geopandas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY pipelines ./pipelines
ARG NOCODB_BASE_ID
ARG NOCODB_URL
ARG NOCODB_TOKEN
ENV NOCODB_BASE_ID=${NOCODB_BASE_ID}
ENV NOCODB_URL=${NOCODB_URL}
ENV NOCODB_TOKEN=${NOCODB_TOKEN}
RUN uv run python -m pipelines.export.export_pmtiles

FROM node:24-alpine AS base

FROM base AS deps
WORKDIR /app
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY webapp/ .
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=pmtiles /app/data/export ./public/pmtiles
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
