<h1 align="center">π-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows</h1>

<p align="center">
  <img src="./assets/pi-bench-overview.png" alt="Pi-Bench Overview" width="100%" />
</p>

<p align="center">
  <a href="https://arxiv.org/abs/2605.14678">
    <img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.14678-B31B1B?style=for-the-badge&logo=arxiv&logoColor=white" />
  </a>
  <a href="https://simplified-reasoning.github.io/Pi-Bench/">
    <img alt="Project Page" src="https://img.shields.io/badge/PROJECT_PAGE-3B82F6?style=for-the-badge&logo=googlechrome&logoColor=white" />
  </a>
  <a href="https://github.com/Simplified-Reasoning/Pi-Bench">
    <img alt="GitHub" src="https://img.shields.io/badge/GITHUB-181717?style=for-the-badge&logo=github&logoColor=white" />
  </a>
  <a href="https://huggingface.co/datasets/zzzhr97/Pi-Bench">
    <img alt="Dataset" src="https://img.shields.io/badge/DATASET-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" />
  </a>
  <a href="https://huggingface.co/papers/2605.14678">
    <img alt="HF Daily Paper" src="https://img.shields.io/badge/HF--DAILY--PAPER-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" />
  </a>
</p>

<p align="center">
  <a href="#news">📢 News</a> •
  <a href="#introduction">🧭 Introduction</a> •
  <a href="https://simplified-reasoning.github.io/Pi-Bench/#results">🏆 Leaderboard</a> •
  <a href="#setup">🚀 Getting Started</a>
</p>
<p align="center">
  <a href="#run">🛠️ Run</a> •
  <a href="#outputs">📦 Outputs</a> •
  <a href="#acknowledgement">🙏 Acknowledgement</a> •
  <a href="#citation">📚 Citation</a>
</p>

---

<a id="news"></a>
## 📢 News

- [May 2026] `π-BENCH` is available on arXiv: [2605.14678](https://arxiv.org/abs/2605.14678).
- [May 2026] Project page is online: https://simplified-reasoning.github.io/Pi-Bench/

<a id="introduction"></a>
## 🧭 Introduction

`π-BENCH` evaluates **proactive personal assistant agents** in long-horizon,
multi-session workflows. It contains **100 multi-turn tasks** across **5
personas** (`researcher`, `marketer`, `pharmacist`, `law_trainee`,
`financier`) in persistent workspaces where user requirements are often
underspecified and emerge over time.

The benchmark reports **Proactivity (PROC)** and **Completeness (COMP)**. PROC
measures whether an agent discovers or infers hidden intents early; COMP
measures whether final artifacts satisfy checklist requirements. Unlike
short-horizon, GUI/mobile, or memory-only benchmarks, `π-BENCH` focuses on
persistent artifact workflows with hidden intents, inter-task dependencies, and
cross-session continuity.

<a id="setup"></a>
## 🧰 Setup

1. Create and activate a Python environment:

```bash
conda create -n pi-bench python=3.11
conda activate pi-bench
```

2. Install local dependencies and prepare AppWorld data:

```bash
pip install -e .
pip install -e third_party/nanobot
bash scripts/setup_appworld.sh
```

3. Create a local environment file:

```bash
cp env.example.sh env.sh
```

Edit `env.sh` with your credentials, then run `source env.sh`. The default
model configs read `MODEL_BASE_URL`, `MODEL_API_KEY`, `USER_BASE_URL`,
`USER_API_KEY`, `JUDGER_BASE_URL`, `JUDGER_API_KEY`, and
`BRAVE_SEARCH_API_KEY`.

4. Pull the benchmark Docker image:

```bash
docker pull zzzhr97/pi-bench:latest
```

5. Optional: edit `config/models/<model-id>.yaml` for model-specific names,
endpoints, proxy settings, or timeouts. The filename stem is the `pibench`
model id; see `config/models/example.full.yaml` for the full schema.

<a id="run"></a>
## ▶️ Run

Run from the repository root. Use `--run 3` for
[leaderboard-style reporting](https://simplified-reasoning.github.io/Pi-Bench/#results):

```bash
pibench --model-id deepseek-v3.2 --run 3
```

Each repeat is written to a separate `__runNN` output directory. If a repeated
run is interrupted or fails, rerun only the missing/failed repeat with:

```bash
pibench --model-id deepseek-v3.2 --run 3 --rerun-failed
```

Completed repeats are reused and are not launched again.

Additional examples:

| Goal | Command |
| --- | --- |
| Single trial | `pibench --model-id deepseek-v3.2` |
| Specific user | `pibench --user-id law_trainee --model-id deepseek-v3.2` |
| Multiple models | `pibench --model-id deepseek-v3.2,MiniMax-M2.5` |
| Multiple users and models | `pibench --user-id researcher,law_trainee --model-id deepseek-v3.2,MiniMax-M2.5` |

<a id="outputs"></a>
## 📦 Outputs

Main outputs:

```text
outputs/<model-id>/<user-id>/
```

Container runtime logs:

```text
outputs/<model-id>/<user-id>/run/<timestamp>-runtime/
```

<a id="acknowledgement"></a>
## 🙏 Acknowledgement

Pi-Bench is built on AppWorld and NanoBot. We thank the contributors to these
open-source projects.

<a id="citation"></a>
## 📚 Citation

```bibtex
@misc{zhang2026pibenchevaluatingproactivepersonal,
  title={$\pi$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows},
  author={Haoran Zhang and Luxin Xu and Zhilin Wang and Runquan Gui and Shunkai Zhang and Haodi Lei and Zihao He and Bingsu He and Chicheng Qin and Tong Zhu and Xiaoye Qu and Yang Yang and Yu Cheng and Yafu Li},
  year={2026},
  eprint={2605.14678},
  archivePrefix={arXiv},
  primaryClass={cs.AI},
  url={https://arxiv.org/abs/2605.14678}
}
```
