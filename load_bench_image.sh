#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_PATH="${1:-/tmp/localhost-bench.tar.gz}"
EXPECTED_IMAGE="localhost/bench:v1"
LEGACY_IMAGE="localhost/bench:v1"

if [[ ! -f "${ARCHIVE_PATH}" ]]; then
  cat <<EOF
Bench image archive not found: ${ARCHIVE_PATH}

Download or copy the image archive to:
  /tmp/localhost-bench.tar.gz

Then rerun:
  bash load_bench_image.sh
EOF
  exit 1
fi

CONTAINER_CLI=""
if command -v podman >/dev/null 2>&1; then
  CONTAINER_CLI="podman"
elif command -v docker >/dev/null 2>&1; then
  CONTAINER_CLI="docker"
else
  echo "[load] neither podman nor docker command found"
  exit 1
fi

bash "${SCRIPT_DIR}/scripts/load_image.sh" \
  --archive "${ARCHIVE_PATH}" \
  --expected-image "${LEGACY_IMAGE}" \
  --skip-checksum

if "${CONTAINER_CLI}" image inspect "${EXPECTED_IMAGE}" >/dev/null 2>&1; then
  echo "[load] image ready: ${EXPECTED_IMAGE}"
  exit 0
fi

if "${CONTAINER_CLI}" image inspect "${LEGACY_IMAGE}" >/dev/null 2>&1; then
  echo "[load] retagging ${LEGACY_IMAGE} -> ${EXPECTED_IMAGE}"
  "${CONTAINER_CLI}" tag "${LEGACY_IMAGE}" "${EXPECTED_IMAGE}"
fi

if "${CONTAINER_CLI}" image inspect "${EXPECTED_IMAGE}" >/dev/null 2>&1; then
  echo "[load] image ready: ${EXPECTED_IMAGE}"
else
  echo "[load] expected image tag not found after retag: ${EXPECTED_IMAGE}"
  echo "[load] check loaded tags with:"
  echo "  ${CONTAINER_CLI} images"
  exit 1
fi
