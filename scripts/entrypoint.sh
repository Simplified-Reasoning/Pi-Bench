#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID}"
MODEL_CONFIG_PATH="${MODEL_CONFIG_PATH}"
ENABLE_APPWORLD="$(echo "${ENABLE_APPWORLD:-true}" | tr '[:upper:]' '[:lower:]')"
BENCH_USER_ID="${BENCH_USER_ID}"
BENCH_TASK_IDS="${BENCH_TASK_IDS:-}"
BENCH_WORKDIR="${BENCH_WORKDIR:-/opt/proactive}"
BENCH_CONFIG_PATH="${BENCH_CONFIG_PATH:-/tmp/pibench.runtime.yaml}"
BENCH_HISTORY_CONFIG_PATH="${BENCH_HISTORY_CONFIG_PATH:-/opt/proactive/config/bench/evaluation/trace_history.yaml}"
BENCH_TEST_SERVER_SCRIPT="${BENCH_TEST_SERVER_SCRIPT:-/opt/proactive/scripts/test_server.py}"
APPWORLD_MCP_APP_NAMES_RAW="${APPWORLD_MCP_APP_NAMES:-}"

APPWORLD_API_PORT="9000"
APPWORLD_MCP_PORT="10000"
BENCH_TEST_SERVER_PORT="9999"
APPWORLD_ROOT="${APPWORLD_ROOT:-/opt/proactive/appworld}"
APPWORLD_USER_TOOLS_CONFIG_FILE="/opt/proactive/data/${BENCH_USER_ID}/tools.yaml"
APPWORLD_DEFAULT_TOOLS_CONFIG_FILE="/opt/proactive/config/appworld/tools.yaml"

NANOBOT_HOME="/root/.nanobot"
NANOBOT_WORKSPACE_DIR="${NANOBOT_HOME}/workspace"
NANOBOT_TRACE_LOGS_DIR="${NANOBOT_HOME}/trace_logs"
NANOBOT_CONFIG_PATH="${NANOBOT_HOME}/config.json"

APPWORLD_API_URL="http://127.0.0.1:${APPWORLD_API_PORT}"
APPWORLD_MCP_URL="http://127.0.0.1:${APPWORLD_MCP_PORT}/mcp"
BENCH_TEST_SERVER_URL="http://127.0.0.1:${BENCH_TEST_SERVER_PORT}"

LOG_DIR="${NANOBOT_HOME}/logs"
mkdir -p "${NANOBOT_HOME}" "${NANOBOT_WORKSPACE_DIR}" "${NANOBOT_TRACE_LOGS_DIR}" "${LOG_DIR}"

pids=()

cleanup() {
  local code=$?
  trap - EXIT INT TERM
  for pid in "${pids[@]:-}"; do
    kill "${pid}" 2>/dev/null || true
  done
  wait || true
  exit "${code}"
}
trap cleanup EXIT INT TERM

start_bg() {
  local name="$1"
  shift
  local logfile="${LOG_DIR}/${name}.log"
  "$@" >"${logfile}" 2>&1 &
  local pid=$!
  pids+=("${pid}")
  echo "[entrypoint] started ${name} pid=${pid} log=${logfile}"
}

normalize_csv_list() {
  local raw="${1:-}"
  local token=""
  local joined=""
  local -a parts=()
  local -a cleaned=()
  local idx=0

  IFS=',' read -r -a parts <<< "${raw}"
  for token in "${parts[@]}"; do
    token="$(echo "${token}" | xargs)"
    if [[ -n "${token}" ]]; then
      cleaned+=("${token}")
    fi
  done

  if [[ "${#cleaned[@]}" -eq 0 ]]; then
    printf '%s' ""
    return 0
  fi

  joined="${cleaned[0]}"
  for ((idx = 1; idx < ${#cleaned[@]}; idx++)); do
    joined+=",${cleaned[$idx]}"
  done
  printf '%s' "${joined}"
}

resolve_appworld_tools_config_file() {
  if [[ -f "${APPWORLD_USER_TOOLS_CONFIG_FILE}" ]]; then
    printf '%s' "${APPWORLD_USER_TOOLS_CONFIG_FILE}"
    return 0
  fi
  if [[ -f "${APPWORLD_DEFAULT_TOOLS_CONFIG_FILE}" ]]; then
    printf '%s' "${APPWORLD_DEFAULT_TOOLS_CONFIG_FILE}"
    return 0
  fi
  printf '%s' "${APPWORLD_USER_TOOLS_CONFIG_FILE}"
}

wait_port() {
  local host="$1"
  local port="$2"
  local timeout_sec="$3"
  python - "$host" "$port" "$timeout_sec" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
timeout_sec = float(sys.argv[3])
deadline = time.time() + timeout_sec
last_err = None
while time.time() < deadline:
    s = socket.socket()
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        sys.exit(0)
    except Exception as exc:
        last_err = exc
        time.sleep(0.5)
    finally:
        try:
            s.close()
        except Exception:
            pass
print(f"timeout waiting for {host}:{port} ({last_err})", file=sys.stderr)
sys.exit(1)
PY
}

sanitize_model() {
  printf '%s' "${1//\//_}"
}

read_nanobot_runtime_model() {
  local config_path="${NANOBOT_CONFIG_PATH}"
  if [[ ! -f "${config_path}" ]]; then
    echo "[entrypoint] nanobot runtime config not found: ${config_path}"
    exit 1
  fi

  NANOBOT_CONFIG_PATH="${config_path}" python - <<'PY'
import json
import os
import sys
from pathlib import Path

config_path = Path(os.environ["NANOBOT_CONFIG_PATH"])
cfg = json.loads(config_path.read_text(encoding="utf-8"))
model = (((cfg.get("agents") or {}).get("defaults") or {}).get("model") or "").strip()
if not model:
    raise SystemExit(f"[entrypoint] missing agents.defaults.model in {config_path}")
sys.stdout.write(model)
PY
}

normalize_trace_log_model_dir_for_eval() {
  local runtime_model
  runtime_model="$(read_nanobot_runtime_model)"

  local source_safe_model
  local target_safe_model
  source_safe_model="$(sanitize_model "${runtime_model}")"
  target_safe_model="$(sanitize_model "${MODEL_ID}")"

  local source_dir="${NANOBOT_TRACE_LOGS_DIR}/${source_safe_model}"
  local target_dir="${NANOBOT_TRACE_LOGS_DIR}/${target_safe_model}"

  if [[ "${source_safe_model}" == "${target_safe_model}" ]]; then
    echo "[entrypoint] trace log model dir already aligned model=${MODEL_ID} trace_dir=${target_dir}"
    return 0
  fi

  echo "[entrypoint] normalizing trace log model dir runtime_model=${runtime_model} target_model=${MODEL_ID}"
  if [[ ! -d "${source_dir}" ]]; then
    echo "[entrypoint] expected trace log source directory not found after run: ${source_dir}"
    exit 1
  fi
  if [[ -e "${target_dir}" ]]; then
    echo "[entrypoint] target trace log directory already exists; refusing to merge source=${source_dir} target=${target_dir}"
    exit 1
  fi
  mv "${source_dir}" "${target_dir}"
  echo "[entrypoint] normalized trace logs source=${source_dir} target=${target_dir}"
}

prepare_runtime_configs() {
  if [[ ! -f "${MODEL_CONFIG_PATH}" ]]; then
    echo "[entrypoint] model config not found: ${MODEL_CONFIG_PATH}"
    exit 1
  fi

  local appworld_arg="--enable-appworld"
  if [[ "${ENABLE_APPWORLD}" != "true" ]]; then
    appworld_arg="--no-enable-appworld"
  fi

  python -m src.main prepare-runtime \
    --model-config "${MODEL_CONFIG_PATH}" \
    --bench-config-output "${BENCH_CONFIG_PATH}" \
    --nanobot-config-output "${NANOBOT_CONFIG_PATH}" \
    --model-id "${MODEL_ID}" \
    --user-id "${BENCH_USER_ID}" \
    --trace-logs-dir "${NANOBOT_TRACE_LOGS_DIR}" \
    --workspace-dir "${NANOBOT_WORKSPACE_DIR}" \
    --history-config-path "${BENCH_HISTORY_CONFIG_PATH}" \
    --test-server-url "${BENCH_TEST_SERVER_URL}" \
    --appworld-mcp-url "${APPWORLD_MCP_URL}" \
    "${appworld_arg}"
}

run_bench() {
  local -a task_id_args=()
  local -a task_ids=()
  local task_id=""
  if [[ -n "${BENCH_TASK_IDS}" ]]; then
    IFS=',' read -r -a task_ids <<< "${BENCH_TASK_IDS}"
    for task_id in "${task_ids[@]}"; do
      task_id="$(echo "${task_id}" | xargs)"
      if [[ -n "${task_id}" ]]; then
        task_id_args+=(--task-id "${task_id}")
      fi
    done
  fi

  local -a run_cmd=(
    python -m src.main
    --config "${BENCH_CONFIG_PATH}"
    --mode run
    --model-id "${MODEL_ID}"
    --user-id "${BENCH_USER_ID}"
    --trace-logs-dir "${NANOBOT_TRACE_LOGS_DIR}"
    --workspace-dir "${NANOBOT_WORKSPACE_DIR}"
  )
  run_cmd+=("${task_id_args[@]}")

  echo "[entrypoint] run command: ${run_cmd[*]}"
  "${run_cmd[@]}"
  normalize_trace_log_model_dir_for_eval

  local -a eval_cmd=(
    python -m src.main
    --config "${BENCH_CONFIG_PATH}"
    --mode eval
    --model-id "${MODEL_ID}"
    --user-id "${BENCH_USER_ID}"
    --trace-logs-dir "${NANOBOT_TRACE_LOGS_DIR}"
    --workspace-dir "${NANOBOT_WORKSPACE_DIR}"
  )
  eval_cmd+=("${task_id_args[@]}")

  echo "[entrypoint] eval command: ${eval_cmd[*]}"
  "${eval_cmd[@]}"
}

main() {
  if [[ ! -d "${BENCH_WORKDIR}" ]]; then
    echo "[entrypoint] bench workdir not found: ${BENCH_WORKDIR}"
    exit 1
  fi
  cd "${BENCH_WORKDIR}"

  local appworld_mcp_app_names
  appworld_mcp_app_names="$(normalize_csv_list "${APPWORLD_MCP_APP_NAMES_RAW}")"
  local appworld_tools_config_file
  appworld_tools_config_file="$(resolve_appworld_tools_config_file)"
  local appworld_mcp_apps_display="all"
  local selected_tools_config_file=""
  if [[ -n "${appworld_mcp_app_names}" ]]; then
    appworld_mcp_apps_display="${appworld_mcp_app_names}"
  else
    selected_tools_config_file="${appworld_tools_config_file}"
  fi

  echo "[entrypoint] model=${MODEL_ID} user=${BENCH_USER_ID} enable_appworld=${ENABLE_APPWORLD} model_config=${MODEL_CONFIG_PATH}"
  echo "[entrypoint] appworld_mcp_app_names=${appworld_mcp_apps_display} appworld_tools_config_file=${selected_tools_config_file}"

  export BENCH_TEST_SERVER_URL APPWORLD_ROOT
  prepare_runtime_configs

  if [[ "${ENABLE_APPWORLD}" == "true" ]]; then
    if [[ -n "${selected_tools_config_file}" && ! -f "${selected_tools_config_file}" ]]; then
      echo "[entrypoint] missing appworld tools config: ${selected_tools_config_file}"
      exit 1
    fi
    start_bg appworld_apis appworld serve apis --root "${APPWORLD_ROOT}" --port "${APPWORLD_API_PORT}"
    wait_port 127.0.0.1 "${APPWORLD_API_PORT}" 120

    local -a mcp_cmd=(
      appworld serve mcp http
      --root "${APPWORLD_ROOT}"
      --remote-apis-url "${APPWORLD_API_URL}"
      --port "${APPWORLD_MCP_PORT}"
    )
    if [[ -n "${selected_tools_config_file}" ]]; then
      mcp_cmd+=(--tools-config-file "${selected_tools_config_file}")
    fi
    if [[ -n "${appworld_mcp_app_names}" ]]; then
      mcp_cmd+=(--app-names "${appworld_mcp_app_names}")
    fi
    echo "[entrypoint] appworld mcp command: ${mcp_cmd[*]}"
    start_bg appworld_mcp "${mcp_cmd[@]}"
    wait_port 127.0.0.1 "${APPWORLD_MCP_PORT}" 120
  else
    echo "[entrypoint] appworld disabled by ENABLE_APPWORLD=${ENABLE_APPWORLD}"
  fi

  start_bg test_server env PORT="${BENCH_TEST_SERVER_PORT}" python "${BENCH_TEST_SERVER_SCRIPT}"
  wait_port 127.0.0.1 "${BENCH_TEST_SERVER_PORT}" 60

  start_bg nanobot_gateway nanobot gateway
  sleep 5

  local bench_log_file="${LOG_DIR}/bench.log"
  echo "[entrypoint] writing bench log to ${bench_log_file}"
  run_bench >"${bench_log_file}" 2>&1

  echo "[entrypoint] completed model=${MODEL_ID}"
}

main
