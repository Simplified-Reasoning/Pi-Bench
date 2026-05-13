#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
DATA_DIR="${REPO_ROOT}/data"
CACHE_DIR="${REPO_ROOT}/.cache/appworld/data"

is_valid_data_dir() {
    local dir="$1"
    [[ -d "${dir}" ]] &&
        [[ -d "${dir}/api_docs" ]] &&
        [[ -d "${dir}/base_dbs" ]] &&
        [[ -d "${dir}/datasets" ]] &&
        [[ -d "${dir}/tasks" ]] &&
        [[ -f "${dir}/version.txt" ]]
}

echo "[refresh] repo root: ${REPO_ROOT}"
echo "[refresh] data dir: ${DATA_DIR}"
echo "[refresh] cache dir: ${CACHE_DIR}"

if is_valid_data_dir "${CACHE_DIR}"; then
    echo "[refresh] cache hit, restoring data from local cache."
    rm -rf "${DATA_DIR}"
    cp -a "${CACHE_DIR}" "${DATA_DIR}"
    echo "[refresh] done: restored ${DATA_DIR} from cache."
    exit 0
fi

echo "[refresh] cache miss (or cache incomplete), downloading data."
if ! command -v appworld >/dev/null 2>&1; then
    echo "[refresh] error: 'appworld' command not found in PATH." >&2
    exit 1
fi

rm -rf "${DATA_DIR}"
appworld download data --root "${REPO_ROOT}"

if ! is_valid_data_dir "${DATA_DIR}"; then
    echo "[refresh] error: downloaded data directory is incomplete: ${DATA_DIR}" >&2
    exit 1
fi

echo "[refresh] updating local cache."
rm -rf "${CACHE_DIR}"
mkdir -p "$(dirname "${CACHE_DIR}")"
cp -a "${DATA_DIR}" "${CACHE_DIR}"
echo "[refresh] done: cache refreshed at ${CACHE_DIR}."
