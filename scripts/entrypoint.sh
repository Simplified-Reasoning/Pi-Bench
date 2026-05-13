#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID}"
NANOBOT_MODEL="${NANOBOT_MODEL}"
ENABLE_APPWORLD="$(echo "${ENABLE_APPWORLD:-true}" | tr '[:upper:]' '[:lower:]')"
APPWORLD_MCP_APP_NAMES_RAW="${APPWORLD_MCP_APP_NAMES:-}"
APPWORLD_MCP_APP_NAMES=""

BENCH_WORKDIR="${BENCH_WORKDIR:-/opt/proactive}"
BENCH_CONFIG_SOURCE_PATH="${BENCH_CONFIG_SOURCE_PATH:-/opt/proactive/config/bench/nanobot.yaml}"
BENCH_CONFIG_PATH="${BENCH_CONFIG_PATH:-/tmp/nanobot.runtime.yaml}"
BENCH_HISTORY_CONFIG_PATH="${BENCH_HISTORY_CONFIG_PATH:-/opt/proactive/config/bench/evaluation/trace_history.yaml}"
BENCH_TEST_SERVER_SCRIPT="${BENCH_TEST_SERVER_SCRIPT:-/opt/proactive/scripts/test_server.py}"
BENCH_USER_ID="${BENCH_USER_ID}"
BENCH_TASK_IDS="${BENCH_TASK_IDS:-}"

APPWORLD_API_PORT="9000"
APPWORLD_MCP_PORT="10000"
BENCH_TEST_SERVER_PORT="9999"
APPWORLD_ROOT="${APPWORLD_ROOT:-/opt/proactive/appworld}"
APPWORLD_USER_TOOLS_CONFIG_FILE="/opt/proactive/data/${BENCH_USER_ID}/tools.yaml"
APPWORLD_DEFAULT_TOOLS_CONFIG_FILE="/opt/proactive/config/appworld/tools.yaml"
APPWORLD_TOOLS_CONFIG_FILE=""

NANOBOT_HOME="/root/.nanobot"
NANOBOT_WORKSPACE_DIR="${NANOBOT_HOME}/workspace"
NANOBOT_TRACE_LOGS_DIR="${NANOBOT_HOME}/trace_logs"
NANOBOT_CONFIGS_DIR="${NANOBOT_CONFIGS_DIR:-/opt/proactive/config/nanobot/models}"
NANOBOT_PROVIDER_API_BASE="${NANOBOT_PROVIDER_API_BASE}"
NANOBOT_PROVIDER_API_KEY="${NANOBOT_PROVIDER_API_KEY}"
NANOBOT_BRAVE_SEARCH_API_KEY="${NANOBOT_BRAVE_SEARCH_API_KEY:-}"
BENCH_LLM_BASE_URL="${BENCH_LLM_BASE_URL:-${NANOBOT_PROVIDER_API_BASE}}"

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

print_nanobot_provider_api_base_summary() {
  local runtime_config_path="${NANOBOT_HOME}/config.json"
  local safe_model
  safe_model="$(sanitize_model "${NANOBOT_MODEL}")"
  local model_config_path="${NANOBOT_CONFIGS_DIR}/${safe_model}/config.json"
  local provider_api_base_source="model_config"
  if [[ -n "${NANOBOT_PROVIDER_API_BASE}" ]]; then
    provider_api_base_source="env_override"
  fi

  NANOBOT_CONFIG_PATH="${runtime_config_path}" \
  MODEL_CONFIG_PATH="${model_config_path}" \
  PROVIDER_API_BASE_SOURCE="${provider_api_base_source}" \
  python - <<'PY'
import json
import os
from pathlib import Path

runtime_config_path = Path(os.environ["NANOBOT_CONFIG_PATH"])
model_config_path = Path(os.environ["MODEL_CONFIG_PATH"])
provider_api_base_source = os.environ["PROVIDER_API_BASE_SOURCE"]

cfg = json.loads(runtime_config_path.read_text(encoding="utf-8"))
provider_api_base = str(
    (((cfg.get("providers") or {}).get("custom") or {}).get("apiBase") or "")
).strip()
provider_api_base_display = provider_api_base or "<empty>"

print(
    "[entrypoint] resolved nanobot provider api base "
    f"source={provider_api_base_source} "
    f"value={provider_api_base_display} "
    f"model_config={model_config_path} "
    f"runtime_config={runtime_config_path}"
)
PY
}

read_nanobot_runtime_model() {
  local config_path="${NANOBOT_HOME}/config.json"

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

copy_model_nanobot_config() {
  local safe_model
  safe_model="$(sanitize_model "${NANOBOT_MODEL}")"
  local source_path="${NANOBOT_CONFIGS_DIR}/${safe_model}/config.json"
  local destination_path="${NANOBOT_HOME}/config.json"

  if [[ ! -f "${source_path}" ]]; then
    echo "[entrypoint] missing model nanobot config: ${source_path}"
    echo "[entrypoint] available configs:"
    find "${NANOBOT_CONFIGS_DIR}" -mindepth 2 -maxdepth 2 -type f -name config.json -print 2>/dev/null || true
    exit 1
  fi

  mkdir -p "${NANOBOT_HOME}"
  cp "${source_path}" "${destination_path}"
  echo "[entrypoint] copied nanobot config model=${NANOBOT_MODEL} source=${source_path} destination=${destination_path}"
}

patch_nanobot_config_runtime() {
  local config_path="${NANOBOT_HOME}/config.json"
  NANOBOT_CONFIG_PATH="${config_path}" \
  ENABLE_APPWORLD="${ENABLE_APPWORLD}" \
  NANOBOT_WORKSPACE_DIR="${NANOBOT_WORKSPACE_DIR}" \
  BENCH_TEST_SERVER_URL="${BENCH_TEST_SERVER_URL}" \
  APPWORLD_MCP_URL="${APPWORLD_MCP_URL}" \
  NANOBOT_PROVIDER_API_KEY="${NANOBOT_PROVIDER_API_KEY}" \
  NANOBOT_PROVIDER_API_BASE="${NANOBOT_PROVIDER_API_BASE}" \
  NANOBOT_BRAVE_SEARCH_API_KEY="${NANOBOT_BRAVE_SEARCH_API_KEY}" \
  python - <<'PY'
import json
import os
from pathlib import Path

config_path = Path(os.environ["NANOBOT_CONFIG_PATH"])
enable_appworld = os.environ["ENABLE_APPWORLD"] == "true"
cfg = json.loads(config_path.read_text(encoding="utf-8"))

agents = cfg.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
defaults["workspace"] = os.environ["NANOBOT_WORKSPACE_DIR"]

channels = cfg.setdefault("channels", {})
channels["sendProgress"] = False
test_bench = channels.setdefault("test_bench", {})
test_bench["enabled"] = True
test_bench["base_url"] = os.environ["BENCH_TEST_SERVER_URL"]
test_bench["allow_from"] = ["*"]

providers = cfg.setdefault("providers", {})
custom_provider = providers.setdefault("custom", {})
if os.environ.get("NANOBOT_PROVIDER_API_KEY"):
    custom_provider["apiKey"] = os.environ["NANOBOT_PROVIDER_API_KEY"]
if os.environ.get("NANOBOT_PROVIDER_API_BASE"):
    custom_provider["apiBase"] = os.environ["NANOBOT_PROVIDER_API_BASE"]
    provider_api_base_source = "env_override"
else:
    provider_api_base_source = "model_config"
provider_api_base_value = str(custom_provider.get("apiBase", "")).strip()

tools = cfg.setdefault("tools", {})
web_cfg = tools.setdefault("web", {})
search_cfg = web_cfg.setdefault("search", {})
if os.environ.get("NANOBOT_BRAVE_SEARCH_API_KEY"):
    search_cfg["apiKey"] = os.environ["NANOBOT_BRAVE_SEARCH_API_KEY"]
mcp_servers = tools.setdefault("mcpServers", {})

if enable_appworld:
    mcp_servers["appworld"] = {
        "url": os.environ["APPWORLD_MCP_URL"],
        "headers": {"Accept": "application/json"},
    }
else:
    mcp_servers.pop("appworld", None)

config_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
print(
    "[entrypoint] patched nanobot config "
    f"config={config_path} "
    f"provider_api_base_source={provider_api_base_source} "
    f"provider_api_base={provider_api_base_value}"
)
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

  echo "[entrypoint] normalizing trace log model dir runtime_model=${runtime_model} runtime_safe_model=${source_safe_model} target_model=${MODEL_ID} target_safe_model=${target_safe_model}"

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

patch_bench_config_runtime() {
  local config_path="${BENCH_CONFIG_PATH}"
  BENCH_CONFIG_PATH="${config_path}" \
  BENCH_LLM_BASE_URL="${BENCH_LLM_BASE_URL}" \
  BENCH_HISTORY_CONFIG_PATH="${BENCH_HISTORY_CONFIG_PATH}" \
  python - <<'PY'
import os
from pathlib import Path

import yaml

config_path = Path(os.environ["BENCH_CONFIG_PATH"])
bench_llm_base_url = os.environ.get("BENCH_LLM_BASE_URL", "").strip()
bench_history_config_path = os.environ.get("BENCH_HISTORY_CONFIG_PATH", "").strip()
if not config_path.is_file():
    raise SystemExit(f"[entrypoint] bench config not found: {config_path}")
if not bench_llm_base_url:
    raise SystemExit("[entrypoint] BENCH_LLM_BASE_URL is empty")
if not bench_history_config_path:
    raise SystemExit("[entrypoint] BENCH_HISTORY_CONFIG_PATH is empty")

cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
if not isinstance(cfg, dict):
    raise SystemExit(f"[entrypoint] invalid bench config format: {config_path}")

run_cfg = cfg.setdefault("run", {})
if not isinstance(run_cfg, dict):
    raise SystemExit("[entrypoint] config.run must be a mapping")

for section in ("interaction", "evaluation"):
    section_cfg = run_cfg.setdefault(section, {})
    if not isinstance(section_cfg, dict):
        raise SystemExit(f"[entrypoint] config.run.{section} must be a mapping")
    llm_cfg = section_cfg.setdefault("llm", {})
    if not isinstance(llm_cfg, dict):
        raise SystemExit(f"[entrypoint] config.run.{section}.llm must be a mapping")
    llm_cfg["base_url"] = bench_llm_base_url

evaluation_cfg = run_cfg.setdefault("evaluation", {})
if not isinstance(evaluation_cfg, dict):
    raise SystemExit("[entrypoint] config.run.evaluation must be a mapping")
evaluation_cfg["history_config_path"] = bench_history_config_path

config_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(
    "[entrypoint] patched bench runtime config "
    f"interaction_base_url={bench_llm_base_url} "
    f"evaluation_base_url={bench_llm_base_url} "
    f"history_config_path={bench_history_config_path} "
    f"config={config_path}"
)
PY
}

prepare_bench_config_runtime() {
  local source_path="${BENCH_CONFIG_SOURCE_PATH}"
  local runtime_path="${BENCH_CONFIG_PATH}"

  if [[ ! -f "${source_path}" ]]; then
    echo "[entrypoint] bench config source not found: ${source_path}"
    exit 1
  fi

  mkdir -p "$(dirname "${runtime_path}")"
  cp "${source_path}" "${runtime_path}"
  echo "[entrypoint] copied bench config source=${source_path} runtime=${runtime_path}"
}

run_bench() {
  local -a task_id_args=()
  local -a task_ids=()
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

  APPWORLD_MCP_APP_NAMES="$(normalize_csv_list "${APPWORLD_MCP_APP_NAMES_RAW}")"
  APPWORLD_TOOLS_CONFIG_FILE="$(resolve_appworld_tools_config_file)"
  local appworld_mcp_apps_display="all"
  local appworld_tools_config_file=""
  if [[ -n "${APPWORLD_MCP_APP_NAMES}" ]]; then
    appworld_mcp_apps_display="${APPWORLD_MCP_APP_NAMES}"
  else
    appworld_tools_config_file="${APPWORLD_TOOLS_CONFIG_FILE}"
  fi
  echo "[entrypoint] model=${MODEL_ID} enable_appworld=${ENABLE_APPWORLD} appworld_mcp_app_names=${appworld_mcp_apps_display} appworld_tools_config_file=${appworld_tools_config_file} bench_llm_base_url=${BENCH_LLM_BASE_URL} appworld_root=${APPWORLD_ROOT} bench_workdir=${BENCH_WORKDIR} bench_config_source=${BENCH_CONFIG_SOURCE_PATH} bench_config_runtime=${BENCH_CONFIG_PATH}"
  export BENCH_TEST_SERVER_URL APPWORLD_ROOT

  copy_model_nanobot_config
  patch_nanobot_config_runtime
  print_nanobot_provider_api_base_summary
  prepare_bench_config_runtime
  patch_bench_config_runtime

  if [[ "${ENABLE_APPWORLD}" == "true" ]]; then
    if [[ -n "${appworld_tools_config_file}" && ! -f "${appworld_tools_config_file}" ]]; then
      echo "[entrypoint] missing appworld tools config: ${appworld_tools_config_file}"
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
    if [[ -n "${appworld_tools_config_file}" ]]; then
      mcp_cmd+=(--tools-config-file "${appworld_tools_config_file}")
    fi
    if [[ -n "${APPWORLD_MCP_APP_NAMES}" ]]; then
      mcp_cmd+=(--app-names "${APPWORLD_MCP_APP_NAMES}")
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

  bench_log_file="${LOG_DIR}/bench.log"
  echo "[entrypoint] writing bench log to ${bench_log_file}"
  run_bench >"${bench_log_file}" 2>&1

  echo "[entrypoint] completed model=${MODEL_ID}"
}

main
