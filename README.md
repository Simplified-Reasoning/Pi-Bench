<p align="center">
  <img src="./image2.png" alt="Pi-Bench Banner" width="100%" />
</p>

<h1 align="center">Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflow</h1>

---

## 🚀 Bench Public Code

This directory contains the public code release for running the Agent Arena
benchmark. It includes the benchmark runner, task data, runtime configuration,
model configuration templates, and the locally modified runtime source trees
mounted into the prebuilt container:

```text
code/
  src/          # benchmark Python package
  data/         # benchmark users, profiles, episodes, tools, skills, and tasks
  config/       # benchmark YAML and nanobot model configs
  scripts/      # launchers, container entrypoint, image loader, test server
  third_party/
    appworld/   # locally modified AppWorld source tree
    nanobot/    # locally modified nanobot source tree
```

The Docker launcher mounts these directories into the prebuilt image
`localhost/bench:v1`. The launcher does not build the image. It expects the
image to have been loaded from the release archive before a benchmark run.

`third_party/appworld/` and `third_party/nanobot/` are public assets used by
this benchmark with local modifications. The paper cites these assets, and this
release preserves and follows their corresponding licenses.

## ✅ Prerequisites

Before running the benchmark, prepare:

- Docker or Podman on the host machine.
- Python and `pip` for the one-time AppWorld data setup.
- Network access to the LLM provider endpoint used by the selected model
  configuration.
- API keys for the model provider, benchmark evaluation LLM endpoint, and Brave
  Search.
- The prebuilt image archive `docker-image.tar.gz` from the anonymous OSF
  project linked below.

If your network requires a proxy, set the usual host proxy variables:

```bash
export HTTP_PROXY="http://<proxy-host>:<proxy-port>"
export HTTPS_PROXY="http://<proxy-host>:<proxy-port>"
export NO_PROXY="127.0.0.1,localhost"
```

The launcher forwards these values into the container and prints a warning when
any are missing.

## 🧰 Setup

Prepare AppWorld data once from this `code/` directory:

```bash
cd third_party/appworld
pip install -e .
appworld install
appworld download data
appworld install --repo
appworld download data
cd ../..
```

Download the prebuilt Docker image archive `docker-image.tar.gz` from the
anonymous OSF project:

```text
https://osf.io/dnb5k/overview?view_only=5ff4eeb8c32a417fad136a54735c44db
```

Then load the benchmark image from this `code/` directory:

```bash
bash load_bench_image.sh /path/to/docker-image.tar.gz
```

If the image archive is copied to `/tmp/localhost-bench.tar.gz`, the path can be
omitted:

```bash
bash load_bench_image.sh
```

The loader delegates to `scripts/load_image.sh`, checks for Docker or Podman,
loads the archive, and verifies that `localhost/bench:v1` is available.

## ⚙️ Configuration

The main benchmark config is:

```text
config/bench/nanobot.yaml
```

Evaluation trace-history config lives under:

```text
config/bench/evaluation/
```

Nanobot model configs live under:

```text
config/nanobot/models/<model-id>/config.json
```

Available user ids are the directory names under `data/`:
`researcher`, `marketer`, `pharmacist`, `law_trainee`, and `Financier`.

Available model ids are the directory names under `config/nanobot/models/`.

Before running Docker jobs, edit the user-config section near the top of
`scripts/run_parallel_models_docker.sh`. The script intentionally keeps routine
configuration in this section instead of reading benchmark credentials from
environment variables.

Required values:

- `BENCH_LLM_BASE_URL`
- `NANOBOT_PROVIDER_API_KEY`
- `NANOBOT_BRAVE_SEARCH_API_KEY`

Optional values:

- `OPENAI_API_KEY_FOR_BENCH`, used by the benchmark evaluation LLM. If left
  empty, it falls back to `NANOBOT_PROVIDER_API_KEY`.
- `NANOBOT_PROVIDER_API_BASE`; when empty, the container keeps the selected
  model config's `providers.custom.apiBase`.
- `DEFAULT_BENCH_USER_ID`, currently `law_trainee`.
- `BENCH_TASK_IDS`, left empty to run all tasks for the selected user.

To run only a subset of tasks, set `BENCH_TASK_IDS` in the script to a
comma-separated list of task ids. Task ids are the task directory names under
`data/<user-id>/tasks/`.

## 🏆 Leaderboard

Overall results for `Proc / Comp` (%). Results are averaged over three runs,
with subscripts denoting standard deviation.

| Model | Average Proc | Average Comp | Researcher (Proc / Comp) | Marketer (Proc / Comp) | Pharmacist (Proc / Comp) | Law Trainee (Proc / Comp) | Financier (Proc / Comp) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-5.4 | **67.0**<sub>2.1</sub> | 65.6<sub>1.8</sub> | 46.0 / 66.4 | **78.2** / 67.1 | 75.9 / 71.5 | **56.9 / 61.9** | **78.1** / 61.2 |
| Gemini 3.1 Pro | 57.1<sub>0.9</sub> | 60.0<sub>0.8</sub> | 41.1 / 59.2 | 65.0 / 62.1 | 71.0 / 72.1 | 50.0 / 55.3 | 58.6 / 51.1 |
| Claude Opus 4.6 | 65.5<sub>1.4</sub> | **67.6**<sub>1.5</sub> | **50.3 / 74.5** | 75.0 / **74.6** | **82.8** / 68.6 | 45.7 / 57.2 | 73.8 / **63.2** |
| DeepSeek V3.2 | 53.3<sub>1.9</sub> | 57.8<sub>3.0</sub> | 29.0 / 66.9 | 69.1 / 59.4 | 75.9 / 62.6 | 33.2 / 51.1 | 59.1 / 48.9 |
| MiniMax M2.7 | 55.6<sub>3.2</sub> | 60.0<sub>1.8</sub> | 33.4 / 63.9 | 71.9 / 61.9 | 77.1 / 63.6 | 38.6 / 52.5 | 57.2 / 58.1 |
| Kimi K2.5 | 43.1<sub>0.2</sub> | 61.6<sub>1.9</sub> | 28.9 / 63.5 | 41.2 / 62.3 | 70.1 / **74.8** | 34.8 / 54.4 | 40.4 / 52.9 |
| Seed2.0 Pro | 58.4<sub>0.9</sub> | 52.1<sub>3.8</sub> | 38.9 / 59.6 | 71.4 / 44.2 | 77.0 / 67.6 | 46.0 / 44.7 | 58.7 / 44.5 |
| GLM-5.1 | 58.4<sub>0.8</sub> | 63.6<sub>2.9</sub> | 41.8 / 61.6 | 62.6 / 69.1 | 75.2 / 70.3 | 45.5 / 57.3 | 66.7 / 59.8 |
| Qwen3.6 Plus | 64.0<sub>1.1</sub> | 64.1<sub>0.6</sub> | 40.1 / 70.0 | 77.5 / 66.6 | 79.7 / 70.2 | 45.7 / 60.2 | 77.1 / 53.6 |

## ▶️ Run

Run from this `code/` directory:

```bash
bash scripts/run_parallel_models_docker.sh --model-id deepseek-v3.2
```

Run multiple models:

```bash
bash scripts/run_parallel_models_docker.sh \
  --model-id deepseek-v3.2,MiniMax-M2.5
```

Run a specific user:

```bash
bash scripts/run_parallel_models_docker.sh \
  --user-id law_trainee \
  --model-id deepseek-v3.2
```

Run multiple users and models in one command:

```bash
bash scripts/run_parallel_models_docker.sh \
  --user-id researcher,law_trainee \
  --model-id deepseek-v3.2,MiniMax-M2.5
```

Repeated runs of the same model can be requested by repeating the model id. The
launcher writes each repeated run to a distinct output directory with a
`__runNN` suffix:

```bash
bash scripts/run_parallel_models_docker.sh \
  --user-id law_trainee \
  --model-id deepseek-v3.2,deepseek-v3.2,deepseek-v3.2
```

For a direct local import check or non-Docker invocation, run the benchmark
package from the repository root so relative `data/` paths resolve correctly:

```bash
python -m src.main \
  --config config/bench/nanobot.yaml \
  --history-config-path config/bench/evaluation/trace_history.yaml
```

## 🐳 Container Layout

`scripts/run_parallel_models_docker.sh` mounts host paths into the prebuilt
container as follows:

```text
src/                    -> /opt/proactive/src
data/                   -> /opt/proactive/data
config/                 -> /opt/proactive/config
scripts/                -> /opt/proactive/scripts
third_party/appworld/   -> /opt/proactive/appworld
third_party/nanobot/    -> /opt/proactive/nanobot
```

It also overrides the container entrypoint with:

```text
/opt/proactive/scripts/entrypoint.sh
```

When AppWorld is enabled, the entrypoint starts AppWorld APIs and MCP, then
starts the local test channel server from `scripts/test_server.py`, then starts
`nanobot gateway`, runs benchmark `--mode run`, normalizes trace-log model
directories when needed, and runs benchmark `--mode eval`.

AppWorld MCP is launched inside the container with user-specific tools from:

```text
/opt/proactive/data/<user-id>/tools.yaml
```

## 📦 Outputs

Results and logs are written under:

```text
outputs/<model-id>/<user-id>/
```

Per-task evaluation JSON files are written below each task's `eval/results/`
directory. The run also generates a trace viewer HTML file under the user output
directory when evaluation completes.

Runtime logs for each container run are under:

```text
outputs/<model-id>/<user-id>/run/<timestamp>-runtime/
```

Important runtime files include:

- `container.log`, the benchmark process log for the container.
- `inspect.before.log` and `inspect.after.log`, container inspection snapshots.
- `inspect.summary.log`, a compact container status and exit-code summary.
- `service-logs/`, nanobot service logs mounted from inside the container.

The launcher leaves containers available for inspection by default. To remove
containers automatically after completion, set `REMOVE_CONTAINER_ON_EXIT="true"`
near the top of `scripts/run_parallel_models_docker.sh`.

Do not commit generated `outputs/` files.

## 🛠️ Troubleshooting

If the launcher exits before starting a run, check the printed validation
message first. Common causes are:

- `localhost/bench:v1` has not been loaded.
- Docker or Podman is not available.
- Required API keys or base URLs are still blank in the script.
- The requested `--user-id` is not present under `data/`.
- The requested `--model-id` has no matching
  `config/nanobot/models/<model-id>/config.json`.

If a container starts but the run fails, inspect
`outputs/<model-id>/<user-id>/run/<timestamp>-runtime/container.log` first,
then check `service-logs/` for nanobot-specific logs.

To inspect a running container:

```bash
docker ps
docker exec -it <container_id_or_name> /bin/bash
```

If the image does not include `bash`, use `/bin/sh`. For exited containers, use
`docker ps -a` to find the container and `docker cp` to copy files out, or start
the container again before `docker exec`.

Container-side nanobot runtime files are under `/root/.nanobot/`, especially:

- `/root/.nanobot/workspace`
- `/root/.nanobot/logs`
- `/root/.nanobot/config.json`
