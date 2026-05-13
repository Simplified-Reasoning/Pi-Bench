#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_ROOT="${REPO_ROOT}/config"
SCRIPTS_HOST_DIR="${REPO_ROOT}/scripts"
NANOBOT_CONFIGS_HOST_DIR="${CONFIG_ROOT}/nanobot/models"
BENCH_CONFIG_HOST_FILE="${CONFIG_ROOT}/bench/nanobot.yaml"
ENTRYPOINT_HOST_FILE="${SCRIPTS_HOST_DIR}/entrypoint.sh"
BENCH_SRC_DIR="${REPO_ROOT}/src"
BENCH_DATA_DIR="${REPO_ROOT}/data"
NANOBOT_SRC_DIR="${REPO_ROOT}/third_party/nanobot"
APPWORLD_SRC_DIR="${REPO_ROOT}/third_party/appworld"
PROACTIVE_ROOT_CONTAINER="/opt/proactive"
BENCH_SRC_CONTAINER="/opt/proactive/src"
BENCH_DATA_CONTAINER="/opt/proactive/data"
CONFIG_ROOT_CONTAINER="/opt/proactive/config"
SCRIPTS_ROOT_CONTAINER="/opt/proactive/scripts"
BENCH_CONFIG_CONTAINER_FILE="${CONFIG_ROOT_CONTAINER}/bench/nanobot.yaml"
BENCH_HISTORY_CONFIG_CONTAINER_FILE="${CONFIG_ROOT_CONTAINER}/bench/evaluation/trace_history.yaml"
NANOBOT_CONFIGS_CONTAINER_DIR="${CONFIG_ROOT_CONTAINER}/nanobot/models"
ENTRYPOINT_CONTAINER_FILE="${SCRIPTS_ROOT_CONTAINER}/entrypoint.sh"
APPWORLD_ROOT_CONTAINER="/opt/proactive/appworld"

# -----------------------------------------------------------------------------
# User-config section (encode everything in this script; no env overrides)
# -----------------------------------------------------------------------------
IMAGE_NAME="localhost/bench:v1"
CONTAINER_PREFIX="bench"
ENABLE_APPWORLD="true"
CLEAN_RUNTIME="true"
REMOVE_CONTAINER_ON_EXIT="false"
# Terminal log behavior:
# - separate_files: do not print container business logs to terminal; print paths only.
# - inline_preview: print first 120 lines of failed model log to terminal.
TERMINAL_LOG_MODE="separate_files"

# Used to override:
# - config.run.interaction.llm.base_url
# - config.run.evaluation.llm.base_url
OPENAI_API_KEY_FOR_BENCH=""
BENCH_LLM_BASE_URL=""
NANOBOT_PROVIDER_API_KEY=""
NANOBOT_PROVIDER_API_BASE=""

# Brave Search API key used by nanobot tools.web.search.apiKey.
NANOBOT_BRAVE_SEARCH_API_KEY=""

DEFAULT_BENCH_USER_ID="law_trainee"
BENCH_TASK_IDS=""

CLI_USER_IDS_CSV=""
CLI_MODEL_IDS_CSV=""
declare -a CLI_USERS_ARR=()
declare -a CLI_MODELS_ARR=()
declare -a EFFECTIVE_USERS_ARR=()
declare -a EFFECTIVE_MODELS_ARR=()
declare -a EFFECTIVE_RUN_MODEL_IDS_ARR=()

usage() {
  cat <<EOF
Usage:
  $(basename "$0") --model-id <model_a,model_b,...> [--user-id <user_a,user_b,...>] [--help]

Options:
  --user-id   Comma-separated user ids (default: ${DEFAULT_BENCH_USER_ID})
  --model-id  Comma-separated model ids (required)
  --help      Show this help and exit

Examples:
  $(basename "$0") --model-id deepseek-v3.2,MiniMax-M2.5
  $(basename "$0") --user-id researcher,law_trainee --model-id deepseek-v3.2,MiniMax-M2.5
  $(basename "$0") --user-id law_trainee --model-id deepseek-v3.2,deepseek-v3.2,deepseek-v3.2
EOF
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

# model-id reference list (from config/nanobot/models):
#   gpt-5.4
#   gemini-3.1-pro-preview
#   gemini-3-flash-preview
#   claude-sonnet-4-6
#   claude-opus-4-6
#   claude-haiku-4-5-20251001
#   deepseek-v3.2
#   doubao-seed-2-0-pro-260215
#   MiniMax-M2.7
#   MiniMax-M2.5
#   kimi-k2.5
#   glm-5.1
#   glm-5
#   qwen3.6-plus
parse_csv_unique() {
  local raw_csv="$1"
  local arg_name="$2"
  local out_arr_name="$3"
  local -n out_arr_ref="${out_arr_name}"
  local -a parsed_items=()
  local -A seen_items=()
  local item=""
  local token=""

  if [[ "${raw_csv}" =~ (^|,)[[:space:]]*(,|$) ]]; then
    echo "[parallel] --${arg_name} contains empty item: ${raw_csv}"
    exit 1
  fi

  IFS=',' read -r -a parsed_items <<< "${raw_csv}"
  if [[ "${#parsed_items[@]}" -eq 0 ]]; then
    echo "[parallel] --${arg_name} is empty"
    exit 1
  fi

  for item in "${parsed_items[@]}"; do
    token="$(trim "${item}")"
    if [[ -z "${token}" ]]; then
      echo "[parallel] --${arg_name} contains empty item: ${raw_csv}"
      exit 1
    fi
    if [[ -n "${seen_items["${token}"]+x}" ]]; then
      echo "[parallel] duplicate ${arg_name} in --${arg_name}: ${token}"
      exit 1
    fi
    seen_items["${token}"]=1
    out_arr_ref+=("${token}")
  done
}

parse_csv() {
  local raw_csv="$1"
  local arg_name="$2"
  local out_arr_name="$3"
  local -n out_arr_ref="${out_arr_name}"
  local -a parsed_items=()
  local item=""
  local token=""

  if [[ "${raw_csv}" =~ (^|,)[[:space:]]*(,|$) ]]; then
    echo "[parallel] --${arg_name} contains empty item: ${raw_csv}"
    exit 1
  fi

  IFS=',' read -r -a parsed_items <<< "${raw_csv}"
  if [[ "${#parsed_items[@]}" -eq 0 ]]; then
    echo "[parallel] --${arg_name} is empty"
    exit 1
  fi

  for item in "${parsed_items[@]}"; do
    token="$(trim "${item}")"
    if [[ -z "${token}" ]]; then
      echo "[parallel] --${arg_name} contains empty item: ${raw_csv}"
      exit 1
    fi
    out_arr_ref+=("${token}")
  done
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --user-id)
        if [[ $# -lt 2 ]]; then
          echo "[parallel] --user-id requires a value"
          usage
          exit 1
        fi
        if [[ -n "${CLI_USER_IDS_CSV}" ]]; then
          echo "[parallel] --user-id can only be specified once"
          exit 1
        fi
        CLI_USER_IDS_CSV="$2"
        if [[ -z "$(trim "${CLI_USER_IDS_CSV}")" ]]; then
          echo "[parallel] --user-id value cannot be empty"
          exit 1
        fi
        shift 2
        ;;
      --model-id)
        if [[ $# -lt 2 ]]; then
          echo "[parallel] --model-id requires a value"
          usage
          exit 1
        fi
        if [[ -n "${CLI_MODEL_IDS_CSV}" ]]; then
          echo "[parallel] --model-id can only be specified once"
          exit 1
        fi
        CLI_MODEL_IDS_CSV="$2"
        if [[ -z "$(trim "${CLI_MODEL_IDS_CSV}")" ]]; then
          echo "[parallel] --model-id value cannot be empty"
          exit 1
        fi
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "[parallel] unknown argument: $1"
        usage
        exit 1
        ;;
    esac
  done

  if [[ -z "${CLI_MODEL_IDS_CSV}" ]]; then
    echo "[parallel] --model-id is required"
    usage
    exit 1
  fi

  if [[ -n "${CLI_USER_IDS_CSV}" ]]; then
    parse_csv_unique "${CLI_USER_IDS_CSV}" "user-id" CLI_USERS_ARR
  fi
  parse_csv "${CLI_MODEL_IDS_CSV}" "model-id" CLI_MODELS_ARR
}

if [[ -z "${OPENAI_API_KEY_FOR_BENCH}" ]]; then
  OPENAI_API_KEY_FOR_BENCH="${NANOBOT_PROVIDER_API_KEY}"
fi
if [[ -z "${BENCH_LLM_BASE_URL}" && -n "${NANOBOT_PROVIDER_API_BASE}" ]]; then
  BENCH_LLM_BASE_URL="${NANOBOT_PROVIDER_API_BASE}"
fi

HTTP_PROXY_VALUE=""
HTTPS_PROXY_VALUE=""
NO_PROXY_VALUE=""

OUTPUTS_ROOT="${REPO_ROOT}/outputs"
RUN_TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
CONTAINER_TIMESTAMP="${RUN_TIMESTAMP//_/}"

parse_args "$@"

mkdir -p "${OUTPUTS_ROOT}"

if [[ "${#CLI_USERS_ARR[@]}" -gt 0 ]]; then
  EFFECTIVE_USERS_ARR=("${CLI_USERS_ARR[@]}")
else
  EFFECTIVE_USERS_ARR=("${DEFAULT_BENCH_USER_ID}")
fi

EFFECTIVE_MODELS_ARR=("${CLI_MODELS_ARR[@]}")

CONTAINER_CLI=""
if command -v podman >/dev/null 2>&1; then
  CONTAINER_CLI="podman"
elif command -v docker >/dev/null 2>&1; then
  CONTAINER_CLI="docker"
else
  echo "neither podman nor docker command found"
  exit 1
fi

if [[ ! -d "${NANOBOT_CONFIGS_HOST_DIR}" ]]; then
  echo "nanobot configs dir not found: ${NANOBOT_CONFIGS_HOST_DIR}"
  exit 1
fi

if [[ ! -f "${BENCH_CONFIG_HOST_FILE}" ]]; then
  echo "bench config file not found: ${BENCH_CONFIG_HOST_FILE}"
  exit 1
fi

if [[ ! -f "${ENTRYPOINT_HOST_FILE}" ]]; then
  echo "entrypoint file not found: ${ENTRYPOINT_HOST_FILE}"
  exit 1
fi

if [[ ! -d "${CONFIG_ROOT}" ]]; then
  echo "config root not found: ${CONFIG_ROOT}"
  exit 1
fi

if [[ ! -d "${SCRIPTS_HOST_DIR}" ]]; then
  echo "scripts dir not found: ${SCRIPTS_HOST_DIR}"
  exit 1
fi

if [[ ! -d "${BENCH_SRC_DIR}" ]]; then
  echo "src source dir not found: ${BENCH_SRC_DIR}"
  exit 1
fi

if [[ ! -d "${BENCH_DATA_DIR}" ]]; then
  echo "data dir not found: ${BENCH_DATA_DIR}"
  exit 1
fi

if [[ ! -d "${NANOBOT_SRC_DIR}" ]]; then
  echo "nanobot source dir not found: ${NANOBOT_SRC_DIR}"
  exit 1
fi

if [[ ! -d "${APPWORLD_SRC_DIR}" ]]; then
  echo "appworld source dir not found: ${APPWORLD_SRC_DIR}"
  exit 1
fi

if ! "${CONTAINER_CLI}" image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  cat <<EOF
required image not found: ${IMAGE_NAME}
build it first
EOF
  exit 1
fi

if [[ -z "${NANOBOT_PROVIDER_API_KEY}" ]]; then
  echo "NANOBOT_PROVIDER_API_KEY is empty; edit this script and set it"
  exit 1
fi

if [[ -z "${NANOBOT_BRAVE_SEARCH_API_KEY}" ]]; then
  echo "NANOBOT_BRAVE_SEARCH_API_KEY is empty; edit this script and set it"
  exit 1
fi

if [[ -z "${OPENAI_API_KEY_FOR_BENCH}" ]]; then
  echo "OPENAI_API_KEY_FOR_BENCH is empty; edit this script and set it"
  exit 1
fi
if [[ -z "${BENCH_LLM_BASE_URL}" ]]; then
  echo "BENCH_LLM_BASE_URL is empty; edit this script and set it"
  exit 1
fi

if [[ -z "${HTTP_PROXY_VALUE}" ]]; then
  HTTP_PROXY_VALUE="${HTTP_PROXY:-${http_proxy:-}}"
fi
if [[ -z "${HTTPS_PROXY_VALUE}" ]]; then
  HTTPS_PROXY_VALUE="${HTTPS_PROXY:-${https_proxy:-}}"
fi
if [[ -z "${NO_PROXY_VALUE}" ]]; then
  NO_PROXY_VALUE="${NO_PROXY:-${no_proxy:-}}"
fi

missing_proxy=()
if [[ -z "${HTTP_PROXY_VALUE}" ]]; then
  missing_proxy+=("HTTP_PROXY/http_proxy")
fi
if [[ -z "${HTTPS_PROXY_VALUE}" ]]; then
  missing_proxy+=("HTTPS_PROXY/https_proxy")
fi
if [[ -z "${NO_PROXY_VALUE}" ]]; then
  missing_proxy+=("NO_PROXY/no_proxy")
fi

if [[ "${#missing_proxy[@]}" -gt 0 ]]; then
  echo "[parallel][warning] missing proxy variables: ${missing_proxy[*]}"
  echo "[parallel][warning] continuing without those proxy values; set host proxy envs or hardcode *_PROXY_VALUE in this script if your network requires a proxy"
fi

echo "[parallel] container cli: ${CONTAINER_CLI}"
echo "[parallel] using prebuilt image ${IMAGE_NAME}"
if [[ "${#missing_proxy[@]}" -gt 0 ]]; then
  echo "[parallel] proxy env source incomplete; empty proxy env values will still be passed into containers"
else
  echo "[parallel] proxy env source ready (HTTP/HTTPS/NO_PROXY will be passed into containers)"
fi
if [[ -n "${NANOBOT_PROVIDER_API_BASE}" ]]; then
  echo "[parallel] nanobot provider api base override enabled: ${NANOBOT_PROVIDER_API_BASE}"
else
  echo "[parallel] nanobot provider api base override disabled; containers will keep providers.custom.apiBase from each model config.json"
fi
echo "[parallel] host roots: src=${BENCH_SRC_DIR} data=${BENCH_DATA_DIR} config=${CONFIG_ROOT} scripts=${SCRIPTS_HOST_DIR}"
echo "[parallel] source mounts: nanobot=${NANOBOT_SRC_DIR} appworld=${APPWORLD_SRC_DIR}"
echo "[parallel] terminal log mode: ${TERMINAL_LOG_MODE}"
echo "[parallel] effective users (${#EFFECTIVE_USERS_ARR[@]}): ${EFFECTIVE_USERS_ARR[*]}"
echo "[parallel] effective models (${#EFFECTIVE_MODELS_ARR[@]}): ${EFFECTIVE_MODELS_ARR[*]}"

sanitize_token() {
  local raw="$1"
  echo "${raw}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_.-]/-/g'
}

safe_model_id() {
  local raw="$1"
  printf '%s' "${raw//\//_}"
}

build_run_model_ids() {
  local -A model_counts=()
  local -A model_seen=()
  local -A run_model_seen=()
  local -A safe_run_model_seen=()
  local model=""
  local run_model_id=""
  local safe_run_model=""
  local run_number=0

  EFFECTIVE_RUN_MODEL_IDS_ARR=()

  for model in "${EFFECTIVE_MODELS_ARR[@]}"; do
    model_counts["${model}"]=$(( ${model_counts["${model}"]:-0} + 1 ))
  done

  for model in "${EFFECTIVE_MODELS_ARR[@]}"; do
    if [[ "${model_counts["${model}"]}" -eq 1 ]]; then
      EFFECTIVE_RUN_MODEL_IDS_ARR+=("${model}")
      continue
    fi

    run_number=$(( ${model_seen["${model}"]:-0} + 1 ))
    model_seen["${model}"]="${run_number}"
    EFFECTIVE_RUN_MODEL_IDS_ARR+=("$(printf '%s__run%02d' "${model}" "${run_number}")")
  done

  for run_model_id in "${EFFECTIVE_RUN_MODEL_IDS_ARR[@]}"; do
    if [[ -n "${run_model_seen["${run_model_id}"]+x}" ]]; then
      echo "[parallel] duplicate generated run model id: ${run_model_id}"
      echo "[parallel] choose model ids that do not collide with the __runNN duplicate-run aliases"
      exit 1
    fi
    run_model_seen["${run_model_id}"]=1

    safe_run_model="$(safe_model_id "${run_model_id}")"
    if [[ -n "${safe_run_model_seen["${safe_run_model}"]+x}" ]]; then
      echo "[parallel] duplicate safe run model id: ${safe_run_model}"
      echo "[parallel] choose model ids whose safe output directories do not collide"
      exit 1
    fi
    safe_run_model_seen["${safe_run_model}"]=1
  done
}

missing_user_data=()
for user_id in "${EFFECTIVE_USERS_ARR[@]}"; do
  user_dir="${BENCH_DATA_DIR}/${user_id}"
  if [[ ! -d "${user_dir}" ]]; then
    missing_user_data+=("${user_id}:missing_dir:${user_dir}")
    continue
  fi
  if [[ ! -f "${user_dir}/profile.yaml" ]]; then
    missing_user_data+=("${user_id}:missing_profile:${user_dir}/profile.yaml")
  fi
  if [[ ! -f "${user_dir}/episode.yaml" ]]; then
    missing_user_data+=("${user_id}:missing_episode:${user_dir}/episode.yaml")
  fi
done

if [[ "${#missing_user_data[@]}" -gt 0 ]]; then
  echo "[parallel] user data check failed:"
  for item in "${missing_user_data[@]}"; do
    echo "  - ${item}"
  done
  exit 1
fi

missing_model_configs=()
for model in "${EFFECTIVE_MODELS_ARR[@]}"; do
  safe_model="$(safe_model_id "${model}")"
  model_config_file="${NANOBOT_CONFIGS_HOST_DIR}/${safe_model}/config.json"
  if [[ ! -f "${model_config_file}" ]]; then
    missing_model_configs+=("${model}:${model_config_file}")
  fi
done

if [[ "${#missing_model_configs[@]}" -gt 0 ]]; then
  echo "[parallel] missing model nanobot config(s):"
  for item in "${missing_model_configs[@]}"; do
    echo "  - ${item}"
  done
  echo "[parallel] available model configs:"
  find "${NANOBOT_CONFIGS_HOST_DIR}" -mindepth 2 -maxdepth 2 -type f -name config.json -print || true
  exit 1
fi

build_run_model_ids
echo "[parallel] effective run model ids (${#EFFECTIVE_RUN_MODEL_IDS_ARR[@]}): ${EFFECTIVE_RUN_MODEL_IDS_ARR[*]}"

declare -a JOB_USER_IDS=()
declare -a JOB_NANOBOT_MODELS=()
declare -a JOB_RUN_MODEL_IDS=()
declare -a JOB_CONTAINER_NAMES=()
declare -a JOB_RUNTIME_DIRS=()
declare -a JOB_SERVICE_LOG_DIRS=()
declare -a JOB_START_PIDS=()

for user_id in "${EFFECTIVE_USERS_ARR[@]}"; do
  safe_user="$(sanitize_token "${user_id}")"
  for idx in "${!EFFECTIVE_MODELS_ARR[@]}"; do
    model="${EFFECTIVE_MODELS_ARR[$idx]}"
    run_model_id="${EFFECTIVE_RUN_MODEL_IDS_ARR[$idx]}"
    safe_run_model="$(safe_model_id "${run_model_id}")"
    runtime_dir="${OUTPUTS_ROOT}/${safe_run_model}/${user_id}/run/${RUN_TIMESTAMP}-runtime"
    service_logs_dir="${runtime_dir}/service-logs"

    if [[ "${CLEAN_RUNTIME}" == "true" ]]; then
      rm -rf "${runtime_dir}"
    fi
    mkdir -p "${runtime_dir}"
    mkdir -p "${service_logs_dir}"

    container_name="${CONTAINER_PREFIX}-${CONTAINER_TIMESTAMP}-${safe_user}-${safe_run_model}"

    echo "[parallel] launching user=${user_id} model=${model} run_model_id=${run_model_id} container=${container_name}"
    create_cmd=(
      "${CONTAINER_CLI}" create
      --name "${container_name}"
      --entrypoint "${ENTRYPOINT_CONTAINER_FILE}"
      -e "MODEL_ID=${run_model_id}"
      -e "NANOBOT_MODEL=${model}"
      -e "ENABLE_APPWORLD=${ENABLE_APPWORLD}"
      -e "BENCH_USER_ID=${user_id}"
      -e "BENCH_CONFIG_SOURCE_PATH=${BENCH_CONFIG_CONTAINER_FILE}"
      -e "BENCH_HISTORY_CONFIG_PATH=${BENCH_HISTORY_CONFIG_CONTAINER_FILE}"
      -e "NANOBOT_CONFIGS_DIR=${NANOBOT_CONFIGS_CONTAINER_DIR}"
      -e "BENCH_WORKDIR=${PROACTIVE_ROOT_CONTAINER}"
      -e "BENCH_TEST_SERVER_SCRIPT=${SCRIPTS_ROOT_CONTAINER}/test_server.py"
      -e "BENCH_LLM_BASE_URL=${BENCH_LLM_BASE_URL}"
      -e "NANOBOT_PROVIDER_API_BASE=${NANOBOT_PROVIDER_API_BASE}"
      -e "NANOBOT_PROVIDER_API_KEY=${NANOBOT_PROVIDER_API_KEY}"
      -e "NANOBOT_BRAVE_SEARCH_API_KEY=${NANOBOT_BRAVE_SEARCH_API_KEY}"
      -e "OPENAI_API_KEY=${OPENAI_API_KEY_FOR_BENCH}"
      -e "APPWORLD_ROOT=${APPWORLD_ROOT_CONTAINER}"
    )

    if [[ -n "${BENCH_TASK_IDS}" ]]; then
      create_cmd+=(-e "BENCH_TASK_IDS=${BENCH_TASK_IDS}")
    fi

    create_cmd+=(
      -e "HTTP_PROXY=${HTTP_PROXY_VALUE}"
      -e "http_proxy=${HTTP_PROXY_VALUE}"
      -e "HTTPS_PROXY=${HTTPS_PROXY_VALUE}"
      -e "https_proxy=${HTTPS_PROXY_VALUE}"
      -e "NO_PROXY=${NO_PROXY_VALUE}"
      -e "no_proxy=${NO_PROXY_VALUE}"
    )

    create_cmd+=(
      -v "${service_logs_dir}:/root/.nanobot/logs"
      -v "${OUTPUTS_ROOT}:${PROACTIVE_ROOT_CONTAINER}/outputs"
      -v "${BENCH_SRC_DIR}:${BENCH_SRC_CONTAINER}"
      -v "${BENCH_DATA_DIR}:${BENCH_DATA_CONTAINER}"
      -v "${CONFIG_ROOT}:${CONFIG_ROOT_CONTAINER}"
      -v "${SCRIPTS_HOST_DIR}:${SCRIPTS_ROOT_CONTAINER}"
      -v "${NANOBOT_SRC_DIR}:/opt/proactive/nanobot"
      -v "${APPWORLD_SRC_DIR}:${APPWORLD_ROOT_CONTAINER}"
      "${IMAGE_NAME}"
    )
    cid="$("${create_cmd[@]}")"

    inspect_before_log="${runtime_dir}/inspect.before.log"
    start_log="${runtime_dir}/container.log"

    "${CONTAINER_CLI}" inspect "${container_name}" > "${inspect_before_log}" 2>&1 || true

    # Attach mode provides deterministic per-container logs, independent of logs driver.
    "${CONTAINER_CLI}" start -a "${container_name}" > "${start_log}" 2>&1 &
    start_pid="$!"

    JOB_USER_IDS+=("${user_id}")
    JOB_NANOBOT_MODELS+=("${model}")
    JOB_RUN_MODEL_IDS+=("${run_model_id}")
    JOB_CONTAINER_NAMES+=("${container_name}")
    JOB_RUNTIME_DIRS+=("${runtime_dir}")
    JOB_SERVICE_LOG_DIRS+=("${service_logs_dir}")
    JOB_START_PIDS+=("${start_pid}")
    echo "[parallel] user=${user_id} model=${model} run_model_id=${run_model_id} cid=${cid} runtime_dir=${runtime_dir}"
  done
done

overall_code=0

echo "[parallel] waiting containers to finish"
for idx in "${!JOB_USER_IDS[@]}"; do
  user_id="${JOB_USER_IDS[$idx]}"
  model="${JOB_NANOBOT_MODELS[$idx]}"
  run_model_id="${JOB_RUN_MODEL_IDS[$idx]}"
  name="${JOB_CONTAINER_NAMES[$idx]}"
  runtime_dir="${JOB_RUNTIME_DIRS[$idx]}"
  service_logs_dir="${JOB_SERVICE_LOG_DIRS[$idx]}"
  start_pid="${JOB_START_PIDS[$idx]}"
  log_file="${runtime_dir}/container.log"
  inspect_after_log="${runtime_dir}/inspect.after.log"
  inspect_summary_log="${runtime_dir}/inspect.summary.log"

  start_cmd_code=0
  wait "${start_pid}" || start_cmd_code=$?

  "${CONTAINER_CLI}" inspect "${name}" > "${inspect_after_log}" 2>&1 || true

  state_summary="$("${CONTAINER_CLI}" inspect "${name}" \
    --format 'status={{.State.Status}} exit_code={{.State.ExitCode}} started_at={{.State.StartedAt}} finished_at={{.State.FinishedAt}} oom_killed={{.State.OOMKilled}} error={{.State.Error}}' \
    2>/dev/null || echo "status=unknown exit_code=unknown")"
  echo "${state_summary}" > "${inspect_summary_log}"

  exit_code="$(echo "${state_summary}" | sed -n 's/.*exit_code=\([^ ]*\).*/\1/p')"
  if [[ -z "${exit_code}" || "${exit_code}" == "unknown" ]]; then
    exit_code="${start_cmd_code}"
  fi

  if [[ "${exit_code}" != "0" ]]; then
    overall_code=1
    if [[ "${TERMINAL_LOG_MODE}" == "inline_preview" ]]; then
      echo "[parallel] user=${user_id} model=${model} run_model_id=${run_model_id} failed; showing first 120 lines of ${log_file}"
      sed -n '1,120p' "${log_file}" || true
    else
      echo "[parallel] user=${user_id} model=${model} run_model_id=${run_model_id} failed; business log is kept in ${log_file}"
      echo "[parallel] inspect with: tail -f \"${log_file}\""
      echo "[parallel] service logs dir: ${service_logs_dir}"
      echo "[parallel] inspect with: ls -lah \"${service_logs_dir}\""
    fi
  fi

  printf '[parallel] user=%s model=%s run_model_id=%s container=%s start_cmd_code=%s exit_code=%s runtime_dir=%s log=%s service_logs_dir=%s inspect=%s\n' \
    "${user_id}" "${model}" "${run_model_id}" "${name}" "${start_cmd_code}" "${exit_code}" "${runtime_dir}" "${log_file}" "${service_logs_dir}" "${inspect_summary_log}"

  if [[ "${REMOVE_CONTAINER_ON_EXIT}" == "true" ]]; then
    "${CONTAINER_CLI}" rm "${name}" >/dev/null 2>&1 || true
  fi
done

exit "${overall_code}"
