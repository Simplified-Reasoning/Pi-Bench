#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_PATH=""
EXPECTED_IMAGE="localhost/bench:v1"
SKIP_CHECKSUM="false"

usage() {
  cat <<EOF
Usage:
  $(basename "$0") --archive <image-archive.tar.gz> [--expected-image <image>] [--skip-checksum]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive)
      if [[ $# -lt 2 ]]; then
        echo "[load] --archive requires a value"
        usage
        exit 1
      fi
      ARCHIVE_PATH="$2"
      shift 2
      ;;
    --expected-image)
      if [[ $# -lt 2 ]]; then
        echo "[load] --expected-image requires a value"
        usage
        exit 1
      fi
      EXPECTED_IMAGE="$2"
      shift 2
      ;;
    --skip-checksum)
      SKIP_CHECKSUM="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "[load] unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${ARCHIVE_PATH}" ]]; then
  echo "[load] --archive is required"
  usage
  exit 1
fi

if [[ ! -f "${ARCHIVE_PATH}" ]]; then
  echo "[load] image archive not found: ${ARCHIVE_PATH}"
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

if [[ "${SKIP_CHECKSUM}" != "true" ]]; then
  checksum_file="${ARCHIVE_PATH}.sha256"
  if [[ -f "${checksum_file}" ]]; then
    checksum_dir="$(cd "$(dirname "${checksum_file}")" && pwd)"
    checksum_name="$(basename "${checksum_file}")"
    (cd "${checksum_dir}" && shasum -a 256 -c "${checksum_name}")
  else
    echo "[load] checksum file not found: ${checksum_file}"
    echo "[load] pass --skip-checksum to load without checksum validation"
    exit 1
  fi
fi

echo "[load] loading archive with ${CONTAINER_CLI}: ${ARCHIVE_PATH}"
"${CONTAINER_CLI}" load -i "${ARCHIVE_PATH}"

if "${CONTAINER_CLI}" image inspect "${EXPECTED_IMAGE}" >/dev/null 2>&1; then
  echo "[load] image ready: ${EXPECTED_IMAGE}"
else
  echo "[load] expected image tag not found after load: ${EXPECTED_IMAGE}"
  echo "[load] check loaded tags with:"
  echo "  ${CONTAINER_CLI} images"
  exit 1
fi
