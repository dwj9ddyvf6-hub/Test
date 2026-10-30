#!/usr/bin/env bash
# Additive backup of STATE (never secrets) to a private git remote. Never force-pushes.
# Retries with backoff and bounded steps: a single transient 403/TLS error must not lose a backup.
set -eu
cd "${BACKUP_CLONE:?path to a clone of your PRIVATE backup repo}"
git config pull.ff only
for i in 1 2 3; do
  timeout 40 git fetch origin state-backup && break || sleep $((5 * i))
done
git checkout -q state-backup
cp "${STATE_DIR:?}/ledger.jsonl.gz" . ; sha256sum ledger.jsonl.gz > MANIFEST.sha256
# secret scan BEFORE committing: refuse if anything looks like a key
if grep -rEq '(AKIA|sk-[A-Za-z0-9]{20,}|BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|[A-Z0-9]{20,}:[A-Za-z0-9_-]{30,})' .; then
  echo "secret-like content found; refusing to push" >&2; exit 2; fi
git add -A && git commit -qm "state backup $(date -u +%FT%TZ)" || exit 0
for i in 1 2 3; do timeout 60 git push origin state-backup && exit 0 || sleep $((5 * i)); done   # plain push, never --force
exit 1
