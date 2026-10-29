# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS ui
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --strict-ssl=true --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Bundle the small desk sources separately so a VFS builder does not duplicate
# the complete Python runtime once for each source directory.
FROM scratch AS desk_assets
COPY backend/ /backend/
COPY scripts/ /scripts/
COPY strategies/ /strategies/
COPY run.sh /run.sh
COPY --from=ui /build/frontend/dist /frontend/dist/

# Node's native dependencies and Python use the same Debian release. The
# Tensor adapter invokes Node directly and needs no npm packages at runtime.
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 ASTER_DB_PATH=/data/aster.sqlite
WORKDIR /app
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then \
        apt-get -o Acquire::https::CaInfo=/run/secrets/ca_bundle update; \
    else apt-get update; fi \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ui /usr/local/bin/node /usr/local/bin/node
COPY requirements.txt requirements-lock.txt ./
RUN --mount=type=secret,id=ca_bundle \
    set -eu; \
    node --version; \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle; fi; \
    pip install --no-cache-dir -r requirements-lock.txt \
    && mkdir -p /data
COPY --from=desk_assets / ./
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 CMD /bin/sh /app/scripts/aster_healthcheck.sh || exit 1
ENTRYPOINT ["/bin/sh", "/app/scripts/aster_container_entrypoint.sh"]
CMD ["--", "python", "/app/scripts/aster_services.py", "--container-mode"]
