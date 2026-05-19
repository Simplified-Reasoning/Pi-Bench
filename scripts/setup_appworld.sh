#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APPWORLD_DIR="${REPO_ROOT}/third_party/appworld"

if [[ ! -d "${APPWORLD_DIR}" ]]; then
  echo "[setup-appworld] AppWorld source not found: ${APPWORLD_DIR}"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "[setup-appworld] python command not found"
  exit 1
fi

python - <<'PY'
import sys

if sys.version_info < (3, 11):
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"[setup-appworld] Python >= 3.11 is required, found {version}")
PY

echo "[setup-appworld] installing local AppWorld"
python -m pip install -e "${APPWORLD_DIR}"

echo "[setup-appworld] unpacking AppWorld repo assets"
(
  cd "${APPWORLD_DIR}"
  python -m appworld.cli install --repo
)

echo "[setup-appworld] downloading AppWorld data"
(
  cd "${APPWORLD_DIR}"
  python -m appworld.cli download data --root .
)

echo "[setup-appworld] done"
